# Running the foundation-model Ziel study in Google Colab

The protocol (`results/ziel_foundation_v1/`) is already committed. These cells download the pinned weights, verify their SHA-256 against the hashes recorded in earlier audits, and run Chronos-2 and TimesFM-3 on CPU. Expect roughly 1–3 hours in total. If a cell stops, do not delete anything: tell me what it printed.

Use a CPU runtime (Runtime → Change runtime type → CPU). Run one cell at a time.

```bash
!git clone https://github.com/Binay-verma/tsaf_project.git /content/tsaf_project
%cd /content/tsaf_project
!pip -q install -r requirements.txt
!pip -q install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
!pip -q install chronos-forecasting==2.3.2 transformers==5.22.0 huggingface-hub==2.4.0
!pip -q install "git+https://github.com/google-research/timesfm@e51928e27119cb17bebc005be2696b75e0a9e688"
!git config user.name "Binay Verma"
!git config user.email "binayvermabtech24@rvu.edu.in"
```

Download and verify the weights. The cell fails loudly if any hash differs; in that case stop.

```bash
%cd /content/tsaf_project/src
!python ziel_foundation_v1.py weights
```

Run the four workers (one cell each; each prints progress):

```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python ziel_foundation_v1.py chronos --cohort event_window
```
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python ziel_foundation_v1.py chronos --cohort ordinary
```
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python ziel_foundation_v1.py timesfm --cohort event_window
```
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python ziel_foundation_v1.py timesfm --cohort ordinary
```

Then the registered analysis, and commit the outputs (the model weights are outside the repository and are never committed):

```bash
!python ziel_foundation_analysis_v1.py
%cd /content/tsaf_project
!git status --short
!git add results/ziel_foundation_v1
!git commit -m "Foundation-model Ziel study: forecasts and registered analysis (Colab run)"
```

Push as in `RUNBOOK_NOVEMBER_2026.md` (token entered with `getpass`). If the analysis prints "Reference arms outside tolerance", still commit and push: the failure is a result and is kept.

Colab sessions disconnect after inactivity. A worker that stops leaves `started.json` and `checkpoint.csv`; it will refuse to restart in the same folder. Do not delete them; send me the error and I will version a resumable run.
