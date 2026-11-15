# -*- coding: utf-8 -*-
"""Read retained original regional timestamps and saved prediction indices; no training or scoring."""
from pathlib import Path
import hashlib,json,subprocess,io,csv
import pandas as pd
P=Path(__file__).resolve().parent;data=Path('/Users/yue/Interpretable-BU-LSTM-for-Rainfall-Prediction-in-Dublin/data/dublin_regional_2004_2021.csv');b=data.read_bytes();t=pd.to_datetime(pd.read_csv(io.BytesIO(b),usecols=['valid_time']).valid_time,utc=True)
assert len(t)==26300 and not t.duplicated().any() and t.is_monotonic_increasing and t.diff().dropna().eq(pd.Timedelta(hours=6)).all()
parts=[('Training',0,int(len(t)*.70)),('Validation',int(len(t)*.70),int(len(t)*.85)),('Testing',int(len(t)*.85),len(t))];rows=[]
fmt=lambda x:x.strftime('%Y-%m-%d %H:%M')
for name,a,z in parts:
 part=t.iloc[a:z];targets=part.iloc[6:];row=dict(partition=name,raw_first=fmt(part.iloc[0]),raw_last=fmt(part.iloc[-1]),raw_n=len(part),target_first=fmt(targets.iloc[0]),target_last=fmt(targets.iloc[-1]),target_n=len(targets),dropped_initial=6,first_target_source_row=a+8,last_target_source_row=z+1)
 assert targets.iloc[0]-part.iloc[0]==pd.Timedelta(hours=36);assert part.iloc[5]-part.iloc[0]==pd.Timedelta(hours=30);assert part.iloc[6]-part.iloc[5]==pd.Timedelta(hours=6);rows.append(row)
expected=[('2004-01-01 00:00','2016-08-07 06:00',18410,'2004-01-02 12:00',18404),('2016-08-07 12:00','2019-04-20 12:00',3945,'2016-08-09 00:00',3939),('2019-04-20 18:00','2021-12-31 18:00',3945,'2019-04-22 06:00',3939)]
for r,e in zip(rows,expected):assert (r['raw_first'],r['raw_last'],r['raw_n'],r['target_first'],r['target_n'])==e
# One original saved-run prediction index corroborates validation/test target times.
commit='d02519c5f153feb712018cf97efb035f6ca2d7ae';pred='results/q21/preds/bilstm_attn__w6__C0__mse__s42.csv';pb=subprocess.check_output(['git','show',commit+':'+pred]);d=pd.read_csv(io.BytesIO(pb),usecols=['split','valid_time'])
for split,(name,a,z) in zip(['val','test'],parts[1:]):
 tt=pd.to_datetime(d.loc[d.split==split,'valid_time'],utc=True).reset_index(drop=True);assert tt.equals(t.iloc[a+6:z].reset_index(drop=True))
# Copy only small source code/log, never raw data or predictions.
source=[]
for path in ['code/q10_prepare_data.py','results/metrics/q10_prepare_output.txt']:
 raw=subprocess.check_output(['git','show','6495abc81101074b02b3a5c8cfc83cd6cbc33d79:'+path]);(P/'source'/Path(path).name).write_bytes(raw);source.append(dict(path=path,commit='6495abc81101074b02b3a5c8cfc83cd6cbc33d79',md5=hashlib.md5(raw).hexdigest()))
source+=[dict(path=str(data),md5=hashlib.md5(b).hexdigest(),bytes=len(b),used_column='valid_time',note='Original retained regional series, not re-downloaded or regenerated; no precipitation metrics computed'),dict(path=pred,commit=commit,md5=hashlib.md5(pb).hexdigest(),used_columns=['split','valid_time'])]
with (P/'SPLIT_INDEX.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(P/'SOURCE_INDEX.json').write_text(json.dumps(source,indent=2));(P/'DATE_CHECK.json').write_text(json.dumps(dict(total_raw=26300,time_zone='UTC',frequency_hours=6,no_duplicates=True,no_missing_timestamps=True,splits=rows,prediction_times_match=True,window=6,input_span_hours=30,lead_hours=6,first_target_offset_hours=36,windows_constructed_after_partition=True,no_cross_partition_windows=True),indent=2));print(json.dumps(rows,indent=2))
