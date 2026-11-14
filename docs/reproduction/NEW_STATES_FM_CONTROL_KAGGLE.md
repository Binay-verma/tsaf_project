# TimesFM-3 encoding control (exploratory) on Kaggle

Two runs, one per cohort. Same settings as the registered foundation runs: Accelerator None, Internet On, and the `GITHUB_TOKEN` secret attached (use the new token). Start each with **Save Version → Save & Run All (Commit)**. Expected time: about 5 h (2017–2020) and about 8 h (2021–2025).

Cell 1 (Python):
```python
import os
from kaggle_secrets import UserSecretsClient
os.environ['GH_TOKEN'] = UserSecretsClient().get_secret('GITHUB_TOKEN')
print('token length', len(os.environ['GH_TOKEN']))
```

Cell 2: change only `COHORT` (fm_2017_2020 for the first run, fm_2021_2025 for the second). `%%bash` must be the first line.
```bash
%%bash
set -e
COHORT=fm_2017_2020
cd /kaggle/working
rm -rf tsaf_project
git clone -q https://github.com/Binay-verma/tsaf_project.git
cd tsaf_project
git log --oneline -1
pip -q install -r requirements.txt
pip -q install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
pip uninstall -y -q torchvision torchaudio
pip -q install chronos-forecasting==2.3.2 transformers==5.22.0 huggingface-hub==2.4.0
pip -q install "git+https://github.com/google-research/timesfm@e51928e27119cb17bebc005be2696b75e0a9e688"
git config user.name "Binay Verma"
git config user.email "binayvermabtech24@rvu.edu.in"
cd src
python new_states_fm_control_v1.py weights
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python new_states_fm_control_v1.py run --cohort $COHORT
cd ..
git add results/new_states_v1_fm_control
git commit -q -m "TimesFM-3 encoding control (exploratory): $COHORT (Kaggle)"
git pull -q --rebase origin main
git push "https://x-access-token:${GH_TOKEN}@github.com/Binay-verma/tsaf_project.git" HEAD:main 2>&1 | sed "s#${GH_TOKEN}#***#g"
git log --oneline -1
echo RUN_DONE
```

If the push fails, download the six files from Output → `tsaf_project/results/new_states_v1_fm_control/<COHORT>/timesfm/` and attach them, as with the earlier runs.
