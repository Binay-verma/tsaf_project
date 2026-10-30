"""Unscored future bands, clearly separated from recorded past observations."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/prospective_interval_20261030_v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (OUT/'plot_metadata.json').exists():raise FileExistsError('Preserveforecastpreview')
    freeze=json.loads((OUT/'freeze.json').read_text());assert sha(OUT/'predictions.csv')==freeze['predictions_sha256']
    future=pd.read_csv(OUT/'predictions.csv',parse_dates=['date'])
    data=pd.read_csv(ROOT/'data/external/latest_state_energy_GWh.csv',index_col=0,parse_dates=True)
    assert data.index.max()==pd.Timestamp('2026-10-28')
    fig,axes=plt.subplots(3,2,figsize=(13,9),sharex=True)
    for i,state in enumerate(['Delhi','Karnataka','Maharashtra']):
        for j,mode in enumerate(['history','calendar']):
            ax=axes[i,j];model='timesfm3_'+mode
            recorded=data[state].loc['2026-10-15':'2026-10-28'];assert recorded.notna().all()
            ax.plot(recorded.index,recorded.values,color='black',linewidth=1.7,label='Recorded past')
            group=future[future.state.eq(state)&future.model.eq(model)]
            native=group[group.arm.eq('native')].sort_values('date')
            ax.plot(native.date,native.prediction,'--',color='#215b9f',linewidth=1.5,label='Unchanged forecast point')
            ax.fill_between(native.date,native.lower,native.upper,color='#80aedd',alpha=.25,label='Native 80%')
            for arm,color,label in [('frozen_september','#cc7b19','Frozen Sept CQR'),('expanding_past','#98528b','Expanding past CQR')]:
                g=group[group.arm.eq(arm)].sort_values('date');ax.plot(g.date,g.lower,color=color,linewidth=1,label=label);ax.plot(g.date,g.upper,color=color,linewidth=1)
            ax.axvspan(pd.Timestamp('2026-10-28 12:00'),pd.Timestamp('2026-10-30 12:00'),color='grey',alpha=.12)
            ax.axvline(pd.Timestamp('2026-10-30 12:00'),color='grey',linestyle=':',linewidth=1)
            ax.set_title(state+' · TimesFM '+mode,fontsize=11);ax.set_ylabel('Energy supplied (GWh)');ax.grid(alpha=.18)
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5));ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=5,fontsize=9,bbox_to_anchor=(.5,.065))
    fig.suptitle('Prospective interval annex · future outcomes pending',fontsize=15)
    fig.text(.5,.02,'Recorded context ends 28 Oct; original forecast origin 29 Oct; annex issued 30 Oct, 20:42 IST.\nGrey forecast dates 29–30 Oct excluded; prospective targets 31 Oct–11 Nov. Nominal 80% is not a coverage guarantee.',ha='center',fontsize=10)
    fig.tight_layout(rect=[0,.13,1,.95])
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'forecast_preview.{ext}',dpi=190)
    plt.close(fig)
    svg=OUT/'forecast_preview.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    (OUT/'plot_metadata.json').write_text(json.dumps(dict(status='created_unscored_preview',annex_sha256=freeze['predictions_sha256'],known_context_end='2026-10-28',prospective_eligible_start='2026-10-31',future_actuals_included=False,all_states_modes_and_interval_arms_shown=True,no_model_inference=True,outputs={ext:sha(OUT/f'forecast_preview.{ext}') for ext in ['png','pdf','svg']}),indent=2)+'\n')
    print('Created clearly labelled future forecast preview; no outcomes/scoring')


if __name__=='__main__':main()
