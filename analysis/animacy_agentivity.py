"""
animacy_agentivity.py
---------------------
Analyse GB409_14–21 (agentivity, topicality, animacy, clause type) in
relation to the overall ergativity score (from ergativity_scores.csv).

Outputs
-------
Fig A — boxplots per feature (feature=0 vs =1) with Mann-Whitney annotation
Fig B — point-biserial correlation heatmap (features × score)
Fig C — proportion of ergative languages "active" in each sub-domain
Console — feature predictors ranked by correlation + p-value
"""

import os
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy.stats import mannwhitneyu, pointbiserialr

warnings.filterwarnings("ignore")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLDF  = os.path.join(BASE, "cldf")
OUT   = os.path.join(BASE, "analysis")

# ── features of interest ──────────────────────────────────────────────────────
FOCUS_FEATURES = [f"GB409_{i}" for i in range(14, 22)]   # 14–21
FOCUS_LABELS = {
    "GB409_14": "Agentive A",
    "GB409_15": "Non-agentive A",
    "GB409_16": "Topical A",
    "GB409_17": "Non-topical A",
    "GB409_18": "Animate A",
    "GB409_19": "Inanimate A",
    "GB409_20": "Main clause",
    "GB409_21": "Non-main clause",
}

# sub-domains (for Fig C)
DOMAINS = {
    "Person (2–5)":      [f"GB409_{i}" for i in range(2, 6)],
    "Aspect (6–7)":      ["GB409_6",  "GB409_7"],
    "Tense (8–9)":       ["GB409_8",  "GB409_9"],
    "Mood (10–11)":      ["GB409_10", "GB409_11"],
    "Realis (12–13)":    ["GB409_12", "GB409_13"],
    "Agentivity (14–15)":["GB409_14", "GB409_15"],
    "Topicality (16–17)":["GB409_16", "GB409_17"],
    "Animacy (18–19)":   ["GB409_18", "GB409_19"],
    "Clause (20–21)":    ["GB409_20", "GB409_21"],
}

# ── matplotlib style ──────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "serif",
    "font.serif":         ["Times New Roman", "DejaVu Serif", "serif"],
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.titlesize":     10,
    "axes.labelsize":     9,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "figure.dpi":         150,
})

# ── significance stars ────────────────────────────────────────────────────────
def sig_stars(p):
    if p < 0.001:  return "***"
    if p < 0.01:   return "**"
    if p < 0.05:   return "*"
    return "ns"


# ── load data ─────────────────────────────────────────────────────────────────
print("Loading data …")
languages  = pd.read_csv(os.path.join(CLDF, "languages.csv"))
values_raw = pd.read_csv(os.path.join(CLDF, "values.csv"))
scores_df  = pd.read_csv(os.path.join(OUT,  "ergativity_scores.csv"))

# ergative only
erg_ids = set(languages.loc[languages["Ergative_type"] == "Ergative", "ID"])

# binary values, ergative languages
val = values_raw[
    values_raw["Language_ID"].isin(erg_ids) &
    values_raw["Value"].isin(["0", "1", 0, 1])
].copy()
val["Value"] = val["Value"].astype(int)

# pivot wide
all_features = [f"GB409_{i}" for i in range(1, 25)]
wide = (val[val["Parameter_ID"].isin(all_features)]
        .pivot_table(index="Language_ID", columns="Parameter_ID",
                     values="Value", aggfunc="first")
        .reindex(columns=all_features))

# merge scores
scores_erg = scores_df[scores_df["Glottocode"].isin(erg_ids)].copy()
wide = wide.merge(scores_erg[["Glottocode", "score"]],
                  left_index=True, right_on="Glottocode", how="inner")
wide = wide.set_index("Glottocode")
print(f"  Languages available: {len(wide)}")


# ── Fig A: boxplots with Mann-Whitney ─────────────────────────────────────────
print("Plotting Fig A: boxplots …")

fig_a, axes = plt.subplots(2, 4, figsize=(14, 7), sharey=True)
axes = axes.flatten()
colors = {"0": "#4878CF", "1": "#D65F5F"}

for idx, feat in enumerate(FOCUS_FEATURES):
    ax = axes[idx]
    col = wide[feat].dropna()
    g0  = wide.loc[col[col == 0].index, "score"].dropna()
    g1  = wide.loc[col[col == 1].index, "score"].dropna()

    data   = [g0.values, g1.values]
    bp = ax.boxplot(data, patch_artist=True, widths=0.5,
                    medianprops=dict(color="white", linewidth=2),
                    whiskerprops=dict(linewidth=1),
                    capprops=dict(linewidth=1),
                    flierprops=dict(marker="o", markersize=3,
                                   markerfacecolor="gray", alpha=0.5))
    bp["boxes"][0].set_facecolor("#4878CF")
    bp["boxes"][1].set_facecolor("#D65F5F")

    ax.set_xticks([1, 2])
    ax.set_xticklabels([f"0  (n={len(g0)})", f"1  (n={len(g1)})"], fontsize=7)
    ax.set_title(FOCUS_LABELS[feat], fontsize=9)
    if idx % 4 == 0:
        ax.set_ylabel("Ergativity score", fontsize=8)

    # Mann-Whitney
    if len(g0) >= 3 and len(g1) >= 3:
        stat, p = mannwhitneyu(g0, g1, alternative="two-sided")
        stars = sig_stars(p)
        y_max = max(g0.max() if len(g0) else 0,
                    g1.max() if len(g1) else 0) + 0.03
        ax.annotate("", xy=(2, y_max), xytext=(1, y_max),
                    arrowprops=dict(arrowstyle="-", color="black", lw=1))
        ax.text(1.5, y_max + 0.01, f"{stars}\n(p={p:.3f})",
                ha="center", va="bottom", fontsize=6.5)

fig_a.suptitle("Ergativity Score by Feature Presence (GB409_14–21)\nMann-Whitney U test",
               fontsize=11, y=1.01)
plt.tight_layout()
fig_a.savefig(os.path.join(OUT, "figA_boxplots.pdf"), bbox_inches="tight")
fig_a.savefig(os.path.join(OUT, "figA_boxplots.png"), dpi=200, bbox_inches="tight")
plt.close(fig_a)
print("  Saved figA_boxplots.pdf / .png")


# ── Fig B: point-biserial correlation heatmap ─────────────────────────────────
print("Plotting Fig B: point-biserial correlation heatmap …")

pb_results = []
for feat in FOCUS_FEATURES:
    sub = wide[[feat, "score"]].dropna()
    if len(sub) < 5:
        pb_results.append({"Feature": feat, "r": np.nan, "p": np.nan, "n": len(sub)})
        continue
    r, p = pointbiserialr(sub[feat].astype(int), sub["score"])
    pb_results.append({"Feature": feat, "r": r, "p": p, "n": len(sub)})

pb_df = pd.DataFrame(pb_results)

# build 1-row matrix for heatmap (features × r-value)
pb_mat = pb_df.set_index("Feature")[["r"]].T.reindex(columns=FOCUS_FEATURES)
label_list = [FOCUS_LABELS[f] for f in FOCUS_FEATURES]

fig_b, ax_b = plt.subplots(figsize=(10, 2.8))
cmap_b = sns.diverging_palette(220, 20, as_cmap=True)
im = ax_b.imshow(pb_mat.values.astype(float), cmap=cmap_b,
                 vmin=-1, vmax=1, aspect="auto")

ax_b.set_xticks(range(len(FOCUS_FEATURES)))
ax_b.set_xticklabels(label_list, fontsize=9)
ax_b.set_yticks([0])
ax_b.set_yticklabels(["r (point-biserial)"], fontsize=9)
ax_b.set_title("Point-Biserial Correlation: GB409_14–21 vs Ergativity Score",
               fontsize=10, pad=10)

# annotate cells
for j, feat in enumerate(FOCUS_FEATURES):
    row = pb_df[pb_df["Feature"] == feat].iloc[0]
    if not np.isnan(row["r"]):
        stars = sig_stars(row["p"])
        ax_b.text(j, 0, f"r={row['r']:.2f}\n{stars}\nn={int(row['n'])}",
                  ha="center", va="center", fontsize=7.5,
                  color="white" if abs(row["r"]) > 0.5 else "black")

cbar_b = fig_b.colorbar(im, ax=ax_b, fraction=0.02, pad=0.04,
                        orientation="vertical")
cbar_b.set_label("r", fontsize=9)

plt.tight_layout()
fig_b.savefig(os.path.join(OUT, "figB_pointbiserial.pdf"), bbox_inches="tight")
fig_b.savefig(os.path.join(OUT, "figB_pointbiserial.png"), dpi=200, bbox_inches="tight")
plt.close(fig_b)
print("  Saved figB_pointbiserial.pdf / .png")


# ── Fig C: proportion "fully active" per domain ───────────────────────────────
print("Plotting Fig C: domain activity proportions …")

domain_props = {}
n_total = len(wide)
for domain_name, feats in DOMAINS.items():
    avail = [f for f in feats if f in wide.columns]
    if not avail:
        domain_props[domain_name] = np.nan
        continue
    # a language is "active" in the domain if ALL available features are 1
    sub = wide[avail].dropna(how="all")
    active = sub.apply(lambda row: all(row[f] == 1 for f in avail
                                        if not np.isnan(row[f])), axis=1)
    domain_props[domain_name] = active.sum() / len(sub) if len(sub) > 0 else np.nan

domain_s = pd.Series(domain_props).dropna().sort_values(ascending=True)

fig_c, ax_c = plt.subplots(figsize=(8, 5))
bars = ax_c.barh(domain_s.index, domain_s.values * 100,
                 color="#4878CF", edgecolor="white", height=0.6)
ax_c.set_xlabel("Proportion of ergative languages fully active in domain (%)", fontsize=9)
ax_c.set_title("Domain Saturation Among Ergative Languages\n(all features in domain = 1)",
               fontsize=11)
ax_c.set_xlim(0, 105)

for bar, val in zip(bars, domain_s.values):
    ax_c.text(val * 100 + 1, bar.get_y() + bar.get_height() / 2,
              f"{val*100:.1f}%", va="center", fontsize=8)

plt.tight_layout()
fig_c.savefig(os.path.join(OUT, "figC_domain_activity.pdf"), bbox_inches="tight")
fig_c.savefig(os.path.join(OUT, "figC_domain_activity.png"), dpi=200, bbox_inches="tight")
plt.close(fig_c)
print("  Saved figC_domain_activity.pdf / .png")


# ── console: feature predictors ───────────────────────────────────────────────
print("\n" + "="*60)
print("FEATURE PREDICTORS OF ERGATIVITY SCORE")
print("(Point-biserial r, all 24 features vs score)")
print("="*60)

all_pb = []
feat_labels_all = {f"GB409_{i}": f"GB409_{i}" for i in range(1, 25)}
feat_labels_all.update({
    "GB409_1":"ABS marker","GB409_2":"1st pers","GB409_3":"2nd pers",
    "GB409_4":"3rd pers","GB409_5":"Full NPs","GB409_6":"Imperfective",
    "GB409_7":"Perfective","GB409_8":"Past","GB409_9":"Non-past",
    "GB409_10":"Indicative","GB409_11":"Non-indicative","GB409_12":"Realis",
    "GB409_13":"Irrealis","GB409_14":"Agentive A","GB409_15":"Non-agentive A",
    "GB409_16":"Topical A","GB409_17":"Non-topical A","GB409_18":"Animate A",
    "GB409_19":"Inanimate A","GB409_20":"Main clause","GB409_21":"Non-main clause",
    "GB409_22":"Other conditioning","GB409_23":"ERG=GEN","GB409_24":"ERG=INSTR",
})

for feat in [f"GB409_{i}" for i in range(1, 25)]:
    if feat not in wide.columns:
        continue
    sub = wide[[feat, "score"]].dropna()
    if len(sub) < 5:
        continue
    r, p = pointbiserialr(sub[feat].astype(int), sub["score"])
    all_pb.append({"Feature": feat, "Label": feat_labels_all[feat],
                   "r": r, "p": p, "n": len(sub)})

all_pb_df = pd.DataFrame(all_pb).sort_values("r", ascending=False)
for _, row in all_pb_df.iterrows():
    stars = sig_stars(row["p"])
    print(f"  {row['Label']:22s}  r = {row['r']:+.3f}  p = {row['p']:.4f}  {stars}  (n={int(row['n'])})")

print("\nDone.")
