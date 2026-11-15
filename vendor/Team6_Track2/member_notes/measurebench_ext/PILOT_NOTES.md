# Pilot notes

Existing project results contain a nine-example pilot for `analog_dial_one_tick_counterfactual` only. These values are copied from `prior_results/model_comparison_summary.json`; no model call was made for this handoff.

| Model route | Model ID | Question type | Correct |
|---|---|---|---:|
| OpenRouter | `anthropic/claude-sonnet-4.5` | `one_tick_counterfactual` | 1/9 (11.1%) |
| Anthropic API | `claude-sonnet-4-5-20250929` | `one_tick_counterfactual` | 1/9 (11.1%) |

The OpenRouter run used temperature 0, high reasoning effort, and `max_tokens=8192`. The Anthropic run used an 8,192 token cap and 4,096 budgeted thinking tokens; its API did not accept temperature 0 with thinking enabled. Per the saved predictions, both routes commonly estimated 0.5 bar or 1.0 bar for the gold 0.2 bar change. This suggests the one-tick comparison is challenging for these pilots; it does not indicate that the task was too easy. No generator changes were made: this export only adds a thin adapter, and the existing sample is too small to justify changing the benchmark logic.

No pilot run exists in the saved project results for the other nine question types.
