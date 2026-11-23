"""
Technical validation of ERGON: every number, table and figure reported in the
Data Descriptor is produced by this script from the released CLDF tables.

    python scripts/technical_validation.py [--external DIR]

Outputs (outputs/):
  stats.json                 all reported statistics
  numbers.tex                the same statistics as LaTeX macros (\\input by the manuscript)
  tab_*.tex                  LaTeX tables
  fig*.png / fig*.pdf        figures
  missing_by_macroarea.csv, missing_by_family.csv, feature_summary.csv, phi_matrix.csv,
  external_agreement.csv     derived tables

--external DIR points to local clones of the comparison datasets
(grambank/grambank v1.0, cldf-datasets/wals v2020.4, autotyp/autotyp-data v1.1.1,
davidainman/atlas-data); if absent, the external comparison is skipped.
"""
import argparse
import collections
import csv
import itertools
import json
import math
import pathlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs'
PIDS = [f'GB409_{i}' for i in range(1, 25)]
PAIRS = [(7, 6, 'Aspect', 'perfective', 'imperfective'),
         (8, 9, 'Tense', 'past', 'non-past'),
         (10, 11, 'Mood', 'indicative', 'non-indicative'),
         (12, 13, 'Reality status', 'realis', 'irrealis'),
         (14, 15, 'Agentivity of A', 'agentive', 'non-agentive'),
         (16, 17, 'Topicality of A', 'topical', 'non-topical'),
         (18, 19, 'Animacy of A', 'animate', 'inanimate'),
         (20, 21, 'Clause type', 'main', 'non-main')]
# reference palette (dataviz skill, light mode)
BLUE, ORANGE, AQUA, GREY, INK, INK2 = '#2a78d6', '#eb6834', '#1baf7a', '#b9b8b2', '#0b0b0b', '#52514e'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': INK2,
                     'axes.labelcolor': INK, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300})


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def pct(a, b):
    return round(100 * a / b, 1) if b else float('nan')


def phi(x, y):
    """phi coefficient for two 0/1 lists; None if undefined (no variance)."""
    n11 = sum(1 for a, b in zip(x, y) if a and b)
    n10 = sum(1 for a, b in zip(x, y) if a and not b)
    n01 = sum(1 for a, b in zip(x, y) if not a and b)
    n00 = sum(1 for a, b in zip(x, y) if not a and not b)
    den = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return (n11 * n00 - n10 * n01) / den if den else None


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    cats = {a for a, _ in pairs} | {b for _, b in pairs}
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else None


def main(external=None):
    OUT.mkdir(exist_ok=True)
    langs = {r['ID']: r for r in read(ROOT / 'cldf' / 'languages.csv')}
    params = {r['ID']: r for r in read(ROOT / 'cldf' / 'parameters.csv')}
    V = collections.defaultdict(dict)
    for r in read(ROOT / 'cldf' / 'values.csv'):
        V[r['Language_ID']][r['Parameter_ID']] = r['Value']
    S = {}  # statistics
    erg = sorted(g for g, l in langs.items() if l['Status'] == 'ergative')
    nonerg = sorted(g for g, l in langs.items() if l['Status'] == 'no-ergative-flagging')
    probl = sorted(g for g, l in langs.items() if l['Status'] == 'problematic')
    allv = [V[g][p] for g in langs for p in PIDS]
    ergv = [V[g][p] for g in erg for p in PIDS]
    S.update(nLanguages=len(langs), nErgative=len(erg), nNonErgative=len(nonerg), nProblematic=len(probl),
             nParameters=len(params), nValues=len(allv),
             nCoded=sum(v in '01' for v in allv), nUnknown=allv.count('?'),
             pctUnknown=pct(allv.count('?'), len(allv)),
             nErgValues=len(ergv), nErgUnknown=ergv.count('?'), pctErgUnknown=pct(ergv.count('?'), len(ergv)),
             nFamiliesErgative=len({langs[g]['Family'] for g in erg}),
             nFamiliesAll=len({l['Family'] for l in langs.values()}),
             nMacroareasErgative=len({langs[g]['Macroarea'].split(';')[0] for g in erg}),
             nSources=len({s.split('[')[0] for g in langs for s in []}))
    srcs = set()
    for r in read(ROOT / 'cldf' / 'values.csv'):
        for s in filter(None, r['Source'].split(';')):
            srcs.add(s.split('[')[0])
    S['nSources'] = len(srcs)
    sm = read(ROOT / 'raw' / 'source_map.csv')
    S['nCitGrambank'] = sum(1 for r in sm if r['Match'].startswith('Grambank'))
    S['nCitGlottolog'] = sum(1 for r in sm if r['Match'].startswith('Glottolog'))
    S['nCitManual'] = sum(1 for r in sm if r['Match'] == 'manual')
    vals_all = read(ROOT / 'cldf' / 'values.csv')
    S['nCodedNoPageAll'] = sum(1 for r in vals_all if r['Value'] in ('0', '1') and '[' not in r['Source'])
    S['nCodedNoComment'] = sum(1 for r in vals_all if r['Value'] in ('0', '1') and not r['Comment'].strip())
    S['nUnknownNoSource'] = sum(1 for r in vals_all if r['Value'] == '?' and not r['Source'].strip())
    S['nReviewed'] = sum(1 for l in langs.values() if l['Reviewer'])
    S['nNoPage'] = sum(1 for r in read(ROOT / 'cldf' / 'values.csv') if r['Source_comment'].startswith('[no page'))
    S['nNotCoded'] = sum(1 for r in read(ROOT / 'cldf' / 'values.csv') if r['Comment'].startswith('Not coded'))
    gb_ll = collections.Counter(langs[g]['Language_level_Glottocode'] for g in langs)
    S['nDialectLevel'] = sum(1 for l in langs.values() if l['Level'] == 'dialect')

    # ------------------------------------------------------------------ Table: features
    feat_rows = []
    for p in PIDS:
        vals = [V[g][p] for g in erg]
        n = sum(v in '01' for v in vals)
        n1 = vals.count('1')
        feat_rows.append(dict(ID=p, Name=params[p]['Name'], Domain=params[p]['Domain'],
                              Subdomain=params[p]['Subdomain'], n_coded=n, pct_coded=pct(n, len(erg)),
                              n_1=n1, n_0=vals.count('0'), n_unknown=vals.count('?'), pct_1_of_coded=pct(n1, n)))
    with open(OUT / 'feature_summary.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(feat_rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(feat_rows)
    cov = sorted(feat_rows, key=lambda r: r['pct_coded'])
    S['coverageMin'], S['coverageMax'] = cov[0]['pct_coded'], cov[-1]['pct_coded']
    S['coverageMinFeatures'] = [r['ID'] for r in cov if r['pct_coded'] == cov[0]['pct_coded']]
    S['coverageMaxFeatures'] = [r['ID'] for r in cov if r['pct_coded'] == cov[-1]['pct_coded']]
    S['features'] = {r['ID']: r for r in feat_rows}
    with open(OUT / 'tab_features.tex', 'w') as f:
        for r in feat_rows:
            f.write(f"\\feat{{{r['ID'].replace('_', '\\_')}}} & {r['Subdomain']} & {params[r['ID']]['Description']} & "
                    f"{r['n_coded']} & {100 * r['n_coded'] / len(erg):.0f} & {100 * r['n_1'] / r['n_coded']:.0f} \\\\\n")

    # ------------------------------------------------------------------ Table: families
    fam = collections.Counter(langs[g]['Family'] for g in erg)
    big = [(k, v) for k, v in fam.most_common() if v >= 2 and k != 'Isolate']
    small = [(k, v) for k, v in fam.items() if v < 2 and k != 'Isolate']
    iso = fam.get('Isolate', 0)
    with open(OUT / 'tab_families.tex', 'w') as f:
        for k, v in big:
            f.write(f'{k} & {v} \\\\\n')
        if iso:
            f.write(f'Isolates & {iso} \\\\\n')
        f.write(f'Other families ({len(small)}, one language each) & {sum(v for _, v in small)} \\\\\n')
    S['familiesTop'] = big[:6]
    S['nFamiliesSingleton'] = len(small)
    S['nIsolatesErgative'] = iso
    S['pctTop4Families'] = pct(sum(v for _, v in fam.most_common(4)), len(erg))
    macro = collections.Counter(langs[g]['Macroarea'].split(';')[0] for g in erg)
    S['macroareasErgative'] = dict(macro.most_common())

    # ------------------------------------------------------------------ Table: no ergative flagging / problematic
    # Table 5 uses the one-line summaries in etc/status_short_reasons.csv; the full justification
    # is Status_comment in cldf/languages.csv.
    short = {r['Glottocode']: r['Short_reason_LaTeX'] for r in csv.DictReader(open(ROOT / 'etc' / 'status_short_reasons.csv', encoding='utf-8'))}
    missing = [g for g in nonerg + probl if g not in short]
    if missing:
        raise SystemExit(f'etc/status_short_reasons.csv lacks: {missing}')
    with open(OUT / 'tab_status.tex', 'w') as f:
        for g in sorted(nonerg, key=lambda g: langs[g]['Name']) + sorted(probl, key=lambda g: langs[g]['Name']):
            l = langs[g]
            f.write(f"{l['Name']} & {g} & {l['Family']} & {l['Status'].replace('-', ' ')} & {short[g]} \\\\\n")

    # ------------------------------------------------------------------ Referential hierarchy (GB409_2-5)
    complete = [g for g in erg if all(V[g][f'GB409_{i}'] in '01' for i in (2, 3, 4, 5))]
    pats = collections.Counter(tuple(int(V[g][f'GB409_{i}']) for i in (2, 3, 4, 5)) for g in complete)
    conform = lambda p: p[0] <= p[1] <= p[2] <= p[3]
    viol = [g for g in complete if not conform(tuple(int(V[g][f'GB409_{i}']) for i in (2, 3, 4, 5)))]
    S.update(nHierComplete=len(complete), nHierConform=len(complete) - len(viol), nHierViolations=len(viol),
             pctHierConform=pct(len(complete) - len(viol), len(complete)),
             hierPatterns={''.join(map(str, k)): v for k, v in pats.most_common()},
             nHierAll=pats.get((1, 1, 1, 1), 0), pctHierAll=pct(pats.get((1, 1, 1, 1), 0), len(complete)),
             nHierNPonly=pats.get((0, 0, 0, 1), 0), nHierThirdNP=pats.get((0, 0, 1, 1), 0))
    # expected share of conforming patterns under independence (permutation of columns within features)
    rng = np.random.default_rng(1)
    M = np.array([[int(V[g][f'GB409_{i}']) for i in (2, 3, 4, 5)] for g in complete])
    sims = []
    for _ in range(10000):
        Mp = np.column_stack([rng.permutation(M[:, j]) for j in range(4)])
        sims.append(np.mean([(r[0] <= r[1] <= r[2] <= r[3]) for r in Mp]))
    S['hierConformNull'] = round(100 * float(np.mean(sims)), 1)
    S['hierConformNullP'] = float((np.sum(np.array(sims) >= (len(complete) - len(viol)) / len(complete)) + 1) / (len(sims) + 1))
    with open(OUT / 'tab_violations.tex', 'w') as f:
        for g in viol:
            l = langs[g]
            pat = ', '.join(V[g][f'GB409_{i}'] for i in (2, 3, 4, 5))
            f.write(f"{l['Name']} & {g} & {l['Family']} & ({pat}) \\\\\n")
    S['hierViolationLanguages'] = [langs[g]['Name'] for g in viol]

    # ------------------------------------------------------------------ paired contexts
    pair_stats = {}
    for a, b, dom, la, lb in PAIRS:
        both = [g for g in erg if V[g][f'GB409_{a}'] in '01' and V[g][f'GB409_{b}'] in '01']
        c = collections.Counter((V[g][f'GB409_{a}'], V[g][f'GB409_{b}']) for g in both)
        pair_stats[dom] = dict(n=len(both), both=c[('1', '1')], only_a=c[('1', '0')], only_b=c[('0', '1')],
                               neither=c[('0', '0')], la=la, lb=lb, pct_uniform=pct(c[('1', '1')], len(both)))
    S['pairs'] = pair_stats
    tam = [g for g in erg if any(V[g][f'GB409_{i}'] == '0' for i in range(6, 14))]
    S['nTAMSplit'] = len(tam)
    S['pctNoTAMSplit'] = pct(len([g for g in erg if all(V[g][f'GB409_{i}'] in '1?' for i in range(6, 14))]), len(erg))

    # ------------------------------------------------------------------ phi coefficients
    phis, phin = {}, {}
    for p, q in itertools.combinations(PIDS, 2):
        gs = [g for g in erg if V[g][p] in '01' and V[g][q] in '01']
        x = [V[g][p] == '1' for g in gs]; y = [V[g][q] == '1' for g in gs]
        phis[(p, q)] = phi(x, y); phin[(p, q)] = len(gs)
    def getphi(p, q):
        return phis.get((p, q), phis.get((q, p)))
    def getn(p, q):
        return phin.get((p, q), phin.get((q, p)))
    r2 = lambda v, d=2: None if v is None else round(v, d)
    S['nPastPerfZero'] = sum(1 for g in erg if V[g]['GB409_7'] == '0' or V[g]['GB409_8'] == '0')
    S['phiPastPerf'] = r2(getphi('GB409_7', 'GB409_8'), 2); S['nPhiPastPerf'] = getn('GB409_7', 'GB409_8')
    S['phiIndPast'] = r2(getphi('GB409_8', 'GB409_10'), 2)
    S['phiIndPerf'] = r2(getphi('GB409_7', 'GB409_10'), 2)
    S['phiFirstSecond'] = r2(getphi('GB409_2', 'GB409_3'), 2)
    S['phiSecondThird'] = r2(getphi('GB409_3', 'GB409_4'), 2)
    S['phiFirstThird'] = r2(getphi('GB409_2', 'GB409_4'), 2)
    # Reviewer 1: restricted to languages that show any TAM split
    gs = [g for g in tam if V[g]['GB409_7'] in '01' and V[g]['GB409_8'] in '01']
    S['phiPastPerfSplitOnly'] = r2(phi([V[g]['GB409_7'] == '1' for g in gs], [V[g]['GB409_8'] == '1' for g in gs]), 2)
    S['nPhiPastPerfSplitOnly'] = len(gs)
    # share of pairs whose phi is driven by uniformly-1 languages
    with open(OUT / 'phi_matrix.csv', 'w', newline='') as f:
        w = csv.writer(f, lineterminator='\n'); w.writerow(['Feature_1', 'Feature_2', 'phi', 'n'])
        for (p, q), v in phis.items():
            w.writerow([p, q, '' if v is None else round(v, 3), phin[(p, q)]])
    neg_within = [(p, q, round(v, 2)) for (p, q), v in phis.items() if v is not None and v < -0.3
                  and params[p]['Subdomain'] == params[q]['Subdomain']]
    S['strongNegativeWithinDomain'] = neg_within

    # ------------------------------------------------------------------ missing data
    def lang_missing(g):
        return sum(V[g][p] == '?' for p in PIDS)
    rows = []
    by_area = collections.defaultdict(list)
    for g in erg:
        by_area[langs[g]['Macroarea'].split(';')[0]].append(lang_missing(g))
    for a, xs in sorted(by_area.items()):
        rows.append(dict(Macroarea=a, n_languages=len(xs), mean_unknown_per_language=round(np.mean(xs), 2),
                         pct_unknown=pct(sum(xs), 24 * len(xs))))
    with open(OUT / 'missing_by_macroarea.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    groups = [xs for xs in by_area.values() if len(xs) >= 5]
    kw = stats.kruskal(*groups)
    S['missingByArea'] = {r['Macroarea']: r['pct_unknown'] for r in rows}
    S['missingAreaKW_H'], S['missingAreaKW_p'] = round(float(kw.statistic), 2), round(float(kw.pvalue), 3)
    by_fam = collections.defaultdict(list)
    for g in erg:
        by_fam[langs[g]['Family']].append(lang_missing(g))
    famrows = [dict(Family=k, n_languages=len(v), pct_unknown=pct(sum(v), 24 * len(v))) for k, v in sorted(by_fam.items())]
    with open(OUT / 'missing_by_family.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(famrows[0]), lineterminator='\n'); w.writeheader(); w.writerows(famrows)
    fgroups = [v for v in by_fam.values() if len(v) >= 5]
    kwf = stats.kruskal(*fgroups)
    S['missingFamKW_H'], S['missingFamKW_p'] = round(float(kwf.statistic), 2), round(float(kwf.pvalue), 3)
    S['nFamiliesFiveplus'] = len(fgroups)
    # source year vs missingness (older/shorter sources)
    per_lang = [lang_missing(g) for g in erg]
    med = float(np.median(per_lang)); S['missingPerLangMedian'] = int(med) if med.is_integer() else med; S['missingPerLangMax'] = int(max(per_lang))
    S['nLangsNoMissing'] = sum(1 for x in per_lang if x == 0)
    # missing concentrated by feature
    fm = sorted(((r['n_unknown'], r['ID']) for r in feat_rows), reverse=True)
    S['missingTopFeatures'] = [f'{p} ({n})' for n, p in fm[:6]]

    # ------------------------------------------------------------------ curation statistics
    log = read(ROOT / 'raw' / 'curation_log.csv')
    hist = read(ROOT / 'raw' / 'curation_history_v1_0.csv')
    S['nChangesV11'] = len(log)
    S['changesV11ByRule'] = dict(collections.Counter(r['Rule'] for r in log))
    S['nChangesCuration'] = len(hist)
    S['pctChangesCuration'] = pct(len(hist), 24 * 196)
    S['nLangsChangedCuration'] = len({r['Glottocode'] for r in hist})
    S['changesCurationTypes'] = dict(collections.Counter(f"{r['Value_original_coding']}->{r['Value_v1_0_1']}" for r in hist))

    # ------------------------------------------------------------------ external comparison
    if external:
        S['external'] = external_comparison(pathlib.Path(external), langs, V, erg)
        S['resources'] = resource_counts(pathlib.Path(external))

    # ------------------------------------------------------------------ figures
    fig_map(langs)
    fig_profile(feat_rows, params, len(erg))
    fig_hierarchy(pats, len(complete))
    fig_pairs(pair_stats)
    fig_phi(phis, phin, params)

    # ------------------------------------------------------------------ outputs
    json.dump(S, open(OUT / 'stats.json', 'w'), indent=1, default=str, ensure_ascii=False)
    write_macros(S)
    print(json.dumps({k: S[k] for k in ('nLanguages', 'nErgative', 'nNonErgative', 'nProblematic', 'nValues',
                                        'nCoded', 'nUnknown', 'pctUnknown', 'nHierComplete', 'nHierViolations',
                                        'phiPastPerf', 'phiPastPerfSplitOnly')}, indent=0))


# ====================================================================== external datasets
def external_comparison(ext, langs, V, erg):
    res = {}
    ll = collections.defaultdict(list)
    for g, l in langs.items():
        ll[l['Language_level_Glottocode']].append(g)
    any_np = lambda g: V[g]['GB409_5']
    any_pro = lambda g: '1' if '1' in [V[g][f'GB409_{i}'] for i in (2, 3, 4)] else ('?' if '?' in [V[g][f'GB409_{i}'] for i in (2, 3, 4)] else '0')
    status_flag = lambda g: '1' if langs[g]['Status'] == 'ergative' else ('0' if langs[g]['Status'] == 'no-ergative-flagging' else '?')
    rows = []

    detail = []

    def add(name, feature, pairs):
        for a, b, g in pairs:
            if a in '01' and b in '01' and a != b:
                detail.append(dict(Dataset=name, Comparison=feature, Glottocode=g, Name=langs[g]['Name'], ERGON=a, Other=b))
        pairs = [(a, b) for a, b, g in pairs if a in '01' and b in '01']
        if not pairs:
            return
        agree = sum(a == b for a, b in pairs)
        k = kappa(pairs)
        o1 = [a for a, b in pairs if b == '1']
        rows.append(dict(Dataset=name, Comparison=feature, n=len(pairs), agreement_pct=pct(agree, len(pairs)),
                         kappa='' if k is None else round(k, 2),
                         other_ERG=len(o1), other_ERG_and_ERGON_1=o1.count('1'),
                         recall_pct=pct(o1.count('1'), len(o1)),
                         ERGON1_other0=sum(a == '1' and b == '0' for a, b in pairs),
                         ERGON0_other1=sum(a == '0' and b == '1' for a, b in pairs)))

    # Grambank GB409 (A flagged differently from S) - all ERGON languages were sampled as GB409=1
    gb = {}
    for r in read(ext / 'grambank' / 'cldf' / 'values.csv'):
        if r['Parameter_ID'] == 'GB409':
            gb[r['Language_ID']] = r['Value']
    res['grambankGB409'] = {f'{a}|GB409={b}': n for (a, b), n in collections.Counter(
        (langs[g]['Status'], gb.get(g) or gb.get(langs[g]['Language_level_Glottocode'], 'NA')) for g in langs).items()}
    res['notInGrambankGB409'] = sorted(langs[g]['Name'] for g in langs
                                       if (gb.get(g) or gb.get(langs[g]['Language_level_Glottocode'])) != '1')
    # WALS 98A / 99A
    wl = {r['ID']: r['Glottocode'] for r in read(ext / 'wals' / 'cldf' / 'languages.csv')}
    w = collections.defaultdict(dict)
    for r in read(ext / 'wals' / 'cldf' / 'values.csv'):
        if r['Parameter_ID'] in ('98A', '99A'):
            w[wl.get(r['Language_ID'])][r['Parameter_ID']] = r['Value']
    p98, p99 = [], []
    for code, gs in ll.items():
        for g in gs:
            if '98A' in w.get(code, {}):
                p98.append((any_np(g), '1' if w[code]['98A'] == '4' else '0', g))
            if '99A' in w.get(code, {}) and w[code]['99A'] != '7':
                p99.append((any_pro(g), '1' if w[code]['99A'] == '4' else '0', g))
    add('WALS 98A', 'GB409_5 vs. full-NP alignment = ergative-absolutive', p98)
    add('WALS 99A', 'any of GB409_2-4 vs. pronoun alignment = ergative-absolutive', p99)
    # AUTOTYP: flagging (case marker or adposition) with S=P≠A in any condition
    au = collections.defaultdict(lambda: {'np': set(), 'pro': set()})
    for r in read(ext / 'autotyp-data' / 'data' / 'csv' / 'GrammaticalRelations' / 'Alignment.csv'):
        if r['SelectorType'] != 'case marker or adposition':
            continue
        rc = r['ReferentialCondition']
        kind = 'pro' if 'Pro' in rc else ('np' if rc.startswith('N') else 'np')
        au[r['Glottocode']][kind].add(r['Alignment2'] == 'S=P≠Atr')
        if rc == '':
            au[r['Glottocode']]['pro'].add(r['Alignment2'] == 'S=P≠Atr')
    a_np, a_any = [], []
    for code, gs in ll.items():
        if code not in au:
            continue
        for g in gs:
            if au[code]['np']:
                a_np.append((any_np(g), '1' if True in au[code]['np'] else '0', g))
            a_any.append((status_flag(g), '1' if (True in au[code]['np'] or True in au[code]['pro']) else '0', g))
    add('AUTOTYP', 'GB409_5 vs. S=P≠A flagging of nouns in any condition', a_np)
    add('AUTOTYP', 'ERGON status vs. S=P≠A flagging anywhere', a_any)
    # ATLAs: Align-02 (all noun alignments), Align-05 (all pronoun alignments)
    at = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in read(ext / 'atlas-data' / 'cldf-atlas' / 'values.csv'):  # multi-valued: one row per alignment
        if r['ParameterID'] in ('Align-02', 'Align-05'):
            at[r['LanguageID']][r['ParameterID']].add(r['Value'])
    t_np, t_pro = [], []
    for code, gs in ll.items():
        for g in gs:
            if 'Align-02' in at.get(code, {}):
                t_np.append((any_np(g), '1' if 'ergative' in at[code]['Align-02'] else '0', g))
            if at.get(code, {}).get('Align-05') and at[code]['Align-05'] != {'NA'}:
                t_pro.append((any_pro(g), '1' if 'ergative' in at[code]['Align-05'] else '0', g))
    add('ATLAs', 'GB409_5 vs. ergative among noun alignments (Align-02)', t_np)
    add('ATLAs', 'any of GB409_2-4 vs. ergative among pronoun alignments (Align-05)', t_pro)
    with open(OUT / 'external_agreement.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); wr.writeheader(); wr.writerows(rows)
    with open(OUT / 'tab_external.tex', 'w') as f:
        for r in rows:
            f.write(f"{r['Dataset']} & {r['Comparison'].replace('≠', '$\\neq$').replace('_', '\\_').replace('2-4', '2--4')} & {r['n']} & {r['other_ERG_and_ERGON_1']}/{r['other_ERG']} & {r['ERGON1_other0']} & {r['agreement_pct']:.0f} \\\\\n")
    with open(OUT / 'external_disagreements.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(detail[0]), lineterminator='\n'); wr.writeheader(); wr.writerows(detail)
    res['agreement'] = rows
    return res


def resource_counts(ext):
    import subprocess
    r = {}
    gb = [x for x in read(ext / 'grambank' / 'cldf' / 'values.csv') if x['Parameter_ID'] == 'GB409']
    r['grambankGBcoded'] = sum(1 for x in gb if x['Value'] in ('0', '1'))
    r['grambankGBpositive'] = sum(1 for x in gb if x['Value'] == '1')
    w = [x for x in read(ext / 'wals' / 'cldf' / 'values.csv') if x['Parameter_ID'] in ('98A', '99A')]
    r['walsNinetyEightA'] = sum(1 for x in w if x['Parameter_ID'] == '98A')
    r['walsNinetyNineA'] = sum(1 for x in w if x['Parameter_ID'] == '99A')
    au = read(ext / 'autotyp-data' / 'data' / 'csv' / 'GrammaticalRelations' / 'Alignment.csv')
    r['autotypFlagging'] = len({x['Glottocode'] for x in au if x['SelectorType'] == 'case marker or adposition'})
    al = read(ext / 'atlas-data' / 'cldf-atlas' / 'languages.csv')
    r['atlasLanguages'] = len(al)
    r['atlasAmericas'] = sum(1 for x in al if x['Macroarea'] in ('North America', 'South America'))
    versions = {}
    for d in ('grambank', 'wals', 'autotyp-data', 'atlas-data'):
        try:
            versions[d] = subprocess.run(['git', '-C', str(ext / d), 'rev-parse', 'HEAD'], capture_output=True,
                                         text=True).stdout.strip()
        except Exception:
            versions[d] = ''
    json.dump(versions, open(OUT / 'external_versions.json', 'w'), indent=1)
    return r


# ====================================================================== figures
def save(fig, name):
    fig.savefig(OUT / f'{name}.png', bbox_inches='tight', facecolor='white')
    fig.savefig(OUT / f'{name}.pdf', bbox_inches='tight', facecolor='white', metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)


def fig_map(langs):
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    land = ROOT / 'etc' / 'ne_110m_land.json'
    if land.exists():
        geo = json.load(open(land))
        for feat in geo['features']:
            geom = feat['geometry']
            polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
            for poly in polys:
                xs, ys = zip(*poly[0])
                xs = [x + 360 if x < -25 else x for x in xs]
                if max(xs) - min(xs) > 300:
                    continue
                ax.fill(xs, ys, color='#ecebe7', lw=0)
    style = {'ergative': (BLUE, 'o', 'Ergative flagging'),
             'no-ergative-flagging': (ORANGE, 's', 'GB409 = 1 in Grambank, ergative flagging not confirmed'),
             'problematic': (AQUA, '^', 'Unresolved classification')}
    for st, (c, m, lab) in style.items():
        pts = [(float(l['Longitude']), float(l['Latitude'])) for l in langs.values() if l['Status'] == st and l['Latitude']]
        xs = [x + 360 if x < -25 else x for x, _ in pts]
        ax.scatter(xs, [y for _, y in pts], s=26, c=c, marker=m, edgecolor='white', linewidth=0.6,
                   label=f'{lab} (n = {len(pts)})', zorder=3)
    ax.set_xlim(-25, 335); ax.set_ylim(-58, 78)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_aspect('equal')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 0.0), ncol=1, frameon=False, fontsize=8, markerscale=1.3, handletextpad=0.3)
    save(fig, 'fig1_map')


def fig_profile(rows, params, n_erg):
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    ys = np.arange(len(rows))[::-1]
    one = np.array([r['n_1'] for r in rows]); zero = np.array([r['n_0'] for r in rows]); unk = np.array([r['n_unknown'] for r in rows])
    ax.barh(ys, one, color=BLUE, height=0.7, label='1 (yes)', edgecolor='white', linewidth=1)
    ax.barh(ys, zero, left=one, color=ORANGE, height=0.7, label='0 (no)', edgecolor='white', linewidth=1)
    ax.barh(ys, unk, left=one + zero, color=GREY, height=0.7, label='? (not known)', edgecolor='white', linewidth=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['ID']}  {r['Name']}" for r in rows], fontsize=8)
    for y, r in zip(ys, rows):
        ax.text(n_erg + 2, y, f"{r['pct_1_of_coded']:.0f}% of {r['n_coded']}", va='center', fontsize=7, color=INK2)
    prev = None
    for y, r in zip(ys, rows):
        if prev and params[r['ID']]['Domain'] != prev:
            ax.axhline(y + 0.5, color=INK2, lw=0.5, ls=':')
        prev = params[r['ID']]['Domain']
    ax.set_xlim(0, n_erg + 30)
    ax.set_xlabel(f'Number of languages with ergative flagging (n = {n_erg})')
    ax.legend(loc='upper center', bbox_to_anchor=(0.45, 1.06), ncol=3, frameon=False, fontsize=8)
    save(fig, 'fig2_feature_values')


def fig_hierarchy(pats, n):
    items = pats.most_common()
    labels = ['1st', '2nd', '3rd', 'NP']
    fig = plt.figure(figsize=(7.2, 3.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.2, 1], hspace=0.05)
    ax = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1], sharex=ax)
    xs = np.arange(len(items))
    conform = [p[0] <= p[1] <= p[2] <= p[3] for p, _ in items]
    cols = [BLUE if c else ORANGE for c in conform]
    ax.bar(xs, [v for _, v in items], color=cols, width=0.6)
    for x, (_, v) in zip(xs, items):
        ax.text(x, v + 1, str(v), ha='center', fontsize=8, color=INK)
    ax.set_ylabel('Languages'); ax.tick_params(axis='x', bottom=False, labelbottom=False)
    ax.spines['bottom'].set_visible(False)
    for j, lab in enumerate(labels):
        for x, (p, _) in zip(xs, items):
            ax2.scatter(x, j, s=40, color=(cols[x] if p[j] else '#e2e1dc'), zorder=3)
        ax2.text(-0.8, j, lab, ha='right', va='center', fontsize=8)
    ax2.set_ylim(-0.6, 3.6); ax2.axis('off')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label='Conforms to 1st ≤ 2nd ≤ 3rd ≤ NP'),
                       Patch(color=ORANGE, label='Deviates')], frameon=False, fontsize=8, loc='upper right')
    save(fig, 'fig3_hierarchy')


def fig_pairs(ps):
    doms = list(ps)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ys = np.arange(len(doms))[::-1]
    left = np.zeros(len(doms))
    segs = [('both', BLUE, 'ERG in both contexts'), ('only_a', ORANGE, 'ERG in first context only'),
            ('only_b', '#f3a882', 'ERG in second context only'), ('neither', GREY, 'ERG in neither')]
    for key, c, lab in segs:
        vals = np.array([pct(ps[d][key], ps[d]['n']) for d in doms])
        ax.barh(ys, vals, left=left, color=c, height=0.65, label=lab, edgecolor='white', linewidth=1)
        for y, l0, v, d in zip(ys, left, vals, doms):
            if v >= 6:
                ax.text(l0 + v / 2, y, str(ps[d][key]), ha='center', va='center', fontsize=7,
                        color='white' if key in ('both', 'only_a') else INK)
        left += vals
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{d}: {ps[d]['la']} / {ps[d]['lb']} (n = {ps[d]['n']})" for d in doms], fontsize=8)
    ax.set_xlabel('% of languages with values for both contexts'); ax.set_xlim(0, 100)
    ax.legend(loc='upper center', bbox_to_anchor=(0.4, 1.17), ncol=2, frameon=False, fontsize=8)
    save(fig, 'fig4_paired_contexts')


def fig_phi(phis, phin, params):
    from matplotlib.colors import LinearSegmentedColormap
    n = len(PIDS)
    M = np.full((n, n), np.nan)
    for i, p in enumerate(PIDS):
        M[i, i] = 1
        for j, q in enumerate(PIDS):
            if i != j:
                v = phis.get((p, q), phis.get((q, p)))
                M[i, j] = np.nan if v is None else v
    cmap = LinearSegmentedColormap.from_list('div', [ORANGE, '#f4f3ef', BLUE]); cmap.set_bad('#ffffff')
    fig, ax = plt.subplots(figsize=(7.2, 6.6))
    im = ax.imshow(np.tril(M, -1) + np.triu(np.full((n, n), np.nan)), cmap=cmap, vmin=-1, vmax=1)
    for i in range(n):
        for j in range(i):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f'{M[i, j]:.2f}'.replace('0.', '.'), ha='center', va='center', fontsize=5.2,
                        color='white' if abs(M[i, j]) > 0.6 else INK)
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels([p.replace('GB409_', '') for p in PIDS], fontsize=7)
    ax.set_yticklabels([f"{p.replace('GB409_', '')} {params[p]['Name']}" for p in PIDS], fontsize=7)
    prev = None
    for i, p in enumerate(PIDS):
        d = params[p]['Subdomain']
        if prev is not None and d != prev:
            ax.plot([-0.5, i - 0.5], [i - 0.5, i - 0.5], color=INK2, lw=0.4)
            ax.plot([i - 0.5, i - 0.5], [i - 0.5, n - 0.5], color=INK2, lw=0.4)
        prev = d
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.02); cb.set_label('φ', fontsize=9)
    save(fig, 'fig5_phi')


# ====================================================================== LaTeX macros
def write_macros(S):
    def num(x):
        return f'{x:,}'.replace(',', '{,}') if isinstance(x, int) and x >= 1000 else str(x)
    m = {}
    for k, v in S.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            m[k] = num(v)
    for d, r in S['pairs'].items():
        key = ''.join(w.capitalize() for w in d.replace(' of A', '').split())
        m[f'pair{key}N'] = r['n']; m[f'pair{key}Both'] = r['both']; m[f'pair{key}Uniform'] = r['pct_uniform']; m[f'pair{key}OnlyB'] = r['only_b']
    for p, r in S['features'].items():
        k = 'f' + p.split('_')[1].replace('1', 'One').replace('2', 'Two').replace('3', 'Three').replace('4', 'Four') \
            .replace('5', 'Five').replace('6', 'Six').replace('7', 'Seven').replace('8', 'Eight').replace('9', 'Nine').replace('0', 'Zero')
        m[k + 'Cov'] = r['pct_coded']; m[k + 'Prev'] = r['pct_1_of_coded']; m[k + 'N'] = r['n_coded']
    for a, v in S['missingByArea'].items():
        m['miss' + a.replace(' ', '')] = v
    if 'external' in S:
        for i, r in enumerate(S['external']['agreement']):
            tag = 'ext' + 'ABCDEFGH'[i]
            m[tag + 'N'] = r['n']; m[tag + 'Agree'] = r['agreement_pct']; m[tag + 'Kappa'] = r['kappa']
            m[tag + 'OtherErg'] = r['other_ERG']; m[tag + 'OtherErgErgon'] = r['other_ERG_and_ERGON_1']
            m[tag + 'ErgonOnly'] = r['ERGON1_other0']
    if 'external' in S:
        m['nNotInGrambank'] = len(S['external']['notInGrambankGB409'])
        m['nGrambankPositive'] = S['nLanguages'] - m['nNotInGrambank']
    m['pctTopFourFamilies'] = S['pctTop4Families']
    for k, v in S.get('resources', {}).items():
        m[k] = num(v)
    for k, v in S['changesV11ByRule'].items():
        m['rule' + k.replace('1', 'One').replace('2', 'Two').replace('3', 'Three').replace('4', 'Four').replace('5', 'Five')] = v
    m['hierConformNullP'] = '< 0.001' if S['hierConformNullP'] < 0.001 else round(S['hierConformNullP'], 3)
    m['missingAreaKWp'] = S['missingAreaKW_p']; m['missingAreaKWH'] = S['missingAreaKW_H']
    m['missingFamKWp'] = S['missingFamKW_p']; m['missingFamKWH'] = S['missingFamKW_H']
    for t, n in S['changesCurationTypes'].items():
        m['cur' + t.replace('->', 'to').replace('?', 'Q').replace('0', 'Zero').replace('1', 'One')] = n
    with open(OUT / 'numbers.tex', 'w') as f:
        f.write('% Generated by scripts/technical_validation.py - do not edit by hand\n')
        for k, v in sorted(m.items()):
            if k.isalpha():
                f.write(f'\\newcommand{{\\{k}}}{{{v}}}\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--external', default=None)
    a = ap.parse_args()
    main(a.external)
