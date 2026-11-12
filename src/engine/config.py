"""Mapping-config structure, structural validation, and the approval lock.

A config is the ONLY thing passed from the agent to the engine. Nothing here knows about any
particular source.

Config shape (written by the agent, never by hand):

  source_id, config_version
  reader:      {format, encoding?, delimiter?, sheet?, header_row?, records_path?, ...}  (all options: engine/readers.py)
  record_id:   {from: [columns]}  or  {hash_row: true}
  observed_at: {from_metadata: <key of metadata.json>}  or  {source, transforms}
  valid_from / valid_to: optional {source, transforms} (per-record dates)
  fields:      [{source (column or list), canonical, transforms, group, mapping_confidence, ...}]
  unmapped:    [{source, reason}]            columns deliberately left out
  needs_transform: [{source, why}]           things the engine cannot do yet
  source_reliability: {identity, address, classification, contact}  (+ _basis text)

Approval lock: configs/<source>.approval.json holds the SHA-256 of the config file the human
approved. The engine refuses to run a config whose hash differs. This is how "never hand-edit
a config" is enforced by code and not just by promise.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from src.engine.readers import ALL_FORMATS
from src.engine.transforms import CATALOGUE

CONFIG_DIR = Path("configs")
ONTOLOGY_PATH = Path("firmable_ontology.yaml")
ENGINE_VERSION = "0.1.0"

# Which kind of claim each canonical field is, for source_reliability (per publisher, per kind).
CLAIM_KIND = {
    "entity.legal_name": "identity", "entity.trading_name": "identity", "entity.abn": "identity",
    "entity.acn": "identity", "entity.nzbn": "identity", "entity.entity_type": "identity",
    "entity.status": "identity", "entity.date_registered": "identity",
    "entity.website": "contact", "entity.industry_code": "classification",
    "address.full": "address", "address.locality": "address", "address.state": "address",
    "address.postcode": "address", "address.country": "address",
}
RELIABILITY_KINDS = ("identity", "address", "classification", "contact")
METADATA_DATE_KEYS = ("resource_last_modified", "dataset_modified", "downloaded_at")
VALUE_ONLY_TRANSFORMS = {"entity_type_from_suffix"}
L1_TRANSFORMS = {"abn", "acn", "parse_date", "map_values", "entity_type_from_suffix",
                 "state_code", "regex_extract", "postcode"}


def load_ontology() -> dict:
    """Canonical field name -> {type, values?, pattern?}, e.g. 'entity.abn'."""
    raw = yaml.safe_load(ONTOLOGY_PATH.read_text())
    out = {}
    for section in ("entity", "address"):
        for name, spec in raw[section].items():
            out[f"{section}.{name}"] = spec
    return out


def derivation_level(transforms: list[dict]) -> str:
    """L0 if the value is carried over (cosmetic cleaning only); L1 if we parsed, validated
    or mapped it deterministically. Computed from the transforms, never claimed by the agent."""
    return "L1" if any(t["name"] in L1_TRANSFORMS for t in transforms) else "L0"


def normalise_transforms(raw) -> list[dict]:
    """Accept 'name', {'name':..., 'arg':...}; parse JSON-encoded args (the LLM returns args
    as strings because structured output cannot express free-form objects)."""
    out = []
    for t in raw or []:
        if isinstance(t, str):
            t = {"name": t}
        arg = t.get("arg")
        if isinstance(arg, str) and arg.strip() != "":
            try:
                arg = json.loads(arg)
            except json.JSONDecodeError:
                pass  # plain strings such as ';' or a regex stay as they are
        elif arg == "":
            arg = None
        out.append({"name": t["name"], "arg": arg})
    return out


def structural_errors(cfg: dict, ontology: dict, headers: list[str] | None, metadata: dict) -> list[str]:
    """Problems that make a config unusable. Returned as plain sentences so they can be fed
    straight back to the model."""
    errs: list[str] = []
    r = cfg.get("reader") or {}
    if r.get("format") not in ALL_FORMATS:
        errs.append(f"reader.format must be one of {ALL_FORMATS}")

    rid = cfg.get("record_id") or {}
    if not (rid.get("from") or rid.get("hash_row")):
        errs.append("record_id needs either `from: [columns]` or `hash_row: true`")

    obs = cfg.get("observed_at") or {}
    if obs.get("from_metadata"):
        if obs["from_metadata"] not in METADATA_DATE_KEYS:
            errs.append(f"observed_at.from_metadata must be one of {METADATA_DATE_KEYS}")
        elif not metadata.get(obs["from_metadata"]):
            errs.append(f"metadata has no value for {obs['from_metadata']!r}")
    elif not obs.get("source"):
        errs.append("observed_at needs `from_metadata` or a `source` column")

    def check_cols(spec_source, where):
        cols = spec_source if isinstance(spec_source, list) else [spec_source]
        for c in cols:
            if headers is not None and c not in headers:
                errs.append(f"{where}: column {c!r} does not exist in the file")

    if rid.get("from"):
        for c in rid["from"]:
            check_cols(c, "record_id")
    for key in ("observed_at", "valid_from", "valid_to"):
        spec = cfg.get(key)
        if spec and spec.get("source"):
            check_cols(spec["source"], key)
            _check_transforms(spec.get("transforms", []), key, errs, is_list_source=False)

    seen = set()
    for i, f in enumerate(cfg.get("fields") or []):
        where = f"fields[{i}] ({f.get('canonical')})"
        if f.get("canonical") not in ontology:
            errs.append(f"{where}: canonical field is not in the ontology. Allowed: {sorted(ontology)}")
        if not f.get("source"):
            errs.append(f"{where}: missing source")
            continue
        check_cols(f["source"], where)
        _check_transforms(f.get("transforms", []), where, errs, is_list_source=isinstance(f["source"], list))
        key = (str(f["source"]), f.get("canonical"), f.get("group", "main"))
        if key in seen:
            errs.append(f"{where}: duplicate mapping of the same source column to the same canonical field")
        seen.add(key)
        c = f.get("mapping_confidence")
        if not isinstance(c, (int, float)) or not 0 <= c <= 1:
            errs.append(f"{where}: mapping_confidence must be a number 0..1")

    rel = cfg.get("source_reliability") or {}
    for k in RELIABILITY_KINDS:
        if not isinstance(rel.get(k), (int, float)) or not 0 <= rel[k] <= 1:
            errs.append(f"source_reliability.{k} must be a number 0..1")
    return errs


def _check_transforms(transforms, where, errs, is_list_source):
    ts = normalise_transforms(transforms)
    for j, t in enumerate(ts):
        if t["name"] not in CATALOGUE:
            errs.append(f"{where}: transform {t['name']!r} is not on the whitelist {sorted(CATALOGUE)}")
        elif t["name"] == "join_nonempty" and (j != 0 or not is_list_source):
            errs.append(f"{where}: join_nonempty must be first and used only when source is a list")
        elif t["name"] in ("split", "regex_extract", "parse_date", "map_values", "join_nonempty") and t["arg"] is None:
            errs.append(f"{where}: transform {t['name']} needs an argument")
    if is_list_source and (not ts or ts[0]["name"] != "join_nonempty"):
        errs.append(f"{where}: a list of source columns needs join_nonempty as its first transform")


# ---- storage, hashing, approval lock -------------------------------------------------------

def config_path(source_id: str) -> Path:
    return CONFIG_DIR / f"{source_id}.yaml"


def approval_path(source_id: str) -> Path:
    return CONFIG_DIR / f"{source_id}.approval.json"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_config(cfg: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True, width=110))


def load_config_file(path: Path) -> dict:
    cfg = yaml.safe_load(path.read_text())
    for f in cfg.get("fields", []):
        f["transforms"] = normalise_transforms(f.get("transforms"))
    for key in ("observed_at", "valid_from", "valid_to"):
        if cfg.get(key) and "transforms" in cfg[key]:
            cfg[key]["transforms"] = normalise_transforms(cfg[key]["transforms"])
    return cfg


def load_approved_config(source_id: str) -> dict:
    """The only way production extraction gets a config. Refuses anything not approved, or
    changed since approval."""
    cp, ap = config_path(source_id), approval_path(source_id)
    if not cp.exists() or not ap.exists():
        raise PermissionError(f"{source_id}: no approved config. Run the agent, then `approve`.")
    approval = json.loads(ap.read_text())
    if approval.get("status") != "approved":
        raise PermissionError(f"{source_id}: config is not approved (status={approval.get('status')!r}).")
    if approval["config_sha256"] != sha256_of(cp):
        raise PermissionError(
            f"{source_id}: {cp} changed after approval (hash mismatch). Configs are written only "
            "by the agent; re-run the agent and re-approve.")
    return load_config_file(cp)


def extractor_version(cfg: dict, cfg_hash: str) -> str:
    """e.g. 'asic_credit_licensee@cfg2.1a2b3c4d+engine0.1.0'. Lets a later matcher or auditor
    know exactly which mapping and engine produced an observation."""
    return f"{cfg['source_id']}@cfg{cfg['config_version']}.{cfg_hash[:8]}+engine{ENGINE_VERSION}"
