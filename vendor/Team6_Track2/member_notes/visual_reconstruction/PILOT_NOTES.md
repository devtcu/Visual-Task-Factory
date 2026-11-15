# Existing pilot results

No model calls were made for this export. The figures below are copied from evaluation records that already existed in the source project. They are one-photo pilot measurements, not a general model comparison.

| Existing run | Model | Fully correct placements | Other recorded result |
|---|---|---:|---|
| 180px irregular, one 8-hole instance | Claude Haiku 5.5 | 0/8 | mask IoU 0.0084 |
| 180px irregular, one 8-hole instance | GPT-6 Luna | 1/8 | mask IoU 0.8279 |
| 180px uniform, first pilot | Claude Haiku 5.5 | 0/8 | mask IoU 0.0412 |
| 180px uniform, first pilot | GPT-6 Luna | 1/8 | mask IoU 0.9068 |
| 180px uniform, jittered v2 | Claude Haiku 5.5 | 0/8 | mask IoU 0.0199 |
| 180px uniform, jittered v2 | GPT-6 Luna | 3/8 | mask IoU 0.8956 |
| 520px square, one 8-hole instance, high reasoning / 32,768 tokens | Claude Haiku 5.5 | 0/8 | mask IoU 0.4642 |
| 520px square, one 8-hole instance, high reasoning / 32,768 tokens | GPT-6 Luna | 4/8 | mask IoU 0.9952 |
| 520px square, 5-hole seeded instances, high reasoning / 32,768 tokens | Claude Haiku 5.5 | 0/50 across 10 instances | mapping 72%; centers within 30px 0%; mean mask IoU 0.4150 |
| 520px square, 5-hole seeded instances, high reasoning / 32,768 tokens | GPT-6 Luna | 19/45 across 9 completed instances | mapping 88.9%; centers within 30px 100%; mean mask IoU 0.9959 |

The ten five-hole instances use different seeds, jittered hole positions, and shuffled candidate order, but all use the same source photograph. Instance 10 has no completed GPT-6 Luna answer. A duplicate Claude record for that instance is counted once.

The pipeline history contains irregular 180px patches, uniform 180px patches, 520px square patches, and the current five-hole 520px setting. These changes predate this handoff. No generator changes were made to chase a new model score in this export. Earlier GPT results show that center placement and image overlap can remain high even when exact piece/transform accuracy is lower; the five-hole run also shows this setting is not reliably hard for both models. More photos and human ambiguity review are needed before treating it as a benchmark.
