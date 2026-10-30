# TimesFM 3.0 independent-model audit v1

## Identity, rights and exposure

- Official model: `google/timesfm-3.0-pytorch`, revision `43046b85ec22d584a13f8098c2ed39c889e129c2`.
- Code: Google Research TimesFM revision `e51928e27119cb17bebc005be2696b75e0a9e688`, package 3.0.2.
  Forty installed Python files match the pinned source bytes; installed hashes are recorded.
- Actual downloaded safetensors: 1,322,898,824 bytes; SHA-256
  `a7592b0a8432baee54483254e5647856911ce69e09d09a9bb65904b2d98f17da`.
- Earliest weight-upload commit `6455822fd4703713f3bf9cb2845f7ba51dc65250`,
  24 August 2026 22:41:42 UTC. Its LFS object equals evaluated weights; predecessor has no safetensors.
  This is upload chronology, not an exact training cutoff. Historical/proxy overlap remains unresolved.
- The model card lists GIFT-Eval pretraining excluding fev-bench overlap, Wikipedia and Google Trends,
  and synthetic/augmented data. It is not an exhaustive corpus identity or numeric deduplication audit.
- Source code is separately Apache-2.0; the downloadable model has TimesFM Non-Commercial License v1.0.
  Its text permits noncommercial academic research and prohibits distributing the model/derivatives.
  The weights and vendor installation are kept outside the Git checkout and are not pushed.
  Future commercial/production use is not covered by this research setup.

## Actual API validation

CPU, torch 2.15.0+cpu, context 730, horizon 14, batch 1, symmetry averaging off; independent cases.
18 predeclared tasks: three states, origins 1 September / 1 October 2026, history/calendar/regional modes.
252 forecast days and 2,268 native quantile values are saved. Future-known covariate arrays cover past730+
future14 without future target observations. Perturbing unseen target values leaves inputs unchanged.
All forecasts are finite, shapes match the documented API and no adjacent native quantile crossings occur.

These targets postdate unchanged weight upload, conditional on accurate source dates. They were already
historically inspected: **not an untouched confirmation**. The tiny fixture has no festival outcomes and
does not establish model superiority, a successful calendar method, or multi-model festival replication.
Native quantile metrics are descriptive fixture checks, not a calibrated uncertainty study.

## Remaining model work

Run the full matched calendar/feature-count/placebo experiment for both model families under a new
protocol and compute budget. Do not inherit Chronos exposure evidence or compare differing cases.
Any event-year before August 2026 remains overlap-uncertain for TimesFM. The frozen source ends before
2026 Diwali; no retrospective clean post-weight festival result can be manufactured.

## Reproduce

The audit evidence stores API commit/tree metadata, pinned model card/licence/config, downloaded-byte
hashes, installed-code hashes, package versions and the fixture protocol/tasks/results. To reproduce,
install the pinned Google source (outside this repo) plus torch 2.15.0+cpu, huggingface-hub 2.4.0 and
safetensors 0.8.0; download the exact HF revision with TLS enabled and verify the safetensors hash.
`src/timesfm_fixture.py` uses the local path recorded in `weight_download.json` and refuses overwrite.
For another machine, prepare a new audit directory and update that location explicitly; local model paths
and installed processes are not assumed to transfer automatically.
