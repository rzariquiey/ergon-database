"""
ERGON — Phylogenetic Signal Analysis
Script 4

Uses family membership as a proxy for phylogenetic distance.
Analyses ergativity score from analysis/ergativity_scores.csv.

Measures:
  1. Eta-squared (η²) — one-way ANOVA of score by family
  2. Within- vs between-family variance
  3. Family consistency index (CV = std/mean)
  4. Permutation test (1 000 permutations)
  5. Per-feature phylogenetic signal (Cramér's V)

Figures
  A — η² vs permutation null distribution
  B — Within-family variance scatter (family mean × SD)
  C — Per-feature Cramér's V, horizontal bar chart
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
OUT  = Path(__file__).parent

# ── style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "serif",
    "font.serif":         ["Georgia", "Times New Roman", "DejaVu Serif"],
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.titlesize":     13,
    "axes.labelsize":     11,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
})

RNG = np.random.default_rng(42)
N_PERM = 1_000

# ── domain colour mapping (for Fig C) ─────────────────────────────────────────
FEATURE_DOMAIN = {
    "GB409_1":  "Baseline",
    "GB409_2":  "Person",
    "GB409_3":  "Person",
    "GB409_4":  "Person",
    "GB409_5":  "Person",
    "GB409_6":  "Aspect",
    "GB409_7":  "Aspect",
    "GB409_8":  "Tense",
    "GB409_9":  "Tense",
    "GB409_10": "Mood",
    "GB409_11": "Mood",
    "GB409_12": "Realis",
    "GB409_13": "Realis",
    "GB409_14": "Agentivity",
    "GB409_15": "Agentivity",
    "GB409_16": "Topicality",
    "GB409_17": "Topicality",
    "GB409_18": "Animacy",
    "GB409_19": "Animacy",
    "GB409_20": "Clause type",
    "GB409_21": "Clause type",
    "GB409_22": "Other",
    "GB409_23": "Other",
    "GB409_24": "Other",
}
DOMAIN_COLOR = {
    "Baseline":    "#aaaaaa",
    "Person":      "#4393c3",
    "Aspect":      "#d6604d",
    "Tense":       "#f4a582",
    "Mood":        "#878787",
    "Realis":      "#bababa",
    "Agentivity":  "#74add1",
    "Topicality":  "#abd9e9",
    "Animacy":     "#fee090",
    "Clause type": "#fdae61",
    "Other":       "#cccccc",
}

# ── load data ─────────────────────────────────────────────────────────────────
scores_df = pd.read_csv(OUT / "ergativity_scores.csv")
langs     = pd.read_csv(ROOT / "cldf/languages.csv")
vals      = pd.read_csv(ROOT / "cldf/values.csv")

# Keep only ergative languages
erg_scores = scores_df[scores_df["Ergative_type"] == "Ergative"].copy()
erg_scores = erg_scores.dropna(subset=["score", "Family"])

# Families with ≥ 2 and ≥ 3 languages (for different analyses)
fam_counts = erg_scores["Family"].value_counts()
fams_ge2   = fam_counts[fam_counts >= 2].index
fams_ge3   = fam_counts[fam_counts >= 3].index

print("=" * 65)
print("ERGON — Phylogenetic Signal Analysis")
print("=" * 65)
print(f"\nErgative languages with score data: {len(erg_scores)}")
print(f"Families represented:               {erg_scores['Family'].nunique()}")
print(f"Families with ≥ 2 languages:        {len(fams_ge2)}")
print(f"Families with ≥ 3 languages:        {len(fams_ge3)}")

# ══════════════════════════════════════════════════════════════════════════════
# 1. Eta-squared — one-way ANOVA
# ══════════════════════════════════════════════════════════════════════════════
def eta_squared(data: pd.DataFrame, score_col: str, group_col: str) -> float:
    """Compute η² from one-way ANOVA groups."""
    groups = [g[score_col].values for _, g in data.groupby(group_col)]
    grand_mean = data[score_col].mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_total   = ((data[score_col] - grand_mean) ** 2).sum()
    return ss_between / ss_total if ss_total > 0 else 0.0

observed_eta2 = eta_squared(erg_scores, "score", "Family")

# ANOVA p-value via scipy
groups_for_anova = [g["score"].values
                    for _, g in erg_scores.groupby("Family")
                    if len(g) >= 1]
f_stat, anova_p = stats.f_oneway(*groups_for_anova)

print(f"\n── 1. Eta-squared (η²) ──")
print(f"   η²       = {observed_eta2:.4f}")
print(f"   F-stat   = {f_stat:.3f}")
print(f"   p-value  = {anova_p:.4e}")
if observed_eta2 < 0.06:
    interp = "small effect — weak phylogenetic signal"
elif observed_eta2 < 0.14:
    interp = "medium effect — moderate phylogenetic signal"
else:
    interp = "large effect — strong phylogenetic signal"
print(f"   Interpret: η² = {observed_eta2:.3f} → {interp}")

# ══════════════════════════════════════════════════════════════════════════════
# 2. Within- vs between-family variance
# ══════════════════════════════════════════════════════════════════════════════
overall_var = erg_scores["score"].var(ddof=1)

within_vars = []
fam_stats = []
for fam in fams_ge2:
    sub  = erg_scores.loc[erg_scores["Family"] == fam, "score"]
    wvar = sub.var(ddof=1) if len(sub) > 1 else np.nan
    within_vars.append(wvar)
    fam_stats.append({
        "Family": fam,
        "n":      len(sub),
        "mean":   sub.mean(),
        "sd":     sub.std(ddof=1) if len(sub) > 1 else 0.0,
        "var":    wvar,
    })

mean_within_var = np.nanmean(within_vars)
within_between_ratio = mean_within_var / overall_var if overall_var > 0 else np.nan
fam_stats_df = pd.DataFrame(fam_stats)

print(f"\n── 2. Within- vs between-family variance ──")
print(f"   Overall variance:          {overall_var:.4f}")
print(f"   Mean within-family var:    {mean_within_var:.4f}")
print(f"   Within/Overall ratio:      {within_between_ratio:.4f}")
print(f"   (Lower ratio = more variance explained by family)")

# ══════════════════════════════════════════════════════════════════════════════
# 3. Family consistency index (CV)
# ══════════════════════════════════════════════════════════════════════════════
cv_records = []
for fam in fams_ge3:
    sub  = erg_scores.loc[erg_scores["Family"] == fam, "score"]
    mean = sub.mean()
    std  = sub.std(ddof=1)
    cv   = std / mean if mean > 0 else np.nan
    cv_records.append({"Family": fam, "n": len(sub), "mean": mean, "std": std, "cv": cv})

cv_df = pd.DataFrame(cv_records).sort_values("cv")
print(f"\n── 3. Family consistency index (CV = std/mean), families ≥ 3 ──")
print(cv_df.to_string(index=False, float_format="{:.4f}".format))
most_consistent  = cv_df.iloc[0]
least_consistent = cv_df.iloc[-1]
print(f"\n   Most internally consistent:  {most_consistent['Family']} "
      f"(CV = {most_consistent['cv']:.4f}, n={int(most_consistent['n'])})")
print(f"   Least internally consistent: {least_consistent['Family']} "
      f"(CV = {least_consistent['cv']:.4f}, n={int(least_consistent['n'])})")

# ══════════════════════════════════════════════════════════════════════════════
# 4. Permutation test
# ══════════════════════════════════════════════════════════════════════════════
perm_eta2 = np.empty(N_PERM)
scores_arr = erg_scores["score"].values
labels_arr = erg_scores["Family"].values

for i in range(N_PERM):
    shuffled = erg_scores.copy()
    shuffled["Family"] = RNG.permutation(labels_arr)
    perm_eta2[i] = eta_squared(shuffled, "score", "Family")

perm_p = (perm_eta2 >= observed_eta2).mean()

print(f"\n── 4. Permutation test (n = {N_PERM} permutations) ──")
print(f"   Observed η²  = {observed_eta2:.4f}")
print(f"   Perm. mean   = {perm_eta2.mean():.4f}")
print(f"   Perm. 95th %-ile = {np.percentile(perm_eta2, 95):.4f}")
print(f"   Permutation p-value = {perm_p:.4f}")
if perm_p < 0.001:
    sig_str = "p < 0.001 *** (highly significant)"
elif perm_p < 0.01:
    sig_str = f"p = {perm_p:.3f} ** (significant)"
elif perm_p < 0.05:
    sig_str = f"p = {perm_p:.3f} * (significant)"
else:
    sig_str = f"p = {perm_p:.3f} (not significant)"
print(f"   Significance: {sig_str}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. Per-feature phylogenetic signal — Cramér's V
# ══════════════════════════════════════════════════════════════════════════════
# Keep only ergative languages with ≥3-member families
erg_lang_ids  = set(erg_scores.loc[erg_scores["Family"].isin(fams_ge3), "Glottocode"])

vals_coded = vals[vals["Value"].isin(["0", "1"])].copy()
vals_coded["Value"] = vals_coded["Value"].astype(int)
vals_erg   = vals_coded[vals_coded["Language_ID"].isin(erg_lang_ids)].copy()

# Attach family
lang_fam = erg_scores.set_index("Glottocode")["Family"].to_dict()
vals_erg["Family"] = vals_erg["Language_ID"].map(lang_fam)
vals_erg = vals_erg.dropna(subset=["Family"])

def cramers_v(series_x, series_y):
    """Cramér's V for two categorical series."""
    ct   = pd.crosstab(series_x, series_y)
    chi2 = stats.chi2_contingency(ct, correction=False)[0]
    n    = ct.sum().sum()
    k    = min(ct.shape) - 1
    if n == 0 or k == 0:
        return np.nan
    return np.sqrt(chi2 / (n * k))

feature_cv_records = []
for feat, grp in vals_erg.groupby("Parameter_ID"):
    grp_clean = grp.dropna(subset=["Value", "Family"])
    if grp_clean["Value"].nunique() < 2:
        continue
    if grp_clean["Family"].nunique() < 2:
        continue
    v = cramers_v(grp_clean["Value"].astype(str), grp_clean["Family"])
    feature_cv_records.append({
        "Feature": feat,
        "CramersV": v,
        "Domain": FEATURE_DOMAIN.get(feat, "Other"),
        "n_langs": grp_clean["Language_ID"].nunique(),
    })

feat_cv_df = pd.DataFrame(feature_cv_records).dropna(subset=["CramersV"])
feat_cv_df = feat_cv_df.sort_values("CramersV", ascending=False).reset_index(drop=True)

print(f"\n── 5. Per-feature phylogenetic conservatism (Cramér's V) ──")
print(feat_cv_df.to_string(index=False, float_format="{:.4f}".format))
print(f"\n   Top 5 most phylogenetically conserved features:")
print(feat_cv_df.head(5)[["Feature","Domain","CramersV"]].to_string(index=False))
print(f"\n   Top 5 least phylogenetically conserved features:")
print(feat_cv_df.tail(5)[["Feature","Domain","CramersV"]].to_string(index=False))

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE A — η² vs permutation null distribution
# ═══════════════════════════════════════════════════════════════════════════════
fig_a, ax_a = plt.subplots(figsize=(8, 5))

ax_a.hist(perm_eta2, bins=40, color="#aac4e8", edgecolor="white",
          linewidth=0.7, density=True, alpha=0.85, label="Null distribution\n(permuted family labels)")

ax_a.axvline(observed_eta2, color="#d62728", lw=2.2, ls="--",
             label=f"Observed η² = {observed_eta2:.3f}")
ax_a.axvline(np.percentile(perm_eta2, 95), color="#f28e2b", lw=1.5, ls=":",
             label=f"95th percentile = {np.percentile(perm_eta2, 95):.3f}")

# Shade tail
x_shade = perm_eta2[perm_eta2 >= observed_eta2]
if len(x_shade) > 0:
    ax_a.hist(x_shade, bins=40, color="#d62728", alpha=0.4,
              density=True, label=f"p = {perm_p:.4f}")

ax_a.set_xlabel("η² (eta-squared)")
ax_a.set_ylabel("Density")
ax_a.set_title("Phylogenetic signal: observed η² vs. permutation null\n"
               "(one-way ANOVA of ergativity score by family)")

# Annotation box
bbox_props = dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=1)
annotation = (f"Observed η² = {observed_eta2:.3f}\n"
              f"Permutation p = {perm_p:.4f}\n"
              f"{sig_str}")
ax_a.text(0.97, 0.97, annotation, transform=ax_a.transAxes,
          fontsize=8.5, va="top", ha="right", bbox=bbox_props)

ax_a.legend(frameon=False, fontsize=9, loc="upper left")
plt.tight_layout()
fig_a.savefig(OUT / "figA_phylogenetic_eta2.pdf")
fig_a.savefig(OUT / "figA_phylogenetic_eta2.png")
print("\nSaved figA_phylogenetic_eta2")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE B — Within-family variance scatter
# ═══════════════════════════════════════════════════════════════════════════════
fam_plot_df = fam_stats_df.dropna(subset=["sd"])

# Identify outlier families (high SD = internally diverse)
sd_threshold = fam_plot_df["sd"].quantile(0.75)

fig_b, ax_b = plt.subplots(figsize=(8.5, 6))

# Build colour gradient by sd
cmap_b = plt.cm.RdYlGn_r
norm_b = plt.Normalize(fam_plot_df["sd"].min(), fam_plot_df["sd"].max())

sc = ax_b.scatter(
    fam_plot_df["mean"], fam_plot_df["sd"],
    s=fam_plot_df["n"] * 14 + 20,
    c=fam_plot_df["sd"],
    cmap=cmap_b, norm=norm_b,
    alpha=0.8, edgecolors="#555555", linewidths=0.6, zorder=3
)

# Label all outlier families + any with n ≥ 5
label_mask = (fam_plot_df["sd"] >= sd_threshold) | (fam_plot_df["n"] >= 5)
for _, row in fam_plot_df[label_mask].iterrows():
    ax_b.annotate(
        row["Family"],
        (row["mean"], row["sd"]),
        textcoords="offset points", xytext=(5, 4),
        fontsize=7.5, color="#222222",
        arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.6)
    )

# Reference lines (overall SD)
overall_sd = erg_scores["score"].std(ddof=1)
ax_b.axhline(overall_sd, color="#888888", lw=1, ls="--",
             label=f"Overall SD = {overall_sd:.3f}")
ax_b.axhline(0, color="#cccccc", lw=0.7)

cb = plt.colorbar(sc, ax=ax_b, shrink=0.8)
cb.set_label("Within-family SD", fontsize=9)

# Size legend
sizes_legend = [2, 5, 10, 20]
handles_size = [
    plt.scatter([], [], s=s * 14 + 20, color="#aaaaaa",
                edgecolors="#555555", linewidths=0.5, label=f"n={s}")
    for s in sizes_legend
]
leg1 = ax_b.legend(handles=handles_size, title="Family size", frameon=False,
                   fontsize=8, loc="upper right", title_fontsize=8)
ax_b.add_artist(leg1)
ax_b.legend(frameon=False, fontsize=9, loc="upper left")

ax_b.set_xlabel("Family mean ergativity score")
ax_b.set_ylabel("Within-family SD of ergativity score")
ax_b.set_title("Within-family score variance\n"
               "(families ≥ 2 ergative languages; "
               "high SD = internally diverse)")
plt.tight_layout()
fig_b.savefig(OUT / "figB_within_family_variance.pdf")
fig_b.savefig(OUT / "figB_within_family_variance.png")
print("Saved figB_within_family_variance")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE C — Per-feature Cramér's V (horizontal bar chart)
# ═══════════════════════════════════════════════════════════════════════════════
feat_plot = feat_cv_df.sort_values("CramersV", ascending=True).reset_index(drop=True)
bar_colors = [DOMAIN_COLOR.get(d, "#cccccc") for d in feat_plot["Domain"]]

fig_c, ax_c = plt.subplots(figsize=(8, max(5, len(feat_plot) * 0.45 + 1.5)))

bars = ax_c.barh(
    feat_plot["Feature"], feat_plot["CramersV"],
    color=bar_colors, edgecolor="white", linewidth=0.5, height=0.7
)

# Value labels
for bar, v in zip(bars, feat_plot["CramersV"]):
    ax_c.text(v + 0.005, bar.get_y() + bar.get_height() / 2,
              f"{v:.3f}", va="center", fontsize=7.5)

# Domain colour legend
domain_seen = {}
for d, c in DOMAIN_COLOR.items():
    if d in feat_plot["Domain"].values:
        domain_seen[d] = c
legend_patches = [mpatches.Patch(color=c, label=d) for d, c in domain_seen.items()]
ax_c.legend(handles=legend_patches, title="Feature domain",
            frameon=False, fontsize=8, title_fontsize=8,
            loc="lower right")

ax_c.set_xlabel("Cramér's V (phylogenetic conservatism)")
ax_c.set_title("Per-feature phylogenetic conservatism\n"
               "(Cramér's V: feature value × family membership, ergative languages with ≥3 family members)")
ax_c.set_xlim(0, min(1.05, feat_plot["CramersV"].max() + 0.08))

plt.tight_layout()
fig_c.savefig(OUT / "figC_feature_conservatism.pdf")
fig_c.savefig(OUT / "figC_feature_conservatism.png")
print("Saved figC_feature_conservatism")

# ── save results CSV ───────────────────────────────────────────────────────────
feat_cv_df.to_csv(OUT / "phylogenetic_feature_conservatism.csv", index=False)
cv_df.to_csv(OUT / "phylogenetic_family_consistency.csv", index=False)
fam_stats_df.to_csv(OUT / "phylogenetic_family_variance.csv", index=False)

print("\n── Summary ──")
print(f"η²                  = {observed_eta2:.4f}  ({interp})")
print(f"Permutation p-value = {perm_p:.4f}  ({sig_str})")
print(f"Most conserved feature:  {feat_cv_df.iloc[0]['Feature']}  "
      f"({feat_cv_df.iloc[0]['Domain']}, V = {feat_cv_df.iloc[0]['CramersV']:.3f})")
print(f"Least conserved feature: {feat_cv_df.iloc[-1]['Feature']}  "
      f"({feat_cv_df.iloc[-1]['Domain']}, V = {feat_cv_df.iloc[-1]['CramersV']:.3f})")
print(f"Most consistent family:  {most_consistent['Family']}  "
      f"(CV = {most_consistent['cv']:.4f})")
print(f"Least consistent family: {least_consistent['Family']}  "
      f"(CV = {least_consistent['cv']:.4f})")
print("\nResults saved to analysis/phylogenetic_*.csv")
print("Done.")
