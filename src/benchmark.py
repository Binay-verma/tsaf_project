"""One-command matched forecasting experiment with resumable model outputs."""
import argparse,json,time,hashlib,platform,importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
from forecasting import *

def execute(args):
    started=time.perf_counter(); data=load_data(args.source)
    out=ROOT/'results'/f'benchmark_{args.source}_s{args.stride}';out.mkdir(exist_ok=True)
    config={'source':args.source,'stride':args.stride,'years':[2022,2023],'horizons':[1,7,14],'context':730,'train_end':'2021-12-31','ridge_alpha':10,'calendar':'weekday+3 annual harmonics; state holiday; main Diwali +/-3','schedule':'every stride days Jan1-Dec18 plus main Diwali minus3; fixed before scoring','checkpoint':'amazon/chronos-2','revision':'29ec3766d36d6f73f0696f85560a422f50e8498c','limitations':['Historical state holidays only partially verified','Pretraining contamination unknown','Sampled forecast origins; not daily full-year scores','One main Diwali occurrence per held-out year','No weather inputs; retrospective source corrections possible']}
    if (out/'protocol.json').exists() and json.loads((out/'protocol.json').read_text())!=config:
        raise ValueError('Output protocol differs; choose a fresh output directory before rerunning.')
    (out/'protocol.json').write_text(json.dumps(config,indent=2))
    source_path=ROOT/('data/clean_daily_energy_GWh.csv' if args.source=='original' else 'data/external/latest_state_energy_GWh.csv')
    signature={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source_path,ROOT/'src/forecasting.py',Path(__file__)]}
    signature_path=out/'cache_signature.json'
    if signature_path.exists() and json.loads(signature_path.read_text())!=signature:
        raise ValueError('Code or data changed since cached outputs; use a fresh experiment output directory.')
    if not signature_path.exists() and list(out.glob('chronos_*.csv')):
        raise ValueError('Cache lacks provenance; use a fresh output directory.')
    signature_path.write_text(json.dumps(signature,indent=2))
    records=[];frames=[];tasks=[]
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    for state in STATES:
        observed=data[state]; y=causal_fill(observed); cal,cols,festival,names=calendar(y.index,state);scale=mase_scale(observed)
        origins=[o for year in config['years'] for o in choose_origins(year,args.stride)]
        for mode in MODES:
            # Fit all direct horizon regressions only on pre-2022 labels.
            for h in config['horizons']:
                model=fit_direct(y,observed,cal,cols[mode],h)
                yp=model.predict(design(y,cal,cols[mode],h,origins))
                for o,v in zip(origins,yp):
                    add(records,state,o,o+pd.Timedelta(days=h-1),h,'ridge',mode,v,observed,festival,scale)
            # Same initial training span and calendar inputs for SARIMAX ablations.
            train=y.loc[:'2021-12-31'].tail(730)/100
            exog=cal.loc[train.index,cols[mode]].copy() if cols[mode] else None
            # Fourier/weekday constants can duplicate intercept; omit trend with exogenous terms.
            fit=SARIMAX(train,exog=exog,order=(1,0,0),seasonal_order=(1,0,0,7),trend='n' if cols[mode] else 'c',enforce_stationarity=False).fit(disp=False,maxiter=150)
            converged=bool(fit.mle_retvals['converged'])
            (out/f'sarimax_{state}_{mode}.json').write_text(json.dumps({'converged':converged},indent=2))
            if not converged: print('WARNING: nonconverged',state,mode,flush=True)
            cutoff=pd.Timestamp('2022-01-01')
            for o in origins:
                update=y.loc[cutoff:o-pd.Timedelta(days=1)]/100
                if len(update):fit=fit.extend(update,exog=cal.loc[update.index,cols[mode]] if cols[mode] else None)
                dates=pd.date_range(o,periods=14);future=cal.loc[dates,cols[mode]] if cols[mode] else None
                pred=fit.forecast(14,exog=future)*100
                for h in config['horizons']:add(records,state,o,dates[h-1],h,'sarimax',mode,float(pred.iloc[h-1]),observed,festival,scale)
                cutoff=o
        for o in origins:
            dates=pd.date_range(o,periods=14);a=y.loc[:o-pd.Timedelta(days=1)]
            for h in config['horizons']:
                add(records,state,o,dates[h-1],h,'last_value','A_history',a.iloc[-1],observed,festival,scale)
                add(records,state,o,dates[h-1],h,'seasonal_naive','A_history',a.iloc[-7+(h-1)%7],observed,festival,scale)
            tasks.append((state,o,a.tail(730),cal,cols,observed,festival,scale))
        print('Classical complete:',state,flush=True)
    pd.DataFrame(records).to_csv(out/'classical_predictions.csv',index=False)
    if not args.skip_chronos:
        import torch
        from chronos import Chronos2Pipeline
        torch.set_num_threads(4)
        pipeline=Chronos2Pipeline.from_pretrained(config['checkpoint'],revision=config['revision'],device_map='cpu')
        for mode in MODES:
            cache=out/f'chronos_{mode}.csv'
            if cache.exists():
                records.extend(pd.read_csv(cache).to_dict('records'));print('Cached Chronos:',mode,flush=True);continue
            cr=[]
            for start in range(0,len(tasks),6):
                group=tasks[start:start+6];context=[];future=[]
                for i,(state,o,hist,cal,cols,observed,festival,scale) in enumerate(group):
                    f=pd.DataFrame({'id':str(i),'timestamp':hist.index,'target':hist.values})
                    for c in cols[mode]:f[c]=cal.loc[hist.index,c].values
                    context.append(f)
                    dates=pd.date_range(o,periods=14);fut=pd.DataFrame({'id':str(i),'timestamp':dates})
                    for c in cols[mode]:fut[c]=cal.loc[dates,c].values
                    future.append(fut)
                predictions=pipeline.predict_df(pd.concat(context,ignore_index=True),future_df=pd.concat(future,ignore_index=True) if cols[mode] else None,prediction_length=14,quantile_levels=[.1,.5,.9],id_column='id',timestamp_column='timestamp',target='target',cross_learning=False)
                for i,(state,o,hist,cal,cols,observed,festival,scale) in enumerate(group):
                    q=predictions[predictions.id.astype(str)==str(i)].sort_values('timestamp')
                    assert len(q)==14
                    for h in config['horizons']:
                        add(cr,state,o,o+pd.Timedelta(days=h-1),h,'chronos2',mode,float(q.iloc[h-1]['0.5']),observed,festival,scale)
            pd.DataFrame(cr).to_csv(cache,index=False);records.extend(cr);print('Chronos complete:',mode,flush=True)
    predictions=pd.DataFrame(records);predictions.to_csv(out/'predictions.csv',index=False)
    (out/'run.json').write_text(json.dumps({'seconds':time.perf_counter()-started,'chronos_included':not args.skip_chronos,'python':platform.python_version(),'versions':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scikit-learn','statsmodels','holidays']},'prediction_rows':len(predictions)},indent=2))
    print('SAVED',out,flush=True)
    return out

def add(rows,state,origin,date,h,model,mode,pred,observed,festival,scale):
    truth=observed.get(date,np.nan)
    rows.append({'state':state,'origin':str(origin.date()),'date':str(date.date()),'year':date.year,'horizon':h,'model':model,'mode':mode,'actual':truth,'prediction':float(pred),'observed':int(pd.notna(truth)),'festival_window':int(festival.loc[date]),'mase_scale':scale})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',choices=['original','latest'],default='original');parser.add_argument('--stride',type=int,default=28);parser.add_argument('--skip-chronos',action='store_true');a=parser.parse_args()
    if a.stride<1:parser.error('stride must be positive')
    execute(a)
