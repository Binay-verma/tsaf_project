"""Reject stale expanded-model caches when source, features or settings change."""
from pathlib import Path
import hashlib,json,sys,importlib.metadata

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity():
 root=Path(__file__).resolve().parents[1]
 return {'files':{str(p.relative_to(root)):digest(p) for p in [root/'data/external/latest_state_energy_GWh.csv',root/'src/forecasting.py',root/'src/extended_validation.py']},'model':'amazon/chronos-2','revision':'29ec3766d36d6f73f0696f85560a422f50e8498c','context':730,'prediction_length':14,'cross_learning':False,'packages':{k:importlib.metadata.version(k) for k in ['chronos-forecasting','torch','holidays','numpy','pandas']}}
def guard(adopt=False):
 root=Path(__file__).resolve().parents[1];out=root/'results/extended_validation';path=out/'cache_identity.json';now=identity();caches=sorted(out.glob('chronos_*.csv'))
 if path.exists():
  saved=json.loads(path.read_text());assert saved['identity']==now,'Cache inputs/settings changed. Archive the prior experiment and create a separate output directory.'
  for p in caches:
   if p.name in saved['cache_sha256']:assert digest(p)==saved['cache_sha256'][p.name],f'Cached bytes changed: {p.name}'
  return
 assert not caches or adopt,'Unattested caches exist. Review provenance before explicit adoption.'
 path.write_text(json.dumps({'identity':now,'cache_sha256':{p.name:digest(p) for p in caches},'attestation':'Reviewed existing completed run; identity manifest added afterwards, not a contemporaneous preregistration' if adopt else 'Before new run'},indent=2))
if __name__=='__main__':guard('--adopt-reviewed-caches' in sys.argv);print('Cache identity verified')
