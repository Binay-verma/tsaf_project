# Simulation v2, part D: foundation models on Kaggle

Synthetic data only; it does not touch the registered new-states study. One run does Chronos-2 and then TimesFM-3
(roughly 2-4 hours on CPU). Use the same notebook settings as the new-states runs: Accelerator None, Internet On,
secret GITHUB_TOKEN attached. Cell 1 is the same token cell as in NEW_STATES_KAGGLE.md.

Cell 2:
```bash
%%bash
set -e
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
python simulation_typed_pooled_v2.py weights
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python simulation_typed_pooled_v2.py chronos
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python simulation_typed_pooled_v2.py timesfm
cd ..
git add results/simulation_typed_pooled_v2/fm results/simulation_typed_pooled_v2/weights_identity.json
git commit -q -m "Simulation v2 part D: Chronos-2 and TimesFM-3 on synthetic series (Kaggle)"
git pull -q --rebase origin main
git push "https://x-access-token:${GH_TOKEN}@github.com/Binay-verma/tsaf_project.git" HEAD:main 2>&1 | sed "s#${GH_TOKEN}#***#g"
git log --oneline -1
echo RUN_DONE
```
Start with Save Version -> Save & Run All (Commit). If it stops part-way, finished h-levels are kept in the Output
tab (one CSV per h); send the log.
