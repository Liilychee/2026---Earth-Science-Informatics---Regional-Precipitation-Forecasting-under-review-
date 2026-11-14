r"""
fig_style.py — shared figure style for the ESI revision (all main-text and supplementary figures).

Fonts: text is typeset by LaTeX (matplotlib text.usetex) with \usepackage[T1]{fontenc} and
\usepackage{lmodern}, i.e. the same Latin Modern Type 1 fonts (LMRoman*, LMMathItalic*, LMMathSymbols*)
that pdflatex embeds in manuscript.pdf. Text, math, superscripts, minus signs and units therefore match
the body text. cmr10 is NOT used.

Usage in every plotting script:
    import sys; sys.path.insert(0, "/root/autodl-tmp/code")
    import fig_style as fs
    fs.apply()                      # stops with an install hint if LaTeX / Latin Modern is missing
    fig, axes = fs.figure(height_mm=80, ncols=2)
    ...
    fs.panel_label(axes[0], "a"); fs.panel_label(axes[1], "b")
    fs.save(fig, "r1M1_prediction_distribution")   # PDF + EPS + PNG; size, layout and font checks

Rules (do not override in individual scripts):
- Figures are drawn at their final printed size: width = \textwidth of revised.tex
  (338.58778 pt = 119.1 mm, sn-jnl referee layout). In LaTeX insert WITHOUT scaling:
  \includegraphics{r1M1_prediction_distribution.pdf}   (no width= option), so 9 pt in the script is 9 pt in the PDF.
- No bbox_inches="tight" (it changes the canvas size); layout is handled by constrained_layout.
- Minimum font size 8 pt; save() refuses to finish if any text is smaller.
- save() reads the fonts actually embedded in the PDF and refuses to finish if any is not Latin Modern.
- save() stops if text boxes overlap each other or are clipped by the figure edge, but it cannot see text
  covering lines, bars or markers: every PDF must still be inspected visually at 100 %.
- File names: <comment>_<content>, e.g. r1M1_prediction_distribution (R1 major 1), r4m14_study_region
  (R4 minor 14); save() rejects other names and names that differ from an existing file only in case.
  The journal names (Fig1.eps, ...) are assigned only at submission, after figure numbers are final.
- Model names come from fs.name(); colours ONLY from fs.color(model) (never color="red" etc.), observations
  in fs.OBSERVED_COLOR, everything else in greys. save() refuses any other colour.
- Wet labels: fs.WET / fs.WET_SHORT for the revised definition (>= 0.1 mm h-1); fs.LEGACY_WET only for
  results of the original manuscript (target > 0).
- Text is LaTeX: the characters # $ % & _ { } ~ ^ \ in strings read from CSV files must go through tex().
  The symbols ≥ ≤ × − – ± ° are mapped to LaTeX automatically, so they can be typed directly.

Requirements on the machine (AutoDL / Ubuntu):
    latex, dvips, dvipng (matplotlib usetex), pdftops + pdftoppm (poppler-utils, for EPS and PNG),
    LaTeX packages lmodern, type1cm, fix-cm, geometry, underscore, textcomp, helvet, courier,
    newunicodechar, amsmath (cm-super is NOT needed).
    Check:   python3 code/fig_style.py --check
    Install: apt-get update && apt-get install -y texlive-latex-base texlive-latex-recommended \
             texlive-latex-extra texlive-fonts-recommended lmodern dvipng poppler-utils
    Self-test (writes r1M1_style_test.pdf/.eps/.png and lists the embedded fonts):
             python3 code/fig_style.py --test
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------- page geometry (unchanged)
PT_PER_IN = 72.27                          # TeX points
TEXTWIDTH_PT = 338.58778                   # \the\textwidth of revised.tex (2026-11-13)
FULL_W = TEXTWIDTH_PT / PT_PER_IN          # inches, = 4.685 in = 119.1 mm
MM = 1 / 25.4
MAX_H = 180 * MM                           # keep a figure plus caption on one page

# ---------------------------------------------------------------- font sizes (pt, unchanged)
FS_BASE = 9      # axis labels, titles
FS_TICK = 8      # tick labels
FS_LEGEND = 8
FS_PANEL = 10    # (a), (b) panel labels, bold
FS_MIN = 8       # hard lower limit, checked in save()

# ---------------------------------------------------------------- fixed wording (LaTeX)
UNIT = r"mm\,h$^{-1}$"
UPPER_TAIL = r"Upper tail ($\geq$Q95)"
WET = r"Wet ($\geq$0.1 mm\,h$^{-1}$)"      # revised wet definition (target >= 0.1 mm h-1)
WET_SHORT = r"Wet ($\geq$0.1)"               # same, for tick labels
LEGACY_WET = r"Legacy wet ($>$0)"            # ONLY for results of the original manuscript (target > 0)
ALL = "All test cases"

# ---------------------------------------------------------------- model names and colours (unchanged)
# Okabe–Ito colour-blind-safe palette for trained models; greys and black for references.
MODEL_NAME = {
    "xgboost": "XGBoost",
    "bilstm_attn": "BiLSTM-Attention",
    "bilstm_noattn": "BiLSTM-NoAttention",
    "transformer": "Transformer",
    "bulstm": "BU-LSTM",
    "bulstm_attn": "BU-LSTM-Attention",
    "prob_bilstm_attn": "Prob. BiLSTM-Attention",
    "persistence": "Persistence",
    "clim_month_hour": "Climatology (month × hour)",
    "ar1": "AR(1)",
    "ridge_l1": "Ridge regression",
    "hres": "IFS HRES",
    "probabilistic bilstm-attention": "Prob. BiLSTM-Attention",   # name used in the original CSV files
}
COLOR = {
    "XGBoost": "#E69F00",
    "BiLSTM-Attention": "#0072B2",
    "BiLSTM-NoAttention": "#56B4E9",
    "Transformer": "#CC79A7",
    "BU-LSTM": "#009E73",
    "BU-LSTM-Attention": "#D55E00",
    "Prob. BiLSTM-Attention": "#882255",   # wine (Okabe–Ito yellow is too faint for lines)
    "Persistence": "#000000",
    "Climatology (month × hour)": "#7F7F7F",
    "AR(1)": "#4D4D4D",
    "Ridge regression": "#B3B3B3",
    "IFS HRES": "#7A5195",
}
OBSERVED_COLOR = "#BDBDBD"     # observations (ERA5 target) in every figure
# Colours allowed in a figure: the model/reference colours above, OBSERVED_COLOR, and neutral greys
# (black ... white) for axes, grids and reference lines. save() rejects any other colour.
ALLOWED_COLORS = {c.upper() for c in COLOR.values()} | {OBSERVED_COLOR.upper()}

MARKER = {
    "XGBoost": "s", "BiLSTM-Attention": "o", "BiLSTM-NoAttention": "o",
    "Transformer": "^", "BU-LSTM": "D", "BU-LSTM-Attention": "v",
    "Prob. BiLSTM-Attention": "P", "Persistence": "x", "Climatology (month × hour)": "_",
    "AR(1)": "+", "Ridge regression": "*", "IFS HRES": "h",
}
MODEL_ORDER = ["XGBoost", "BiLSTM-Attention", "BiLSTM-NoAttention", "Transformer", "BU-LSTM",
               "BU-LSTM-Attention", "Prob. BiLSTM-Attention"]
REF_ORDER = ["Persistence", "Climatology (month × hour)", "AR(1)", "Ridge regression", "IFS HRES"]

# ---------------------------------------------------------------- LaTeX set-up
PREAMBLE = "\n".join([
    r"\usepackage[T1]{fontenc}",
    r"\usepackage{lmodern}",            # Latin Modern, as in manuscript.pdf (text and math)
    r"\usepackage{amsmath}",
    r"\usepackage{newunicodechar}",
    r"\newunicodechar{≥}{\ensuremath{\geq}}",
    r"\newunicodechar{≤}{\ensuremath{\leq}}",
    r"\newunicodechar{×}{\ensuremath{\times}}",
    r"\newunicodechar{±}{\ensuremath{\pm}}",
    r"\newunicodechar{°}{\ensuremath{^\circ}}",
    r"\newunicodechar{–}{--}",
])
LATEX_PACKAGES = ["lmodern.sty", "t1lmr.fd", "type1cm.sty", "fix-cm.sty", "geometry.sty", "underscore.sty",
                  "textcomp.sty", "helvet.sty", "courier.sty", "newunicodechar.sty", "amsmath.sty"]
PROGRAMS = ["latex", "dvips", "dvipng", "kpsewhich", "pdftops", "pdftoppm"]   # dvipng: matplotlib usetex on screen/Agg (layout check)
FONT_OK = re.compile(r"^LM(Roman|Sans|Mono|MathItalic|MathSymbols|MathExtension)")
INSTALL_HINT = ("apt-get update && apt-get install -y texlive-latex-base texlive-latex-recommended "
                "texlive-latex-extra texlive-fonts-recommended lmodern dvipng poppler-utils")
# File names: <reviewer comment>_<content>, e.g. r1M1_prediction_distribution, r2M2_issue_time_skill,
# r4m14_study_region (R = reviewer number, M = major comment, m = minor comment). A figure that answers
# several comments is named after the first comment that requests it.
STEM_RE = re.compile(r"^r[1-4][Mm][0-9]+_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$")
_TEX_ESC = {"\\": r"\textbackslash{}", "#": r"\#", "$": r"\$", "%": r"\%", "&": r"\&", "_": r"\_",
            "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def check_environment(verbose=True):
    """Return a list of missing programs / LaTeX packages (empty list = ready)."""
    missing = [p for p in PROGRAMS if shutil.which(p) is None]
    found = {}
    if shutil.which("kpsewhich"):
        for f in LATEX_PACKAGES:
            r = subprocess.run(["kpsewhich", f], capture_output=True, text=True)
            found[f] = r.stdout.strip()
            if not found[f]:
                missing.append(f)
    if verbose:
        for p in PROGRAMS:
            print(f"  {p:20s} {shutil.which(p) or 'MISSING'}")
        for f, path in found.items():
            print(f"  {f:20s} {path or 'MISSING'}")
        print("  READY" if not missing else f"  MISSING: {missing}\n  install: {INSTALL_HINT}")
    return missing


def tex(s) -> str:
    """Escape LaTeX special characters in a plain string (e.g. a label read from a CSV)."""
    return "".join(_TEX_ESC.get(c, c) for c in str(s))


def name(raw: str) -> str:
    """Map any name found in CSVs/scripts to the printed name; strips '(proposed)'."""
    s = str(raw).replace("(proposed)", "").strip()
    return MODEL_NAME.get(s, MODEL_NAME.get(s.lower(), s))


def color(raw: str) -> str:
    """The only way plotting scripts should obtain a model colour: fs.color(<any name of the model>).
    Raises KeyError for a model without an assigned colour (add it to COLOR here, not in the script)."""
    n = name(raw)
    if n not in COLOR:
        raise KeyError(f"no colour assigned to '{raw}' (printed name '{n}'); add it to fig_style.COLOR")
    return COLOR[n]


def marker(raw: str) -> str:
    return MARKER[name(raw)]


def _hex(c):
    return mpl.colors.to_hex(c, keep_alpha=False).upper()


def _is_grey(h):
    r, g, b = h[1:3], h[3:5], h[5:7]
    return r == g == b


def color_problems(fig):
    """Colours of lines, patches (bars, histograms, legend handles) and markers that are neither a
    fig_style colour nor a neutral grey."""
    used = set()
    for art in fig.findobj(lambda a: isinstance(a, (mpl.lines.Line2D, mpl.patches.Patch,
                                                    mpl.collections.Collection))):
        if not art.get_visible():
            continue
        cols = []
        if isinstance(art, mpl.lines.Line2D):
            cols = [art.get_color(), art.get_markerfacecolor(), art.get_markeredgecolor()]
        elif isinstance(art, mpl.patches.Patch):
            cols = [art.get_facecolor(), art.get_edgecolor()]
        else:
            cols = list(art.get_facecolors()) + list(art.get_edgecolors())
        for c in cols:
            try:
                rgba = mpl.colors.to_rgba(c)
            except (ValueError, TypeError):
                continue
            if rgba[3] == 0:          # fully transparent ("none")
                continue
            used.add(_hex(rgba))
    return sorted(h for h in used if h not in ALLOWED_COLORS and not _is_grey(h))


def apply():
    missing = check_environment(verbose=False)
    if missing:
        raise RuntimeError(f"fig_style: missing {missing}. Install with:\n  {INSTALL_HINT}")
    mpl.rcParams.update({
        "text.usetex": True,
        "text.latex.preamble": PREAMBLE,
        "font.family": "serif",
        # matplotlib writes its own font preamble BEFORE text.latex.preamble; \usepackage{lmodern} in
        # PREAMBLE then redefines the roman, sans and typewriter families to Latin Modern. The names below
        # only keep matplotlib from requiring cm-super (type1ec) and are overridden; save() verifies this.
        "font.serif": ["Latin Modern Roman"],
        "font.sans-serif": ["Helvetica"],
        "font.monospace": ["Courier"],
        "font.size": FS_BASE,
        "axes.titlesize": FS_BASE,
        "axes.labelsize": FS_BASE,
        "xtick.labelsize": FS_TICK,
        "ytick.labelsize": FS_TICK,
        "legend.fontsize": FS_LEGEND,
        "legend.title_fontsize": FS_LEGEND,
        "legend.frameon": False,
        "axes.linewidth": 0.6,
        "lines.linewidth": 1.2,
        "lines.markersize": 4,
        "errorbar.capsize": 2,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.direction": "out", "ytick.direction": "out",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False,
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "figure.constrained_layout.use": True,
        "pdf.fonttype": 42, "ps.fonttype": 42,    # usetex embeds the Latin Modern Type 1 fonts regardless
        "axes.unicode_minus": True,
    })


def figure(height_mm=80, nrows=1, ncols=1, width_frac=1.0, **kw):
    """Create a figure at final printed size. width_frac=1.0 -> full \\textwidth."""
    h = height_mm * MM
    if h > MAX_H:
        raise ValueError(f"height {height_mm} mm exceeds {MAX_H / MM:.0f} mm")
    return plt.subplots(nrows, ncols, figsize=(FULL_W * width_frac, h), **kw)


def panel_label(ax, letter, x=-0.02, y=1.02):
    # with usetex, fontweight is ignored, so bold is set in LaTeX
    ax.text(x, y, rf"\textbf{{({letter})}}", transform=ax.transAxes, fontsize=FS_PANEL,
            ha="right", va="bottom")


def _font_sizes(fig):
    sizes = []
    for t in fig.findobj(mpl.text.Text):
        if t.get_visible() and t.get_text().strip():
            sizes.append((t.get_fontsize(), t.get_text()[:30]))
    return sizes


def layout_problems(fig, pad_pt=0.5):
    """Text that is clipped by the figure edge, or text boxes that overlap each other.
    Does NOT detect text covering lines, bars or markers: visual inspection is still required."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    pad = pad_pt * fig.dpi / 72
    # tick labels exist for ticks outside the view limits but are not drawn: keep only drawn ones
    all_tick, drawn_tick = set(), set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tk in axis.get_major_ticks() + axis.get_minor_ticks():
                all_tick.update({id(tk.label1), id(tk.label2)})
            for tk in axis._update_ticks():
                drawn_tick.update({id(tk.label1)} if tk.label1.get_visible() else set())
                drawn_tick.update({id(tk.label2)} if tk.label2.get_visible() else set())
    boxes, problems = [], []
    for t in fig.findobj(mpl.text.Text):
        if not (t.get_visible() and t.get_text().strip()):
            continue
        if id(t) in all_tick and id(t) not in drawn_tick:
            continue
        bb = t.get_window_extent(r)
        if bb.width == 0 or bb.height == 0:
            continue
        label = t.get_text()[:40]
        if bb.x0 < -pad or bb.y0 < -pad or bb.x1 > W + pad or bb.y1 > H + pad:
            problems.append(f"clipped by figure edge: '{label}'")
        boxes.append((bb.expanded(1, 1).padded(-pad), label))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][0].overlaps(boxes[j][0]):
                problems.append(f"overlap: '{boxes[i][1]}' / '{boxes[j][1]}'")
    return problems


def embedded_fonts(pdf_path):
    """Fonts actually embedded in a PDF (via pdffonts if available, else /BaseFont entries)."""
    if shutil.which("pdffonts"):
        out = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True).stdout.splitlines()[2:]
        return sorted({ln.split()[0].split("+")[-1] for ln in out if ln.strip()})
    raw = Path(pdf_path).read_bytes()
    return sorted({m.decode().split("+")[-1] for m in re.findall(rb"/BaseFont\s*/([^\s/>\]]+)", raw)})


def save(fig, stem, outdir="/root/autodl-tmp/results/figures/revision", png=True, eps=True, allow_overlap=False):
    """Save PDF (for LaTeX), EPS (journal upload) and a PNG preview at exact size.
    Checks: font sizes >= FS_MIN; no text clipped by the figure edge and no overlapping text boxes
    (set allow_overlap=True only after checking a reported case by eye); every font embedded in the
    PDF is Latin Modern. Text covering data is not detected: inspect the PDF at 100 %.
    EPS and PNG are converted from the same PDF (pdftops / pdftoppm), so all three are identical."""
    if not STEM_RE.match(stem):
        raise ValueError(f"file name '{stem}' must look like r1M1_<content> (reviewer, M/m, number, '_', content)")
    out = Path(outdir)
    if out.is_dir():   # r1M1_x and r1m1_x are the same file on a case-insensitive disk (macOS default)
        clash = sorted({f.stem for f in out.iterdir() if f.stem.lower() == stem.lower() and f.stem != stem})
        if clash:
            raise ValueError(f"'{stem}' differs only in upper/lower case from existing {clash}; rename one of them")
    small = [(s, txt) for s, txt in _font_sizes(fig) if s < FS_MIN - 1e-6]
    if small:
        raise ValueError(f"text below {FS_MIN} pt: {small[:5]}")
    # an unescaped % starts a LaTeX comment and silently deletes the rest of the label
    pct = [t.get_text() for t in fig.findobj(mpl.text.Text)
           if t.get_visible() and re.search(r"(?<!\\)%", t.get_text())]
    if pct:
        raise ValueError(f"{stem}: unescaped % in {pct[:3]}; write \\% (or use fs.tex())")
    bad_cols = color_problems(fig)
    if bad_cols:
        raise ValueError(f"{stem}: colours not defined in fig_style: {bad_cols}. Use fs.color(model), "
                         f"fs.OBSERVED_COLOR or a grey; add genuinely new colours to fig_style.COLOR.")
    probs = layout_problems(fig)
    if probs and not allow_overlap:
        raise ValueError(f"{stem}: layout problems:\n  " + "\n  ".join(probs))
    for p in probs:
        print(f"[fig] {stem}: WARNING {p}")
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    w, h = fig.get_size_inches()
    pdf = out / f"{stem}.pdf"
    fig.savefig(pdf)
    fonts = embedded_fonts(pdf)
    bad = [f for f in fonts if not FONT_OK.match(f)]
    if bad:
        raise ValueError(f"{pdf}: non-Latin-Modern fonts embedded: {bad} (all: {fonts})")
    if eps:
        subprocess.run(["pdftops", "-eps", "-level3", str(pdf), str(out / f"{stem}.eps")], check=True)
    if png:
        subprocess.run(["pdftoppm", "-png", "-r", "300", "-singlefile", str(pdf), str(out / stem)], check=True)
    sizes = sorted({round(s, 1) for s, _ in _font_sizes(fig)})
    print(f"[fig] {stem}: {w / MM:.1f} x {h / MM:.1f} mm; font sizes {sizes} pt; embedded fonts {fonts} -> {out}")
    print(f"[fig] {stem}: automatic checks passed (sizes, %, colours, text overlap/clipping, fonts); text over data NOT checked -> inspect {pdf.name} at 100 %")


def _self_test(outdir):
    """Test figure with text, math, superscripts, minus signs, ≥, ×, legend, axes and panel labels."""
    import numpy as np
    apply()
    fig, ax = figure(height_mm=65, ncols=2)
    x = np.linspace(-0.1, 3, 60)
    for m, k in zip(["XGBoost", "BiLSTM-Attention", "BU-LSTM-Attention"], (1.0, 0.8, 0.6)):
        ax[0].plot(x, k * np.exp(-x) - 0.05, color=color(m), marker=marker(m), markevery=10, label=m)
    ax[0].axvline(0.574, color="0.5", lw=0.6, ls=(0, (2, 2)))
    ax[0].set_xlabel(f"Precipitation ({UNIT})")
    ax[0].set_ylabel(r"$\Delta$RMSE (mm\,h$^{-1}$)")
    ax[0].legend(loc="upper right")
    ax[0].text(0.9, 0.3, r"$\sigma_{\mathrm{pred}}/\sigma_{\mathrm{obs}} = 0.41$", fontsize=FS_TICK)
    ax[1].bar([0, 1, 2], [0.2437, 0.2671, 0.8417], color=[OBSERVED_COLOR, color("xgboost"), color("bilstm_attn")])
    ax[1].set_xticks([0, 1, 2], ["All", "Wet", "Upper tail"])
    ax[1].set_xlabel(r"Subset (upper tail $\geq$Q95)")
    ax[1].set_title("Month × hour, −0.5 ± 0.1")
    ax[1].set_ylabel(f"RMSE ({UNIT})")
    panel_label(ax[0], "a"); panel_label(ax[1], "b")
    save(fig, "r1M1_style_test", outdir=outdir)   # test file, named in the required pattern


if __name__ == "__main__":
    if "--check" in sys.argv:
        print("environment:")
        sys.exit(1 if check_environment() else 0)
    if "--test" in sys.argv:
        print("environment:"); check_environment()
        i = sys.argv.index("--test")
        d = sys.argv[i + 1] if len(sys.argv) > i + 1 else "/root/autodl-tmp/results/figures/revision"
        _self_test(d)
