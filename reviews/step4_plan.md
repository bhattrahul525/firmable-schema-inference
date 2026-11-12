# Step 4 plan: transform primitives (level P), generated code (level G), sandbox, custom execution

Plan only. Nothing here is built. ARCHITECTURE.md section c is the specification (v2.8 at the time of writing); where this plan
adds detail it says so, and anything that would deviate from section c is listed under "Questions for the owner" rather than decided.

## 1. What step 4 delivers
1. **Level P, parametric primitives** in the engine whitelist: `regex_replace`, `template`, `constant` (new), beside `regex_extract`,
   `map_values`, `split` (already W). `constant` is tagged L3, capped at 0.6, and only allowed for `address.state` and `address.country`.
2. **Level G, generated Python**: a `define_transform` tool, an AST static check, a restricted runtime namespace, a `python -I -S`
   subprocess with a start-up capability probe, batching with bisection, and `custom_transforms` in the config (code, tests, sha256).
3. **`try_transform` for P and G** (today: W only), and **`field_confidence` / `transform_level` per field** (W, P, G) with G capped at 0.8.
4. **Engine custom execution**: the extractor runs generated code only from an APPROVED config, in the same sandbox.
5. **Packet and approval**: the review packet shows level per field and the generated code; the approval hash already covers the config file,
   so code and tests inside `custom_transforms` are covered by construction (a test proves it).
6. **`promote` report**: lists recurring G transforms across onboarded configs, for the human to move into the whitelist.

## 2. Order of work (each step ends with tests, then a mutation check on its new rules)
1. P primitives in `src/engine/transforms.py` and `config.py` (catalogue entries, argument checks, `transform_level`, the `constant` rule,
   `L1_TRANSFORMS` / derivation level for each). Tests: each primitive on edge cases (empty, None, non-string cells, regex groups,
   template placeholders that name a missing column), `constant` refused anywhere but state and country, capped at 0.6, tagged L3.
2. `try_transform` and `validate` accept P (they already run the real engine; mostly schema and `_check_transforms`). The agent prompt and
   the tool descriptions gain the P catalogue (generic text only).
3. `src/engine/sandbox.py`:
   - static check: one function `transform(value)`; allowlist of AST node types, of every name and of every attribute name; forbidden:
     `import`, `while`, `lambda`, `*` and `**`, any attribute starting with `_`, `.format`, `format_map`; limits on lines (40) and nodes;
   - runtime: builtins replaced by the short allowlist (`str int float len min max sorted any all enumerate zip range isinstance`), `re` and date
     parsing as facade objects, regex patterns over 200 characters rejected;
   - process: `python -I -S`, empty environment, temp cwd, JSON on stdin/stdout, limits chosen by a start-up probe of which rlimits really
     stop a violator on this host (Linux: memory, CPU, wall; macOS: CPU and wall; Windows: wall only); the probe result is printed in the packet;
   - extraction: values batched per field, a batch that times out is bisected, offending values become rejects, output size capped.
4. `src/engine/custom.py`: loads `custom_transforms` from a config, checks the stored sha256 of each function, refuses to run from an
   unapproved config, runs the batches through the sandbox, and plugs the result into the same `apply_transforms` path the W and P levels use.
5. `define_transform` tool (level G): arguments are the code, a name, and 3 or more `{input, expected}` test pairs; the harness runs the static
   check, the tests and a sample of training values; it is only accepted when `try_transform` shows W and P stay below 90% parse rate on the same
   column (section c). The tool returns the capped result; the code itself is data in the config, never executed outside the sandbox.
6. Packet, `approve` (shows generated code and tests next to the field, numbers every setting) and the `promote` report.
7. Benchmark columns W/P/G counts and "sandbox capabilities" are already in the report schema; wire real values.

## 3. Sandbox tests (all required by section c, plus the ones step 2 taught us)
Unbounded loop (no `while`; a huge `range` and a recursive-looking comprehension); catastrophic regex `(a+)+$` on long input (the per-call
timeout stopped it in step 2 on POSIX; in the sandbox the wall timeout must do the same, and the Windows gap stays reported); `import`;
dunder and `_`-prefixed access; `.format`; module traversal (`re.sys`, `().__class__`); memory bomb (where the probe says rlimit works,
otherwise reported as unprotected); oversize output; a cell holding an injection string passes through as data; the capability probe itself;
a generated function that raises on some values (those become rejects, the batch survives); a generated function that returns a non-string.
Also: a config whose code was edited after approval is refused (hash mismatch); a config with `custom_transforms` run by the engine without
approval is refused.

## 4. Risks and what I would watch
- **Weakest point:** the sandbox is defence in depth, not a security boundary (section c says so): the subprocess shares the user and the file
  system; file and network blocking rests on the AST allowlist and the facade. The demo must say so out loud. A container or WASM runtime is the production answer.
- **macOS memory limit** is unreliable (`RLIMIT_AS`); the probe may find only CPU and wall. The memory-bomb test must therefore assert what
  the probe says, not a fixed result.
- **Model use of G:** a model may reach for G too early. The gate (W and P below 90% first) is enforced in code; the benchmark reports how often
  G was needed. Dev-draw evidence from this session: none of 11 datasets or the 3+3 live runs needed anything beyond W, so G should stay rare.
- **Replay:** `define_transform` results must be replayable from the trace like every other tool; the code version covers `sandbox.py` and
  `custom.py`; a sandbox probe result that differs on a resumed run is a trace mismatch candidate (decide below).
- **Cost:** none of step 4 needs a model call except the live checks; the sandbox tests run offline. Budget: two live runs on Haiku.

## 5. Re-onboarding the six (step 5) depends on this
The WA bracket names and the QLD comma lists were left unmapped in round 1 because W had no regex_replace / template. Step 4 must make
those two expressible at level P without G; if the live check shows they need G, record it as a result, do not hide it.

## 6. Questions for the owner (not decided here)
1. `define_transform` may emit code that reads columns other than its own (a transform over two cells). Section c defines `transform(value)`
   (one value). Default: one value only; multi-column joins stay `join_nonempty` at level W. Confirm.
2. Should a G transform be allowed on identifier fields (`entity.abn`, `entity.acn`) or only on names, addresses and dates? Default (conservative): not on ABN/ACN; the checksum transforms stay W.
3. The capability-probe result goes in the packet. If the probe differs between the machine that onboarded and the machine that extracts, is that a
   refusal or a warning? Default: a warning in the extract summary (the approved code and hash are what matter).
4. `promote` report: a G transform is "recurring" when the same sha256 appears in two or more configs. Confirm that is the right bar for a human to look.
