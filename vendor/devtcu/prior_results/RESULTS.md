# Results so far (14 Nov 2026)

Both models via OpenRouter: anthropic/claude-haiku-5.5 and openai/gpt-6-luna, settings in each results/<set>/run_config.json.
Every reply complete (no API errors, no truncation). Raw replies in results/<set>/raw/.

## Pilot 1: levels 1 to 4, all four question types (`results/pilot`)

| Task | Correct | Haiku 5.5 | Luna |
| --- | --- | --- | --- |
| critical_count_L1_s1 | 2 | 2 ✅ | 2 ✅ |
| critical_count_L1_s2 | 2 | 2 ✅ | 2 ✅ |
| delay_after_failure_L1_s1 | 7 | 7 ✅ | 7 ✅ |
| delay_after_failure_L1_s2 | 5 | 5 ✅ | 5 ✅ |
| min_edge_cut_L1_s1 | 1 | 1 ✅ | 1 ✅ |
| min_edge_cut_L1_s2 | 1 | 1 ✅ | 1 ✅ |
| redundant_edge_L1_s1 | C | C ✅ | C ✅ |
| redundant_edge_L1_s2 | B | B ✅ | B ✅ |
| critical_count_L2_s1 | 6 | 6 ✅ | 6 ✅ |
| critical_count_L2_s2 | 5 | 5 ✅ | 0 ❌ |
| delay_after_failure_L2_s1 | 35 | 35 ✅ | 35 ✅ |
| delay_after_failure_L2_s2 | 33 | 33 ✅ | 33 ✅ |
| min_edge_cut_L2_s1 | 2 | 2 ✅ | 2 ✅ |
| min_edge_cut_L2_s2 | 2 | 2 ✅ | 2 ✅ |
| redundant_edge_L2_s1 | B | B ✅ | B ✅ |
| redundant_edge_L2_s2 | B | B ✅ | B ✅ |
| critical_count_L3_s1 | 2 | 2 ✅ | 2 ✅ |
| critical_count_L3_s2 | 3 | 3 ✅ | 3 ✅ |
| delay_after_failure_L3_s1 | 24 | 24 ✅ | 24 ✅ |
| delay_after_failure_L3_s2 | 19 | 19 ✅ | 19 ✅ |
| min_edge_cut_L3_s1 | 4 | 4 ✅ | 4 ✅ |
| min_edge_cut_L3_s2 | 3 | 3 ✅ | 3 ✅ |
| redundant_edge_L3_s1 | B | B ✅ | B ✅ |
| redundant_edge_L3_s2 | D | D ✅ | D ✅ |
| critical_count_L4_s1 | 4 | 4 ✅ | 1 ❌ (ignored arrow direction) |
| critical_count_L4_s2 | 4 | 4 ✅ | 3 ❌ |
| delay_after_failure_L4_s1 | 23 | 23 ✅ | 23 ✅ |
| delay_after_failure_L4_s2 | 21 | 20 ❌ | 21 ✅ |
| min_edge_cut_L4_s1 | 2 | 2 ✅ | 2 ✅ |
| min_edge_cut_L4_s2 | 2 | 2 ✅ | 2 ✅ |
| redundant_edge_L4_s2 | C | C ✅ | C ✅ |

## Pilot 2: level 5, circuit rules (`results/pilot_L5`)

| Task | Correct | Haiku 5.5 | Luna |
| --- | --- | --- | --- |
| critical_count_L5_s1 | 6 | 6 ✅ | 6 ✅ |
| critical_count_L5_s2 | 5 | 5 ✅ | 5 ✅ |
| critical_count_L5_s3 | 7 | 7 ✅ | 7 ✅ |
| critical_count_L5_s4 | 6 | 6 ✅ | 5 ❌ |
| critical_count_L5_s5 | 6 | 6 ✅ | 6 ✅ |
| delay_after_failure_L5_s1 | 26 | 26 ✅ | 26 ✅ |
| delay_after_failure_L5_s2 | 35 | 35 ✅ | 35 ✅ |
| delay_after_failure_L5_s4 | 36 | 36 ✅ | 19 ❌ |

## Pilot 3: level 6, connectogram (`results/pilot_L6`)

| Task | Correct | Haiku 5.5 | Luna |
| --- | --- | --- | --- |
| critical_count_L6_s1 | 5 | 5 ✅ | 2 ❌ |
| critical_count_L6_s2 | 7 | 7 ✅ | 6 ❌ |
| critical_count_L6_s3 | 3 | 3 ✅ | 3 ✅ |
| critical_count_L6_s4 | 6 | 7 ❌ | 6 ✅ |
| critical_count_L6_s5 | 4 | 4 ✅ | 1 ❌ (ignored arrow direction) |
| critical_count_L6_s6 | 8 | 3 ❌ (ignored arrow direction) | 5 ❌ |
| delay_after_failure_L6_s1 | 22 | 22 ✅ | 12 ❌ (ignored arrow direction) |
| delay_after_failure_L6_s2 | 19 | 19 ✅ | 15 ❌ |
| delay_after_failure_L6_s3 | 15 | 15 ✅ | 15 ✅ |
| delay_after_failure_L6_s4 | 14 | 14 ✅ | 10 ❌ (ignored arrow direction,added failed delays) |
| delay_after_failure_L6_s5 | 16 | 16 ✅ | 16 ✅ |
| delay_after_failure_L6_s6 | 13 | 11 ❌ (ignored failure Y) | 11 ❌ (ignored failure Y) |

## Pilot 4: level 6 double failure, rebuilt with clearer labels (`results/pilot_L6_fail`)

| Task | Correct | Haiku 5.5 | Luna |
| --- | --- | --- | --- |
| delay_after_failure_L6_s11 | 12 | 11 ❌ | 13 ❌ |
| delay_after_failure_L6_s12 | 14 | 14 ✅ | 10 ❌ (ignored arrow direction,ignored failure Y) |
| delay_after_failure_L6_s15 | 16 | 16 ✅ | 16 ✅ |
| delay_after_failure_L6_s16 | 15 | 15 ✅ | 15 ✅ |
| delay_after_failure_L6_s17 | 11 | 11 ✅ | 11 ✅ |
| delay_after_failure_L6_s18 | 11 | 11 ✅ | 11 ✅ |

## By level, all pilots

| Level | Haiku 5.5 | Luna |
| --- | --- | --- |
| 1 | 8/8 | 8/8 |
| 2 | 8/8 | 7/8 |
| 3 | 8/8 | 8/8 |
| 4 | 6/7 | 5/7 |
| 5 | 8/8 | 6/8 |
| 6 | 14/18 | 8/18 |
| **All** | **52/57** | **42/57** |

Known issue: level-6 test5 (delay_after_failure_L6_s11) has about five arrowheads overlapping at PMv; a rule against overlapping arrowheads is still to add.
