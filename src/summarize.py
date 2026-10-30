"""Independently verify, score and render the completed benchmark."""
from pathlib import Path
import sys,json,html,base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from forecasting import ROOT,load_data

def markdown_table(frame):
 return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(map(str,row))+' |' for row in frame.itertuples(index=False,name=None))

def summarize(out):
 out=Path(out); p=pd.read_csv(out/'predictions.csv',parse_dates=['date','origin']);cfg=json.loads((out/'protocol.json').read_text());obs=load_data(cfg['source'])
 keys=['state','origin','horizon','model','mode'];assert not p.duplicated(keys).any();assert np.isfinite(p.prediction).all()
 assert ((p.date-p.origin).dt.days==p.horizon-1).all();assert p.mase_scale.gt(0).all()
 for state,g in p.groupby('state'):np.testing.assert_allclose(g.actual,obs[state].reindex(g.date),equal_nan=True)
 expected=len(p.groupby(['state','origin','horizon']))
 for (model,mode),g in p.groupby(['model','mode']):assert len(g)==expected,(model,mode,len(g),expected)
 scored=p[p.observed.eq(1)].copy();scored['ae']=(scored.actual-scored.prediction).abs();scored['scaled']=scored.ae/scored.mase_scale
 rows=[]
 for subset,q in [('all',scored),('diwali',scored[scored.festival_window.eq(1)]),('outside_diwali',scored[scored.festival_window.eq(0)])]:
  for key,g in q.groupby(['year','state','horizon','model','mode']):
   rows.append(dict(zip(['year','state','horizon','model','mode'],key),subset=subset,n=len(g),MAE_GWh=g.ae.mean(),MASE=g.scaled.mean()))
 m=pd.DataFrame(rows);m.to_csv(out/'metrics.csv',index=False)
 # Paired moving-block resampling of origin-level state-averaged error differences.
 # Descriptive interval only: few origins and one Diwali per year cannot establish event generalisation.
 rng=np.random.default_rng(42);ci=[]
 for (year,h,model),g in scored.groupby(['year','horizon','model']):
  z=g.groupby(['origin','mode']).scaled.mean().unstack()
  if not {'B_calendar','D_festival'}<=set(z):continue
  delta=(z.D_festival-z.B_calendar).dropna().to_numpy();n=len(delta)
  means=[]
  for _ in range(1000):
   starts=rng.integers(0,n,size=(n+2)//3);inds=np.concatenate([(k+np.arange(3))%n for k in starts])[:n];means.append(delta[inds].mean())
  ci.append({'year':year,'horizon':h,'model':model,'D_minus_B_MASE':delta.mean(),'descriptive_block_ci_low':np.quantile(means,.025),'descriptive_block_ci_high':np.quantile(means,.975),'origins':n,'block_origins':3})
 pd.DataFrame(ci).to_csv(out/'paired_intervals.csv',index=False)
 overview=m.query("subset=='all'").groupby(['year','horizon','model','mode']).MASE.mean().reset_index();overview.to_csv(out/'macro_metrics.csv',index=False)
 fig,axs=plt.subplots(1,3,figsize=(18,7))
 for ax,h in zip(axs,[1,7,14]):
  q=overview.query('year==2023 and horizon==@h').copy();q['label']=q.model+' / '+q['mode'];q.sort_values('MASE').plot.barh(x='label',y='MASE',ax=ax,legend=False);ax.set_title(f'2023 / day {h}');ax.set_xlabel('Macro MASE (lower is better)')
 fig.tight_layout();fig.savefig(out/'comparison.png',dpi=160);plt.close(fig)
 limitations='Sampled rolling origins, not all days. 2022 development and 2023 held-out year use frozen parameters; historical target context updates as time advances. Chronos pretraining overlap is unknown. Dates are only partially officially verified. One Diwali per year; no causal or publication-ready claim. Newer source is not silently substituted.'
 text='# Completed benchmark\n\n'+limitations+'\n\n'+markdown_table(overview.round(4))+'\n\nAll results use observed labels only. MAE values remain per-state because demand scales differ; macro MASE gives each state equal weight. Chronos generates 14-step forecasts and we score steps 1, 7 and 14; ridge uses direct horizon models. Classical models fit on the same 730-day pre-2022 period. SARIMAX updates latent state with past data without refitting parameters. Check convergence JSON files.\n'
 (out/'REPORT.md').write_text(text)
 body='<html><head><meta charset="utf-8"><title>TSFM India results</title><style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:20px;color:#17283d}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}th{background:#eaf1fa}img{max-width:100%}</style></head><body><h1>TSFM India forecasting experiment</h1><p>'+html.escape(limitations)+'</p><img src="comparison.png" alt="Forecast model comparison"><h2>State-averaged MASE</h2>'+overview.round(4).to_html(index=False)+'<p>Detailed metrics, observed-label predictions and descriptive paired intervals are available as CSV files in this folder.</p></body></html>'
 body=body.replace('src="comparison.png"','src="data:image/png;base64,'+base64.b64encode((out/'comparison.png').read_bytes()).decode()+'"')
 (out/'report.html').write_text(body)
 (out/'verification.json').write_text(json.dumps({'passed':['unique_predictions','finite_forecasts','horizon_date_alignment','positive_training_scale','actuals_match_source','identical_model_origin_coverage'],'predictions':len(p),'scored':len(scored),'models':sorted(p.model.unique().tolist())},indent=2));print(text[:3000])
if __name__=='__main__':summarize(sys.argv[1])
