# V4 Kaggle source record

Read-only Kaggle MCP discovery was performed on 21 October 2026. These records
identify candidate sources; they do not prove that a runtime can mount, download
or legally redistribute the files. No dataset bytes were downloaded by this
step.

| Role | Kaggle reference | Version | Reported size | License | Decision |
|---|---|---:|---:|---|---|
| Paired xBD primary | [`tunguz/xview2-challenge-dataset-train-and-test`](https://www.kaggle.com/datasets/tunguz/xview2-challenge-dataset-train-and-test) | 3 | 11,105,326,709 bytes | CC-BY-NC-SA-4.0 | Candidate primary input; verify file layout and labels in a mounted audit |
| xBD supplementary tier | [`tunguz/xview2-challenge-dataset-tier-3-data`](https://www.kaggle.com/datasets/tunguz/xview2-challenge-dataset-tier-3-data) | 2 | 18,593,707,905 bytes | CC-BY-NC-SA-4.0 | Candidate supplementary input; do not mix until overlap and split policy are verified |
| Post-only/UAV specialist | [`yaroslavchyrko/rescuenet`](https://www.kaggle.com/datasets/yaroslavchyrko/rescuenet) | 1 | 23,465,841,944 bytes | CDLA Permissive 1.0 | Later specialist branch; not an xBD substitute |

The xBD metadata points to the official xView2 download source and the v3 file
listing begins under `test/test/images/`; the complete tree still needs a paged
inventory and mounted-content audit. RescueNet metadata reports 4,494 post-event
UAV images at 3000×4000 with 12 semantic classes and links the original authors'
release. The Kaggle `get_dataset_status` calls for both sources returned
`Unauthenticated`, so K1 remains **BLOCKED** until a permitted runtime can verify
access without embedding credentials in notebook source.

The V4 adapter currently accepts the canonical raw xBD pair/label layout described
in `docs/dataset_setup.md`. A source attachment is accepted only after its mounted
paths, counts, hashes, label encodings and split-overlap report pass the CPU audit.
