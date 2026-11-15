# Pilot notes (real runs only; CSVs in prior_results/)

All runs: OpenRouter, anthropic/claude-haiku-5.5 and openai/gpt-6-luna, temperature 0, reasoning effort high,
max_tokens 32000, prompt = question + "FINAL ANSWER: <answer>" line (prior_results/*/run_config.json).

| Family / version | Claude right | GPT right | What we changed because of it |
|---|---|---|---|
| Factory, one line per chart, zone lines drawn (90 tasks, levels 1-5) | 89/90 | 85/90 | Too easy. Hid the 1 and 2 sigma lines (next row) |
| Factory, "plant style": only UCL/CL/LCL (60 tasks) | 57/60 | 57/60 | Still easy. Switched to 6 crossing heads |
| **Factory heads v1.0** (6 similar blue/teal lines, 20 tasks) | 2/20 | 1/20 | Fairness: colours too alike. v1.1 = six distinct colours, same data |
| **Factory heads v1.1** (20 tasks; seeds 401-420) | **4/20** | **2/20** | Kept. Difficulty is the crossings, not colour |
| Fiber prototype (teammate, colour-coded cords) | 8/8 | 8/8 | Too easy: colours matched end to end |
| Fiber v2 (one cord colour, curved, 1 MTP trunk; 8 tasks) | 4/8 | 3/8 | Added a second trunk and the fault question |
| **Fiber v3** (2 trunks; trace + fault; 16 tasks; seeds 11-88) | **8/16** (trace 2/8, fault 6/8) | **2/16** (trace 0/8, fault 2/8) | Kept |
| Brain fair version (8 patients x 5 questions) | rem 8/8, wakes 8/8, **spike 2/8**, audit 8/8, fix 8/8 | 8/8, 8/8, **6/8**, 6/8, 8/8 | Earlier unfair audit result (unclear WASO definition) withdrawn; definitions now printed |
| Cross sections (teammate generator, 6 tasks) | 6/6 (4 needed noise-free re-render) | 5/6 | Easy. Noise made PNGs 16 MB (Claude API refused) -> adapter sets noise 0 |
| Tennis 3D (teammate, 5 tasks, no generator code) | 0/5 high effort, 0/5 capped | 1/5, 0/5 | Teammate's own run: Claude 2/5, GPT 1/5 |

No-picture runs: factory 0/90 and 1/90; brain 0/25 both; tennis 3D all refused.
