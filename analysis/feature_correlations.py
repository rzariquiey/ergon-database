"""
feature_correlations.py
-----------------------
Pairwise phi-coefficient analysis of GB409 features among ergative languages.

Outputs
-------
Fig A  — clustered heatmap of phi coefficients  (PDF + PNG)
Fig B  — implication-strength matrix P(B=1|A=1) (PDF + PNG)
Console — top 15 positive / top 5 negative phi pairs; top 10 implications
"""

import os
import warnings
import itertools

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.stats import chi2_contingency
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform

warnings.filterwarnings("ignore")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLDF = os.path.join(BASE, "cldf")
OUT  = os.path.join(BASE, "analysis")

# ── feature labels ────────────────────────────────────────────────────────────
FEATURE_LABELS = {
    "GB409_1":  "ABS marker",
    "GB409_2":  "1st pers",
    "GB409_3":  "2nd pers",
    "GB409_4":  "3rd pers",
    "GB409_5":  "Full NPs",
    "GB409_6":  "Imperfective",
    "GB409_7":  "Perfective",
    "GB409_8":  "Past",
    "GB409_9":  "Non-past",
    "GB409_10": "Indicative",
    "GB409_11": "Non-indicative",
    "GB409_12": "Realis",
    "GB409_13": "Irrealis",
    "GB409_14": "Agentive A",
    "GB409_15": "Non-agentive A",
    "GB409_16": "Topical A",
    "GB409_17": "Non-topical A",
    "GB409_18": "Animate A",
    "GB409_19": "Inanimate A",
    "GB409_20": "Main clause",
    "GB409_21": "Non-main clause",
    "GB409_22": "Other conditioning",
    "GB409_23": "ERG=GEN",
    "GB409_24": "ERG=INSTR",
}
FEATURES = [f"GB409_{i}" for i in range(1, 25)]

# ── matplotlib style ──────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "serif",
    "font.serif":         ["Times New Roman", "DejaVu Serif", "serif"],
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.titlesize":     12,
    "axes.labelsize":     10,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "figure.dpi":         150,
})


# ── helpers ───────────────────────────────────────────────────────────────────

def phi_coefficient(x, y):
    """Compute phi coefficient from two binary series (aligned, no NaN)."""
    mask = x.notna() & y.notna()
    x, y = x[mask].astype(int), y[mask].astype(int)
    n = len(x)
    if n < 5:
        return np.nan, n
    ct = pd.crosstab(x, y)
    # ensure 2×2
    for v in [0, 1]:
        if v not in ct.index:
            ct.loc[v] = 0
        if v not in ct.columns:
            ct[v] = 0
    ct = ct.loc[[0, 1], [0, 1]]
    a, b, c, d = ct.loc[1,1], ct.loc[1,0], ct.loc[0,1], ct.loc[0,0]
    denom = np.sqrt((a+b)*(c+d)*(a+c)*(b+d))
    if denom == 0:
        return np.nan, n
    phi = (a*d - b*c) / denom
    return phi, n


def implication_strength(x, y):
    """P(y=1 | x=1) with sample size n_{x=1,*coded}."""
    mask = x.notna() & y.notna()
    x_m, y_m = x[mask].astype(int), y[mask].astype(int)
    sub = y_m[x_m == 1]
    if len(sub) < 5:
        return np.nan, 0
    return sub.mean(), len(sub)


# ── load data ─────────────────────────────────────────────────────────────────
print("Loading data …")
languages = pd.read_csv(os.path.join(CLDF, "languages.csv"))
values    = pd.read_csv(os.path.join(CLDF, "values.csv"))

# ergative only
erg_ids = set(languages.loc[languages["Ergative_type"] == "Ergative", "ID"])
values_erg = values[values["Language_ID"].isin(erg_ids)].copy()

# keep only binary values
values_erg = values_erg[values_erg["Value"].isin(["0", "1", 0, 1])].copy()
values_erg["Value"] = values_erg["Value"].astype(int)

# pivot to wide: rows=languages, cols=features
wide = (values_erg[values_erg["Parameter_ID"].isin(FEATURES)]
        .pivot_table(index="Language_ID", columns="Parameter_ID",
                     values="Value", aggfunc="first"))
# reindex columns in order
wide = wide.reindex(columns=FEATURES)
print(f"  Ergative languages with data: {len(wide)}")

# ── phi matrix ────────────────────────────────────────────────────────────────
print("Computing phi coefficients …")
n_feat = len(FEATURES)
phi_mat = pd.DataFrame(np.nan, index=FEATURES, columns=FEATURES)
n_mat   = pd.DataFrame(0,      index=FEATURES, columns=FEATURES)

pairs = list(itertools.combinations(FEATURES, 2))
phi_records = []
for f1, f2 in pairs:
    phi, n = phi_coefficient(wide[f1], wide[f2])
    phi_mat.loc[f1, f2] = phi
    phi_mat.loc[f2, f1] = phi
    n_mat.loc[f1, f2] = n
    n_mat.loc[f2, f1] = n
    if not np.isnan(phi):
        phi_records.append({"f1": f1, "f2": f2, "phi": phi, "n": n})
np.fill_diagonal(phi_mat.values, 1.0)

phi_df = pd.DataFrame(phi_records).sort_values("phi", ascending=False)

# ── implication matrix ────────────────────────────────────────────────────────
print("Computing implication strengths …")
impl_mat  = pd.DataFrame(np.nan, index=FEATURES, columns=FEATURES)
impl_n    = pd.DataFrame(0,      index=FEATURES, columns=FEATURES)
impl_records = []
for f_a, f_b in itertools.permutations(FEATURES, 2):
    p, n = implication_strength(wide[f_a], wide[f_b])
    impl_mat.loc[f_a, f_b] = p
    impl_n.loc[f_a, f_b] = n
    if not np.isnan(p) and n >= 5:
        impl_records.append({"A": f_a, "B": f_b, "P(B|A)": p, "n_A1": n})

impl_df = (pd.DataFrame(impl_records)
           .query("`P(B|A)` < 1.001")          # include 1.0
           .sort_values("P(B|A)", ascending=False))


# ── console output ────────────────────────────────────────────────────────────
short = FEATURE_LABELS

print("\n" + "="*60)
print("TOP 15 POSITIVE PHI CORRELATIONS")
print("="*60)
for _, row in phi_df.head(15).iterrows():
    print(f"  {short[row.f1]:20s}  ↔  {short[row.f2]:20s}  φ = {row.phi:+.3f}  (n={int(row.n)})")

print("\n" + "="*60)
print("TOP 5 NEGATIVE PHI CORRELATIONS")
print("="*60)
for _, row in phi_df.tail(5).sort_values("phi").iterrows():
    print(f"  {short[row.f1]:20s}  ↔  {short[row.f2]:20s}  φ = {row.phi:+.3f}  (n={int(row.n)})")

print("\n" + "="*60)
print("TOP 10 IMPLICATIONS  P(B=1 | A=1) > 0.90")
print("="*60)
top_impl = impl_df[impl_df["P(B|A)"] > 0.90].head(10)
if len(top_impl) == 0:
    top_impl = impl_df.head(10)
for _, row in top_impl.iterrows():
    print(f"  {short[row.A]:20s}  →  {short[row.B]:20s}  P = {row['P(B|A)']:.3f}  (n_A1={int(row.n_A1)})")


# ── Fig A: clustered heatmap ──────────────────────────────────────────────────
print("\nPlotting Fig A: clustered phi heatmap …")

# replace NaN with 0 for clustering distance
phi_fill = phi_mat.fillna(0).values
dist_mat = 1 - phi_fill          # distances in [0, 2]
np.fill_diagonal(dist_mat, 0)
dist_condensed = squareform(dist_mat, checks=False)
dist_condensed = np.clip(dist_condensed, 0, None)

link = linkage(dist_condensed, method="ward")
order = leaves_list(link)

feat_ordered  = [FEATURES[i] for i in order]
label_ordered = [FEATURE_LABELS[f] for f in feat_ordered]
phi_ordered   = phi_mat.loc[feat_ordered, feat_ordered]

fig_a, ax_a = plt.subplots(figsize=(12, 10))
cmap = sns.diverging_palette(220, 20, as_cmap=True)
im = ax_a.imshow(phi_ordered.values.astype(float),
                 cmap=cmap, vmin=-1, vmax=1, aspect="auto")

ax_a.set_xticks(range(n_feat))
ax_a.set_yticks(range(n_feat))
ax_a.set_xticklabels(label_ordered, rotation=45, ha="right", fontsize=7)
ax_a.set_yticklabels(label_ordered, fontsize=7)
ax_a.set_title("Phi Coefficients Among GB409 Features\n(Ergative Languages, Ward Clustering)",
               fontsize=12, pad=12)

cbar = fig_a.colorbar(im, ax=ax_a, fraction=0.03, pad=0.02)
cbar.set_label("φ coefficient", fontsize=9)

plt.tight_layout()
fig_a.savefig(os.path.join(OUT, "figA_phi_heatmap.pdf"), bbox_inches="tight")
fig_a.savefig(os.path.join(OUT, "figA_phi_heatmap.png"), dpi=200, bbox_inches="tight")
plt.close(fig_a)
print("  Saved figA_phi_heatmap.pdf / .png")


# ── Fig B: implication matrix ─────────────────────────────────────────────────
print("Plotting Fig B: implication-strength matrix …")

short_labels = [FEATURE_LABELS[f] for f in FEATURES]
impl_vals = impl_mat.reindex(index=FEATURES, columns=FEATURES).values.astype(float)

fig_b, ax_b = plt.subplots(figsize=(13, 11))
cmap_b = plt.cm.YlOrRd
masked = np.ma.masked_invalid(impl_vals)
im_b = ax_b.imshow(masked, cmap=cmap_b, vmin=0, vmax=1, aspect="auto")

ax_b.set_xticks(range(n_feat))
ax_b.set_yticks(range(n_feat))
ax_b.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=7)
ax_b.set_yticklabels(short_labels, fontsize=7)
ax_b.set_xlabel("Feature B", fontsize=9)
ax_b.set_ylabel("Feature A  (conditioning)", fontsize=9)
ax_b.set_title("Implication Strength  P(B=1 | A=1)\n(Ergative Languages)",
               fontsize=12, pad=12)

cbar_b = fig_b.colorbar(im_b, ax=ax_b, fraction=0.03, pad=0.02)
cbar_b.set_label("P(B=1 | A=1)", fontsize=9)

# annotate top 10 strongest implications
annot_df = impl_df.head(10)
thresh = 0.90
for _, row in annot_df.iterrows():
    i = FEATURES.index(row["A"])
    j = FEATURES.index(row["B"])
    p_val = row["P(B|A)"]
    ax_b.text(j, i, f"{p_val:.2f}", ha="center", va="center",
              fontsize=5.5, color="black" if p_val < 0.85 else "white",
              fontweight="bold")

plt.tight_layout()
fig_b.savefig(os.path.join(OUT, "figB_implication_matrix.pdf"), bbox_inches="tight")
fig_b.savefig(os.path.join(OUT, "figB_implication_matrix.png"), dpi=200, bbox_inches="tight")
plt.close(fig_b)
print("  Saved figB_implication_matrix.pdf / .png")

print("\nDone.")
