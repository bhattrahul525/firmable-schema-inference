"""Print the profiles that contain a mention from one source, compactly.  python -m src.part4_profiles.show <source_id>
Reads outputs/profiles/graph_profiles.jsonl only (build it with `python -m src.part4_profiles.profiles`). No network, no LLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

FILE = Path("outputs/profiles/graph_profiles.jsonl")


def render(p: dict) -> str:
    lines = [f"{p['profile_id']}  [{p['type']}]  trust: {p['trust']}  sources: {', '.join(p['sources'])}"
             + (f"  register: {', '.join(p['register_records'])} (not a source)" if p["register_records"] else ""),
             "  links: " + "; ".join(f"{l['tier']} {l['band']} {l['link_confidence']}" + (f" label={l['human_label']}" if l["human_label"] else "")
                                       for l in p["links"])]
    for f, r in p["fields"].items():
        lines.append(f"  {f}  ({r['decided']})")
        for v in r["values"]:
            c = v["claims"][0]
            lines.append(f"    {'*' if v['chosen'] else ' '} {v['value']}   score {v['score']}  from {', '.join(v['sources'])} row {c['source_record_id']} observed {c['observed_at']}")
    if p["address"]:
        lines.append(f"  address  ({p['address']['decided']})")
        for v in p["address"]["values"]:
            lines.append(f"    {'*' if v['chosen'] else ' '} {', '.join(str(x) for x in v['value'].values())}   score {v['score']}  from {', '.join(v['sources'])}")
    if p["trading_names"]:
        lines.append("  trading names: " + "; ".join(t["value"] for t in p["trading_names"]))
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m src.part4_profiles.show <source_id>")
    if not FILE.exists():
        raise SystemExit(f"{FILE} missing: run `python -m src.part4_profiles.profiles` first")
    hits = [p for p in map(json.loads, FILE.open()) if any(m["source_id"] == sys.argv[1] for m in p["members"])]
    print(f"{len(hits)} profile(s) contain a mention from {sys.argv[1]}\n")
    print("\n\n".join(render(p) for p in hits[:20]))
    if len(hits) > 20:
        print(f"\n... {len(hits) - 20} more (first 20 shown)")


if __name__ == "__main__":
    main()
