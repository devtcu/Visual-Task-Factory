# MeasureBench integration changes

Generator version `measurebench_ext-2.0` fixes the handoff's cylinder calibration. The liquid and the printed 0–100 mL scale now share the same coordinates. Validation independently locates all 21 tick marks and the meniscus boundary in the PNG, computes the visible volume from the observed tick endpoints, and compares it with the reference answer. The fixed canvas gives these measurements stable coordinates.

The legacy `analog_dial_one_tick_counterfactual` name remains accepted, but the revised question asks for the signed change from image A to image B. The seed now chooses a change of one to five 0.2 bar divisions in either direction. The answer is computed from both values. Composite comparisons also vary which gauge has the higher value. The words `EASY`, `MEDIUM`, and `HARD` are no longer printed on instrument images.

The three wording aliases `analog_dial_precision`, `vernier_precision`, and `meniscus_meniscus_convention` remain callable for compatibility. They are excluded from the seven advertised question types so they do not inflate the count of distinct reasoning templates.

The standard adapter delegates validation to `validate/measurebench_ext/checks.py` and returns `passed`, nested `checks`, and measured evidence. Validation includes exact rerendering from saved data, independent answer arithmetic, integrity and identity checks, and pixel measurements of gauge needle angles or cylinder readings.

## Selected examples

- `analog_dial_one_tick_counterfactual`, seed `6`: A is 3.0 bar, B is 2.4 bar; reference signed change is `-0.6` bar with absolute tolerance `0.099` bar.
- `meniscus_single_reading`, seed `5`: reference is the `65` mL graduation, read from the bottom of the concave meniscus.

Both examples were inspected visually. With Python 3.12 and the merged pinned environment, 33 varied seed/type cases passed validation. The signed changes covered eight different values and comparison winners included both gauges. Independent rebuilds of the two selected examples were byte-identical for images and data, with identical task records. Deliberately wrong answers failed validation. Replacing the 65 mL image with a 55 mL render and updating its hash still failed the independent pixel check, which measured 55.0862 mL.

These are local generation and validation results. No model calls were made. The prior handoff pilot responses evaluate the older generator and must not be reported as scores for these revised examples. The final Docker build should establish and retain the canonical Linux renders.
