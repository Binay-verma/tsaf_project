# New-states study: foundation models on Kaggle

Four separate runs, one per model and cohort, each about 5-7 hours on CPU. Run them one or two at a time.
Use the same notebook settings as before: Accelerator None, Internet On, secret GITHUB_TOKEN attached.

Cell 1 (Python):
```python
import os
from kaggle_secrets import UserSecretsClient
os.environ['GH_TOKEN'] = UserSecretsClient().get_secret('GITHUB_TOKEN')
print('token length', len(os.environ['GH_TOKEN']))
```

Cell 2 (change MODEL and COHORT for each run: chronos/timesfm, fm_2017_2020/fm_2021_2025):
```bash
%%bash
set -e
MODEL=chronos
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
python new_states_v1.py weights
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python new_states_v1.py $MODEL --cohort $COHORT
cd ..
git add results/new_states_v1/$COHORT/$MODEL results/new_states_v1/weights_identity.json
git commit -q -m "New-states study: $MODEL forecasts for $COHORT (Kaggle)"
git pull -q --rebase origin main
git push "https://x-access-token:${GH_TOKEN}@github.com/Binay-verma/tsaf_project.git" HEAD:main 2>&1 | sed "s#${GH_TOKEN}#***#g"
git log --oneline -1
echo RUN_DONE
```
Start it with Save Version -> Save & Run All (Commit). If the push step fails, the forecasts are still in the version's
Output tab; send the log.
