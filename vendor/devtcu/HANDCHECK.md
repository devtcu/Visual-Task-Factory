# Hand-check notes (devtcu)

Every task below passed all automatic checks: answer recomputed by a second solver (own Dijkstra / max-flow), answer unique, every predicted wrong answer scored wrong, labels present, legible and inked, and the pixel check that every stored line, arrowhead and inhibitory bar is drawn and no line appears between unconnected regions.

**What was checked by eye in this export:** the images of `connectome_delay_after_failure_L6_s1` and `connectome_critical_count_L5_s1` (labels sit on their own line, arrowheads separate, bars and lesion readable). Earlier versions of every level were checked by eye during the pilots (see PILOT_NOTES.md). The per-task lines below are drafted from each task's stored data and check results, not from a separate human pass: a teammate should look at the 10 reported tasks before submission.

Realism, all tasks: connectome-style diagram, module colours, real region abbreviations, synthetic wiring (stated in the title). Answers are exact integers or letters, so no tolerance is needed.

### connectome_redundant_edge_L1_s1
- Valid: all 8 checks pass; answer **C** recomputed by the second solver; 8 regions, 9 connections, level 1 (plain two-way lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (picked hub connection), B (on every fastest route), D (on every fastest route D).

### connectome_redundant_edge_L1_s2
- Valid: all 8 checks pass; answer **D** recomputed by the second solver; 9 regions, 13 connections, level 1 (plain two-way lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (picked hub connection), B (on every fastest route), C (on every fastest route C).

### connectome_redundant_edge_L1_s3
- Valid: all 8 checks pass; answer **C** recomputed by the second solver; 10 regions, 15 connections, level 1 (plain two-way lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (on every fastest route), B (picked hub connection), D (on every fastest route D).

### connectome_redundant_edge_L1_s4
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 10 regions, 14 connections, level 1 (plain two-way lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (picked hub connection), C (on every fastest route), D (on every fastest route D).

### connectome_redundant_edge_L1_s5
- Valid: all 8 checks pass; answer **C** recomputed by the second solver; 9 regions, 13 connections, level 1 (plain two-way lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (on every fastest route), B (on every fastest route B), D (picked hub connection).

### connectome_redundant_edge_L2_s1
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 11 regions, 17 connections, level 2 (delays on lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (counted steps not delays), C (slow link assumed unused), D (counted steps not delays D).

### connectome_redundant_edge_L2_s2
- Valid: all 8 checks pass; answer **D** recomputed by the second solver; 11 regions, 16 connections, level 2 (delays on lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (on every fastest route), B (picked hub connection), C (counted steps not delays).

### connectome_redundant_edge_L2_s4
- Valid: all 8 checks pass; answer **D** recomputed by the second solver; 10 regions, 14 connections, level 2 (delays on lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (counted steps not delays), B (counted steps not delays B), C (counted steps not delays C).

### connectome_redundant_edge_L2_s5
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 12 regions, 17 connections, level 2 (delays on lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (counted steps not delays), C (counted steps not delays C), D (counted steps not delays D).

### connectome_redundant_edge_L2_s6
- Valid: all 8 checks pass; answer **B** recomputed by the second solver; 12 regions, 19 connections, level 2 (delays on lines).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (counted steps not delays), C (counted steps not delays C), D (counted steps not delays D).

### connectome_redundant_edge_L3_s4
- Valid: all 8 checks pass; answer **C** recomputed by the second solver; 12 regions, 17 connections, level 3 (tied fastest routes).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (counted steps not delays), B (counted steps not delays B), D (on every fastest route).

### connectome_redundant_edge_L3_s5
- Valid: all 8 checks pass; answer **C** recomputed by the second solver; 12 regions, 20 connections, level 3 (tied fastest routes).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (counted steps not delays), B (counted steps not delays B), D (counted steps not delays D).

### connectome_redundant_edge_L3_s6
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 13 regions, 18 connections, level 3 (tied fastest routes).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (counted steps not delays), C (on every fastest route), D (on every fastest route D).

### connectome_redundant_edge_L3_s8
- Valid: all 8 checks pass; answer **B** recomputed by the second solver; 15 regions, 20 connections, level 3 (tied fastest routes).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (picked hub connection), C (slow link assumed unused), D (on every fastest route).

### connectome_redundant_edge_L3_s9
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 14 regions, 20 connections, level 3 (tied fastest routes).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (counted steps not delays), C (slow link assumed unused), D (counted steps not delays D).

### connectome_redundant_edge_L4_s1
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 12 regions, 21 connections, level 4 (one-way arrows).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (ignored arrow direction), C (ignored arrow direction C), D (ignored arrow direction D).

### connectome_redundant_edge_L4_s3
- Valid: all 8 checks pass; answer **C** recomputed by the second solver; 12 regions, 20 connections, level 4 (one-way arrows).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (ignored arrow direction), B (ignored arrow direction B), D (ignored arrow direction D).

### connectome_redundant_edge_L4_s4
- Valid: all 8 checks pass; answer **A** recomputed by the second solver; 12 regions, 19 connections, level 4 (one-way arrows).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: B (on every fastest route), C (ignored arrow direction), D (ignored arrow direction D).

### connectome_redundant_edge_L4_s5
- Valid: all 8 checks pass; answer **B** recomputed by the second solver; 13 regions, 18 connections, level 4 (one-way arrows).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (ignored arrow direction), C (on every fastest route), D (ignored arrow direction D).

### connectome_redundant_edge_L4_s6
- Valid: all 8 checks pass; answer **D** recomputed by the second solver; 13 regions, 22 connections, level 4 (one-way arrows).
- Hard because the reader must compare the fastest route with and without each of 4 marked connections; only one has an equally fast alternative. Predicted wrong answers: A (ignored arrow direction), B (ignored arrow direction B), C (slow link assumed unused).

### connectome_min_edge_cut_L1_s1
- Valid: all 8 checks pass; answer **1** recomputed by the second solver; 10 regions, 12 connections, level 1 (plain two-way lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 2 (min degree of endpoints), 6 (hop distance).

### connectome_min_edge_cut_L1_s2
- Valid: all 8 checks pass; answer **1** recomputed by the second solver; 9 regions, 10 connections, level 1 (plain two-way lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 2 (min degree of endpoints), 2 (hop distance).

### connectome_min_edge_cut_L1_s3
- Valid: all 8 checks pass; answer **1** recomputed by the second solver; 10 regions, 14 connections, level 1 (plain two-way lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 2 (hop distance).

### connectome_min_edge_cut_L1_s4
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 8 regions, 10 connections, level 1 (plain two-way lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 1 (assumed single bridge).

### connectome_min_edge_cut_L1_s5
- Valid: all 8 checks pass; answer **1** recomputed by the second solver; 9 regions, 11 connections, level 1 (plain two-way lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 4 (hop distance).

### connectome_min_edge_cut_L2_s1
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 12 regions, 19 connections, level 2 (delays on lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 1 (assumed single bridge), 5 (counted edges leaving input module).

### connectome_min_edge_cut_L2_s2
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 11 regions, 18 connections, level 2 (delays on lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 4 (hop distance), 1 (assumed single bridge).

### connectome_min_edge_cut_L2_s3
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 10 regions, 14 connections, level 2 (delays on lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 1 (assumed single bridge), 4 (counted edges leaving input module).

### connectome_min_edge_cut_L2_s4
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 11 regions, 16 connections, level 2 (delays on lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 1 (assumed single bridge).

### connectome_min_edge_cut_L2_s5
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 12 regions, 19 connections, level 2 (delays on lines).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (min degree of endpoints), 1 (node cut size), 1 (assumed single bridge).

### connectome_min_edge_cut_L3_s1
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 13 regions, 19 connections, level 3 (tied fastest routes).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (min degree of endpoints), 2 (node cut size), 1 (assumed single bridge).

### connectome_min_edge_cut_L3_s2
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 14 regions, 23 connections, level 3 (tied fastest routes).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (min degree of endpoints), 2 (node cut size), 2 (hop distance).

### connectome_min_edge_cut_L3_s3
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 14 regions, 23 connections, level 3 (tied fastest routes).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (min degree of endpoints), 2 (node cut size), 2 (hop distance).

### connectome_min_edge_cut_L3_s4
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 15 regions, 27 connections, level 3 (tied fastest routes).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (min degree of endpoints), 2 (node cut size), 2 (hop distance).

### connectome_min_edge_cut_L3_s5
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 12 regions, 17 connections, level 3 (tied fastest routes).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (min degree of endpoints), 2 (hop distance), 1 (assumed single bridge).

### connectome_min_edge_cut_L4_s1
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 12 regions, 28 connections, level 4 (one-way arrows).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L4_s2
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 13 regions, 25 connections, level 4 (one-way arrows).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 1 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L4_s3
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 14 regions, 28 connections, level 4 (one-way arrows).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 1 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L4_s4
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 11 regions, 21 connections, level 4 (one-way arrows).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (ignored arrow direction), 3 (min degree of endpoints), 1 (assumed single bridge).

### connectome_min_edge_cut_L4_s5
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 11 regions, 21 connections, level 4 (one-way arrows).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L6_s1
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 13 regions, 26 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L6_s2
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 14 regions, 26 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L6_s3
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 12 regions, 19 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L6_s4
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 13 regions, 24 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 4 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_min_edge_cut_L6_s5
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 12 regions, 19 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must find the narrowest bottleneck between IN and OUT (edge-disjoint routes), which is below both endpoint degrees by construction. Predicted wrong answers: 3 (ignored arrow direction), 0 (cut in reverse direction), 3 (min degree of endpoints).

### connectome_critical_count_L1_s1
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 10 regions, 12 connections, level 1 (plain two-way lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 6 (counted one fastest route), 8 (counted all fastest route links), 6 (counted fewest step route).

### connectome_critical_count_L1_s2
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 10 regions, 14 connections, level 1 (plain two-way lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 5 (counted one fastest route), 7 (counted all fastest route links), 5 (counted fewest step route).

### connectome_critical_count_L1_s3
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 8 regions, 8 connections, level 1 (plain two-way lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 6 (counted one fastest route), 8 (counted all fastest route links), 6 (counted fewest step route).

### connectome_critical_count_L1_s4
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 10 regions, 12 connections, level 1 (plain two-way lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 5 (counted one fastest route), 7 (counted all fastest route links), 5 (counted fewest step route).

### connectome_critical_count_L1_s5
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 9 regions, 12 connections, level 1 (plain two-way lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 4 (counted one fastest route), 6 (counted all fastest route links), 4 (counted fewest step route).

### connectome_critical_count_L2_s1
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 10 regions, 13 connections, level 2 (delays on lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (counted fewest step route).

### connectome_critical_count_L2_s2
- Valid: all 8 checks pass; answer **6** recomputed by the second solver; 11 regions, 16 connections, level 2 (delays on lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 4 (counted fewest step route).

### connectome_critical_count_L2_s3
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 12 regions, 22 connections, level 2 (delays on lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (counted fewest step route).

### connectome_critical_count_L2_s4
- Valid: all 8 checks pass; answer **6** recomputed by the second solver; 11 regions, 17 connections, level 2 (delays on lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (counted fewest step route).

### connectome_critical_count_L2_s5
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 10 regions, 12 connections, level 2 (delays on lines).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 6 (counted one fastest route), 8 (counted all fastest route links), 6 (counted fewest step route).

### connectome_critical_count_L3_s1
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 14 regions, 23 connections, level 3 (tied fastest routes).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 4 (counted one fastest route), 8 (counted all fastest route links), 4 (counted fewest step route).

### connectome_critical_count_L3_s2
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 15 regions, 24 connections, level 3 (tied fastest routes).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 5 (counted one fastest route), 7 (counted all fastest route links), 5 (counted fewest step route).

### connectome_critical_count_L3_s3
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 14 regions, 21 connections, level 3 (tied fastest routes).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 4 (counted one fastest route), 6 (counted all fastest route links), 4 (counted fewest step route).

### connectome_critical_count_L3_s4
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 15 regions, 19 connections, level 3 (tied fastest routes).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 6 (counted one fastest route), 8 (counted all fastest route links), 6 (counted fewest step route).

### connectome_critical_count_L3_s5
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 14 regions, 22 connections, level 3 (tied fastest routes).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 5 (counted one fastest route), 7 (counted all fastest route links), 5 (counted fewest step route).

### connectome_critical_count_L4_s1
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 12 regions, 23 connections, level 4 (one-way arrows).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 0 (ignored arrow direction).

### connectome_critical_count_L4_s2
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 11 regions, 20 connections, level 4 (one-way arrows).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (ignored arrow direction).

### connectome_critical_count_L4_s3
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 14 regions, 29 connections, level 4 (one-way arrows).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (ignored arrow direction).

### connectome_critical_count_L4_s4
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 13 regions, 24 connections, level 4 (one-way arrows).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 1 (ignored arrow direction).

### connectome_critical_count_L4_s5
- Valid: all 8 checks pass; answer **2** recomputed by the second solver; 11 regions, 21 connections, level 4 (one-way arrows).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 0 (ignored arrow direction).

### connectome_critical_count_L5_s1
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 12 regions, 24 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)). Viewed by eye: OK.
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 3 (ignored inhibitory bars), 3 (routed through lesion), 2 (ignored arrow direction).

### connectome_critical_count_L5_s2
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 11 regions, 20 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 3 (ignored inhibitory bars), 2 (routed through lesion), 3 (ignored arrow direction).

### connectome_critical_count_L5_s3
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 11 regions, 20 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 3 (ignored inhibitory bars), 2 (routed through lesion).

### connectome_critical_count_L5_s4
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 12 regions, 19 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (ignored inhibitory bars), 2 (routed through lesion).

### connectome_critical_count_L5_s5
- Valid: all 8 checks pass; answer **7** recomputed by the second solver; 13 regions, 24 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (ignored inhibitory bars), 2 (routed through lesion), 3 (ignored arrow direction).

### connectome_critical_count_L6_s1
- Valid: all 8 checks pass; answer **4** recomputed by the second solver; 12 regions, 20 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 1 (ignored arrow direction).

### connectome_critical_count_L6_s2
- Valid: all 8 checks pass; answer **3** recomputed by the second solver; 12 regions, 21 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 0 (ignored arrow direction).

### connectome_critical_count_L6_s3
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 12 regions, 19 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (ignored arrow direction).

### connectome_critical_count_L6_s4
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 12 regions, 21 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 0 (ignored arrow direction).

### connectome_critical_count_L6_s5
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 13 regions, 18 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must test every connection, not just those on one route; tied routes make 'count the links on the fastest route' wrong. Predicted wrong answers: 2 (ignored arrow direction).

### connectome_delay_after_failure_L1_s1
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 8 regions, 10 connections, level 1 (plain two-way lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 2 (ignored both failures), 3 (ignored failure Y).

### connectome_delay_after_failure_L1_s2
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 9 regions, 12 connections, level 1 (plain two-way lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 2 (ignored both failures), 3 (ignored failure Y), 2 (ignored failure X).

### connectome_delay_after_failure_L1_s3
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 10 regions, 14 connections, level 1 (plain two-way lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 2 (ignored both failures), 3 (ignored failure Y), 2 (ignored failure X).

### connectome_delay_after_failure_L1_s4
- Valid: all 8 checks pass; answer **6** recomputed by the second solver; 9 regions, 12 connections, level 1 (plain two-way lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 2 (ignored both failures), 5 (ignored failure Y), 2 (ignored failure X).

### connectome_delay_after_failure_L1_s5
- Valid: all 8 checks pass; answer **5** recomputed by the second solver; 10 regions, 16 connections, level 1 (plain two-way lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 2 (ignored both failures), 3 (ignored failure Y), 2 (ignored failure X).

### connectome_delay_after_failure_L2_s1
- Valid: all 8 checks pass; answer **32** recomputed by the second solver; 11 regions, 16 connections, level 2 (delays on lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 2 (ignored both failures), 27 (ignored failure Y), 2 (ignored failure X).

### connectome_delay_after_failure_L2_s2
- Valid: all 8 checks pass; answer **28** recomputed by the second solver; 11 regions, 16 connections, level 2 (delays on lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 18 (ignored both failures), 19 (ignored failure Y), 24 (ignored failure X).

### connectome_delay_after_failure_L2_s4
- Valid: all 8 checks pass; answer **31** recomputed by the second solver; 12 regions, 20 connections, level 2 (delays on lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 8 (ignored both failures), 24 (ignored failure Y), 8 (ignored failure X).

### connectome_delay_after_failure_L2_s5
- Valid: all 8 checks pass; answer **43** recomputed by the second solver; 11 regions, 15 connections, level 2 (delays on lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 18 (ignored both failures), 31 (ignored failure Y), 18 (ignored failure X).

### connectome_delay_after_failure_L2_s6
- Valid: all 8 checks pass; answer **18** recomputed by the second solver; 11 regions, 16 connections, level 2 (delays on lines).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 10 (ignored both failures), 12 (ignored failure Y), 10 (ignored failure X).

### connectome_delay_after_failure_L3_s1
- Valid: all 8 checks pass; answer **25** recomputed by the second solver; 15 regions, 22 connections, level 3 (tied fastest routes).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 13 (ignored both failures), 15 (ignored failure Y), 13 (ignored failure X).

### connectome_delay_after_failure_L3_s2
- Valid: all 8 checks pass; answer **19** recomputed by the second solver; 13 regions, 17 connections, level 3 (tied fastest routes).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 8 (ignored both failures), 13 (ignored failure Y), 8 (ignored failure X).

### connectome_delay_after_failure_L3_s3
- Valid: all 8 checks pass; answer **12** recomputed by the second solver; 12 regions, 20 connections, level 3 (tied fastest routes).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 7 (ignored both failures), 10 (ignored failure Y), 7 (ignored failure X).

### connectome_delay_after_failure_L3_s4
- Valid: all 8 checks pass; answer **12** recomputed by the second solver; 14 regions, 21 connections, level 3 (tied fastest routes).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 6 (ignored both failures), 8 (ignored failure Y).

### connectome_delay_after_failure_L3_s5
- Valid: all 8 checks pass; answer **9** recomputed by the second solver; 12 regions, 18 connections, level 3 (tied fastest routes).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 5 (ignored both failures), 6 (ignored failure Y), 5 (ignored failure X).

### connectome_delay_after_failure_L4_s1
- Valid: all 8 checks pass; answer **15** recomputed by the second solver; 13 regions, 22 connections, level 4 (one-way arrows).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 10 (ignored arrow direction), 3 (ignored both failures), 11 (ignored failure Y).

### connectome_delay_after_failure_L4_s2
- Valid: all 8 checks pass; answer **27** recomputed by the second solver; 11 regions, 18 connections, level 4 (one-way arrows).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 14 (ignored arrow direction), 6 (ignored both failures), 20 (ignored failure Y).

### connectome_delay_after_failure_L4_s3
- Valid: all 8 checks pass; answer **19** recomputed by the second solver; 12 regions, 22 connections, level 4 (one-way arrows).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 7 (ignored arrow direction), 6 (ignored both failures), 16 (ignored failure Y).

### connectome_delay_after_failure_L4_s4
- Valid: all 8 checks pass; answer **19** recomputed by the second solver; 11 regions, 20 connections, level 4 (one-way arrows).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 9 (ignored arrow direction), 5 (ignored both failures), 6 (ignored failure Y).

### connectome_delay_after_failure_L4_s5
- Valid: all 8 checks pass; answer **19** recomputed by the second solver; 11 regions, 22 connections, level 4 (one-way arrows).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 6 (ignored arrow direction), 8 (ignored both failures), 12 (ignored failure Y).

### connectome_delay_after_failure_L5_s1
- Valid: all 8 checks pass; answer **26** recomputed by the second solver; 11 regions, 22 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 11 (ignored inhibitory bars), 4 (routed through lesion), 18 (ignored region delays).

### connectome_delay_after_failure_L5_s2
- Valid: all 8 checks pass; answer **37** recomputed by the second solver; 14 regions, 29 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 29 (ignored inhibitory bars), 7 (routed through lesion), 18 (ignored region delays).

### connectome_delay_after_failure_L5_s3
- Valid: all 8 checks pass; answer **31** recomputed by the second solver; 13 regions, 24 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 17 (ignored inhibitory bars), 8 (routed through lesion), 18 (ignored region delays).

### connectome_delay_after_failure_L5_s4
- Valid: all 8 checks pass; answer **26** recomputed by the second solver; 13 regions, 25 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 22 (ignored inhibitory bars), 11 (routed through lesion), 17 (ignored region delays).

### connectome_delay_after_failure_L5_s6
- Valid: all 8 checks pass; answer **47** recomputed by the second solver; 14 regions, 31 connections, level 5 (circuit rules (inhibitory bars, lesion, region delays)).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 21 (ignored inhibitory bars), 8 (routed through lesion), 29 (ignored region delays).

### connectome_delay_after_failure_L6_s1
- Valid: all 8 checks pass; answer **16** recomputed by the second solver; 13 regions, 20 connections, level 6 (connectogram, curves crossing the centre). Viewed by eye: OK.
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 6 (ignored arrow direction), 8 (ignored both failures), 13 (ignored failure Y).

### connectome_delay_after_failure_L6_s2
- Valid: all 8 checks pass; answer **22** recomputed by the second solver; 13 regions, 20 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 7 (ignored arrow direction), 4 (ignored both failures), 11 (ignored failure Y).

### connectome_delay_after_failure_L6_s3
- Valid: all 8 checks pass; answer **17** recomputed by the second solver; 13 regions, 21 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 8 (ignored arrow direction), 5 (ignored both failures), 12 (ignored failure Y).

### connectome_delay_after_failure_L6_s4
- Valid: all 8 checks pass; answer **19** recomputed by the second solver; 12 regions, 21 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 4 (ignored arrow direction), 2 (ignored both failures), 5 (ignored failure Y).

### connectome_delay_after_failure_L6_s5
- Valid: all 8 checks pass; answer **14** recomputed by the second solver; 13 regions, 25 connections, level 6 (connectogram, curves crossing the centre).
- Hard because the reader must re-route twice: the obvious detour around X is blocked by Y, so the true route is longer. Predicted wrong answers: 8 (ignored arrow direction), 6 (ignored both failures), 7 (ignored failure Y).
