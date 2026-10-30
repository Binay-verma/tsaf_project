"""CPU smoke test only. No final holdout evaluation; failures recorded explicitly."""
from pathlib import Path
import json,time,traceback
p=Path(__file__).resolve().parents[1]
t=time.perf_counter()
try:
    import pandas as pd
    import torch
    from chronos import Chronos2Pipeline
    from huggingface_hub import model_info
    torch.set_num_threads(4)
    info=model_info('amazon/chronos-2')
    pipe=Chronos2Pipeline.from_pretrained('amazon/chronos-2',revision=info.sha,device_map='cpu')
    data=pd.read_csv(p/'data/clean_daily_energy_GWh.csv',parse_dates=['date']).set_index('date')
    # Single origin on development-year Diwali; context ends the previous day.
    past=data.loc[:'2022-10-23','Delhi'].tail(730).ffill()
    frame=pd.DataFrame({'id':'Delhi','timestamp':past.index,'target':past.values})
    forecast=pipe.predict_df(frame,prediction_length=1,quantile_levels=[.1,.5,.9],id_column='id',timestamp_column='timestamp',target='target')
    forecast.to_csv(p/'results/chronos_smoke_forecast.csv',index=False)
    status={'status':'passed','checkpoint':'amazon/chronos-2','revision':info.sha,'origin':'2022-10-24','device':'cpu','seconds':time.perf_counter()-t,'note':'Single-origin history-only smoke test. Not a model evaluation.'}
except Exception as e:
    status={'status':'blocked','exception_type':type(e).__name__,'reason':str(e),'seconds':time.perf_counter()-t}
    traceback.print_exc()
(p/'results/chronos_status.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status,indent=2))
