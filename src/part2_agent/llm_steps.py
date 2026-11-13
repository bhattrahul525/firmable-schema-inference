"""The four steps that call the model: inspect, propose, revise, critique.

Every call goes through src/llm.py (cost/tokens/time logged, model chosen there). Each step has a
JSON schema so the model can only answer in a shape the engine understands; the code after the
call still re-checks everything (field names, transforms, columns) because a schema cannot know
what columns exist.
"""

from __future__ import annotations

import json

import yaml

from src import llm
from src.engine.config import (METADATA_DATE_KEYS, ONTOLOGY_PATH, RELIABILITY_KINDS, load_ontology,
                               normalise_transforms)
from src.engine.readers import FORMATS
from src.engine.transforms import CATALOGUE, STEP4A_TRANSFORMS

ROUND1_CATALOGUE = {n: v for n, v in CATALOGUE.items() if n not in STEP4A_TRANSFORMS}   # the fixed list of the original 12

ONTOLOGY = load_ontology()

# ---- shared system prompt (stable across steps, so it is cached) --------------------------------

_catalogue_text = "\n".join(
    f"- {name}" + (f"(arg: {arg})" if arg else "") + f": {doc}" for name, (_, doc, arg) in ROUND1_CATALOGUE.items())

SYSTEM = f"""You are the schema-inference agent of a data-ingestion system for Australian business data.
You map ONE raw public dataset onto a fixed canonical ontology by writing a mapping CONFIG. A generic
engine executes the config; you never write code. Be accurate and conservative: a wrong mapping is worse
than a missing one.

ONTOLOGY (a contract: use these exact field names; fields not listed here do not exist):
{ONTOLOGY_PATH.read_text()}

TRANSFORMS (the only ones available; arguments are given as strings, JSON for lists/objects):
{_catalogue_text}

RULES
1. Observations, not facts. Each mapped field becomes a claim by this source. Do not reconcile or clean beyond the transforms.
2. Never guess. If a column cannot be mapped with confidence, put it in `unmapped` with a reason. If correct mapping would need a transform that does not exist, put it in `needs_transform`.
3. Account for every column: each must be used in `fields`, `record_id`, `observed_at`/`valid_from`/`valid_to`, or listed in `unmapped` / `needs_transform`. Completely empty columns may be ignored.
4. The entity is what each row is about. In contract or invoice data the entity is the SUPPLIER; the government buyer/agency is not mapped (list it as unmapped, reason: government buyer). Individuals (people) listed as licensees are still mapped as legal_name; never infer sole_trader from a person-like name.
5. entity.legal_name is the registered name; entity.trading_name is a name traded under ("trading as", "business name"). Map a name to legal_name only if the data says it is the registered/licensee/supplier name. If a name column holds "Trading (Legal)" style text, say so in `reason` and use regex_extract/split only if the pattern is consistent in the samples.
6. ABN and ACN: always use the `abn` / `acn` transforms (checksum). A column that mixes 11-digit and 9-digit identifiers is mapped twice: once with `abn`, once with `acn`.
7. entity.entity_type: only from an explicit source column (map_values) or, if the source has no such column, `entity_type_from_suffix` on the name column. Otherwise do not map it; the engine records `unknown`.
8. entity.status: use map_values with every raw value you can see in the profile; do not invent mappings for values you cannot interpret (leave them out; they will be rejected and shown to you).
9. entity.industry_code: map the source's own code or description as it is. The engine keeps the raw value alongside. Do not translate to ANZSIC yourself.
10. Dates: parse_date with the exact strptime formats you see. valid_from/valid_to only if the source states when the described licence/status started/ended. date_registered only if a column states when the entity was registered, not when a licence started.
11. observed_at: when the source stated the claim. Use {{"from_metadata": ...}} (one of {list(METADATA_DATE_KEYS)}) unless each row carries its own statement date. For a snapshot register use resource_last_modified.
12. Several entities in one cell (e.g. suppliers separated by ';'): use `split` on every aligned column in the same `group` so items line up by position. A split entity.trading_name is the exception: its items are several names of one entity.
13. group: "main" unless a row genuinely holds two different kinds of entity.
14. mapping_confidence (0-1) is how sure you are the column MEANS that canonical field. Code measures parse quality separately. Use >=0.9 only when column name and sample values clearly agree.
15. record_id: a column or columns that uniquely identify a row (check distinct vs row count in the profile); otherwise hash_row=true.
16. source_reliability (0-1 per claim kind: identity, address, classification, contact): your judgement of how far this publisher can be trusted on that kind of claim (e.g. a statutory regulator's register is high for identity). It is a judgement, not a measurement; say why in source_reliability_basis. Use 0.5 when you cannot tell.
"""

# ---- schemas ----------------------------------------------------------------------------------

_T = {"type": "object", "additionalProperties": False, "required": ["name", "arg"],
      "properties": {"name": {"type": "string", "enum": sorted(ROUND1_CATALOGUE)}, "arg": {"type": "string"}}}
_COL_REASON = {"type": "object", "additionalProperties": False, "required": ["source", "reason"],
               "properties": {"source": {"type": "string"}, "reason": {"type": "string"}}}
_PER_ROW_DATE = {"type": "object", "additionalProperties": False, "required": ["source", "transforms"],
                 "properties": {"source": {"type": "string", "description": "column name, or empty string if not used"},
                                "transforms": {"type": "array", "items": _T}}}

MAPPING_PROPERTIES = {
    "record_id": {"type": "object", "additionalProperties": False, "required": ["columns", "hash_row", "reason"],
                  "properties": {"columns": {"type": "array", "items": {"type": "string"}},
                                 "hash_row": {"type": "boolean"}, "reason": {"type": "string"}}},
    "observed_at": {"type": "object", "additionalProperties": False, "required": ["from_metadata", "source", "transforms"],
                    "properties": {"from_metadata": {"type": "string", "enum": [""] + list(METADATA_DATE_KEYS)},
                                   "source": {"type": "string"}, "transforms": {"type": "array", "items": _T}}},
    "valid_from": _PER_ROW_DATE,
    "valid_to": _PER_ROW_DATE,
    "fields": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["source", "canonical", "transforms", "group", "mapping_confidence", "reason"],
        "properties": {
            "source": {"type": "array", "items": {"type": "string"}, "description": "one column; several only with join_nonempty"},
            "canonical": {"type": "string", "enum": sorted(ONTOLOGY)},
            "transforms": {"type": "array", "items": _T},
            "group": {"type": "string"},
            "mapping_confidence": {"type": "number"},
            "reason": {"type": "string"}}}},
    "unmapped": {"type": "array", "items": _COL_REASON},
    "needs_transform": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["source", "why"],
        "properties": {"source": {"type": "string"}, "why": {"type": "string"}}}},
    "source_reliability": {"type": "object", "additionalProperties": False, "required": list(RELIABILITY_KINDS),
                           "properties": {k: {"type": "number"} for k in RELIABILITY_KINDS}},
    "source_reliability_basis": {"type": "string"},
}
PROPOSE_SCHEMA = {"type": "object", "additionalProperties": False,
                  "required": list(MAPPING_PROPERTIES), "properties": MAPPING_PROPERTIES}

REVISE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": list(MAPPING_PROPERTIES) + ["changes", "warning_responses"],
    "properties": {**MAPPING_PROPERTIES,
                   "changes": {"type": "array", "items": {
                       "type": "object", "additionalProperties": False, "required": ["what", "why"],
                       "properties": {"what": {"type": "string"}, "why": {"type": "string"}}}},
                   "warning_responses": {"type": "array", "items": {
                       "type": "object", "additionalProperties": False, "required": ["check_id", "action", "reason"],
                       "properties": {"check_id": {"type": "string"},
                                      "action": {"type": "string", "enum": ["changed", "kept"]},
                                      "reason": {"type": "string"}}}}}}

INSPECT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["what_it_is", "one_row_is", "contains_business_entities", "format", "encoding", "delimiter",
                 "sheet", "header_row", "records_path"],
    "properties": {
        "what_it_is": {"type": "string", "description": "one sentence: what this dataset is"},
        "one_row_is": {"type": "string", "description": "what one record represents"},
        "contains_business_entities": {"type": "boolean"},
        "format": {"type": "string", "enum": list(FORMATS)},
        "encoding": {"type": "string"}, "delimiter": {"type": "string", "description": "csv/tsv only, else empty"},
        "sheet": {"type": "string", "description": "xlsx only, else empty"},
        "header_row": {"type": "integer", "description": "1-based row holding the column names (csv/xlsx)"},
        "records_path": {"type": "string", "description": "json only: dotted path to the list of records, empty if top level"}}}

CRITIQUE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["issues", "overall"],
    "properties": {"issues": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["field", "problem", "suggested_fix"],
        "properties": {"field": {"type": "string"}, "problem": {"type": "string"}, "suggested_fix": {"type": "string"}}}},
        "overall": {"type": "string"}}}


# ---- helpers ----------------------------------------------------------------------------------

def meta_summary(metadata: dict) -> dict:
    keys = ("title", "organisation", "licence", "licence_flag", "resource_name", "resource_format",
            "resource_last_modified", "dataset_modified", "file")
    return {k: metadata.get(k) for k in keys}


def reader_from_inspect(inspect: dict) -> dict:
    reader = {"format": inspect["format"], "encoding": inspect["encoding"] or "utf-8-sig"}
    if inspect["delimiter"]:
        reader["delimiter"] = inspect["delimiter"]
    if inspect["sheet"]:
        reader["sheet"] = inspect["sheet"]
    if inspect["format"] in ("csv", "tsv", "xlsx"):
        reader["header_row"] = inspect["header_row"]
    if inspect["records_path"]:
        reader["records_path"] = inspect["records_path"]
    return reader


def to_config(p: dict, inspect: dict, source_id: str, version: int) -> dict:
    """Model answer (schema shape) -> engine config shape."""
    def date_spec(spec):
        return {"source": spec["source"], "transforms": normalise_transforms(spec["transforms"])} if spec["source"] else None

    rid = p["record_id"]
    obs = p["observed_at"]
    reader = reader_from_inspect(inspect)

    cfg = {
        "source_id": source_id,
        "config_version": version,
        "what_it_is": inspect["what_it_is"],
        "one_row_is": inspect["one_row_is"],
        "reader": reader,
        "record_id": {"from": rid["columns"]} if rid["columns"] and not rid["hash_row"] else {"hash_row": True},
        "record_id_reason": rid["reason"],
        "observed_at": {"from_metadata": obs["from_metadata"]} if obs["from_metadata"] else
                       {"source": obs["source"], "transforms": normalise_transforms(obs["transforms"])},
        "valid_from": date_spec(p["valid_from"]),
        "valid_to": date_spec(p["valid_to"]),
        "fields": [{
            "source": f["source"][0] if len(f["source"]) == 1 else f["source"],
            "canonical": f["canonical"],
            "transforms": normalise_transforms(f["transforms"]),
            "group": f["group"] or "main",
            "mapping_confidence": f["mapping_confidence"],
            "reason": f["reason"],
        } for f in p["fields"]],
        "unmapped": p["unmapped"],
        "needs_transform": p["needs_transform"],
        "source_reliability": p["source_reliability"],
        "source_reliability_basis": p["source_reliability_basis"],
    }
    for k in ("valid_from", "valid_to"):
        if cfg[k] is None:
            del cfg[k]
    return cfg


def _arg_str(arg) -> str:
    return "" if arg is None else (arg if isinstance(arg, str) else json.dumps(arg))


def _ts(transforms) -> list[dict]:
    return [{"name": t["name"], "arg": _arg_str(t["arg"])} for t in (transforms or [])]


def config_for_prompt(cfg: dict) -> str:
    """The config in the same shape the model answers in (the inverse of to_config), so the model
    edits what it sees. Engine-only bookkeeping (validation numbers etc.) is left out."""
    rid, obs = cfg["record_id"], cfg["observed_at"]

    def date_spec(spec):
        return {"source": spec["source"], "transforms": _ts(spec["transforms"])} if spec else {"source": "", "transforms": []}

    return json.dumps({
        "record_id": {"columns": rid.get("from", []), "hash_row": bool(rid.get("hash_row")),
                      "reason": cfg.get("record_id_reason", "")},
        "observed_at": {"from_metadata": obs.get("from_metadata", ""), "source": obs.get("source", ""),
                        "transforms": _ts(obs.get("transforms"))},
        "valid_from": date_spec(cfg.get("valid_from")),
        "valid_to": date_spec(cfg.get("valid_to")),
        "fields": [{"source": f["source"] if isinstance(f["source"], list) else [f["source"]],
                    "canonical": f["canonical"], "transforms": _ts(f["transforms"]), "group": f["group"],
                    "mapping_confidence": f["mapping_confidence"], "reason": f.get("reason", "")}
                   for f in cfg["fields"]],
        "unmapped": cfg["unmapped"], "needs_transform": cfg["needs_transform"],
        "source_reliability": cfg["source_reliability"],
        "source_reliability_basis": cfg.get("source_reliability_basis", ""),
    }, indent=1, default=str)


# ---- step 1: inspect ---------------------------------------------------------------------------

def inspect_step(source_id: str, metadata: dict, raw_preview: list, sheets: list[str] | None,
                 previous_error: str | None = None) -> dict:
    prompt = (
        "Work out what this raw file is and how to read it. Look at the first raw lines/rows below.\n"
        f"Dataset metadata: {json.dumps(meta_summary(metadata))}\n"
        f"Sheets (xlsx): {sheets}\n"
        f"Raw preview (each item is one raw row/line; None = empty cell):\n{json.dumps(raw_preview, default=str)[:6000]}\n\n"
        "Return reader settings. header_row is the 1-based row with the column NAMES (there may be title or "
        "blank rows above it). If the file holds no business or organisation entities, set contains_business_entities=false."
    )
    if previous_error:
        prompt += f"\n\nYour previous reader settings failed when tried on the real file: {previous_error}\nFix them."
    return llm.call(prompt, step="part2.inspect", source_id=source_id, system=SYSTEM, schema=INSPECT_SCHEMA).data


# ---- step 3: propose ---------------------------------------------------------------------------

def propose_step(source_id: str, label: str, metadata: dict, inspect: dict, profile: list[dict],
                 sample_rows: list[dict], n_rows: int) -> dict:
    prompt = (
        f"Propose the mapping config for this dataset.\n\n"
        f"Dataset metadata: {json.dumps(meta_summary(metadata))}\n"
        f"What it is: {inspect['what_it_is']}\nOne row is: {inspect['one_row_is']}\nRows in file: {n_rows}\n\n"
        f"COLUMN PROFILE (whole file; fill_rate, distinct values, common values, shapes):\n{json.dumps(profile)}\n\n"
        f"SAMPLE ROWS (non-blank cells only):\n" + "\n".join(json.dumps(r) for r in sample_rows) + "\n\n"
        "Write the mapping. Remember: unmapped/needs_transform for anything you cannot map with confidence; "
        "every column accounted for."
    )
    return llm.call(prompt, step=f"part2.propose_{label}", source_id=source_id, system=SYSTEM,
                    schema=PROPOSE_SCHEMA, effort="medium").data


# ---- step 5: revise ----------------------------------------------------------------------------

def revise_step(source_id: str, label: str, cfg: dict, feedback_text: str, profile: list[dict],
                metadata: dict) -> dict:
    prompt = (
        "Your mapping config for this dataset was tested on rows you had not seen. Fix it.\n\n"
        f"Dataset metadata: {json.dumps(meta_summary(metadata))}\n\n"
        f"CURRENT CONFIG:\n{config_for_prompt(cfg)}\n\n"
        f"{feedback_text}\n\n"
        f"COLUMN PROFILE (for reference):\n{json.dumps(profile)}\n\n"
        "Return the FULL corrected config in the same schema, plus `changes` (what you changed and why) and "
        "`warning_responses` (for each meaning warning above: action 'changed' or 'kept' with a reason). "
        "Change only what the report justifies. If a field cannot be made to work, remove it from `fields` and "
        "list its column under `unmapped` with the reason. Never invent a mapping to make a number look better."
    )
    return llm.call(prompt, step=f"part2.revise_{label}", source_id=source_id, system=SYSTEM,
                    schema=REVISE_SCHEMA, effort="medium").data


# ---- step 6: critique --------------------------------------------------------------------------

def critique_step(source_id: str, cfg: dict, examples: list[dict]) -> dict:
    prompt = (
        "You are reviewing a finished mapping for MEANING errors that code cannot detect (e.g. legal and trading "
        "name swapped, a column mapped to a field it does not mean, a status mapped the wrong way round). Below, "
        "each example shows a raw row and the observations the engine produced from it.\n\n"
        f"CONFIG:\n{config_for_prompt(cfg)}\n\n"
        "EXAMPLES:\n" + "\n".join(json.dumps(e, default=str) for e in examples) + "\n\n"
        "List only real problems you can point to in the examples; do not invent issues. If the mapping looks right, "
        "return an empty `issues` list."
    )
    return llm.call(prompt, step="part2.critique", source_id=source_id, system=SYSTEM,
                    schema=CRITIQUE_SCHEMA, effort="medium").data
