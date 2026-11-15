# TimesFM-3 on the second-test states (exploratory) on Kaggle

Two runs, one per cohort; they can run at the same time in two notebooks. Settings as before: Accelerator None, Internet On, the `GITHUB_TOKEN` secret attached. Start each with **Save Version → Save & Run All (Commit)**. Expected time: about 3 h (2017–2020) and about 4 h (2021–2025).

Before starting: the commits up to the one that adds this file must be on GitHub (push the bundle first).

Cell 1 (Python):
```python
import os
from kaggle_secrets import UserSecretsClient
os.environ['GH_TOKEN'] = UserSecretsClient().get_secret('GITHUB_TOKEN')
print('token length', len(os.environ['GH_TOKEN']))
```

Cell 2: change only `COHORT` (fm_2017_2020 in the first notebook, fm_2021_2025 in the second). `%%bash` must be the first line.
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
python new_states_v2_fm_v1.py weights --cohort $COHORT
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python new_states_v2_fm_v1.py run --cohort $COHORT
cd ..
git add results/new_states_v2_fm/$COHORT
git commit -q -m "TimesFM-3 second-test states (exploratory): $COHORT (Kaggle)"
for i in 1 2 3; do git pull -q --rebase origin main && git push "https://x-access-token:${GH_TOKEN}@github.com/Binay-verma/tsaf_project.git" HEAD:main 2>&1 | sed "s#${GH_TOKEN}#***#g" && break; sleep 20; done
git log --oneline -1
echo RUN_DONE
```

Each cohort writes only inside its own folder (including its own weights_identity.json), so the two runs cannot conflict. If the push still fails, download the files in Output → `tsaf_project/results/new_states_v2_fm/<COHORT>/` and attach them here.
