"""
ERGON — Dimensionality of Ergativity Conditioning
Script 3

For each ergative language, computes how many of the 9 conditioning domains
are fully (all features = 1) or partially (at least one = 1) covered.

Domains:
  Person      GB409_2–5
  Aspect      GB409_6–7
  Tense       GB409_8–9
  Mood        GB409_10–11
  Realis      GB409_12–13
  Agentivity  GB409_14–15
  Topicality  GB409_16–17
  Animacy     GB409_18–19
  Clause type GB409_20–21

Figures
  A — Distribution of n_domains_full (histogram + density)
  B — Heatmap: languages × domains (0 / partial / full)
  C — Boxplot of dimensionality by family (families ≥ 3 languages)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import seaborn as sns
from scipy.stats import gaussian_kde
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

# ── domain definitions ────────────────────────────────────────────────────────
DOMAINS = {
    "Person":      ["GB409_2",  "GB409_3",  "GB409_4",  "GB409_5"],
    "Aspect":      ["GB409_6",  "GB409_7"],
    "Tense":       ["GB409_8",  "GB409_9"],
    "Mood":        ["GB409_10", "GB409_11"],
    "Realis":      ["GB409_12", "GB409_13"],
    "Agentivity":  ["GB409_14", "GB409_15"],
    "Topicality":  ["GB409_16", "GB409_17"],
    "Animacy":     ["GB409_18", "GB409_19"],
    "Clause type": ["GB409_20", "GB409_21"],
}
DOMAIN_NAMES = list(DOMAINS.keys())
N_DOMAINS    = len(DOMAIN_NAMES)

# Domain color mapping for Fig C bars (feature domain groupings)
DOMAIN_COLORS = {
    "Person":      "#4393c3",
    "Aspect":      "#d6604d",
    "Tense":       "#f4a582",
    "Mood":        "#878787",
    "Realis":      "#bababa",
    "Agentivity":  "#74add1",
    "Topicality":  "#abd9e9",
    "Animacy":     "#fee090",
    "Clause type": "#fdae61",
}

# ── load data ─────────────────────────────────────────────────────────────────
langs = pd.read_csv(ROOT / "cldf/languages.csv")
vals  = pd.read_csv(ROOT / "cldf/values.csv")

# Keep only 0/1 values; convert to int
vals_coded = vals[vals["Value"].isin(["0", "1"])].copy()
vals_coded["Value"] = vals_coded["Value"].astype(int)

# Ergative languages only
erg_ids = set(langs.loc[langs["Ergative_type"] == "Ergative", "ID"])

# ── compute per-language domain coverage ──────────────────────────────────────
# Wide pivot: rows = language, cols = features
all_feats = [f for feats in DOMAINS.values() for f in feats]
pivot = (
    vals_coded[vals_coded["Parameter_ID"].isin(all_feats)]
    .pivot_table(index="Language_ID", columns="Parameter_ID", values="Value",
                 aggfunc="first")
    .reindex(columns=all_feats)
)

records = []
for lang_id in pivot.index:
    if lang_id not in erg_ids:
        continue
    lang_info = langs[langs["ID"] == lang_id]
    if lang_info.empty:
        continue
    lang_info = lang_info.iloc[0]

    row = pivot.loc[lang_id]
    n_full    = 0
    n_partial = 0
    domain_status = {}   # 0 / "partial" / "full"
    domains_full    = []
    domains_partial = []

    for domain, feats in DOMAINS.items():
        coded = row[feats].dropna()
        if coded.empty:
            domain_status[domain] = 0
            continue
        n_ones = (coded == 1).sum()
        n_total = len(coded)
        if n_ones == n_total:          # all coded features = 1  → full
            domain_status[domain] = "full"
            n_full    += 1
            n_partial += 1             # full also counts as partial
            domains_full.append(domain)
            domains_partial.append(domain)
        elif n_ones > 0:               # at least one = 1         → partial
            domain_status[domain] = "partial"
            n_partial += 1
            domains_partial.append(domain)
        else:
            domain_status[domain] = 0

    rec = {
        "Glottocode":       lang_id,
        "Name":             lang_info["Name"],
        "Family":           lang_info["Family"],
        "n_domains_full":   n_full,
        "n_domains_partial":n_partial,
        "domains_full":     "; ".join(domains_full),
        "domains_partial":  "; ".join(domains_partial),
    }
    rec.update({f"status_{d}": domain_status[d] for d in DOMAIN_NAMES})
    records.append(rec)

df = pd.DataFrame(records).sort_values("n_domains_full", ascending=False)

# ── print summary ──────────────────────────────────────────────────────────────
print("=" * 65)
print("ERGON — Dimensionality Analysis")
print("=" * 65)
print(f"\nErgative languages analysed: {len(df)}")
print(f"Mean n_domains_full:    {df['n_domains_full'].mean():.2f}")
print(f"Median n_domains_full:  {df['n_domains_full'].median():.1f}")
print(f"Range:                  {df['n_domains_full'].min()}–{df['n_domains_full'].max()}")

print("\n── Top 10 most dimensional languages ──")
top10 = df.head(10)[["Name","Family","n_domains_full","n_domains_partial","domains_full"]]
print(top10.to_string(index=False))

print("\n── Bottom 10 least dimensional languages ──")
bot10 = df.tail(10)[["Name","Family","n_domains_full","n_domains_partial","domains_full"]]
print(bot10.to_string(index=False))

# Family means
fam_counts = df["Family"].value_counts()
fams_ge3   = fam_counts[fam_counts >= 3].index
fam_means  = (df[df["Family"].isin(fams_ge3)]
              .groupby("Family")["n_domains_full"]
              .agg(["mean","median","count"])
              .sort_values("mean", ascending=False))
print("\n── Family means (families ≥ 3 ergative languages) ──")
print(fam_means.to_string())

# Domain coverage
print("\n── Domain coverage (among all ergative languages) ──")
for domain in DOMAIN_NAMES:
    col = f"status_{domain}"
    n_full    = (df[col] == "full").sum()
    n_partial = (df[col] == "partial").sum()
    n_none    = (df[col] == 0).sum()
    pct_full    = 100 * n_full / len(df)
    pct_partial = 100 * (n_full + n_partial) / len(df)
    print(f"  {domain:<14} full={n_full:3d} ({pct_full:4.1f}%)  "
          f"partial={n_partial:3d}  none={n_none:3d}  "
          f"any coverage={pct_partial:4.1f}%")

full_rates  = {d: (df[f"status_{d}"] == "full").mean() for d in DOMAIN_NAMES}
any_rates   = {d: ((df[f"status_{d}"] == "full") | (df[f"status_{d}"] == "partial")).mean()
               for d in DOMAIN_NAMES}
most_full   = max(full_rates, key=full_rates.get)
least_full  = min(full_rates, key=full_rates.get)
most_any    = max(any_rates, key=any_rates.get)
least_any   = min(any_rates, key=any_rates.get)
print(f"\nMost commonly fully covered domain:    {most_full}  ({100*full_rates[most_full]:.1f}%)")
print(f"Least commonly fully covered domain:   {least_full}  ({100*full_rates[least_full]:.1f}%)")
print(f"Most commonly any-covered domain:      {most_any}  ({100*any_rates[most_any]:.1f}%)")
print(f"Least commonly any-covered domain:     {least_any}  ({100*any_rates[least_any]:.1f}%)")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE A — Distribution of n_domains_full
# ═══════════════════════════════════════════════════════════════════════════════
fams_ge3_list = sorted(fams_ge3.tolist())
# Build a palette for families
family_palette = dict(zip(
    fams_ge3_list,
    sns.color_palette("tab20", n_colors=len(fams_ge3_list))
))

fig_a, axes_a = plt.subplots(1, 2, figsize=(14, 5.5))

# ── Left panel: overall histogram + density ──
ax = axes_a[0]
vals_hist = df["n_domains_full"].values
bins = np.arange(-0.5, N_DOMAINS + 1.5, 1)

ax.hist(vals_hist, bins=bins, color="#5599cc", edgecolor="white",
        linewidth=0.8, alpha=0.85, density=True, label="All ergative langs")

# KDE overlay
if len(vals_hist) > 5:
    x_kde = np.linspace(0, N_DOMAINS, 300)
    kde   = gaussian_kde(vals_hist, bw_method=0.5)
    ax.plot(x_kde, kde(x_kde), color="#1a3a5c", lw=2, label="KDE")

mean_val   = df["n_domains_full"].mean()
median_val = df["n_domains_full"].median()
ax.axvline(mean_val,   color="#d62728", lw=1.8, ls="--", label=f"Mean = {mean_val:.2f}")
ax.axvline(median_val, color="#2ca02c", lw=1.8, ls=":",  label=f"Median = {median_val:.1f}")

ax.set_xlabel("Number of fully covered domains")
ax.set_ylabel("Density")
ax.set_title("Distribution of conditioning dimensionality\n(ergative languages)")
ax.set_xticks(range(N_DOMAINS + 1))
ax.legend(frameon=False, fontsize=9)

# ── Right panel: small multiples by family (families ≥ 3) ──
ax2 = axes_a[1]
df_fam = df[df["Family"].isin(fams_ge3)].copy()

# Jitter + mean per family, sorted by mean
fam_order = (df_fam.groupby("Family")["n_domains_full"]
             .mean().sort_values(ascending=False).index.tolist())

y_ticks = []
y_labels = []
for i, fam in enumerate(fam_order):
    sub    = df_fam[df_fam["Family"] == fam]["n_domains_full"].values
    color  = family_palette[fam]
    jitter = np.random.default_rng(i).uniform(-0.25, 0.25, len(sub))
    ax2.scatter(sub + jitter * 0, [i] * len(sub), color=color,
                alpha=0.6, s=28, zorder=3)
    ax2.scatter([sub.mean()], [i], color=color, s=80, zorder=4,
                marker="D", edgecolors="white", linewidths=0.7)
    ax2.axhline(i, color="#eeeeee", lw=0.6, zorder=1)
    n_fam = fam_counts[fam]
    y_ticks.append(i)
    y_labels.append(f"{fam}  (n={n_fam})")

ax2.set_yticks(y_ticks)
ax2.set_yticklabels(y_labels, fontsize=8)
ax2.set_xlabel("Number of fully covered domains")
ax2.set_title("Family comparison\n(families ≥ 3 ergative languages; ◆ = family mean)")
ax2.set_xticks(range(N_DOMAINS + 1))
ax2.set_xlim(-0.5, N_DOMAINS + 0.5)
ax2.invert_yaxis()

plt.tight_layout()
fig_a.savefig(OUT / "figA_dimensionality_distribution.pdf")
fig_a.savefig(OUT / "figA_dimensionality_distribution.png")
print("\nSaved figA_dimensionality_distribution")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE B — Heatmap: languages × domains
# ═══════════════════════════════════════════════════════════════════════════════

# Numeric matrix for heatmap: 0 = none, 1 = partial, 2 = full
df_sorted = df.sort_values(["n_domains_full", "n_domains_partial", "Family", "Name"],
                            ascending=[False, False, True, True]).reset_index(drop=True)

heat_vals = np.zeros((len(df_sorted), N_DOMAINS), dtype=float)
for i, (_, row) in enumerate(df_sorted.iterrows()):
    for j, domain in enumerate(DOMAIN_NAMES):
        st = row[f"status_{domain}"]
        if st == "full":
            heat_vals[i, j] = 2.0
        elif st == "partial":
            heat_vals[i, j] = 1.0
        else:
            heat_vals[i, j] = 0.0

# Family strip colors
all_families = df_sorted["Family"].unique().tolist()
n_fams_total = len(all_families)
fam_strip_palette = dict(zip(
    all_families,
    sns.color_palette("tab20", n_colors=min(n_fams_total, 20))
    + sns.color_palette("tab20b", n_colors=max(0, n_fams_total - 20))
))
strip_colors = [fam_strip_palette[f] for f in df_sorted["Family"]]

# Figure layout: family strip | heatmap
n_langs  = len(df_sorted)
fig_width  = max(10, N_DOMAINS * 1.0 + 4)
fig_height = max(8,  n_langs  * 0.22 + 2)
fig_b = plt.figure(figsize=(fig_width, fig_height))
gs    = gridspec.GridSpec(1, 3, width_ratios=[0.03, 0.97, 0.05],
                          wspace=0.02, figure=fig_b)
ax_strip = fig_b.add_subplot(gs[0])
ax_heat  = fig_b.add_subplot(gs[1])
ax_cbar  = fig_b.add_subplot(gs[2])

# Draw family color strip
for i, color in enumerate(strip_colors):
    ax_strip.add_patch(mpatches.Rectangle((0, i - 0.5), 1, 1,
                                           color=color, lw=0))
ax_strip.set_xlim(0, 1)
ax_strip.set_ylim(-0.5, n_langs - 0.5)
ax_strip.set_xticks([])
ax_strip.set_yticks([])
ax_strip.invert_yaxis()
for spine in ax_strip.spines.values():
    spine.set_visible(False)
ax_strip.set_ylabel("Languages (sorted by dimensionality)", fontsize=10)

# Heatmap
cmap_heat = plt.cm.colors.LinearSegmentedColormap.from_list(
    "dim_cmap", ["#f7f7f7", "#92c5de", "#0571b0"], N=3
)
im = ax_heat.imshow(heat_vals, aspect="auto", cmap=cmap_heat,
                    vmin=0, vmax=2, interpolation="nearest", origin="upper")

ax_heat.set_xticks(range(N_DOMAINS))
ax_heat.set_xticklabels(DOMAIN_NAMES, rotation=40, ha="right", fontsize=9)
ax_heat.set_yticks(range(n_langs))
ax_heat.set_yticklabels(df_sorted["Name"], fontsize=4.5)
ax_heat.tick_params(axis="y", length=0)

# Mark family group boundaries
prev_fam = None
for i, fam in enumerate(df_sorted["Family"]):
    if fam != prev_fam and i > 0:
        ax_heat.axhline(i - 0.5, color="white", lw=1.0)
        ax_strip.axhline(i - 0.5, color="white", lw=0.8)
    prev_fam = fam

ax_heat.set_title("Domain coverage per language × conditioning domain\n"
                  "(dark = full, light blue = partial, white = none)",
                  pad=10, fontsize=12)

# Colorbar
cb = fig_b.colorbar(im, cax=ax_cbar, ticks=[0, 1, 2])
cb.ax.set_yticklabels(["None", "Partial", "Full"], fontsize=8)

# Legend for family strip: only the families with ≥3 languages
legend_patches = [
    mpatches.Patch(color=fam_strip_palette[f], label=f"{f} (n={fam_counts.get(f,0)})")
    for f in sorted(fams_ge3)
]
fig_b.legend(handles=legend_patches, loc="lower center",
             bbox_to_anchor=(0.5, -0.01), ncol=min(4, len(legend_patches)),
             fontsize=7, frameon=False, title="Families (≥ 3 ergative languages)")

plt.tight_layout(rect=[0, 0.04, 1, 1])
fig_b.savefig(OUT / "figB_dimensionality_heatmap.pdf")
fig_b.savefig(OUT / "figB_dimensionality_heatmap.png")
print("Saved figB_dimensionality_heatmap")

# ═══════════════════════════════════════════════════════════════════════════════
# FIGURE C — Boxplot by family
# ═══════════════════════════════════════════════════════════════════════════════
df_fam_box = df[df["Family"].isin(fams_ge3)].copy()
fam_medians = (df_fam_box.groupby("Family")["n_domains_full"]
               .median().sort_values(ascending=True))
fam_order_c = fam_medians.index.tolist()

fig_c, ax_c = plt.subplots(figsize=(10, max(5, len(fam_order_c) * 0.52 + 1.5)))

bp = ax_c.boxplot(
    [df_fam_box.loc[df_fam_box["Family"] == f, "n_domains_full"].values
     for f in fam_order_c],
    vert=False, patch_artist=True,
    positions=range(len(fam_order_c)),
    widths=0.55,
    medianprops=dict(color="#d62728", lw=2),
    whiskerprops=dict(color="#555555", lw=1.2),
    capprops=dict(color="#555555", lw=1.2),
    flierprops=dict(marker="o", markersize=4, alpha=0.5, markeredgewidth=0.5)
)

# Color boxes by family
for patch, fam in zip(bp["boxes"], fam_order_c):
    color = family_palette.get(fam, "#aaaaaa")
    patch.set_facecolor(color)
    patch.set_alpha(0.75)

# Jitter overlay
for i, fam in enumerate(fam_order_c):
    sub    = df_fam_box.loc[df_fam_box["Family"] == fam, "n_domains_full"].values
    jitter = np.random.default_rng(i + 42).uniform(-0.22, 0.22, len(sub))
    color  = family_palette.get(fam, "#aaaaaa")
    ax_c.scatter(sub, i + jitter, color=color, s=18, alpha=0.7,
                 zorder=5, edgecolors="white", linewidths=0.4)

# n= labels
for i, fam in enumerate(fam_order_c):
    n = fam_counts[fam]
    ax_c.text(N_DOMAINS + 0.1, i, f"n={n}", va="center", fontsize=8, color="#555")

ax_c.set_yticks(range(len(fam_order_c)))
ax_c.set_yticklabels(fam_order_c, fontsize=9)
ax_c.set_xlabel("Number of fully covered conditioning domains")
ax_c.set_title("Ergativity conditioning dimensionality by family\n"
               "(families ≥ 3 ergative languages, sorted by median)")
ax_c.set_xlim(-0.5, N_DOMAINS + 0.7)
ax_c.set_xticks(range(N_DOMAINS + 1))

plt.tight_layout()
fig_c.savefig(OUT / "figC_dimensionality_boxplot.pdf")
fig_c.savefig(OUT / "figC_dimensionality_boxplot.png")
print("Saved figC_dimensionality_boxplot")

# ── save results CSV ───────────────────────────────────────────────────────────
out_cols = (["Glottocode", "Name", "Family",
             "n_domains_full", "n_domains_partial",
             "domains_full", "domains_partial"]
            + [f"status_{d}" for d in DOMAIN_NAMES])
df[out_cols].to_csv(OUT / "dimensionality_scores.csv", index=False)
print("\nResults saved to analysis/dimensionality_scores.csv")
print("Done.")
