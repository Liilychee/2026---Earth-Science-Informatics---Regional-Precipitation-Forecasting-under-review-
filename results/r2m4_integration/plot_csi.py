# coding: utf-8
"""Plot saved CSV CSI values only. PGF/pdflatex adapter for archived fig_style.py; no metric estimation."""
from pathlib import Path
import os,sys,json
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/esi-r2m4-mpl')
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
sys.path.insert(0,str(P/'evidence') if (P/'evidence/fig_style.py').exists() else str(ROOT/'code'))
import fig_style as fs
# This machine lacks dvipng/Poppler CLI. Only PDF is produced via PGF/pdflatex; fitz renders it for QA.
fs.PROGRAMS=['latex','kpsewhich']
fs.apply()
import matplotlib as mpl
mpl.rcParams.update({'pgf.texsystem':'pdflatex','pgf.rcfonts':False,'pgf.preamble':fs.PREAMBLE,'figure.constrained_layout.use':False})
from matplotlib.backends.backend_pgf import FigureCanvasPgf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
def source(n):
 return P/'evidence'/n if (P/'evidence'/n).exists() else ROOT/'results/metrics'/n
fixed=pd.read_csv(source('r2m4_fixed_event_scores.csv'));tuned=pd.read_csv(source('q05e_event_scores.csv'))
tuned['Model']=tuned.Model.map(fs.name);fixed['Model']=fixed.Model.map(fs.name)
models=['XGBoost','Transformer','BU-LSTM','BiLSTM-Attention','BU-LSTM-Attention','Prob. BiLSTM-Attention','Persistence']
keys=['wet>=0.1','Q90','0.5 mm','Q95','Q97.5','1.0 mm'];tkeys=['wet>=0.1','Q90',None,'Q95','Q97.5','1.0']
fig,axes=plt.subplots(2,1,figsize=(fs.FULL_W,145*fs.MM),sharey=True);FigureCanvasPgf(fig)
fig.subplots_adjust(left=.125,right=.975,bottom=.12,top=.79,hspace=.62)
points=[]
for ai,ax in enumerate(axes):
 for mi,m in enumerate(models):
  xx=[];yy=[]
  for k,x in enumerate(keys):
   t=(x if ai==0 else tkeys[k])
   if t is None:continue
   d=fixed if ai==0 else tuned;r=d[(d.Model==m)&(d.Threshold==t)].iloc[0]
   xx.append(k+(mi-3)*.095);yy.append(float(r.CSI));points.append(dict(panel='fixed' if ai==0 else 'validation-selected',model=m,threshold=t,CSI=float(r.CSI),source='r2m4_fixed_event_scores.csv' if ai==0 else 'q05e_event_scores.csv'))
  ax.scatter(xx,yy,s=19,color=fs.color(m),marker=fs.marker(m),linewidths=.8,label=fs.tex(m),zorder=3)
 ax.set_xlim(-.48,5.48);ax.set_ylim(-.014,.46);ax.set_yticks([0,.1,.2,.3,.4]);ax.set_ylabel('CSI')
 ax.set_xticks(range(6));ax.set_xticklabels([lab+'\n'+format(float(fixed[fixed.Threshold==key].iloc[0].thr_mm_h),'.4f') for lab,key in zip(['Wet','Q90','0.5','Q95','Q97.5','1.0'],keys)])
 ax.grid(axis='y',color='.88',linewidth=.5,zorder=0)
 ax.set_title((r'\textbf{(A)} Fixed cutoff: $c_\tau=\tau$' if ai==0 else r'\textbf{(B)} Validation-selected cutoff $c_\tau$'),loc='left',pad=9)
 ax.set_xlabel(r'Event threshold $\tau$ (mm\,h$^{-1}$)',labelpad=5)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.52,.995),ncol=2,columnspacing=1.5,handletextpad=.45,labelspacing=.45)
assert not fs.color_problems(fig)
assert all(sz>=8 for sz,tx in fs._font_sizes(fig))
out=P.parents[1]/'Figures/r2M4_event_csi_comparison.pdf';assert not out.exists(),'Refuse overwriting existing figure'
fig.savefig(out)
(P/'FIGURE_POINTS.json').write_text(json.dumps(points,indent=2))
import fitz
pdf=fitz.open(out);pg=pdf[0];pg.get_pixmap(matrix=fitz.Matrix(2,2)).save(P/'figure_preview.png')
fonts=sorted(set(f[3].split('+')[-1] for f in pg.get_fonts()));assert all(fs.FONT_OK.match(f) for f in fonts),fonts
print('Saved',out,'size mm',pg.rect.width*25.4/72,pg.rect.height*25.4/72,'fonts',fonts)
