# Hand-check notes

All five generated tasks passed the adapter checks: the saved composite is byte-consistent with its two panels, all five 520×520 hole boxes are non-overlapping, candidate patches exist, and the reference answer recomputes from the stored structured ground truth. The square cutouts and transformations are procedurally valid. A human ambiguity/legibility panel was not run; these notes do not claim human verification.

## `visual_reconstruction_global_spatial_reconstruction_s0001`

The masked left panel and shuffled candidate sheet were composed from the saved generated panels. The answer was recomputed from the seeded ground-truth placements; ±30px is the stated center tolerance. Reasoning requires candidate identification, hole matching, undo transforms, and position estimation.

## `visual_reconstruction_global_spatial_reconstruction_s0002`

Image/data hashes and five-square geometry pass validation. The answer sequence is independently derived from the private structured placements; ±30px applies to centers. Similar fence/building textures and rotated square patches require visual context beyond candidate labels.

## `visual_reconstruction_global_spatial_reconstruction_s0003`

The composite panel image matches the stored puzzle and candidate sheet, and oracle reconstruction checks pass. Centers use a 30px tolerance. Solving requires rejecting same-photo distractors and jointly inferring patch identity, orientation, and location.

## `visual_reconstruction_global_spatial_reconstruction_s0004`

Five uniform square holes, 15 candidate pieces, panel hashes, and answer recomputation pass. The scene is a real licensed Chicago building photograph; the stated ±30px tolerance is less than 6% of a 520px patch width. Scene continuity and transforms provide the reasoning load.

## `visual_reconstruction_global_spatial_reconstruction_s0005`

Automated checks confirm exact panel composition, disjoint hole boxes, and a reference sequence recomputed from structured data. The task states its 30px coordinate tolerance and JSON fields. It tests global scene matching, transform inversion, and approximate placement; human ambiguity review remains outstanding.
