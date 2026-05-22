"""
ERGON Quantitative Analysis
Focus: Total Ergativity (fully_ergative hypothesis)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT  = Path(__file__).parent

# ── style (clean, publication-quality) ───────────────────────────────────────
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

# ── load ERGON data ───────────────────────────────────────────────────────────
langs = pd.read_csv(ROOT / "cldf/languages.csv")
vals  = pd.read_csv(ROOT / "cldf/values.csv")

# Only coded values (0 or 1), exclude ?
vals_coded = vals[vals["Value"].isin(["0", "1"])].copy()
vals_coded["Value"] = vals_coded["Value"].astype(int)

# ── load hypothesis template from Excel ──────────────────────────────────────
xl = pd.read_excel(
    "/Users/robertozariquiey/Downloads/ergon_testing universals.xlsx",
    sheet_name=0
)
xl.columns = xl.columns.str.strip()

# Extract the "fully ergative" hypothesis: feature → required value (NaN = irrelevant)
hyp_col = "fully ergative"
fully_erg_template = xl[["Ergon_ID", hyp_col]].dropna(subset=[hyp_col])
fully_erg_template = fully_erg_template.set_index("Ergon_ID")[hyp_col]
# {GB409_X: 1.0 or 0.0}
print(f"Fully-ergative hypothesis covers {len(fully_erg_template)} features:")
print(fully_erg_template.to_dict())

# ── compute ergativity score per language ─────────────────────────────────────
# Score = fraction of relevant features where the language matches the hypothesis
relevant_features = fully_erg_template.index.tolist()

scores = []
for gc, group in vals_coded[vals_coded["Parameter_ID"].isin(relevant_features)].groupby("Language_ID"):
    feature_vals = group.set_index("Parameter_ID")["Value"]
    n_total = len(relevant_features)
    n_coded  = 0
    n_match  = 0
    for feat, expected in fully_erg_template.items():
        if feat in feature_vals.index:
            n_coded += 1
            if feature_vals[feat] == int(expected):
                n_match += 1
    if n_coded >= 12:  # at least half of features must be coded
        scores.append({
            "Glottocode": gc,
            "n_coded": n_coded,
            "n_match": n_match,
            "score": n_match / n_coded,
            "score_of_total": n_match / n_total,
        })

score_df = pd.DataFrame(scores)
score_df = score_df.merge(langs[["ID","Name","Family","Ergative_type"]],
                          left_on="Glottocode", right_on="ID")
score_df = score_df.sort_values("score", ascending=False)

print(f"\nLanguages with sufficient data: {len(score_df)}")
print(f"\nTop 20 most ergative languages:")
print(score_df[["Name","Family","score","n_coded"]].head(20).to_string(index=False))
print(f"\nDescriptive stats (score):")
print(score_df["score"].describe())

# ── family-level aggregation ──────────────────────────────────────────────────
# Only families with >= 3 languages
family_counts = score_df["Family"].value_counts()
families_ok = family_counts[family_counts >= 3].index
fam_df = score_df[score_df["Family"].isin(families_ok)]
fam_means = fam_df.groupby("Family")["score"].mean().sort_values(ascending=False)

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 1 — Distribution of ergativity scores
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))

erg_scores  = score_df[score_df["Ergative_type"] == "Ergative"]["score"]
nerg_scores = score_df[score_df["Ergative_type"] == "Non-ergative"]["score"]

ax.hist(erg_scores,  bins=20, alpha=0.75, color="#2166ac", label=f"Ergative (n={len(erg_scores)})")
ax.hist(nerg_scores, bins=20, alpha=0.75, color="#d6604d", label=f"Non-ergative (n={len(nerg_scores)})")

ax.axvline(erg_scores.mean(),  color="#2166ac", linestyle="--", lw=1.5,
           label=f"Mean (erg.) = {erg_scores.mean():.2f}")
ax.axvline(nerg_scores.mean(), color="#d6604d", linestyle="--", lw=1.5,
           label=f"Mean (non-erg.) = {nerg_scores.mean():.2f}")

ax.set_xlabel("Ergativity score (proportion of fully-ergative features matched)")
ax.set_ylabel("Number of languages")
ax.set_title("Distribution of ergativity scores across ERGON languages")
ax.legend(frameon=False, fontsize=9)
plt.tight_layout()
fig.savefig(OUT / "fig1_score_distribution.pdf")
fig.savefig(OUT / "fig1_score_distribution.png")
print("\nSaved fig1")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 2 — Top 30 most ergative languages
# ─────────────────────────────────────────────────────────────────────────────
top30 = score_df.head(30).iloc[::-1]  # reverse for horizontal bar

# Color by ergative type
colors = ["#2166ac" if t == "Ergative" else "#d6604d"
          for t in top30["Ergative_type"]]

fig, ax = plt.subplots(figsize=(8, 10))
bars = ax.barh(top30["Name"], top30["score"], color=colors, edgecolor="white", height=0.7)

# Annotate with family
for i, (_, row) in enumerate(top30.iterrows()):
    ax.text(row["score"] + 0.005, i, row["Family"],
            va="center", ha="left", fontsize=7, color="#555555")

ax.set_xlabel("Ergativity score")
ax.set_title("30 most ergative languages in ERGON", pad=12)
ax.set_xlim(0, 1.25)
ax.axvline(1.0, color="gray", linestyle=":", lw=1)

patch_erg  = mpatches.Patch(color="#2166ac", label="Ergative")
patch_nerg = mpatches.Patch(color="#d6604d", label="Non-ergative")
ax.legend(handles=[patch_erg, patch_nerg], frameon=False, fontsize=9)
plt.tight_layout()
fig.savefig(OUT / "fig2_top30.pdf")
fig.savefig(OUT / "fig2_top30.png")
print("Saved fig2")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 3 — Family-level boxplot (families with ≥ 3 languages)
# ─────────────────────────────────────────────────────────────────────────────
# Sort families by median score
fam_order = (fam_df.groupby("Family")["score"]
             .median()
             .sort_values(ascending=False)
             .index.tolist())

fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=fam_df, x="Family", y="score", order=fam_order,
            palette="Blues_r", width=0.5,
            linewidth=1, fliersize=3, ax=ax)
sns.stripplot(data=fam_df, x="Family", y="score", order=fam_order,
              color="black", alpha=0.4, size=4, jitter=True, ax=ax)

ax.set_xlabel("")
ax.set_ylabel("Ergativity score")
ax.set_title("Ergativity scores by language family (families with ≥ 3 languages)")
ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right")
ax.axhline(score_df["score"].mean(), color="red", linestyle="--", lw=1,
           alpha=0.6, label=f"Overall mean = {score_df['score'].mean():.2f}")
ax.legend(frameon=False, fontsize=9)
plt.tight_layout()
fig.savefig(OUT / "fig3_families.pdf")
fig.savefig(OUT / "fig3_families.png")
print("Saved fig3")

# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 4 — Feature-level profile: how often each feature is present
#            in ergative vs non-ergative languages
# ─────────────────────────────────────────────────────────────────────────────
feature_order = [f"GB409_{i}" for i in range(1, 25)]
feature_labels = {
    "GB409_1": "Overt ABS marker",
    "GB409_2": "ERG flagging: 1st person",
    "GB409_3": "ERG flagging: 2nd person",
    "GB409_4": "ERG flagging: 3rd person",
    "GB409_5": "ERG flagging: full NPs",
    "GB409_6": "ERG flagging: imperfective",
    "GB409_7": "ERG flagging: perfective",
    "GB409_8": "ERG flagging: past",
    "GB409_9": "ERG flagging: non-past",
    "GB409_10": "ERG flagging: indicative",
    "GB409_11": "ERG flagging: non-indicative",
    "GB409_12": "ERG flagging: realis",
    "GB409_13": "ERG flagging: irrealis",
    "GB409_14": "ERG flagging: agentive A",
    "GB409_15": "ERG flagging: non-agentive A",
    "GB409_16": "ERG flagging: topical A",
    "GB409_17": "ERG flagging: non-topical A",
    "GB409_18": "ERG flagging: animate A",
    "GB409_19": "ERG flagging: inanimate A",
    "GB409_20": "ERG flagging: main clause",
    "GB409_21": "ERG flagging: non-main clause",
    "GB409_22": "ERG: other conditioning",
    "GB409_23": "ERG = GEN marker",
    "GB409_24": "ERG = INSTR marker",
}

erg_langs  = langs[langs["Ergative_type"] == "Ergative"]["ID"].tolist()
nerg_langs = langs[langs["Ergative_type"] == "Non-ergative"]["ID"].tolist()

feat_rates = []
for feat in feature_order:
    for group, gc_list in [("Ergative", erg_langs), ("Non-ergative", nerg_langs)]:
        sub = vals_coded[(vals_coded["Parameter_ID"] == feat) &
                         (vals_coded["Language_ID"].isin(gc_list))]
        if len(sub) > 0:
            rate = sub["Value"].mean()
            feat_rates.append({"Feature": feat, "Group": group, "Rate": rate, "N": len(sub)})

feat_rate_df = pd.DataFrame(feat_rates)

fig, ax = plt.subplots(figsize=(10, 7))
x = np.arange(len(feature_order))
w = 0.38

erg_rates  = feat_rate_df[feat_rate_df["Group"] == "Ergative"].set_index("Feature")["Rate"]
nerg_rates = feat_rate_df[feat_rate_df["Group"] == "Non-ergative"].set_index("Feature")["Rate"]

ax.bar(x - w/2, [erg_rates.get(f, 0)  for f in feature_order],
       width=w, color="#2166ac", alpha=0.85, label="Ergative")
ax.bar(x + w/2, [nerg_rates.get(f, 0) for f in feature_order],
       width=w, color="#d6604d", alpha=0.85, label="Non-ergative")

ax.set_xticks(x)
ax.set_xticklabels([feature_labels[f] for f in feature_order],
                   rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Proportion of languages with value = 1")
ax.set_title("Feature profiles: ergative vs. non-ergative languages")
ax.legend(frameon=False)
ax.set_ylim(0, 1.05)
plt.tight_layout()
fig.savefig(OUT / "fig4_feature_profile.pdf")
fig.savefig(OUT / "fig4_feature_profile.png")
print("Saved fig4")

# ─────────────────────────────────────────────────────────────────────────────
# Summary statistics
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

print(f"\nTotal languages analysed: {len(score_df)}")
print(f"  Ergative:     {len(erg_scores)}")
print(f"  Non-ergative: {len(nerg_scores)}")

print(f"\nMean ergativity score (ergative langs):     {erg_scores.mean():.3f}")
print(f"Mean ergativity score (non-ergative langs): {nerg_scores.mean():.3f}")

fully = score_df[score_df["score"] == 1.0]
print(f"\nFully ergative languages (score = 1.0): {len(fully)}")
for _, r in fully.iterrows():
    print(f"  {r['Name']} ({r['Glottocode']}) — {r['Family']}")

print(f"\nFamily means (families ≥ 3 languages):")
for fam, mean in fam_means.items():
    n = family_counts[fam]
    print(f"  {fam:<30} mean={mean:.3f}  n={n}")

# Mann-Whitney U test: ergative vs non-ergative scores
u_stat, p_val = stats.mannwhitneyu(erg_scores, nerg_scores, alternative="greater")
print(f"\nMann-Whitney U test (ergative > non-ergative):")
print(f"  U = {u_stat:.1f}, p = {p_val:.4e}")

score_df.to_csv(OUT / "ergativity_scores.csv", index=False)
print("\nFull scores saved to analysis/ergativity_scores.csv")
