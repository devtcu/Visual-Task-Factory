# Inventory: devtcu (Brain Connections)

**Domain:** synthetic brain connectivity diagrams (connectomes) with resilience questions: what still works when
connections fail. Neuroscience-inspired only: region names are real abbreviations (V1, M1, Hipp), the wiring and
delays are generated. No question asks for a diagnosis.

**Real-world sources imitated:** node-and-link connectome figures and circular "connectogram" figures from
connectomics papers, and neural circuit diagrams that mark inhibitory connections with a flat bar end (see REFERENCES.md).

## Entry points
| Job | Command / function |
| --- | --- |
| Generate one task | `generators.devtcu.adapter.generate_task(seed, question_type, out_dir)` |
| Validate one task | `generators.devtcu.adapter.validate_task(task, out_dir)` |
| Build this bundle's task set | `python build_tasks.py tasks` (run from `handoff/devtcu/`) |
| Rebuild exact seeds | `python build_tasks.py OUT --seeds tasks/seeds_used.json` |
| Evaluate (not run here) | `python -m eval.run TASK_DIR RESULTS_DIR` with `OPENROUTER_API_KEY` set |

Original repo equivalents: `python -m generate.build grid|fresh ...` and `python -m eval.run ...`.

## Question types (21 = 4 questions x the levels each supports)
| Question | What the reader must do | Answer type | Levels |
| --- | --- | --- | --- |
| `redundant_edge` | Of 4 marked connections, find the one whose removal keeps the fastest route's length | multiple_choice (A-D) | 1-4 |
| `min_edge_cut` | Fewest connections whose removal disconnects IN from OUT | integer | 1-4, 6 |
| `critical_count` | Test every connection: how many, removed alone, lengthen the fastest route | integer | 1-6 |
| `delay_after_failure` | Marked connections X and Y fail together: new fastest delay | integer (ms or steps) | 1-6 |

| Level | Picture |
| --- | --- |
| 1 | 8-10 regions, plain two-way lines, every connection one step |
| 2 | + conduction delays printed on lines |
| 3 | + tied fastest routes |
| 4 | + one-way arrows; two-way pairs as two curved arrows (ignoring direction always changes the answer) |
| 5 | + circuit rules: inhibitory connections (flat bar) carry no signal, a lesioned region blocks, regions add processing delay |
| 6 | connectogram: regions on a circle, one-way curves crossing the centre |

Question type names in the records are `<question>_L<level>`, e.g. `critical_count_L6`.

## Answer types and tolerances
`multiple_choice` (options list, answer = letter) and `integer`. All answers are exact integers or letters computed
from the graph, so no tolerance is used.

## Language and dependencies
Python 3.11. numpy, matplotlib, networkx, scipy, pillow (versions in requirements.txt); requests for eval only.
Fonts: matplotlib's bundled DejaVu Sans, no system fonts. System packages: none. The shared OCR check
(`ocr_numbers`) needs the tesseract binary and is SKIPPED (reported as passing) when it is absent.

## State
Works: generation for all 21 types, a second solver (hand-written Dijkstra and max-flow, no NetworkX), pixel check
that every stored line, arrowhead and inhibitory bar is drawn and no phantom line exists, label legibility and
clearance rules, called-shot traps, evaluation code with retries and called-shot matching.
Unfinished: no Dockerfile or merged README (merge step); hard levels generate slowly (under 1% of candidate layouts
pass at level 5-6 double failure); OCR check skipped without tesseract.
