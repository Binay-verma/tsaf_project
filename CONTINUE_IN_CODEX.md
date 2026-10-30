# Continue this project in Codex

The project files carry the research state. Do not rely on a new Codex session automatically receiving this ChatGPT thread. `CODEX_HANDOFF.md` captures the important decisions and limitations; it is not an exact conversation export.

## Move the project

1. Download the latest `TSFM_India_Project_Checkpoint.zip` and extract it.
2. Open the **inner `tsfm_india` folder** in your local Codex project/workspace. This folder contains `AGENTS.md`, `src`, `data` and `results`. It can be placed anywhere on your computer.
3. Start a new session in that folder. Paste the contents of `CODEX_START_PROMPT.txt`.
4. Have Codex read the handoff and summarise its understanding before continuing implementation. It can then run the package check and proceed with the next pending experiment.

Codex supports project guidance in `AGENTS.md`; the other handoff filenames are our project conventions, so the prompt explicitly requests them. Official guidance: https://learn.chatgpt.com/docs/agent-configuration/agents-md . Existing global or nested overrides can affect which instructions load.

## Verify the transfer without installing packages

From the project folder:

```bash
python src/verify_package.py
```

This verifies the recorded checkpoint files against SHA-256 checksums. It does not establish scientific validity. Do this before editing; intentional subsequent changes require a new versioned manifest/checkpoint. Keep source files' line endings unchanged when making the initial transfer.

## Python setup and staged recovery

Use Python 3.12 and an isolated environment. On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Linux/macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Then use that environment's Python for all commands. You can read saved reports immediately; no dependency installation or model download is needed to view results.

Stage 1, baseline checks:

```bash
python src/test_forecasting.py
python src/test_extended.py
```

Stage 2, regenerate scoring/report from included predictions:

```bash
python src/summarize_extended.py
python src/write_validation_report.py
```

Stage 3, foundation-model reproduction only when needed: inspect `requirements-foundation.txt` and `results/extended_validation/environment.json`. The recorded CPU torch wheel needs the PyTorch CPU index. An installation sequence is:

```bash
python -m pip install "torch==2.15.0+cpu" --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-foundation.txt
python src/cache_identity.py
```

These cross-machine installation instructions are documented, not tested on your Windows machine. Model weights need a separate download; no paid forecasting API was used. If pinned wheels are unavailable for your platform, record the limitation and use a compatible environment or a separately named reproducibility run. Do not silently remove the cache guard or change package versions while claiming an identical rerun.

`python setup_project.py` is the earlier convenient installer, but its torch installation is not pinned; check against the saved environment before cache reproduction. `python run_extended.py` reruns the expanded pipeline; `python run_all.py` is the older scheduled-origin study. A full rerun is not required merely to resume research.

## Keep future context

Keep `AGENTS.md`, `CODEX_HANDOFF.md`, `WORK_LOG.md`, protocols, code and outputs together. Ask Codex to update the handoff and work log at every substantive checkpoint, including failed attempts. Use Git commits and backups so chat/session loss cannot erase the project state. A repository containing the unresolved-licence source snapshot should stay private pending reuse review. Do not assume a process continues after a session ends.

If you need the exact wording of every message, separately copy/export this chat. The supplied files preserve the actionable research state and original survey, not every conversational sentence.
