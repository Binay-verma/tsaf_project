# Split checkpoint transfer: read this first

The original checkpoint exceeded the receiving tool's 32 MiB compressed-file limit. These are two ordinary, independent ZIP files, each below that limit. They are not binary split volumes and require no archive-joining utility.

## Contents

- TSFM_India_Code_Context.zip: AGENTS.md, CODEX_HANDOFF.md, CODEX_START_PROMPT.txt, WORK_LOG.md, all source/configuration, original survey, reports, summary metrics, row-level historical predictions, calendar/model audit evidence and the original full package manifest. No dataset files or model weights.
- TSFM_India_Data.zip: all original data/ files, including raw snapshots and selected-state inputs. No model weights.

All 180 entries from the saved version-4 checkpoint are assigned exactly once across the two archives and kept byte-for-byte. Additional transfer instructions, a part manifest and a dependency-free verifier are included to support this split. No experiment, prior result or source file was changed. No new model training or test-set tuning occurred.

## Extract

Extract both ZIPs into the SAME parent directory. Each contains a top-level tsfm_india/ folder, so their contents merge into one project. Do not extract the data archive inside the existing tsfm_india folder: that would create an incorrect nested tsfm_india/tsfm_india/data path. Duplicate transfer-support files are identical and may be merged.

For example, extracting both under C:/Projects/ produces C:/Projects/tsfm_india/AGENTS.md and C:/Projects/tsfm_india/data/.... On a shell with Python, from the directory containing both ZIPs:

    python -m zipfile -e TSFM_India_Code_Context.zip .
    python -m zipfile -e TSFM_India_Data.zip .
    cd tsfm_india
    python verify_split_transfer.py
    python src/verify_package.py

## If only the core ZIP is available

You can read instructions, source and all saved results immediately. From its extracted tsfm_india/ directory, run:

    python verify_split_transfer.py --part core

Missing data at this stage is deliberate. Do not start training or source-dependent scientific checks until the data archive is also extracted. The original src/verify_package.py checks the COMPLETE checkpoint and will report missing data until then; this is not evidence that prior records were lost.

After both archives are present, the default transfer verifier checks every original entry. The original full package verifier should then pass for all 179 listed checkpoint files. Model weights still require a separate download if rerunning foundation inference; saved predictions and summaries are already included.

## Continue research

Read AGENTS.md and CODEX_HANDOFF.md, then follow CODEX_START_PROMPT.txt. Current software/evaluation is complete; the journal study remains unfinished. Preserve exploratory/confirmation distinctions, failed hypotheses, source/data-rights limitations and untouched historical results. Research details and next experiments are in DEEP_RESEARCH.md and JOURNAL_PROTOCOL.json.
