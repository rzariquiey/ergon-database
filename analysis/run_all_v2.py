#!/usr/bin/env python3
"""
ERGON Database — Complete Analysis Suite (v2, curated data)
Re-runs all 7 analyses on the updated curated dataset.

Rules:
- Silverstein hierarchy: only ergative languages, exclude rows with '?'
- Degree of ergativity: only ergative languages, exclude languages with any '?'
- Other analyses: ergative languages only unless noted
"""

import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from itertools import combinations

CLDF = os.path.join(os.path.dirname(__file__), '..', 'cldf')
OUTDIR = os.path.dirname(__file__)

FEATURES = [f'GB409_{i}' for i in range(1, 25)]
FEATURE_LABELS = {
    'GB409_1': 'Overt ABS marker',
    'GB409_2': 'ERG on 1st person',
    'GB409_3': 'ERG on 2nd person',
    'GB409_4': 'ERG on 3rd person',
    'GB409_5': 'ERG on full NPs',
    'GB409_6': 'ERG in imperfective',
    'GB409_7': 'ERG in perfective',
    'GB409_8': 'ERG in past',
    'GB409_9': 'ERG in non-past',
    'GB409_10': 'ERG in indicative',
    'GB409_11': 'ERG in non-indicative',
    'GB409_12': 'ERG in realis',
    'GB409_13': 'ERG in irrealis',
    'GB409_14': 'ERG with agentive A',
    'GB409_15': 'ERG with non-agentive A',
    'GB409_16': 'ERG with topical A',
    'GB409_17': 'ERG with non-topical A',
    'GB409_18': 'ERG with animate A',
    'GB409_19': 'ERG with inanimate A',
    'GB409_20': 'ERG in main clauses',
    'GB409_21': 'ERG in non-main clauses',
    'GB409_22': 'ERG other factor',
    'GB409_23': 'ERG = GEN',
    'GB409_24': 'ERG = INSTR/COM',
}

# ── Load data ─────────────────────────────────────────────────────────────────

def load_data():
    with open(os.path.join(CLDF, 'languages.csv'), encoding='utf-8') as f:
        langs = {r['Glottocode']: r for r in csv.DictReader(f)}
    with open(os.path.join(CLDF, 'values.csv'), encoding='utf-8') as f:
        vals = [v for v in csv.DictReader(f) if v['Parameter_ID'] in FEATURES]

    # Build matrix: lang -> {feature: value}
    data = defaultdict(dict)
    for v in vals:
        gc = v['Language_ID']
        val = v['Value']
        data[gc][v['Parameter_ID']] = val

    return langs, data

langs, data = load_data()

# Ergative languages only
erg_langs = {gc for gc, info in langs.items() if info['Ergative_type'] == 'ergative'}
prob_langs = {gc for gc, info in langs.items() if info['Ergative_type'] == 'problematic'}
nonerg_langs = {gc for gc, info in langs.items() if info['Ergative_type'] == 'non_ergative'}

print(f"Total languages: {len(langs)}")
print(f"  Ergative: {len(erg_langs)}")
print(f"  Problematic: {len(prob_langs)}")
print(f"  Non-ergative: {len(nonerg_langs)}")

# ── Helper: build binary matrix (ergative langs, no '?') ─────────────────────

def binary_matrix(lang_set, features, exclude_any_q=False):
    """Build a matrix of 0/1 values.
    If exclude_any_q=True, exclude languages with ANY '?' in features.
    Otherwise, treat '?' as NaN per feature."""
    result = {}
    for gc in lang_set:
        if gc not in data:
            continue
        vals = {f: data[gc].get(f, '?') for f in features}
        if exclude_any_q and any(v == '?' for v in vals.values()):
            continue
        # Convert: 1->1, 0->0, ?->NaN, 2->NaN
        row = {}
        for f in features:
            v = vals[f]
            if v in ('0', '1'):
                row[f] = int(v)
            else:
                row[f] = np.nan
        result[gc] = row
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 1: Ergativity Score Distribution
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 1: Ergativity Score Distribution")
print("="*70)

# Score = count of 1s in GB409_2..GB409_22 (features 2-22), only ergative langs
# Exclude langs with any '?' in those features
score_features = [f'GB409_{i}' for i in range(2, 23)]
mat = binary_matrix(erg_langs, score_features, exclude_any_q=True)

scores = {}
for gc, row in mat.items():
    scores[gc] = sum(row[f] for f in score_features)

print(f"Languages with complete data (no '?'): {len(scores)}")
score_vals = list(scores.values())
print(f"Mean score: {np.mean(score_vals):.2f}")
print(f"Median score: {np.median(score_vals):.1f}")
print(f"Std: {np.std(score_vals):.2f}")
print(f"Min: {min(score_vals)}, Max: {max(score_vals)}")

# Distribution
score_counts = Counter(int(s) for s in score_vals)
print("\nScore distribution:")
for s in sorted(score_counts.keys()):
    print(f"  {s:2d}: {score_counts[s]:3d} languages {'█' * score_counts[s]}")

# Plot
fig, ax = plt.subplots(figsize=(10, 5))
bins = np.arange(-0.5, 22.5, 1)
ax.hist(score_vals, bins=bins, color='steelblue', edgecolor='white', alpha=0.85)
ax.set_xlabel('Ergativity Score (count of 1s in GB409_2–GB409_22)', fontsize=11)
ax.set_ylabel('Number of Languages', fontsize=11)
ax.set_title(f'Distribution of Ergativity Scores (n={len(scores)} ergative languages)', fontsize=13)
ax.set_xticks(range(0, 22))
ax.axvline(np.mean(score_vals), color='red', linestyle='--', label=f'Mean = {np.mean(score_vals):.1f}')
ax.axvline(np.median(score_vals), color='orange', linestyle='--', label=f'Median = {np.median(score_vals):.1f}')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'fig1_score_distribution.png'), dpi=150)
plt.close()

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 2: Top & Bottom Languages
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 2: Top & Bottom Scoring Languages")
print("="*70)

sorted_langs = sorted(scores.items(), key=lambda x: -x[1])
print("\nTop 15:")
for gc, s in sorted_langs[:15]:
    print(f"  {langs[gc]['Name']:30s} ({gc}) [{langs[gc]['Family']}] = {s}")

print("\nBottom 15:")
for gc, s in sorted_langs[-15:]:
    print(f"  {langs[gc]['Name']:30s} ({gc}) [{langs[gc]['Family']}] = {s}")

# Bar chart of top 30
top30 = sorted_langs[:30]
fig, ax = plt.subplots(figsize=(12, 8))
names = [f"{langs[gc]['Name']}" for gc, _ in top30]
vals_top = [s for _, s in top30]
colors = plt.cm.RdYlBu_r(np.linspace(0.2, 0.8, len(top30)))
ax.barh(range(len(top30)), vals_top, color=colors)
ax.set_yticks(range(len(top30)))
ax.set_yticklabels(names, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel('Ergativity Score')
ax.set_title(f'Top 30 Languages by Ergativity Score (n={len(scores)})')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'fig2_top30.png'), dpi=150)
plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 3: Scores by Language Family
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 3: Ergativity Scores by Language Family")
print("="*70)

family_scores = defaultdict(list)
for gc, s in scores.items():
    fam = langs[gc]['Family']
    if fam:
        family_scores[fam].append(s)

# Sort by mean score
fam_stats = []
for fam, ss in family_scores.items():
    if len(ss) >= 2:
        fam_stats.append((fam, len(ss), np.mean(ss), np.std(ss), np.median(ss)))

fam_stats.sort(key=lambda x: -x[2])

print(f"\nFamilies with ≥2 languages (n={len(fam_stats)}):")
print(f"{'Family':35s} {'N':>3s} {'Mean':>6s} {'Std':>6s} {'Med':>5s}")
for fam, n, mean, std, med in fam_stats:
    print(f"  {fam:35s} {n:3d} {mean:6.1f} {std:6.1f} {med:5.1f}")

# Boxplot for families with ≥3 languages
fam_box = [(fam, family_scores[fam]) for fam, n, *_ in fam_stats if n >= 3]
if fam_box:
    fig, ax = plt.subplots(figsize=(14, max(6, len(fam_box)*0.5)))
    bp_data = [s for _, s in fam_box]
    bp_labels = [f"{f} (n={len(s)})" for f, s in fam_box]
    bp = ax.boxplot(bp_data, vert=False, patch_artist=True, labels=bp_labels)
    for patch in bp['boxes']:
        patch.set_facecolor('steelblue')
        patch.set_alpha(0.6)
    ax.set_xlabel('Ergativity Score')
    ax.set_title('Ergativity Score by Language Family (families with ≥3 languages)')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, 'fig3_families.png'), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 4: Feature Prevalence Profile
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 4: Feature Prevalence (ergative languages only)")
print("="*70)

# For each feature, % of 1s among ergative languages with 0 or 1 (not ?)
feat_prev = {}
for f in FEATURES:
    ones = 0
    total = 0
    for gc in erg_langs:
        v = data.get(gc, {}).get(f, '?')
        if v in ('0', '1'):
            total += 1
            if v == '1':
                ones += 1
    if total > 0:
        feat_prev[f] = (ones / total * 100, ones, total)

print(f"\n{'Feature':30s} {'%':>6s} {'1s':>5s} {'N':>5s}")
for f in FEATURES:
    if f in feat_prev:
        pct, ones, total = feat_prev[f]
        print(f"  {FEATURE_LABELS[f]:30s} {pct:5.1f}% {ones:5d} {total:5d}")

# Bar chart
fig, ax = plt.subplots(figsize=(12, 8))
feat_sorted = sorted(feat_prev.items(), key=lambda x: -x[1][0])
fnames = [FEATURE_LABELS[f] for f, _ in feat_sorted]
fpcts = [v[0] for _, v in feat_sorted]
bars = ax.barh(range(len(fnames)), fpcts, color='steelblue', alpha=0.85)
ax.set_yticks(range(len(fnames)))
ax.set_yticklabels(fnames, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel('% of ergative languages with value = 1')
ax.set_title(f'Feature Prevalence in Ergative Languages')
ax.set_xlim(0, 105)
for i, v in enumerate(fpcts):
    ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'fig4_feature_profile.png'), dpi=150)
plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 5: Silverstein Hierarchy
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 5: Silverstein Hierarchy Patterns")
print("="*70)

# Hierarchy: 1st > 2nd > 3rd > NP
# GB409_2 (1st), GB409_3 (2nd), GB409_4 (3rd), GB409_5 (NPs)
# Prediction: if lower in hierarchy has ERG, higher should too
# Only ergative langs, exclude any with '?' in these 4 features

silver_feats = ['GB409_2', 'GB409_3', 'GB409_4', 'GB409_5']
silver_mat = binary_matrix(erg_langs, silver_feats, exclude_any_q=True)

print(f"Ergative languages with complete hierarchy data: {len(silver_mat)}")

# Pattern analysis
patterns = Counter()
for gc, row in silver_mat.items():
    pat = tuple(row[f] for f in silver_feats)
    patterns[pat] += 1

print(f"\nPattern (1st, 2nd, 3rd, NP) -> count:")
for pat, count in sorted(patterns.items(), key=lambda x: -x[1]):
    labels = ['1st', '2nd', '3rd', 'NP']
    desc = ' '.join(f"{l}={'ERG' if v else '---'}" for l, v in zip(labels, pat))
    print(f"  ({','.join(str(v) for v in pat)}) {desc:45s} n={count}")

# Silverstein violations: if NP=1 but pronoun=0, or 3rd=1 but 2nd=0, etc.
violations = 0
conforming = 0
for gc, row in silver_mat.items():
    p1, p2, p3, np_ = row['GB409_2'], row['GB409_3'], row['GB409_4'], row['GB409_5']
    # Hierarchy: if something lower has ERG, everything higher should too
    # lower = more NP-like. Silverstein: pronouns LESS likely to have ERG
    # So: NP > 3rd > 2nd > 1st (likelihood of ERG)
    # Violation: if X has ERG but something MORE NP-like does NOT
    # Actually Silverstein predicts: NPs get ERG first, then 3rd, then 2nd, then 1st
    # So if 1st=1, then 2nd, 3rd, NP should all be 1
    is_valid = True
    if p1 == 1 and (p2 == 0 or p3 == 0 or np_ == 0):
        is_valid = False
    if p2 == 1 and (p3 == 0 or np_ == 0):
        is_valid = False
    if p3 == 1 and np_ == 0:
        is_valid = False
    if is_valid:
        conforming += 1
    else:
        violations += 1

print(f"\nSilverstein hierarchy conformity:")
print(f"  Conforming: {conforming} ({conforming/(conforming+violations)*100:.1f}%)")
print(f"  Violations: {violations} ({violations/(conforming+violations)*100:.1f}%)")

# Violation details
print(f"\nViolation details:")
for gc, row in silver_mat.items():
    p1, p2, p3, np_ = row['GB409_2'], row['GB409_3'], row['GB409_4'], row['GB409_5']
    is_valid = True
    reasons = []
    if p1 == 1 and p2 == 0:
        is_valid = False
        reasons.append("1st=ERG but 2nd=no")
    if p1 == 1 and p3 == 0:
        is_valid = False
        reasons.append("1st=ERG but 3rd=no")
    if p1 == 1 and np_ == 0:
        is_valid = False
        reasons.append("1st=ERG but NP=no")
    if p2 == 1 and p3 == 0:
        is_valid = False
        reasons.append("2nd=ERG but 3rd=no")
    if p2 == 1 and np_ == 0:
        is_valid = False
        reasons.append("2nd=ERG but NP=no")
    if p3 == 1 and np_ == 0:
        is_valid = False
        reasons.append("3rd=ERG but NP=no")
    if not is_valid:
        print(f"  {langs[gc]['Name']:25s} ({gc}) [{langs[gc]['Family']}] "
              f"({p1},{p2},{p3},{np_}) — {'; '.join(reasons)}")

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
# Show pattern frequencies
pat_labels = []
pat_counts = []
for pat, count in sorted(patterns.items(), key=lambda x: -x[1]):
    labels_s = ['1st', '2nd', '3rd', 'NP']
    label = '/'.join(f"{l}:{v}" for l, v in zip(labels_s, pat))
    pat_labels.append(label)
    pat_counts.append(count)

colors = ['#2ecc71' if all(
    (pat[i] <= pat[j] if i < j else True)
    for i in range(4) for j in range(i+1,4)
    if (i,j) != (0,0)
) else '#e74c3c' for pat, _ in sorted(patterns.items(), key=lambda x: -x[1])]

# Simpler: mark Silverstein-conforming green, violations red
def is_silverstein(pat):
    p1,p2,p3,np_ = pat
    if p1 == 1 and (p2 == 0 or p3 == 0 or np_ == 0): return False
    if p2 == 1 and (p3 == 0 or np_ == 0): return False
    if p3 == 1 and np_ == 0: return False
    return True

colors = ['#2ecc71' if is_silverstein(pat) else '#e74c3c'
          for pat, _ in sorted(patterns.items(), key=lambda x: -x[1])]

ax.barh(range(len(pat_labels)), pat_counts, color=colors, alpha=0.8)
ax.set_yticks(range(len(pat_labels)))
ax.set_yticklabels(pat_labels, fontsize=8)
ax.invert_yaxis()
ax.set_xlabel('Number of Languages')
ax.set_title(f'Silverstein Hierarchy Patterns (n={len(silver_mat)} ergative languages)\n'
             f'Green = conforming ({conforming}), Red = violation ({violations})')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'fig5_silverstein_patterns.png'), dpi=150)
plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 6: Feature Correlations (Phi coefficients)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 6: Feature Correlations (Phi coefficient)")
print("="*70)

# Pairwise phi for ergative languages only, using only 0/1 values
feat_list = [f'GB409_{i}' for i in range(2, 25)]  # 2-24
n_feat = len(feat_list)
phi_matrix = np.full((n_feat, n_feat), np.nan)

for i, f1 in enumerate(feat_list):
    for j, f2 in enumerate(feat_list):
        if i == j:
            phi_matrix[i,j] = 1.0
            continue
        # Get paired 0/1 values
        pairs = []
        for gc in erg_langs:
            v1 = data.get(gc, {}).get(f1, '?')
            v2 = data.get(gc, {}).get(f2, '?')
            if v1 in ('0','1') and v2 in ('0','1'):
                pairs.append((int(v1), int(v2)))
        if len(pairs) < 10:
            continue
        a = np.array(pairs)
        n11 = np.sum((a[:,0]==1) & (a[:,1]==1))
        n10 = np.sum((a[:,0]==1) & (a[:,1]==0))
        n01 = np.sum((a[:,0]==0) & (a[:,1]==1))
        n00 = np.sum((a[:,0]==0) & (a[:,1]==0))
        denom = np.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
        if denom > 0:
            phi_matrix[i,j] = (n11*n00 - n10*n01) / denom

# Top correlations
print("\nTop 15 positive correlations:")
corrs = []
for i in range(n_feat):
    for j in range(i+1, n_feat):
        if not np.isnan(phi_matrix[i,j]):
            corrs.append((feat_list[i], feat_list[j], phi_matrix[i,j]))
corrs.sort(key=lambda x: -x[2])
for f1, f2, phi in corrs[:15]:
    print(f"  {FEATURE_LABELS[f1]:30s} × {FEATURE_LABELS[f2]:30s} φ = {phi:+.3f}")

print("\nTop 10 negative correlations:")
corrs_neg = sorted(corrs, key=lambda x: x[2])
for f1, f2, phi in corrs_neg[:10]:
    print(f"  {FEATURE_LABELS[f1]:30s} × {FEATURE_LABELS[f2]:30s} φ = {phi:+.3f}")

# Heatmap
fig, ax = plt.subplots(figsize=(14, 12))
feat_short = [FEATURE_LABELS[f] for f in feat_list]
im = ax.imshow(phi_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax.set_xticks(range(n_feat))
ax.set_yticks(range(n_feat))
ax.set_xticklabels(feat_short, rotation=90, fontsize=7)
ax.set_yticklabels(feat_short, fontsize=7)
plt.colorbar(im, ax=ax, label='Phi coefficient', shrink=0.8)
ax.set_title('Phi Correlation Matrix (ergative languages, pairwise complete)')
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'fig7_heatmap.png'), dpi=150)
plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 7: Split Ergativity Overview
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("ANALYSIS 7: Split Ergativity Patterns")
print("="*70)

# Split domains
split_domains = {
    'Person/NP': ['GB409_2', 'GB409_3', 'GB409_4', 'GB409_5'],
    'Aspect': ['GB409_6', 'GB409_7'],
    'Tense': ['GB409_8', 'GB409_9'],
    'Mood': ['GB409_10', 'GB409_11'],
    'Realis/Irrealis': ['GB409_12', 'GB409_13'],
    'Agency': ['GB409_14', 'GB409_15'],
    'Topicality': ['GB409_16', 'GB409_17'],
    'Animacy': ['GB409_18', 'GB409_19'],
    'Clause type': ['GB409_20', 'GB409_21'],
}

print("\nSplit by domain (ergative languages with data in both features):")
print(f"{'Domain':20s} {'Split':>6s} {'No split':>9s} {'Total':>6s} {'% split':>8s}")

domain_stats = {}
for domain, feats in split_domains.items():
    split = 0
    no_split = 0
    for gc in erg_langs:
        vals_d = [data.get(gc, {}).get(f, '?') for f in feats]
        if any(v not in ('0','1') for v in vals_d):
            continue
        int_vals = [int(v) for v in vals_d]
        if len(set(int_vals)) > 1:
            split += 1
        else:
            no_split += 1
    total = split + no_split
    if total > 0:
        domain_stats[domain] = (split, no_split, total)
        print(f"  {domain:20s} {split:6d} {no_split:9d} {total:6d} {split/total*100:7.1f}%")

# Plot splits overview
fig, ax = plt.subplots(figsize=(10, 6))
domains = list(domain_stats.keys())
split_pcts = [domain_stats[d][0]/domain_stats[d][2]*100 for d in domains]
ax.barh(range(len(domains)), split_pcts, color='coral', alpha=0.8)
ax.set_yticks(range(len(domains)))
ax.set_yticklabels(domains)
ax.invert_yaxis()
ax.set_xlabel('% of languages showing a split')
ax.set_title('Split Ergativity by Domain (ergative languages only)')
ax.set_xlim(0, 100)
for i, v in enumerate(split_pcts):
    n = domain_stats[domains[i]][2]
    ax.text(v + 1, i, f'{v:.0f}% (n={n})', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, 'fig8_splits_overview.png'), dpi=150)
plt.close()

# Split by family
print("\nSplit ergativity by family (Person/NP domain, families with ≥3 languages):")
fam_splits = defaultdict(lambda: [0, 0])
person_feats = ['GB409_2', 'GB409_3', 'GB409_4', 'GB409_5']
for gc in erg_langs:
    vals_d = [data.get(gc, {}).get(f, '?') for f in person_feats]
    if any(v not in ('0','1') for v in vals_d):
        continue
    fam = langs[gc]['Family']
    int_vals = [int(v) for v in vals_d]
    if len(set(int_vals)) > 1:
        fam_splits[fam][0] += 1
    else:
        fam_splits[fam][1] += 1

fam_split_stats = [(fam, s, ns, s+ns) for fam, (s, ns) in fam_splits.items() if s+ns >= 3]
fam_split_stats.sort(key=lambda x: -x[1]/(x[3]) if x[3] > 0 else 0)

print(f"{'Family':35s} {'Split':>6s} {'No split':>9s} {'Total':>6s} {'%':>7s}")
for fam, s, ns, t in fam_split_stats:
    print(f"  {fam:35s} {s:6d} {ns:9d} {t:6d} {s/t*100:6.1f}%")

# Plot splits by family
if fam_split_stats:
    fig, ax = plt.subplots(figsize=(12, max(6, len(fam_split_stats)*0.4)))
    fam_names = [f"{f} (n={t})" for f, s, ns, t in fam_split_stats]
    split_pcts_f = [s/t*100 for f, s, ns, t in fam_split_stats]
    ax.barh(range(len(fam_names)), split_pcts_f, color='darkorange', alpha=0.8)
    ax.set_yticks(range(len(fam_names)))
    ax.set_yticklabels(fam_names, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('% with Person/NP split')
    ax.set_title('Person/NP Split Ergativity by Language Family')
    ax.set_xlim(0, 110)
    for i, v in enumerate(split_pcts_f):
        ax.text(v + 1, i, f'{v:.0f}%', va='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR, 'fig9_splits_families.png'), dpi=150)
    plt.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS EXTRA: Phylogenetic Signal (Eta-squared by family)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("EXTRA: Phylogenetic Signal (Eta-squared)")
print("="*70)

# Eta-squared: how much variance in each feature is explained by family membership
# Only ergative langs, only 0/1 values
for f in FEATURES:
    fam_vals = defaultdict(list)
    for gc in erg_langs:
        v = data.get(gc, {}).get(f, '?')
        if v in ('0', '1'):
            fam_vals[langs[gc]['Family']].append(int(v))

    # Only families with ≥2 members
    fam_vals = {k: v for k, v in fam_vals.items() if len(v) >= 2}
    if len(fam_vals) < 3:
        continue

    all_vals = [v for vs in fam_vals.values() for v in vs]
    grand_mean = np.mean(all_vals)
    ss_total = sum((v - grand_mean)**2 for v in all_vals)
    ss_between = sum(len(vs) * (np.mean(vs) - grand_mean)**2 for vs in fam_vals.values())

    if ss_total > 0:
        eta2 = ss_between / ss_total
    else:
        eta2 = 0

    if f == FEATURES[0] or eta2 > 0.15:
        print(f"  {FEATURE_LABELS[f]:30s} η² = {eta2:.3f} ({len(fam_vals)} families, {len(all_vals)} langs)")


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS EXTRA: Implicational Universals
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("EXTRA: Implicational Universals (if X=1 → Y=1)")
print("="*70)

impl_results = []
for f1 in feat_list:
    for f2 in feat_list:
        if f1 == f2:
            continue
        # Count: f1=1 → f2=1?
        support = 0
        violations_impl = 0
        for gc in erg_langs:
            v1 = data.get(gc, {}).get(f1, '?')
            v2 = data.get(gc, {}).get(f2, '?')
            if v1 == '1' and v2 in ('0','1'):
                if v2 == '1':
                    support += 1
                else:
                    violations_impl += 1
        total = support + violations_impl
        if total >= 10:
            conf = support / total
            impl_results.append((f1, f2, conf, support, violations_impl, total))

impl_results.sort(key=lambda x: (-x[2], -x[5]))
print("\nStrongest implications (confidence ≥ 95%, n ≥ 20):")
print(f"{'If X=1':30s} {'→ Y=1':30s} {'Conf':>6s} {'Supp':>5s} {'Viol':>5s} {'N':>4s}")
for f1, f2, conf, supp, viol, n in impl_results:
    if conf >= 0.95 and n >= 20:
        print(f"  {FEATURE_LABELS[f1]:30s} → {FEATURE_LABELS[f2]:30s} {conf:5.1%} {supp:5d} {viol:5d} {n:4d}")


print("\n" + "="*70)
print("ALL FIGURES SAVED TO:", OUTDIR)
print("="*70)
