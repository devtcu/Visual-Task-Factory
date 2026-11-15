# Team 6 Visual Task Factory

Innodata Hackathon. Pipelines that draw realistic images from
structured data, ask a question whose answer is computed by code, check that the image matches the data, and test
Claude Haiku 5.5 and GPT-6 Luna on them. This repo holds the team's merged submission draft, the Brain Connections
handoff, the tennis tasks, and a local dashboard that runs them all.

## What is here
| Path | What it is |
| --- | --- |
| `app.py`, `gen_worker.py`, `static/` | The dashboard: browse tasks, generate a fresh one live, ask both models |
| `vendor/Team6_Track2/` | The team's merged 7-pipeline draft (SPC charts, fiber patching, EEG, roadway cross sections, finance, instrument reading, visual reconstruction) |
| `vendor/devtcu/` | Brain Connections: brain-network resilience tasks (generator, checks, 105 tasks, pilot results, notes) |
| `vendor/tennis/` | Tennis 3D line-call tasks (5 tasks, 3 camera views each; generator not included) |
| `original-archives/` | The archives these folders were unpacked from, unchanged apart from their names: `team6-merged-submission-draft.zip` (received as Team6_Track2.zip), `brain-connections-handoff.zip` (handoff_devtcu.zip), `tennis-3d-line-call-tasks.zip` (TENNIS-3D.zip) |

## Run the dashboard
Needs macOS or Linux with Python 3.10+ (on Windows use WSL).
```bash
./setup.sh      # once: private Python environment + headless browser (2-5 minutes)
./start.sh      # asks for an OpenRouter key (hidden, never saved), then open http://localhost:8765
```
Without a key everything works except asking the models. See `vendor/devtcu/REPORT.md` and
`vendor/Team6_Track2/README.md` for each part's own commands.

## Brain Connections in brief
Synthetic brain-network diagrams with resilience questions: which connection can fail safely, the fewest cuts to
disconnect input from output, how many connections are critical, and the delay after two failures. Six difficulty
levels end in a circular connectogram with one-way curves crossing the centre. Every answer is computed by NetworkX
and checked by an independent solver; each task records in advance the wrong answer each common mistake produces.
Pilot results (57 tasks): Haiku 52/57, Luna 42/57; at level 6, Haiku 14/18 and Luna 8/18. Every miss came from
misreading the picture, most often an arrow's direction.
