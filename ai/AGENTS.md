# ai/AGENTS.md

Kaggle experiments (`kaggle/<feature>/vN/`), shared ML code (`src/rescuevision_ai`), CPU model services (`serving/`). Read [docs/AI.md](../docs/AI.md) before any change. Locked.

Gate: `make check-ml`.

Most-broken rules here:
1. Choosing settings on the test split, or splitting after tiling so the same scene is in train and test (A2).
2. Committing weights, datasets or notebook outputs (A1).
3. Logic inside a notebook instead of `src/rescuevision_ai`, so the service preprocesses differently (A1).
4. Promoting a model without written thresholds, a model card and ONNX parity (A3, A4).
5. An AI result shown or acted on without "AI proposed" and a person confirming (A6).
6. A model service with database credentials or more threads than physical cores (A5).
