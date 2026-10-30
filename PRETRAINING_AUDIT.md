# Pretraining overlap: evidence and limits

The evaluated model is `amazon/chronos-2` at revision `29ec3766d36d6f73f0696f85560a422f50e8498c`. The first repository commit containing weights is `95a9710e2596287d08352589f42634fa5abdf0a7`, uploaded at **2025-10-30 14:58:57 UTC**. The later evaluated revision changes documentation; its weight object has the same SHA-256 as the first uploaded object:

`ddcda3c7508bf2528087723e98a20707cc04b7f370ae275a9fd88078ddba4f42`

The actual locally cached safetensors bytes were hashed and matched this identifier. Commit history, both repository trees, the pinned model card and the recorded hash check are preserved in `evidence/` and `results/extended_validation/pretraining_audit.json`.

## What this establishes

Genuinely later 2026 electricity observations could not have been directly included in these unchanged weights before their October 2025 upload. This is conditional on source dates correctly identifying later observations. It is stronger evidence than relying on a model-name release year or a current README date. It is **not the model's exact training cutoff**.

The 2022–2025 evaluations are not cleared by this chronological argument. In particular, Diwali 2025 precedes the upload. No observed 2026 Diwali is present in the source snapshot ending 28 October 2026; its main date is 8 November. There is therefore **no post-upload Diwali evaluation in this checkpoint**.

## Corpus identity investigation

The technical report's disclosed training-data table and linked Chronos/GIFT corpus metadata were inspected. No POSOCO, GRID-INDIA or named Indian state energy-met series was identified. The electricity benchmark linked to UCI refers to Portuguese customer series, which does not establish Indian-state inclusion. This investigation is name/provenance based: it is not exhaustive numeric deduplication. Unknown aliases, correlated national/regional series and undisclosed samples remain unresolved. Do not write “contamination-free” or “all overlap ruled out.”

The source is a retrospectively maintained compilation. Publication lag, revisions and curator gap treatment also prevent describing the experiment as a fully reconstructed real-time operational trial. Post-weight chronology and real-time data availability are separate checks.

## Recheck sources

- Repository commits: https://huggingface.co/api/models/amazon/chronos-2/commits/main
- First-weight tree: https://huggingface.co/api/models/amazon/chronos-2/tree/95a9710e2596287d08352589f42634fa5abdf0a7?recursive=true
- Evaluated tree: https://huggingface.co/api/models/amazon/chronos-2/tree/29ec3766d36d6f73f0696f85560a422f50e8498c?recursive=true
- Technical report: https://arxiv.org/abs/2510.15821
- General leakage analysis: https://arxiv.org/abs/2510.13654

For another foundation model, repeat this audit separately. A different or newer checkpoint cannot inherit Chronos-2's chronological evidence.
