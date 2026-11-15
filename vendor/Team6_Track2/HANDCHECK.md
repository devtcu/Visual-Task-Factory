# Team 6: review of the seven-task draft

Reviewed on 2026-11-14. These are **Codex-assisted visual inspections and independent numerical checks**, not a claim that a named human teammate has signed off or that either required model has been evaluated. Team 6 should inspect the full-resolution gallery before final upload. Three additional tasks and final model responses remain pending.

The review uses the actual Linux-generated files in `tasks/final/`. All seven records passed their automated validators. `review.html` displays the exact delivered questions and images; finance uses its six full-resolution pages. Preview resizing was used only for inspection and did not alter the delivered images. The precise reference values remain in `tasks/final/tasks.jsonl`.

## 1. SPC: `akhil_heads_401`

**Reference: `[1, 29]`.** The chart legend, head markers, sample grid, and sigma labels are visible without clipping. The dense traces need full-resolution zoom when counting individual samples.

An independent check of the saved measurements finds H1 samples 22-29 are 499.49, 499.65, 499.39, 499.14, 499.76, 499.29, 499.76, and 498.83 g. All eight are below the 500 g center line, so Rule 4 signals at sample 29. Other first signals are later: H6 at 41, H2 at 43, H5 at 82, and H4 at 95; H3 never signals. The large later outlier is not the first event. The validator also rerenders from the saved data and compares delivered image pixels.

## 2. Fiber: `akhil_fiber_trace_22`

**Reference: port `8`.** The highlighted source, port labels, crossing cords, and printed trunk rules are visible. Cord crossings do not imply connectivity, as stated in the question.

The route is GPU port 03 -> PP-A 11 -> PP-B 12 -> PP-C 01 -> PP-D 02 -> switch port 08. Both trunks are Type C and swap adjacent port pairs. Applying both swaps gives the unique destination. The validator independently follows the permutations and compares the rerendered image with the delivered file.

## 3. EEG: `akhil_brain_p306_spike`

**Reference: `T5`.** Channel labels and calibration are readable. The sharp-wave phase reversal is visible between T3-T5 and T5-O1, whose shared electrode is T5. The separate frontopolar blink is distinguishable and explicitly excluded by the prompt.

The focal event occurs 4.63 seconds after page start, approximately 23:07:46.63; the blink occurs at 2.58 seconds. Validation reconstructs the channel signals to derive the phase reversal and compares the rerendered page pixels with the saved image.

## 4. Roadway: `akhil_xsec_hard_max_cut_interval_20260707`

**Reference: `15+75-16+50`.** The delivered sheet is dense; station and elevation labels should be reviewed at native resolution. Ground and template profiles, unequal station intervals, and cut/fill regions remain visible.

Independent piecewise-profile integration gives approximately 522.450 ft² and 851.355 ft² of cut at 15+75 and 16+50. Their 75 ft interval has volume `(522.450 + 851.355) / 2 * 75 / 27 = 1,908.062 yd³`. The next-largest interval, 14+75-15+75, is 1,561.984 yd³: a 346.078 yd³ margin, or 22.16% above the runner-up. Automated dense integration, Shapely clipping, reading-sensitivity checks, and image/data comparisons also pass.

## 5. Finance: `fin-02400-pri-h-L0`

**Reference: `$5.15`, absolute tolerance `$0.01`.** All six delivered pages were visually inspected: purchase order, two goods receipts, main invoice, split invoice, and authorized amendment. Tables, dates, quantities, rates, and footer policies are readable and stay within the page. The split invoice intentionally retains blank rows to align its line 12 with the main invoice. The question and document footers explicitly state discounted-unit half-up rounding.

The invoice date, 2026-10-09, precedes the amendment's effective date, 2026-10-16; original PO rates apply. Positive differences after discounted-unit rounding are:

| Line | Authorized unit | Billed unit | Combined billed quantity | Overcharge |
|---|---:|---:|---:|---:|
| 1 | $34.94 | $34.96 | 18 | $0.36 |
| 2, after 3% discount | $74.93 | $75.01 | 49 | $3.92 |
| 11, after 5% discount | $138.68 | $138.71 | 29 | $0.87 |

Total: `$0.36 + $3.92 + $0.87 = $5.15`. Split line 12 has 30 + 30 units but an identical authorized and billed discounted unit rate of $104.32, contributing zero. Freight and tax are excluded, and undercharges do not offset overcharges. Independent arithmetic, all six page rerenders, contact-sheet consistency, text bounds, and minimum font checks pass. The future evaluator sends the six full pages, avoiding reliance on a scaled contact sheet.

## 6. MeasureBench: `measurebench_ext_analog_dial_one_tick_counterfactual_0006`

**Reference: `-0.6` bar, absolute tolerance `0.099` bar.** Both gauge scales, labels, units, and needles are visible. The left gauge A reads approximately 3.0 bar; right gauge B reads 2.4 bar. The question specifies B minus A, giving `2.4 - 3.0 = -0.6` bar. The magnitude and negative sign agree with the visible decrease.

The validator independently estimates needle directions from delivered image pixels, checks the signed change, and compares a rerender from saved data. The corrected meniscus renderer remains in the source for future use, but there is no cylinder task among these seven selected records.

## 7. Reconstruction: `visual_reconstruction_global_spatial_reconstruction_s20261114`

**Reference: the five-object placement array in the task record.** The composite displays all holes H1-H5, coordinate rulers, and candidate labels. The task specifies original-photo coordinates (1920 by 2560), origin, axis directions, transformation order, and 30-pixel Euclidean center tolerance. Use the printed rulers rather than the composite page's pixel coordinates.

| Hole | Candidate | Center in original-photo pixels | Clockwise undo rotation | Then undo reflection |
|---|---|---|---:|---|
| H1 | H | [962.5, 262.5] | 270° | horizontal |
| H2 | A | [1558.5, 262.5] | 90° | none |
| H3 | C | [315.5, 999.5] | 180° | horizontal |
| H4 | F | [1647.5, 1569.5] | 90° | horizontal |
| H5 | D | [954.5, 1633.5] | 0° | horizontal |

Visual inspection confirms the task components are present and legible. Exact placement/orientation confirmation is supplied by the independent pixel matcher: it matches candidate pixels against original source crops and reconstructs the source photograph exactly. Equivalent rotation/reflection combinations are accepted; duplicate assignments and nonfinite coordinates are rejected. This does not claim a human solved every patch by eye. The original photograph and CC BY-SA 4.0 attribution are retained.

## Remaining review before final upload

Add three task reviews, have Team 6 inspect the complete ten-task set, provide actual contributor names, and run the two required models with complete saved responses. Current historical pilot evidence concerns earlier task versions and does not establish the revised set's difficulty.
