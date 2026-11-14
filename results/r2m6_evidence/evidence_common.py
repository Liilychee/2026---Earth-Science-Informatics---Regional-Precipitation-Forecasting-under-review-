"""Read only from pinned git blobs. No model framework is imported."""
from pathlib import Path
from io import BytesIO
import subprocess,hashlib,json
import pandas as pd
import numpy as np
COMMIT='d02519c5f153feb712018cf97efb035f6ca2d7ae'
OUT=Path(__file__).resolve().parent
SEEDS=[42,123,7,2024,99]
CONFIGS={'Gaussian':'gaussian','Tobit':'tobit__dry0','Bernoulli-gamma':'bergamma__dry0','Tobit (dry 0.001)':'tobit__dry0.001','Bernoulli-gamma (dry 0.001)':'bergamma__dry0.001'}
ZERO_TOL=1e-6;Q95=.574048

def blob(path):return subprocess.check_output(['git','show',COMMIT+':'+path])
def frame(path):return pd.read_csv(BytesIO(blob(path)))
def load(config,seed):
 path='results/q11/preds/'+CONFIGS[config]+'__s'+str(seed)+'.csv'
 d=frame(path);d=d[d['split']=='test'].reset_index(drop=True)
 assert len(d)==3939
 y=np.where(d.y_true.to_numpy()<=ZERO_TOL,0.,d.y_true.to_numpy())
 return d,y

def write_csv(rows,name):
 pd.DataFrame(rows).to_csv(OUT/name,index=False,float_format='%.17g')
