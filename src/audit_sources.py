"""Audit downloaded candidate sources; never modify the original experiment data."""
from pathlib import Path
import pandas as pd, numpy as np,json,hashlib,zipfile
P=Path(__file__).resolve().parents[1];D=P/'data/external';O=P/'results/data_search';O.mkdir(exist_ok=True)
z=zipfile.ZipFile(D/'sasea_data.zip')
for n in ['data/daily_aggregates/daily_agg_IND_demand.yml','data/raw/raw_IND_demand.yml']:
 (D/Path(n).name).write_bytes(z.read(n))
x=pd.read_csv(D/'POSOCO_data.csv'); dates=pd.to_datetime(x.yyyymmdd.astype(str),format='%Y%m%d',errors='raise');x.index=dates
assert not x.index.duplicated().any()
fields=json.loads((D/'POSOCO_metadata.json').read_text())['fields']
lookup={f['name']:f for f in fields}
states=['Karnataka','Delhi','Maharashtra'];columns=[s+': EnergyMet' for s in states]
for c in columns: assert lookup[c]['units']=='GWh'
y=x[columns].rename(columns=dict(zip(columns,states))).apply(pd.to_numeric,errors='raise')
y.index.name='date';y=y.reindex(pd.date_range(y.index.min(),y.index.max(),name='date')); y.to_csv(D/'latest_state_energy_GWh.csv')
rows=[]
for state in states:
 for year,g in y.groupby(y.index.year):
  rows.append({'state':state,'year':year,'expected_days_within_source_span':len(g),'observed':int(g[state].notna().sum()),'missing':int(g[state].isna().sum()),'nonpositive':int(g[state].le(0).sum()),'min_GWh':g[state].min(),'max_GWh':g[state].max()})
pd.DataFrame(rows).to_csv(O/'latest_coverage.csv',index=False)
old=pd.read_csv(P/'data/clean_daily_energy_GWh.csv',index_col=0,parse_dates=True)
comparison=[]
for s in states:
 a=pd.concat([old[s].rename('old'),y[s].rename('new')],axis=1).dropna(); delta=(a.old-a.new).abs()
 comparison.append({'state':s,'overlap_days':len(a),'equal_within_0.01_GWh':int(delta.le(.01).sum()),'median_absolute_difference_GWh':delta.median(),'max_absolute_difference_GWh':delta.max()})
pd.DataFrame(comparison).to_csv(O/'source_overlap.csv',index=False)
agg=pd.read_csv(D/'daily_agg_IND_demand.csv',parse_dates=['date'])
original=pd.read_csv(P/'data/raw/corrected_daily_energy_met_MU.csv',parse_dates=['Date'])
# Compare all original per-date totals after collapsing only for source-dependence diagnostic.
a=agg.groupby('date').demand_MWh.first().to_frame().join(original.groupby('Date').Total.first().rename('original_GWh')).dropna()
report={'latest':{'raw_rows':len(x),'columns':len(x.columns),'start':str(y.index.min().date()),'end':str(y.index.max().date()),'missing_calendar_dates':int(len(y)-len(x)),'licence':'No explicit dataset reuse licence located in landing page or metadata; verify before public redistribution.','unit':'GWh/day energy met','all_positive_observed':bool((y.stack()>0).all())},'sasea_india':{'rows':len(agg),'start':str(agg.date.min().date()),'end':str(agg.date.max().date()),'duplicate_extra_rows':int(agg.date.duplicated().sum()),'missing_calendar_dates':len(pd.date_range(agg.date.min(),agg.date.max()).difference(agg.date)),'licence':'CC BY 4.0 per repository metadata','overlap_compared':len(a),'matching_original_national_total_after_unit_conversion':int(np.isclose(a.demand_MWh/1000,a.original_GWh,atol=.01).sum()),'decision':'Not an independent external validation source; same historical dates and national totals largely coincide. Catalogue 2025 does not imply Indian coverage through 2025.'}}
(O/'audit.json').write_text(json.dumps(report,indent=2))
manifest=[]
for f in sorted(D.iterdir()):
 if f.is_file():manifest.append({'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(O/'checksums.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(report,indent=2));print(pd.DataFrame(rows).query('year>=2024').to_string(index=False))
