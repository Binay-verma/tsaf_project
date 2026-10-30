"""Run the complete project from any working directory."""
from pathlib import Path
import subprocess,sys,argparse
p=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--source',choices=['original','latest'],default='original');parser.add_argument('--stride',type=int,default=28);parser.add_argument('--skip-chronos',action='store_true');a=parser.parse_args()
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True,cwd=p)
run('src/test_forecasting.py')
run('src/benchmark.py','--source',a.source,'--stride',a.stride,*(['--skip-chronos'] if a.skip_chronos else []))
run('src/summarize.py',p/'results'/f'benchmark_{a.source}_s{a.stride}')
run('src/audit_training.py',p/'results'/f'benchmark_{a.source}_s{a.stride}')
print('Finished. Open results/benchmark_'+a.source+'_s'+str(a.stride)+'/report.html')
