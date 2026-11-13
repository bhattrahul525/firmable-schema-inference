# Step 6 part A summary
- Outcome: validated_config (zip read OK, no CSV pre-extract needed). Model claude-haiku-5-5, resource-index 2 (Current ZIP), source_id asic_business_names.
- Cost $0.0092; 10 turns / 10 tool calls; agent 178.7s, wall-clock 200.3s (incl. 72 MB download).
- Held-out parse rates (3,312,255 rows read): BN_NAME->entity.trading_name 100.0% (field conf 0.60); BN_ABN->entity.abn 100.0% (0.90). Duplicate record ids: 0.
- Critic: 1 blocking + 3 advisory flags (address.state<-BN_STATE_OF_REG; valid_from; valid_to; no licence entry). The final config already leaves state, dates unmapped; the flags look stale vs the final mapping, check at approval.
- Note: BN_STATUS is left unmapped, so the plan's "Registered rows only" rule cannot come from this config; the row filter must read the raw status column.
- Sizes: zip 71,924,719 B (72 MB); CSV inside 247,496,423 B (247 MB), tab-delimited, utf-8-sig.
- Files: outputs/step6/configs/asic_business_names.{yaml,review.md}; zip data/raw/reference/ and data/raw/sources/asic_business_names/ (agent's own copy); licence docs/asic_business_names_licence.md. Not approved.
