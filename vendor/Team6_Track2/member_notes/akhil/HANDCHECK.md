# Hand check

One note per task. 'Valid' = validate_task passed (answer recomputed independently from the data, image present and under the 10 MB limit). Families are generated from data, so every image matches its data by construction; I looked at one image per family by eye (heads 410 from the earlier run, fiber 11 fault, brain spike, xsec hard).

**akhil_heads_401** (seed 401, answer `[1, 29]`): valid = True. Six crossing head lines; the first signal is a quiet run (8 in a row / 4 of 5 beyond 1 sigma) on one head, earlier than an obvious spike on another. Needs following one line through crossings and counting samples (labels every 10th). Realistic: rotary-filler per-head SPC chart. Answer = first signal under the 4 printed rules, recomputed independently.

**akhil_heads_402** (seed 402, answer `[2, 8]`): valid = True. Six crossing head lines; the first signal is a quiet run (8 in a row / 4 of 5 beyond 1 sigma) on one head, earlier than an obvious spike on another. Needs following one line through crossings and counting samples (labels every 10th). Realistic: rotary-filler per-head SPC chart. Answer = first signal under the 4 printed rules, recomputed independently.

**akhil_heads_403** (seed 403, answer `[6, 50]`): valid = True. Six crossing head lines; the first signal is a quiet run (8 in a row / 4 of 5 beyond 1 sigma) on one head, earlier than an obvious spike on another. Needs following one line through crossings and counting samples (labels every 10th). Realistic: rotary-filler per-head SPC chart. Answer = first signal under the 4 printed rules, recomputed independently.

**akhil_heads_404** (seed 404, answer `[6, 8]`): valid = True. Six crossing head lines; the first signal is a quiet run (8 in a row / 4 of 5 beyond 1 sigma) on one head, earlier than an obvious spike on another. Needs following one line through crossings and counting samples (labels every 10th). Realistic: rotary-filler per-head SPC chart. Answer = first signal under the 4 printed rules, recomputed independently.

**akhil_heads_405** (seed 405, answer `[3, 9]`): valid = True. Six crossing head lines; the first signal is a quiet run (8 in a row / 4 of 5 beyond 1 sigma) on one head, earlier than an obvious spike on another. Needs following one line through crossings and counting samples (labels every 10th). Realistic: rotary-filler per-head SPC chart. Answer = first signal under the 4 printed rules, recomputed independently.

**akhil_fiber_trace_11** (seed 11, answer `7`): valid = True. Single-colour cords through 3 patch stages and 2 MTP trunks (printed TIA-568 polarity rules). Needs tracing each cord through crossings and applying two rules in order. Realistic as-built patching diagram. Answer recomputed from the stored permutations.

**akhil_fiber_trace_22** (seed 22, answer `8`): valid = True. Single-colour cords through 3 patch stages and 2 MTP trunks (printed TIA-568 polarity rules). Needs tracing each cord through crossings and applying two rules in order. Realistic as-built patching diagram. Answer recomputed from the stored permutations.

**akhil_fiber_trace_33** (seed 33, answer `10`): valid = True. Single-colour cords through 3 patch stages and 2 MTP trunks (printed TIA-568 polarity rules). Needs tracing each cord through crossings and applying two rules in order. Realistic as-built patching diagram. Answer recomputed from the stored permutations.

**akhil_fiber_trace_44** (seed 44, answer `7`): valid = True. Single-colour cords through 3 patch stages and 2 MTP trunks (printed TIA-568 polarity rules). Needs tracing each cord through crossings and applying two rules in order. Realistic as-built patching diagram. Answer recomputed from the stored permutations.

**akhil_fiber_trace_55** (seed 55, answer `4`): valid = True. Single-colour cords through 3 patch stages and 2 MTP trunks (printed TIA-568 polarity rules). Needs tracing each cord through crossings and applying two rules in order. Realistic as-built patching diagram. Answer recomputed from the stored permutations.

**akhil_fiber_fault_11** (seed 11, answer `6`): valid = True. One cord marked CUT; which GPU port lost its link. Needs a backward trace through both trunk rules. CUT mark placed only where no other cord is within 0.45 units, so the cut cord is unambiguous. Answer recomputed from permutations.

**akhil_fiber_fault_22** (seed 22, answer `8`): valid = True. One cord marked CUT; which GPU port lost its link. Needs a backward trace through both trunk rules. CUT mark placed only where no other cord is within 0.45 units, so the cut cord is unambiguous. Answer recomputed from permutations.

**akhil_fiber_fault_33** (seed 33, answer `3`): valid = True. One cord marked CUT; which GPU port lost its link. Needs a backward trace through both trunk rules. CUT mark placed only where no other cord is within 0.45 units, so the cut cord is unambiguous. Answer recomputed from permutations.

**akhil_fiber_fault_44** (seed 44, answer `8`): valid = True. One cord marked CUT; which GPU port lost its link. Needs a backward trace through both trunk rules. CUT mark placed only where no other cord is within 0.45 units, so the cut cord is unambiguous. Answer recomputed from permutations.

**akhil_fiber_fault_55** (seed 55, answer `6`): valid = True. One cord marked CUT; which GPU port lost its link. Needs a backward trace through both trunk rules. CUT mark placed only where no other cord is within 0.45 units, so the cut cord is unambiguous. Answer recomputed from permutations.

**akhil_brain_p304_rem_latency** (seed 304, answer `91.5`): valid = True. Hypnogram reading with the definition printed. Easy rung (both models 8/8 in the pilot). Tolerance +/-5 min stated.

**akhil_brain_p305_rem_latency** (seed 305, answer `74.0`): valid = True. Hypnogram reading with the definition printed. Easy rung (both models 8/8 in the pilot). Tolerance +/-5 min stated.

**akhil_brain_p306_rem_latency** (seed 306, answer `73.5`): valid = True. Hypnogram reading with the definition printed. Easy rung (both models 8/8 in the pilot). Tolerance +/-5 min stated.

**akhil_brain_p307_rem_latency** (seed 307, answer `84.0`): valid = True. Hypnogram reading with the definition printed. Easy rung (both models 8/8 in the pilot). Tolerance +/-5 min stated.

**akhil_brain_p308_rem_latency** (seed 308, answer `110.0`): valid = True. Hypnogram reading with the definition printed. Easy rung (both models 8/8 in the pilot). Tolerance +/-5 min stated.

**akhil_brain_p304_awakenings** (seed 304, answer `7`): valid = True. Count W periods after sleep onset, definition printed (brief ones count). Easy rung (8/8 both).

**akhil_brain_p305_awakenings** (seed 305, answer `6`): valid = True. Count W periods after sleep onset, definition printed (brief ones count). Easy rung (8/8 both).

**akhil_brain_p306_awakenings** (seed 306, answer `7`): valid = True. Count W periods after sleep onset, definition printed (brief ones count). Easy rung (8/8 both).

**akhil_brain_p307_awakenings** (seed 307, answer `6`): valid = True. Count W periods after sleep onset, definition printed (brief ones count). Easy rung (8/8 both).

**akhil_brain_p308_awakenings** (seed 308, answer `6`): valid = True. Count W periods after sleep onset, definition printed (brief ones count). Easy rung (8/8 both).

**akhil_brain_p304_spike** (seed 304, answer `"T4"`): valid = True. Bipolar-montage EEG page: locate the phase reversal of one sharp wave (eye blink is a decoy). Needs channel-pair reasoning on polarity. Hard for Claude (2/8 right) in the pilot.

**akhil_brain_p305_spike** (seed 305, answer `"F8"`): valid = True. Bipolar-montage EEG page: locate the phase reversal of one sharp wave (eye blink is a decoy). Needs channel-pair reasoning on polarity. Hard for Claude (2/8 right) in the pilot.

**akhil_brain_p306_spike** (seed 306, answer `"T5"`): valid = True. Bipolar-montage EEG page: locate the phase reversal of one sharp wave (eye blink is a decoy). Needs channel-pair reasoning on polarity. Hard for Claude (2/8 right) in the pilot.

**akhil_brain_p307_spike** (seed 307, answer `"T6"`): valid = True. Bipolar-montage EEG page: locate the phase reversal of one sharp wave (eye blink is a decoy). Needs channel-pair reasoning on polarity. Hard for Claude (2/8 right) in the pilot.

**akhil_brain_p308_spike** (seed 308, answer `"P3"`): valid = True. Bipolar-montage EEG page: locate the phase reversal of one sharp wave (eye blink is a decoy). Needs channel-pair reasoning on polarity. Hard for Claude (2/8 right) in the pilot.

**akhil_brain_p304_audit** (seed 304, answer `["Wake after sleep onset", "N2", "N3"]`): valid = True. Check every row of a PSG report against the hypnogram using printed definitions; list wrong rows. Planted bugs are subtle (e.g. WASO without the final wake). Medium/hard.

**akhil_brain_p305_audit** (seed 305, answer `["Wake after sleep onset", "N2", "N3"]`): valid = True. Check every row of a PSG report against the hypnogram using printed definitions; list wrong rows. Planted bugs are subtle (e.g. WASO without the final wake). Medium/hard.

**akhil_brain_p306_audit** (seed 306, answer `["Wake after sleep onset", "N2", "N3"]`): valid = True. Check every row of a PSG report against the hypnogram using printed definitions; list wrong rows. Planted bugs are subtle (e.g. WASO without the final wake). Medium/hard.

**akhil_brain_p307_audit** (seed 307, answer `["Wake after sleep onset", "N2", "N3"]`): valid = True. Check every row of a PSG report against the hypnogram using printed definitions; list wrong rows. Planted bugs are subtle (e.g. WASO without the final wake). Medium/hard.

**akhil_brain_p308_audit** (seed 308, answer `["Wake after sleep onset", "N2", "N3"]`): valid = True. Check every row of a PSG report against the hypnogram using printed definitions; list wrong rows. Planted bugs are subtle (e.g. WASO without the final wake). Medium/hard.

**akhil_brain_p304_find_fix** (seed 304, answer `33.5`): valid = True. Exactly one wrong value in the report; give its correct value from the hypnogram. Tolerance stated in the question.

**akhil_brain_p305_find_fix** (seed 305, answer `38.0`): valid = True. Exactly one wrong value in the report; give its correct value from the hypnogram. Tolerance stated in the question.

**akhil_brain_p306_find_fix** (seed 306, answer `58.0`): valid = True. Exactly one wrong value in the report; give its correct value from the hypnogram. Tolerance stated in the question.

**akhil_brain_p307_find_fix** (seed 307, answer `41.5`): valid = True. Exactly one wrong value in the report; give its correct value from the hypnogram. Tolerance stated in the question.

**akhil_brain_p308_find_fix** (seed 308, answer `53.0`): valid = True. Exactly one wrong value in the report; give its correct value from the hypnogram. Tolerance stated in the question.

**akhil_xsec_easy_cut_total_20260006** (seed 20260006, answer `2606.3`): valid = True. Roadway cross sections; average end area total cut volume, +/-5% stated. Reads ground/template against a labelled grid. Easy for both models in the pilot.

**akhil_xsec_medium_cut_total_20260121** (seed 20260121, answer `4246.8`): valid = True. As easy, plus mixed cut/fill, 4:1 vertical exaggeration, unequal station spacing.

**akhil_xsec_hard_cut_total_20260415** (seed 20260415, answer `3528.0`): valid = True. 8 stations, 5:1 exaggeration, ground elevation callouts. Pilot: both models within 1%.

**akhil_xsec_hard_max_cut_interval_20260707** (seed 20260707, answer `"15+75-16+50"`): valid = True. Which station interval has the largest cut volume (winner beats runner-up by >= 10%, validator-checked).
