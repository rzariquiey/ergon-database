"""
ERGON — Silverstein Hierarchy Analysis
Features: GB409_2 (1st), GB409_3 (2nd), GB409_4 (3rd), GB409_5 (NPs)

Valid implicational patterns:
  hier3:  [0,0,0,1]  ERG only on NPs
  hier2:  [0,0,1,1]  ERG on 3rd + NPs
  hier1:  [0,1,1,1]  ERG on 2nd + 3rd + NPs
  hier4:  [1,1,1,1]  ERG on all (fully ergative on person)
  none:   [0,0,0,0]  No ERG marking
Any other pattern = violation of the hierarchy.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT  = Path(__file__).parent

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Georgia", "Times New Roman", "DejaVu Serif"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ── data ──────────────────────────────────────────────────────────────────────
langs = pd.read_csv(ROOT / "cldf/languages.csv")
vals  = pd.read_csv(ROOT / "cldf/values.csv")
vals_coded = vals[vals["Value"].isin(["0","1"])].copy()
vals_coded["Value"] = vals_coded["Value"].astype(int)

HIER_FEATURES = ["GB409_2","GB409_3","GB409_4","GB409_5"]
FEAT_LABELS   = ["1st person","2nd person","3rd person","Full NPs"]

# Valid Silverstein patterns → label
VALID_PATTERNS = {
    (0,0,0,0): "none",
    (0,0,0,1): "hier3\n[NPs only]",
    (0,0,1,1): "hier2\n[3rd + NPs]",
    (0,1,1,1): "hier1\n[2nd–3rd + NPs]",
    (1,1,1,1): "hier4\n[all persons + NPs]",
}

PATTERN_COLORS = {
    "none":               "#bbbbbb",
    "hier3\n[NPs only]":  "#fee090",
    "hier2\n[3rd + NPs]": "#fc8d59",
    "hier1\n[2nd–3rd + NPs]": "#d73027",
    "hier4\n[all persons + NPs]": "#4d004b",
    "VIOLATION":          "#1a9850",
}

# ── classify each language ────────────────────────────────────────────────────
records = []
for gc, group in vals_coded[vals_coded["Parameter_ID"].isin(HIER_FEATURES)].groupby("Language_ID"):
    row = group.set_index("Parameter_ID")["Value"]
    coded = {f: row[f] for f in HIER_FEATURES if f in row.index}
    if len(coded) < 4:
        continue  # skip languages with missing data on any of the 4 features
    pattern = tuple(coded[f] for f in HIER_FEATURES)
    label   = VALID_PATTERNS.get(pattern, "VIOLATION")
    lang_info = langs[langs["ID"] == gc].iloc[0]
    records.append({
        "Glottocode":    gc,
        "Name":          lang_info["Name"],
        "Family":        lang_info["Family"],
        "Ergative_type": lang_info["Ergative_type"],
        "p1st":  pattern[0],
        "p2nd":  pattern[1],
        "p3rd":  pattern[2],
        "pNPs":  pattern[3],
        "Pattern":   str(pattern),
        "Category":  label,
        "Violation": label == "VIOLATION",
    })

df = pd.DataFrame(records)
erg_df = df[df["Ergative_type"] == "Ergative"].copy()

print(f"Languages with complete data on all 4 hierarchy features: {len(df)}")
print(f"  Ergative:     {len(erg_df)}")
print(f"  Non-ergative: {len(df) - len(erg_df)}")

print(f"\nAll pattern counts:")
print(df["Category"].value_counts().to_string())

print(f"\nAmong ERGATIVE languages:")
print(erg_df["Category"].value_counts().to_string())

violations = erg_df[erg_df["Violation"]].copy()
print(f"\nViolations among ergative languages: {len(violations)} / {len(erg_df)} "
      f"({100*len(violations)/len(erg_df):.1f}%)")
print(f"\nViolation patterns found:")
print(violations["Pattern"].value_counts().to_string())

print(f"\nViolating languages:")
print(violations[["Name","Glottocode","Family","Pattern"]].sort_values("Family").to_string(index=False))

# Family breakdown
fam_counts = erg_df["Family"].value_counts()
fams_ok = fam_counts[fam_counts >= 3].index
fam_df = erg_df[erg_df["Family"].isin(fams_ok)]
fam_viol = (fam_df.groupby("Family")["Violation"].agg(["sum","count"])
            .rename(columns={"sum":"n_violations","count":"n_total"}))
fam_viol["pct_violation"] = 100 * fam_viol["n_violations"] / fam_viol["n_total"]
fam_viol = fam_viol.sort_values("pct_violation", ascending=False)

print(f"\nViolation rate by family (≥3 languages):")
print(fam_viol.to_string())

# ── FIGURE 1 — Donut: pattern distribution among ergative languages ───────────
cat_order   = ["hier3\n[NPs only]","hier2\n[3rd + NPs]",
               "hier1\n[2nd–3rd + NPs]","hier4\n[all persons + NPs]","VIOLATION"]
cat_counts  = erg_df["Category"].value_counts().reindex(cat_order, fill_value=0)
colors_pie  = [PATTERN_COLORS[c] for c in cat_order]
labels_pie  = [f"{c.replace(chr(10),' ')}\n(n={cat_counts[c]})" for c in cat_order]

fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))

# Left: donut chart
wedges, texts, autotexts = axes[0].pie(
    cat_counts, labels=None, colors=colors_pie,
    autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
    startangle=90, pctdistance=0.78,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=1.5)
)
for at in autotexts:
    at.set_fontsize(9)
axes[0].set_title("Silverstein hierarchy patterns\n(ergative languages, n={})".format(len(erg_df)),
                  pad=12)
axes[0].legend(wedges, [c.replace("\n"," ") for c in cat_order],
               loc="lower center", bbox_to_anchor=(0.5, -0.18),
               fontsize=8, frameon=False, ncol=2)

# Right: implicational scale diagram
scale_data = {
    "Pattern": ["hier3\n[NPs only]","hier2\n[3rd + NPs]","hier1\n[2nd–3rd + NPs]","hier4\n[all persons + NPs]"],
    "1st":  [0,0,0,1],
    "2nd":  [0,0,1,1],
    "3rd":  [0,1,1,1],
    "NPs":  [1,1,1,1],
    "n":    [cat_counts.get(c,0) for c in ["hier3\n[NPs only]","hier2\n[3rd + NPs]","hier1\n[2nd–3rd + NPs]","hier4\n[all persons + NPs]"]]
}
scale_df = pd.DataFrame(scale_data)

ax2 = axes[1]
ax2.set_xlim(-0.5, 4.5)
ax2.set_ylim(-0.5, len(scale_df) - 0.5)
ax2.set_aspect("equal")

for i, row in scale_df.iterrows():
    for j, feat in enumerate(["1st","2nd","3rd","NPs"]):
        val = row[feat]
        color = "#2166ac" if val == 1 else "#f0f0f0"
        ec    = "#2166ac" if val == 1 else "#cccccc"
        circle = plt.Circle((j, i), 0.38, color=color, ec=ec, lw=1.5, zorder=3)
        ax2.add_patch(circle)
        ax2.text(j, i, "ERG" if val==1 else "NOM", ha="center", va="center",
                 fontsize=7, color="white" if val==1 else "#aaaaaa", fontweight="bold")
    pct = 100 * row["n"] / len(erg_df)
    ax2.text(4.1, i, f"n={row['n']} ({pct:.0f}%)", va="center", fontsize=9)

ax2.set_xticks(range(4))
ax2.set_xticklabels(["1st pers.","2nd pers.","3rd pers.","Full NPs"], fontsize=9)
ax2.set_yticks(range(len(scale_df)))
ax2.set_yticklabels(scale_df["Pattern"].str.replace("\n"," "), fontsize=9)
ax2.set_title("Implicational scale\n(Silverstein hierarchy)", pad=12)
ax2.spines[:].set_visible(False)
ax2.tick_params(left=False, bottom=False)
ax2.arrow(-0.5, -0.7, 3.8, 0, head_width=0.08, head_length=0.12,
          fc="#555", ec="#555", clip_on=False)
ax2.text(1.5, -0.95, "← more likely NOM-ACC          more likely ERG →",
         ha="center", fontsize=8, color="#555")

plt.tight_layout()
fig.savefig(OUT / "fig5_silverstein_patterns.pdf")
fig.savefig(OUT / "fig5_silverstein_patterns.png")
print("\nSaved fig5")

# ── FIGURE 2 — Violations: who and where ─────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: violation rate by family (stacked bar)
fam_plot = fam_viol.sort_values("pct_violation", ascending=True)
y = range(len(fam_plot))

axes[0].barh(y, fam_plot["n_total"], color="#dddddd", height=0.6, label="Conforms")
axes[0].barh(y, fam_plot["n_violations"], color="#1a9850", height=0.6, label="Violation")
axes[0].set_yticks(y)
axes[0].set_yticklabels([f"{fam} (n={row.n_total})"
                          for fam, row in fam_plot.iterrows()], fontsize=9)
axes[0].set_xlabel("Number of languages")
axes[0].set_title("Hierarchy violations by family\n(ergative languages, families ≥ 3)")
axes[0].legend(frameon=False, fontsize=9)

for i, (fam, row) in enumerate(fam_plot.iterrows()):
    if row["n_violations"] > 0:
        axes[0].text(row["n_total"] + 0.1, i,
                     f"{row['pct_violation']:.0f}%",
                     va="center", fontsize=8, color="#1a9850")

# Right: what violations look like (which features are anomalous)
viol_patterns = violations["Pattern"].value_counts()
viol_decoded = []
for pat_str, count in viol_patterns.items():
    pat = eval(pat_str)
    label = f"[{pat[0]},{pat[1]},{pat[2]},{pat[3]}]"
    viol_decoded.append({"Pattern": label, "Count": count})
viol_dec_df = pd.DataFrame(viol_decoded).sort_values("Count", ascending=True)

axes[1].barh(viol_dec_df["Pattern"], viol_dec_df["Count"],
             color="#1a9850", height=0.5)
axes[1].set_xlabel("Number of languages")
axes[1].set_title("What do violations look like?\n[1st, 2nd, 3rd, NPs]")
for i, (_, row) in enumerate(viol_dec_df.iterrows()):
    axes[1].text(row["Count"] + 0.05, i, str(int(row["Count"])),
                 va="center", fontsize=9)

plt.tight_layout()
fig.savefig(OUT / "fig6_violations.pdf")
fig.savefig(OUT / "fig6_violations.png")
print("Saved fig6")

# ── FIGURE 3 — Heatmap: each ergative language × 4 features ──────────────────
# Sort by pattern category then name
cat_sort_order = {"hier4\n[all persons + NPs]":0,"hier1\n[2nd–3rd + NPs]":1,
                  "hier2\n[3rd + NPs]":2,"hier3\n[NPs only]":3,"VIOLATION":4,"none":5}
erg_sorted = erg_df.copy()
erg_sorted["sort_key"] = erg_sorted["Category"].map(cat_sort_order)
erg_sorted = erg_sorted.sort_values(["sort_key","Family","Name"])

heat_data = erg_sorted[["p1st","p2nd","p3rd","pNPs"]].values.T

fig, ax = plt.subplots(figsize=(14, 4))
cmap = plt.cm.get_cmap("Blues", 2)
im = ax.imshow(heat_data, aspect="auto", cmap=cmap, vmin=-0.1, vmax=1.1,
               interpolation="nearest")

ax.set_yticks(range(4))
ax.set_yticklabels(FEAT_LABELS, fontsize=9)
ax.set_xticks(range(len(erg_sorted)))
ax.set_xticklabels(erg_sorted["Name"], rotation=90, fontsize=5.5)

# Color x-labels by violation status
for tick, (_, row) in zip(ax.get_xticklabels(), erg_sorted.iterrows()):
    tick.set_color("#1a9850" if row["Violation"] else "black")

# Add category separators
prev_cat = None
for i, (_, row) in enumerate(erg_sorted.iterrows()):
    if row["Category"] != prev_cat:
        ax.axvline(i - 0.5, color="white", lw=2)
        cat_label = row["Category"].replace("\n"," ")
        ax.text(i + 0.5, -0.9, cat_label, fontsize=7, color="#333",
                rotation=0, ha="left", clip_on=False)
        prev_cat = row["Category"]

ax.set_title("Silverstein hierarchy patterns across ERGON ergative languages\n"
             "(green labels = hierarchy violations)", pad=20)
ax.set_xlabel("Language")
plt.colorbar(im, ax=ax, ticks=[0,1], shrink=0.6, label="ERG marking (1=yes)")

plt.tight_layout()
fig.savefig(OUT / "fig7_heatmap.pdf")
fig.savefig(OUT / "fig7_heatmap.png")
print("Saved fig7")

# ── save results ──────────────────────────────────────────────────────────────
df.to_csv(OUT / "silverstein_classifications.csv", index=False)
print("\nFull classifications saved to analysis/silverstein_classifications.csv")
