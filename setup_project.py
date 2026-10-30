"""Install project dependencies; foundation model uses CPU, without cloud services."""
import subprocess,sys,argparse
from pathlib import Path
p=Path(__file__).resolve().parent
arg=argparse.ArgumentParser();arg.add_argument('--baseline-only',action='store_true');a=arg.parse_args()
def pip(*args):subprocess.run([sys.executable,'-m','pip','install',*args],check=True)
pip('-r',str(p/'requirements.txt'))
if not a.baseline_only:
 pip('torch','--index-url','https://download.pytorch.org/whl/cpu')
 pip('chronos-forecasting==2.3.2','socksio')
print('Ready: python run_all.py')
