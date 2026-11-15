# Pilot notes

The original 15-task mixed pilot was too easy for these models: on the high-effort run, GPT-6 Luna scored 14/15 and Claude Haiku 5.5 scored 15/15. A first 12-case hard price-rule stress run with larger unit-price differences scored GPT-6 Luna 6/12 and Claude Haiku 8/12. The focused 12-task cents-level price stress run exported here scored GPT-6 Luna 10/12 and Claude Haiku 5/12.

The harder cases add up to three amended PO lines, up to three invoice exceptions, a split invoice, effective-date checks, per-line discounts, and cents-level competing rates. Questions request the total merchandise overcharge rather than a line label. The cited model scores are copied from existing runs; no evaluation was run during export.

Claude's API rejects a `temperature` field for this model, so its existing run used high effort and the provider temperature default. GPT-6 Luna used temperature 0 and high reasoning. Both used `max_tokens=16384`; all recorded replies completed without truncation.
