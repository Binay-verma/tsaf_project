"""Separate estimator/score audit; shares the registered generator explicitly."""
import json,math
import numpy as np
import pandas as pd
from pooling_simulation import OUT,ROOT,generate
from festival_feature_design import sha,dump


def main():
    p=json.loads((OUT/'protocol.json').read_text())
    for f,h in p['input_hashes'].items():assert sha(ROOT/f)==h,f
    r=json.loads((OUT/'run.json').read_text());d=pd.read_csv(OUT/'seed_results.csv')
    assert r['seed_results_sha256']==sha(OUT/'seed_results.csv') and len(d)==2560
    assert not d.duplicated(['frequency','heterogeneity','date_error','noise','seed','method']).any()
    maxdiff=0.
    for scenario in p['scenarios']:
        for seed in p['seeds']:
            truth,x,y,beta,_=generate(seed,**scenario)
            train=x[:730];label=y[:730];xx=train.sum(axis=1)
            pooled=float(np.sum(xx*label)/np.sum(xx**2))
            # Independent normal-equation implementation for this full-rank design.
            gram=np.einsum('ni,nj->ij',train,train)
            rhs=np.einsum('ni,n->i',train,label)
            typed=np.linalg.solve(gram,rhs)
            partial=np.linalg.solve(gram+2*np.eye(5),rhs+2*pooled)
            b={'no_event':np.zeros(5),'pooled_OLS':np.repeat(pooled,5),'typed_OLS':typed,
                'partial_pooling_fixed2':partial,'oracle_true_effect':beta}
            g=d[d.seed.eq(seed)]
            for k,v in scenario.items():g=g[g[k].eq(v)]
            assert set(g.method)==set(p['methods']) and len(g)==5
            event=truth[730:].any(axis=1)
            for row in g.itertuples(index=False):
                query=truth[730:] if row.method=='oracle_true_effect' else x[730:]
                error=np.abs(y[730:]-np.sum(query*b[row.method],axis=1))
                for field,value in [('MAE_all',error.mean()),('MAE_event',error[event].mean()),
                    ('MAE_ordinary',error[~event].mean()),('coefficient_MSE',np.mean((b[row.method]-beta)**2))]:
                    diff=abs(float(getattr(row,field))-value);maxdiff=max(maxdiff,diff)
                    assert diff<1e-10
    keys=['frequency','heterogeneity','date_error','noise']
    for row in pd.read_csv(OUT/'paired_seed_contrasts.csv').itertuples(index=False):
        a=d.copy()
        for k in keys:a=a[a[k].eq(getattr(row,k))]
        a=a.pivot(index='seed',columns='method',values='MAE_event')
        delta=a[row.arm]-a[row.reference]
        assert len(delta)==32 and math.isclose(delta.mean(),row.event_MAE_difference,abs_tol=1e-10)
        se=delta.std(ddof=1)/np.sqrt(32)
        assert math.isclose(se,row.MC_standard_error,abs_tol=1e-10)
        assert math.isclose(delta.mean()-1.96*se,row.MC95_low,abs_tol=1e-10)
        assert math.isclose(delta.mean()+1.96*se,row.MC95_high,abs_tol=1e-10)
    dump(OUT/'independent_audit.json',dict(status='pass',cells=2560,datasets=512,
        max_metric_difference=maxdiff,scope='Separate normal-equation estimator, test-mask and score/paired-MonteCarlo arithmetic. Shares registered generator; does not independently validate generator assumptions or real-data claims.'))
    print('PASS2560simulation cells and48paired contrasts')


if __name__=='__main__':main()
