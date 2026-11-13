# Step 7 plan: IDF, matcher m2.0, graph, rescore gate, profiles (reduced by step 6)

## Scope after step 6
Registers: Business Names only (data/reference/asic_business_names_trimmed.csv, status Registered).
Cut (designed-not-built): Companies register, T3c, renamed_to edges, ABR lookup (stretch).
Built: rarity-weighted names, m2.0 tiers, graph, rescore gate, both profile types, hand-check sheets.

## Builds (each stops for review; no LLM calls anywhere in step 7)
7a  Names + IDF: src/common/names.py, src/part3_resolve/idf.py. Token IDF over all mentions + register names.
7b  Register bridging + m2.0 tiers: registers.py (Business Names), T1, T1r (via BN names), T2, T3, T4,
    refusals (conflict, >1 holder, generic, different ABNs, person-like without equal ABN). Accept 0.80, loose 0.60.
    T4-postcode starts loose (capped), promotion only after a clean 15-row stratum.
7c  Graph + rescore gate: nodes mention/register record/entity/person; edges same_as, nominee_of
    (+ trustee_for per decision 3). Edge stores id, tier, band, confidence, features, sources, matcher_version,
    previous, human_label. Rescore = pure function; refuses to write if a human Y is demoted or N promoted.
7d  Profiles (src/part4_profiles): cross_source and single_source_register_confirmed, link band always shown;
    people with no ABN never profiled. show.py target under 2 s.
7e  3b deferrals (see decision 6) + generate hand-check sheets for new strata (15 rows each).

## Tests: max 2 per rule the code enforces (IDF down-weights common tokens; each refusal; promotion rule;
rescore refusal; profile type labelling).

## DECISION NEEDED
1. IDF corpus: A) mentions + trimmed register; B) mentions + token counts from the FULL register, computed once
   (one 17 s pass) and cached (git-ignored). Recommend B (the trimmed file only holds rows matching mentions, so
   it distorts rarity).
2. T1r (identifier equal, names differ): A) keep, confirmed when a Business Names row for the same ABN carries
   the other name; B) disable. Recommend A, labelled as register-confirmed, not independent.
3. trustee_for edges: A) build with nominee_of; B) nominee_of only, trustee_for designed-not-built.
   Recommend B unless round-1 code already parses "ATF" patterns (7b prompt checks).
4. renamed_to edges: A) cut; B) build from BN registration dates. Recommend A (no name history without Companies).
5. Matcher version string: A) m2.0 as designed; B) m2.0 with a note "BN only". Recommend A, note in DECISIONS.md.
6. 3b deferrals: (i) ABN with evidence `unverified` cannot support a link above loose: BUILD. (ii) code cap on
   legal_name/trading_name confidence by header word: A) build word list; B) stay prompt-only, record
   designed-not-built. Recommend (i) yes, (ii) B (brittle word lists).

## Amendments (review)
R1 Reference sources: hand-written configs/reference_sources.yaml (id, role: reference, path, keep_where).
   load_mentions skips role=reference; the row filter reads keep_where from it. A register record is never
   a mention and never a second source.
R2 Tiers apply to mention-register pairs too: mention ABN == BN_ABN with agreeing names = T1 (accepted);
   a name-only bridge = T3 (loose, never promoted, since T3c is off).
R3 T1r wording: equal ABN, names differ, one name is a Registered BN name under that ABN. BN confirms one
   side only; record this as weaker than the design.
R4 Holder uniqueness: distinct holders = distinct ABNs, each blank-ABN row counting as its own holder.
   More than one = refused. Report the refused count.
R5 Generic name: defined by IDF (summed token weight, legal-suffix tokens dropped, below a threshold).
   7b reports the distribution; the threshold is hand-set once and recorded before any labels are viewed.
R6 IDF counts distinct normalised names per source (ACT repeats suppliers across 127k invoices).
R7 Move deferral 6(i) (unverified ABN caps a link at loose) into 7b. 7e is hand-check sheets only.
R8 Rescore conflict (m2.0 would demote a round-1 Y or promote an N): stop, "This needs a planning
   decision". Never edit labels.
CHECK at the start of 7b (read-only): (a) how many round-1 labels survive re-extraction; (b) whether
postcode/state are derived from address.full; (c) whether extract carries field evidence state to mentions.