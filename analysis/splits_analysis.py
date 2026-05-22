"""
ERGON — Split Ergativity Analysis
Four hypotheses (each tests 2 features):
  aspect:  GB409_6=1 (imperfective) & GB409_7=0 (perfective)  → ERG in IMPF, not PERF
  tense:   GB409_9=1 (non-past)     & GB409_8=0 (past)        → ERG in NON-PAST, not PAST
  mood:    GB409_11=1 (non-indic.)  & GB409_10=0 (indicative) → ERG in NON-IND, not IND
  realis:  GB409_13=1 (irrealis)    & GB409_12=0 (realis)     → ERG in IRR, not REAL

The "expected" typological direction (Dixon 1994, Givón 2001) is the opposite in each case.
We also measure the full 2x2 (both features) to capture:
  - matches hypothesis (split in unexpected direction)
  - reverse split (expected direction: e.g., ERG in PERF not IMPF)
  - uniform ERG (both = 1)
  - uniform NOM-ACC (both = 0)
  - inconsistent (other combinations)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

langs = pd.read_csv(ROOT / "cldf/languages.csv")
vals  = pd.read_csv(ROOT / "cldf/values.csv")
vals_coded = vals[vals["Value"].isin(["0","1"])].copy()
vals_coded["Value"] = vals_coded["Value"].astype(int)

# Only ergative languages
erg_langs = langs[langs["Ergative_type"] == "Ergative"]["ID"].tolist()
erg_vals  = vals_coded[vals_coded["Language_ID"].isin(erg_langs)]

SPLITS = {
    "Aspect\n(IMPF vs PERF)": {
        "feat_a": "GB409_6", "label_a": "Imperfective",
        "feat_b": "GB409_7", "label_b": "Perfective",
        "hypothesis": (1, 0),   # ERG in IMPF, not PERF (unexpected)
        "expected":   (0, 1),   # ERG in PERF, not IMPF (Dixon's classic split)
    },
    "Tense\n(NON-PAST vs PAST)": {
        "feat_a": "GB409_9", "label_a": "Non-past",
        "feat_b": "GB409_8", "label_b": "Past",
        "hypothesis": (1, 0),   # ERG in NON-PAST, not PAST (unexpected)
        "expected":   (0, 1),   # ERG in PAST, not NON-PAST (expected)
    },
    "Mood\n(NON-IND vs IND)": {
        "feat_a": "GB409_11", "label_a": "Non-indicative",
        "feat_b": "GB409_10", "label_b": "Indicative",
        "hypothesis": (1, 0),   # ERG in NON-IND, not IND (unexpected)
        "expected":   (0, 1),   # ERG in IND, not NON-IND (expected)
    },
    "Realis\n(IRR vs REAL)": {
        "feat_a": "GB409_13", "label_a": "Irrealis",
        "feat_b": "GB409_12", "label_b": "Realis",
        "hypothesis": (1, 0),   # ERG in IRR, not REAL (unexpected)
        "expected":   (0, 1),   # ERG in REAL, not IRR (expected)
    },
}

# ── classify each language × split ───────────────────────────────────────────
records = []
for gc, group in erg_vals.groupby("Language_ID"):
    feat_vals = group.set_index("Parameter_ID")["Value"]
    lang_info = langs[langs["ID"] == gc].iloc[0]
    for split_name, cfg in SPLITS.items():
        fa, fb = cfg["feat_a"], cfg["feat_b"]
        if fa not in feat_vals.index or fb not in feat_vals.index:
            continue
        va, vb = feat_vals[fa], feat_vals[fb]
        pat = (int(va), int(vb))
        if pat == cfg["hypothesis"]:
            cat = "Unexpected split\n(matches hypothesis)"
        elif pat == cfg["expected"]:
            cat = "Expected split"
        elif pat == (1, 1):
            cat = "Uniform ERG"
        elif pat == (0, 0):
            cat = "Uniform NOM-ACC"
        else:
            cat = "Other"
        records.append({
            "Glottocode": gc,
            "Name": lang_info["Name"],
            "Family": lang_info["Family"],
            "Split": split_name,
            "val_a": int(va),
            "val_b": int(vb),
            "Category": cat,
        })

df = pd.DataFrame(records)

# ── print summary ─────────────────────────────────────────────────────────────
print("="*65)
print("SPLIT ERGATIVITY — FULL BREAKDOWN")
print("="*65)
for split_name, cfg in SPLITS.items():
    sub = df[df["Split"] == split_name]
    n = len(sub)
    print(f"\n{split_name.replace(chr(10),' ')}  (n languages with data = {n})")
    counts = sub["Category"].value_counts()
    for cat, cnt in counts.items():
        pct = 100 * cnt / n
        print(f"  {cat:<38} {cnt:3d}  ({pct:.1f}%)")
    # List unexpected-split languages
    unexp = sub[sub["Category"].str.startswith("Unexpected")]
    if len(unexp):
        print(f"  → Unexpected-split languages:")
        for _, r in unexp.sort_values("Family").iterrows():
            print(f"     {r['Name']} ({r['Glottocode']}) — {r['Family']}")

# Family breakdown for unexpected splits
print("\n" + "="*65)
print("UNEXPECTED SPLITS BY FAMILY")
print("="*65)
unexp_df = df[df["Category"].str.startswith("Unexpected")].copy()
family_counts = langs[langs["Ergative_type"]=="Ergative"]["Family"].value_counts()

for split_name in SPLITS:
    sub = unexp_df[unexp_df["Split"] == split_name]
    if len(sub) == 0:
        continue
    print(f"\n{split_name.replace(chr(10),' ')}:")
    fc = sub["Family"].value_counts()
    for fam, cnt in fc.items():
        total = family_counts.get(fam, "?")
        print(f"  {fam:<30} {cnt}/{total}")

# ── FIGURE 1 — 2x2 stacked bars for all 4 splits ─────────────────────────────
COLORS = {
    "Uniform ERG":                        "#2166ac",
    "Expected split":                     "#92c5de",
    "Unexpected split\n(matches hypothesis)": "#d6604d",
    "Uniform NOM-ACC":                    "#f4a582",
    "Other":                              "#e0e0e0",
}
CAT_ORDER = ["Uniform ERG", "Expected split",
             "Unexpected split\n(matches hypothesis)", "Uniform NOM-ACC", "Other"]

fig, axes = plt.subplots(1, 4, figsize=(14, 5), sharey=False)

for ax, (split_name, cfg) in zip(axes, SPLITS.items()):
    sub = df[df["Split"] == split_name]
    counts = sub["Category"].value_counts().reindex(CAT_ORDER, fill_value=0)
    n_total = len(sub)
    pcts = 100 * counts / n_total

    bottom = 0
    for cat in CAT_ORDER:
        h = pcts[cat]
        if h > 0:
            bar = ax.bar(0, h, bottom=bottom, color=COLORS[cat],
                         edgecolor="white", linewidth=1, width=0.5)
            if h > 4:
                ax.text(0, bottom + h/2,
                        f"{counts[cat]}\n({h:.0f}%)",
                        ha="center", va="center", fontsize=8, color="white",
                        fontweight="bold")
            bottom += h

    ax.set_xlim(-0.5, 0.5)
    ax.set_ylim(0, 100)
    ax.set_xticks([])
    ax.set_title(split_name, fontsize=10, pad=8)
    ax.set_ylabel("% of languages" if ax == axes[0] else "")

    # Annotate features
    ax.text(0, -8, f"✚ {cfg['label_a']}", ha="center", fontsize=7.5,
            color="#2166ac", clip_on=False)
    ax.text(0, -13, f"✖ {cfg['label_b']}", ha="center", fontsize=7.5,
            color="#d6604d", clip_on=False)

# Legend
handles = [plt.Rectangle((0,0),1,1, color=COLORS[c]) for c in CAT_ORDER]
labels  = [c.replace("\n"," ") for c in CAT_ORDER]
fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=8.5,
           frameon=False, bbox_to_anchor=(0.5, -0.08))
fig.suptitle("Split ergativity patterns in ERGON ergative languages\n"
             "(✚ = ERG present, ✖ = ERG absent in that domain)",
             fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(OUT / "fig8_splits_overview.pdf")
fig.savefig(OUT / "fig8_splits_overview.png")
print("\nSaved fig8")

# ── FIGURE 2 — unexpected splits: which families? ─────────────────────────────
# Pivot: family × split, count of unexpected
pivot = (unexp_df.groupby(["Family","Split"])
         .size().unstack(fill_value=0))
# Only families with >= 1 unexpected split
pivot = pivot[pivot.sum(axis=1) > 0]
# Normalize by family total
fam_totals = family_counts.reindex(pivot.index, fill_value=1)
pivot_pct = pivot.div(fam_totals, axis=0) * 100

# Sort by total unexpected
pivot_pct = pivot_pct.loc[pivot_pct.sum(axis=1).sort_values(ascending=True).index]

fig, ax = plt.subplots(figsize=(10, max(4, len(pivot_pct)*0.55 + 1.5)))
split_colors = ["#4d9221","#a6d96a","#d9ef8b","#fee08b"]
pivot_pct.plot(kind="barh", stacked=False, ax=ax,
               color=split_colors, edgecolor="white", width=0.7)

ax.set_xlabel("% of languages in family with unexpected split")
ax.set_title("Families with unexpected splits\n(% of ergative languages per family)", pad=10)
ax.legend(title="Split type", labels=[s.replace("\n"," ") for s in pivot_pct.columns],
          frameon=False, fontsize=8)
ax.axvline(0, color="gray", lw=0.5)
plt.tight_layout()
fig.savefig(OUT / "fig9_splits_families.pdf")
fig.savefig(OUT / "fig9_splits_families.png")
print("Saved fig9")

# ── FIGURE 3 — co-occurrence heatmap: do splits cluster? ─────────────────────
# For each language, which splits does it show?
lang_splits = (df[df["Category"].str.startswith("Unexpected")]
               .groupby(["Glottocode","Split"]).size()
               .unstack(fill_value=0)
               .clip(upper=1))

if len(lang_splits) > 0:
    split_labels = [s.replace("\n"," ") for s in lang_splits.columns]
    co = lang_splits.T.dot(lang_splits).astype(float)
    np.fill_diagonal(co.values, np.nan)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(co, annot=True, fmt=".0f", cmap="YlOrRd",
                xticklabels=split_labels, yticklabels=split_labels,
                linewidths=0.5, ax=ax, cbar_kws={"label":"# languages"})
    ax.set_title("Co-occurrence of unexpected splits\n(how many languages show both?)", pad=10)
    plt.tight_layout()
    fig.savefig(OUT / "fig10_split_cooccurrence.pdf")
    fig.savefig(OUT / "fig10_split_cooccurrence.png")
    print("Saved fig10")

# Save table
df.to_csv(OUT / "splits_classifications.csv", index=False)
print("Saved splits_classifications.csv")
