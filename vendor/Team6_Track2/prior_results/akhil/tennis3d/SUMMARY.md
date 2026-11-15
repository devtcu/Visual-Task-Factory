# Tennis 3D corner call: results (5 tasks, 2 models, 2 settings)

Answer = signed cm from bounce to the nearest singles boundary (positive = IN). Tolerance per task as given.

| Task | Answer | Claude high effort (32k) | Claude capped (64k, think<=40k) | GPT high effort (32k) | GPT capped (64k, think<=40k) |
|---|---|---|---|---|---|
| tennis3d_01 | 16.4 ±10 | cut off (rerun at 64k: -55) | 380 | **18 ✓** | 5 |
| tennis3d_02 | 11.1 ±5 | -20 | 5 | -15 | -28 |
| tennis3d_03 | 41.5 ±5 | cut off (rerun at 64k: 65) | 11 | 0 | 10 |
| tennis3d_04 | 25.8 ±10 | 10 | -5 | -27 | -10 |
| tennis3d_05 | 28.0 ±5 | cut off (also cut off at 64k) | 15 | -10 | 20 |
| **Right** | | **0/5** | **0/5** | **1/5** | **0/5** |

No-picture run (high effort): both models refused all 5 (10/10), so the images are needed.

Notes
- Cut off = Claude spent the whole token limit thinking and wrote no answer. Capping thinking at 40k
  inside a 64k limit fixed this: every capped reply finished.
- Capped runs thought much less (Claude 3-7k tokens, GPT 4-6k) than high effort (Claude 28-32k+, GPT 9-15k).
  More thinking did not help: neither setting gets above 1/5.
- Every ball is IN, yet 8 of the 19 numeric answers (counting the 64k reruns) called it OUT (negative).
- Raw replies: raw/ (high effort), raw_64k/ (Claude reruns), raw_capped/ (capped, both models), blind_responses.csv.
