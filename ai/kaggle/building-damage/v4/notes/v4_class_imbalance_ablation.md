# V4 training-only class-imbalance ablation

Status: loss helper implemented and tested on Kaggle CPU. A draft paired epoch-3
stage is integrated but has not been used for training; synthetic CPU resume test
K39 passed. K40 tested audit identity validation on synthetic reports, and K41
verified the two generated bounded packages share source and input metadata. Actual
K34 file integrity, mounted inputs and GPU rehearsals are pending. This is a
controlled experiment, not an assertion that weighting will improve damage
detection. K37 established expected baseline failures and K38 version 2 passed
nine helper tests.

## Evidence and hypothesis

K34 stdout reports 2,660 training labels and no validation-label reads. The
full-tile training target pixel counts in the order no damage, minor, major,
destroyed are 92,406,627; 15,508,042; 19,792,146; and 9,309,230. Its JSON
output still needs its integrity and identity checked. K33 grouped validation
has zero minor and major F1; imbalance is a plausible contributor, not a
proven cause. Full-tile counts need not equal the sampled crop distribution.

## Comparison

Start two separately identified runs from the same K33 epoch-2 checkpoint and
restored optimizer and RNG state. Use the same frozen backbone, manifest,
training order, crop seeds, augmentation, optimizer settings, one-epoch budget,
and validation procedure. One run continues the existing unweighted objective;
the other changes only the damage-loss weighting. Preserve all processed IDs,
input hashes, loss configuration, checkpoint identity and random states.

The candidate weights are inverse square roots of K34's training-only pixel
counts, normalized so their pixel-frequency-weighted mean is one:
`[0.67709754, 1.65281525, 1.46304052, 2.13327044]`. Values and formula are
fixed before either run; no validation data determines the weights. For valid
damage pixels, compute `sum(weight[target] * per_pixel_cross_entropy) /
sum(weight[target])`. Ignore unlabeled pixels and retain the existing
localization loss and loss combination. An empty valid mask must yield a finite
zero damage loss. Uniform weights must reproduce the existing valid-pixel mean
and gradients. Record the actual weights and their training-count provenance.

## Gates

1. Verify the K34 output JSON against its stdout counts and hash before using it
   as a machine-readable artifact. Keep the count source and manifest pinned.
2. Kaggle K38 version 2 passed synthetic CPU tests for uniform-weight
   equivalence, ignore masking, per-class gradients, empty masks and malformed
   weights. Integration with the training stage and GPU remains untested.
3. On Kaggle, run bounded same-code rehearsals for both arms with real labels,
   checkpoint restoration, output hashes, finite loss and explicit coverage.
4. Run the full controlled arms only after the rehearsals pass and verify each
   checkpoint and all grouped-validation prediction artifacts independently.
5. Compare combined, localization and per-class F1, recall, prediction counts,
   and event-level metrics with K33 and between arms. Record any tradeoffs;
   neither grouped-validation score is an official held-out leaderboard score.

Independent target-rasterizer parity and cross-dataset overlap remain open.
K6–K9 checkpoints used invalid labels and must not be used as parents.
