"""All pairwise representation contrasts and dependent-cell sensitivities."""
import argparse,itertools,json
from datetime import datetime,timezone
from collections import defaultdict
from statistics import mean
import pandas as pd
from calendar_recenter_study import ROOT,OUT,ARMS,ENCODINGS
from festival_feature_design import sha,dump
from audit_breadth_study import read,close


def register():
    path=OUT/'contrast_registration.json'
    if path.exists():raise FileExistsError('Preserve contrast registration')
    dump(path,dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),
        policy='Fixedbefore complete newfoundation/recenteredresults. Reuses originalpooling/encoding questions; allpairwisecontrasts retained, no favourablepair choice or multiple-testingclaim.',
        breadth_pairs=list(itertools.combinations(ARMS,2)),encoding_pairs=list(itertools.combinations(ENCODINGS+['calendar'],2)),
        aggregation='Matched family/state/year/lead cell differences, then equalstates/years/families. Bothyear results and leave-onefamily-out composition for eventwindows. Descriptiveonly; serialtargets/states/leads correlated, twoeventyears insufficient for preciseannualsamplinginference.'))


def main(part):
    reg=json.loads((OUT/'contrast_registration.json').read_text());assert sha(__file__)==reg['source_sha256']
    base=OUT/('local_checkpoint' if part=='local' else 'analysis');assert json.loads((base/'independent_audit.json').read_text())['status']=='pass'
    dest=base/'contrasts'
    if dest.exists():raise FileExistsError('Preserve prior contrasts')
    dest.mkdir();summaries={}
    for kind in (['breadth'] if part=='local' else ['breadth','encoding']):
        for cohort in ['event_window','ordinary']:
            out=dest/kind/cohort;out.mkdir(parents=True)
            cells=pd.read_csv(base/kind/cohort/'metrics_state_year.csv');cells=cells[cells.version.eq('document_aligned')]
            keys=['family','model','state','year','horizon'];paired=[]
            for arm,reference in reg[kind+'_pairs']:
                d=cells[cells.arm.eq(arm)].merge(cells[cells.arm.eq(reference)],on=keys,suffixes=('_arm','_reference'),validate='one_to_one')
                assert len(d)>0;d['arm']=arm;d['reference']=reference;d['MASE_change']=d.MASE_arm-d.MASE_reference;d['MAE_change_GWh']=d.MAE_GWh_arm-d.MAE_GWh_reference
                paired.append(d[keys+['arm','reference','MASE_change','MAE_change_GWh']])
            d=pd.concat(paired);d.to_csv(out/'state_year.csv',index=False);fields=['MASE_change','MAE_change_GWh']
            y=d.groupby(['family','model','arm','reference','year','horizon'])[fields].mean().reset_index();y.to_csv(out/'year.csv',index=False)
            f=y.groupby(['family','model','arm','reference','horizon'])[fields].mean().reset_index();f.to_csv(out/'family.csv',index=False)
            m=f.groupby(['model','arm','reference','horizon'])[fields].mean().reset_index();m.to_csv(out/'balanced.csv',index=False)
            if cohort=='event_window':
                omit=[]
                for family in sorted(f.family.unique()):
                    table=f[~f.family.eq(family)].groupby(['model','arm','reference','horizon'])[fields].mean().reset_index();table['omitted_family']=family;omit.append(table)
                pd.concat(omit).to_csv(out/'leave_family_out.csv',index=False)
            # Separate scalar grouping validates every table against audited cells.
            raw=read(base/kind/cohort/'metrics_state_year.csv');bycell={tuple(r[k] for k in keys)+ (r['arm'],):float(r['MASE']) for r in raw if r['version']=='document_aligned'}
            ys=defaultdict(list);fs=defaultdict(list);ms=defaultdict(list)
            for r in read(out/'state_year.csv'):
                k=tuple(r[k] for k in keys);value=bycell[k+(r['arm'],)]-bycell[k+(r['reference'],)];close(value,r['MASE_change'])
                ys[r['family'],r['model'],r['arm'],r['reference'],r['year'],r['horizon']].append(value)
            for r in read(out/'year.csv'):
                k=tuple(r[k] for k in ['family','model','arm','reference','year','horizon']);value=mean(ys[k]);close(value,r['MASE_change']);fs[k[:4]+(k[-1],)].append(value)
            for r in read(out/'family.csv'):
                k=tuple(r[k] for k in ['family','model','arm','reference','horizon']);value=mean(fs[k]);close(value,r['MASE_change']);ms[k[1:]].append(value)
            for r in read(out/'balanced.csv'):close(mean(ms[tuple(r[k] for k in ['model','arm','reference','horizon'])]),r['MASE_change'])
            if cohort=='event_window':
                for r in read(out/'leave_family_out.csv'):
                    key=tuple(r[k] for k in ['model','arm','reference','horizon']);values=[mean(v) for k,v in fs.items() if k[0]!=r['omitted_family'] and k[1:]==key];close(mean(values),r['MASE_change'])
            summaries[kind+'/'+cohort]=dict(pairs=len(reg[kind+'_pairs']),balanced_cells=len(m),cell_pairs=len(d),balanced_sha256=sha(out/'balanced.csv'))
    dump(dest/'audit.json',dict(status='pass',scope='Separate scalar contrast/hierarchy/composition calculations from previously audited pointcells; not newforecast or independenthuman significance evidence.',cohorts=summaries,registration_sha256=sha(OUT/'contrast_registration.json')))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','analyze']);p.add_argument('--part',choices=['local','all'],default='all');a=p.parse_args();register() if a.action=='register' else main(a.part)
