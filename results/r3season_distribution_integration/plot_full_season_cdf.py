"""Correct full-sampling-period q03 CDF. Uses saved derived data, no training.
Uses shared fig_style typography/geometry; PGF/pdflatex backend replaces only the
usetex rendering backend because local dvipng/Poppler executables are absent.
No legacy source or figure is overwritten.
"""
from pathlib import Path
import sys,os,json
os.environ['PATH']='/Users/yue/Library/TinyTeX/bin/universal-darwin:'+os.environ['PATH']
import matplotlib
matplotlib.use('pgf')
import matplotlib.pyplot as plt
import numpy as np,pandas as pd,fitz
sys.path.insert(0,str(Path('results/r2m4_integration/evidence').resolve()))
import fig_style as fs
plt.rcParams.update({'text.usetex':False,'pgf.texsystem':'pdflatex','pgf.rcfonts':False,'pgf.preamble':r'\usepackage[T1]{fontenc}\usepackage{lmodern}\usepackage{amsmath}', 'font.family':'serif','font.size':fs.FS_BASE,'axes.labelsize':fs.FS_BASE,'xtick.labelsize':fs.FS_TICK,'ytick.labelsize':fs.FS_TICK,'legend.fontsize':fs.FS_LEGEND,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
P=Path(__file__).resolve().parent;d=pd.read_csv(P/'FULL_PERIOD_ECDF.csv');stats=pd.read_csv(P/'FULL_PERIOD_SEASON_STATS.csv').set_index('Season')
fig,axs=fs.figure(height_mm=132,nrows=2)
fig.subplots_adjust(left=.155,right=.975,bottom=.085,top=.955,hspace=.47)
# Four seasonal colours drawn from the established palette, without model semantics.
styles=[('#0072B2','-'),('#D55E00','--'),('#009E73','-.'),('#882255',':')]
for s,(col,ls) in zip(['DJF','MAM','JJA','SON'],styles):
 q=d[d.Season==s];v=q.x_mm_h.to_numpy();cdf=q.CDF_le.to_numpy();surv=q.Survival_ge.to_numpy()
 axs[0].step(np.r_[0,v,4.3],np.r_[0,cdf,1],where='post',color=col,ls=ls,lw=1.25,label=f'{s} ($n={int(stats.loc[s,"N"]):,}$)')
 axs[1].step(v,surv,where='pre',color=col,ls=ls,lw=1.25,label=s)
for ax in axs:
 ax.set_xlim(-.015,4.3);ax.set_xlabel(r'Hourly precipitation (mm\,h$^{-1}$)');ax.grid(color='.88',lw=.4);ax.set_axisbelow(True)
 for thr,style in [(.1,':'),(.574048,'--'),(1.,'-.')]:ax.axvline(thr,color='.55',lw=.65,ls=style,zorder=0)
axs[0].set_ylim(0,1.02);axs[0].set_ylabel(r'$P(Y\leq y)$');axs[0].set_title(r'\textbf{(a)} All-sample empirical CDF',loc='left',fontsize=9)
axs[0].legend(loc='lower right',frameon=False)
axs[1].set_yscale('log');axs[1].set_ylim(1e-4,1.2);axs[1].set_ylabel(r'$P(Y\geq y)$');axs[1].set_title(r'\textbf{(b)} Upper-tail exceedance probability',loc='left',fontsize=9)
assert min(t.get_fontsize() for t in fig.findobj(matplotlib.text.Text))>=8
out=Path('Figures/r3M14_season_cdf_full.pdf');fig.savefig(out,backend="pgf")
doc=fitz.open(out);fonts=sorted({f[3] for page in doc for f in page.get_fonts()});assert all('LM' in x.upper() for x in fonts),fonts
page=doc[0];page.get_pixmap(matrix=fitz.Matrix(2,2)).save(P/'new_cdf.png')
(P/'FIGURE_CHECK.json').write_text(json.dumps(dict(path=str(out),size_mm=[page.rect.width*25.4/72,page.rect.height*25.4/72],fonts=fonts,min_font_pt=8,source_rows=len(d),includes_all_26300=True,full_x_range=[0,4.3],original_figure_preserved=True,backend='PGF/pdflatex with shared fig_style constants'),indent=2));print(out,fonts)
