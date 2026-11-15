# Pilot notes

All numbers come from the four pilot runs already in the project (copied unchanged into `prior_results/`).
Models: anthropic/claude-haiku-5.5, openai/gpt-6-luna. Settings: temperature 0, max_tokens 32000, reasoning {'effort': 'high'}; every reply complete (no API error, no truncation).

**Note:** these pilots ran on generator versions before devtcu-1.1. The tasks in `tasks/` are new builds; they have not been evaluated (this export makes no model calls).

## Accuracy by model, question and level

| Question | Level | Claude Haiku 5.5 | GPT-6 Luna |
| --- | --- | --- | --- |
| redundant_edge | 1 | 2/2 | 2/2 |
| redundant_edge | 2 | 2/2 | 2/2 |
| redundant_edge | 3 | 2/2 | 2/2 |
| redundant_edge | 4 | 1/1 | 1/1 |
| min_edge_cut | 1 | 2/2 | 2/2 |
| min_edge_cut | 2 | 2/2 | 2/2 |
| min_edge_cut | 3 | 2/2 | 2/2 |
| min_edge_cut | 4 | 2/2 | 2/2 |
| critical_count | 1 | 2/2 | 2/2 |
| critical_count | 2 | 2/2 | 1/2 |
| critical_count | 3 | 2/2 | 2/2 |
| critical_count | 4 | 2/2 | 0/2 |
| critical_count | 5 | 5/5 | 4/5 |
| critical_count | 6 | 4/6 | 2/6 |
| delay_after_failure | 1 | 2/2 | 2/2 |
| delay_after_failure | 2 | 2/2 | 2/2 |
| delay_after_failure | 3 | 2/2 | 2/2 |
| delay_after_failure | 4 | 1/2 | 2/2 |
| delay_after_failure | 5 | 3/3 | 2/3 |
| delay_after_failure | 6 | 10/12 | 6/12 |
| **All** | | **52/57** | **42/57** |

## What was too easy, and what we changed
1. **Pilot 1 (levels 1-4):** Haiku 30/31, Luna 28/31. Multiple choice (A-D) and minimum cut scored 100% for both. Change: added two integer questions that cannot be guessed (critical count, delay after two failures) and one-way arrows (level 4), built so that ignoring direction always changes the answer.
2. **Pilot 2 (level 5, circuit rules at the same size):** Haiku 8/8, Luna 6/8. Rules alone did not trouble Haiku. Change: level 6, a connectogram where one-way curves cross the centre, so every line must be traced through crossings.
3. **Pilot 3 (level 6):** Haiku 9/12, Luna 4/12. A hand check found the marked Y label pressed against a region it did not belong to. Change: marked labels (X, Y, A-D) keep their whole box clear of other regions and lines.
4. **Pilot 4 (level 6 double failure, rebuilt with clearer labels):** Haiku 5/6, Luna 4/6. Clearer labels made the task easier, so part of the earlier failure came from label placement. A hand check then found arrowheads overlapping at a busy region. Change (devtcu-1.1, in this bundle): overlapping arrowheads are resolved by turning or dropping that one connection; answer extraction accepts only the task's option letters; options are a list.

## Failure pattern
Every wrong answer read the picture wrongly (a line followed to the wrong region, an arrow taken the wrong way, a delay misread) and then solved that misread network correctly; none was an arithmetic slip. The most common predicted mistake was ignoring arrow direction.
