# Foundation models on the longer panel (Google Colab)

Registered in `results/longer_panel_foundation_v1/` before any forecast. Runs Chronos-2 and TimesFM-3 (CPU, pinned
weights) on the Stage A cases for the new years 2022-2023, plus a reproduction check on 2024. Expect about 3-6 hours in
total; run one cell at a time. If a cell stops, do not delete anything: send me what it printed.

Runtime → Change runtime type → **CPU**.

**Cell 1: set up**
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

**Cell 2: weights (fails loudly if a hash differs; then stop)**
```bash
%cd /content/tsaf_project/src
!python longer_panel_foundation_v1.py weights
```

**Cell 3: reproduction check first (short)**
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python longer_panel_foundation_v1.py chronos --cohort reproduce_2024
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python longer_panel_foundation_v1.py timesfm --cohort reproduce_2024
```

**Cells 4-7: new years (one cell each)**
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python longer_panel_foundation_v1.py chronos --cohort event_2022_2023
```
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python longer_panel_foundation_v1.py chronos --cohort ordinary_2022_2023
```
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python longer_panel_foundation_v1.py timesfm --cohort event_2022_2023
```
```bash
!OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python longer_panel_foundation_v1.py timesfm --cohort ordinary_2022_2023
```

**Cell 8: analysis and commit** (weights are outside the repository and are never committed)
```bash
!python longer_panel_foundation_analysis_v1.py
%cd /content/tsaf_project
!git add results/longer_panel_foundation_v1
!git commit -m "Foundation models on the longer panel: Colab forecasts and exploratory analysis"
```

**Cell 9: push** (paste a GitHub token when asked; it is not shown or saved)
```python
from getpass import getpass
import subprocess
t = getpass('GitHub token: ')
print(subprocess.run(['git', 'push', f'https://{t}@github.com/Binay-verma/tsaf_project.git', 'HEAD:main'],
                     capture_output=True, text=True, cwd='/content/tsaf_project').stderr.replace(t, '***'))
```
If the push is rejected because `main` moved, run `!git pull --rebase origin main` in `/content/tsaf_project` and push again.
If the analysis prints "Reference arms outside tolerance", still commit and push: the failure is a result and is kept.
Colab disconnects after inactivity; a stopped worker leaves `started.json`/`checkpoint.csv` and refuses to restart in that
folder. Do not delete them; send me the error and I will version a resumable run.
