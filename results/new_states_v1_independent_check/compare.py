import pandas as pd, numpy as np, runpy, sys
g=runpy.run_path('indep.py')
A='/home/claude/handoff/repo/results/new_states_v1/analysis/'
for k,f,drop,cells in [('primary','hypothesis_tests.csv',(),None),('no2020_2021','sensitivity_without_2020_2021.csv',(2020,2021),None),('official_only','sensitivity_official_sources_only.csv',(),g['official_cells'])]:
    o=pd.read_csv(A+f).set_index('hypothesis'); m=g['res'][k].set_index('h')
    for h,mod in [('H1','sarimax'),('H2','timesfm'),('H3','lightgbm_capacity2')]:
        cl=g['clusters'](g['cellvals'](g['dfs'][mod]),drop,cells); yr=cl.groupby('year').d.mean()
        dy=max(abs(yr[y]-o.loc[h,f'year_{y}']) for y in yr.index)
        print(k,h,'effect diff %.2e'%abs(m.effect[h]-o.typed_minus_pooled[h]),'max year-mean diff %.2e'%dy,
          'p diff %.5f'%abs(m.p[h]-o.p_one_sided[h]),'popp diff %.5f'%abs(m.p_opp[h]-o.p_opposite[h]),'holm diff %.5f'%abs(m.p_holm[h]-o.holm[h]),
          'yrs',m.years_in_dir[h],o.years_in_direction[h],'clusters',m.n_clusters[h],o.clusters[h], m.decision_6of9[h],o.decision[h])
