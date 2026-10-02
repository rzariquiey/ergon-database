"""
Inter-coder reliability for ERGON.

    python scripts/intercoder_reliability.py sample [--n 20] [--seed 2026]
        Draws a random sample of ergative languages, stratified by Glottolog family
        (at most one language per family before any family contributes a second one),
        and writes blank coding sheets to intercoder/sheets/<glottocode>.csv.
        The second coder must not consult the released values or comments.

    python scripts/intercoder_reliability.py score
        Compares the completed sheets with the released values and writes
        intercoder/agreement.csv (per feature) and intercoder/summary.json
        (raw agreement and Cohen's kappa on cells coded 0/1 by both coders,
        and the rate at which one coder answered '?' and the other did not).
"""
import argparse
import collections
import csv
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIR = ROOT / 'intercoder'
PIDS = [f'GB409_{i}' for i in range(1, 25)]


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == c for a, _ in pairs) / n) * (sum(b == c for _, b in pairs) / n) for c in ('0', '1'))
    return round((po - pe) / (1 - pe), 3) if pe < 1 else None


def sample(n, seed):
    langs = [l for l in read(ROOT / 'cldf' / 'languages.csv') if l['Status'] == 'ergative']
    rng = random.Random(seed)
    byfam = collections.defaultdict(list)
    for l in langs:
        byfam[l['Family']].append(l)
    for v in byfam.values():
        rng.shuffle(v)
    fams = sorted(byfam)
    rng.shuffle(fams)
    chosen = []
    while len(chosen) < n:
        for f in fams:
            if byfam[f] and len(chosen) < n:
                chosen.append(byfam[f].pop())
    params = {p['ID']: p['Description'] for p in read(ROOT / 'cldf' / 'parameters.csv')}
    (DIR / 'sheets').mkdir(parents=True, exist_ok=True)
    with open(DIR / 'sample.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Glottocode', 'Name', 'Family', 'Primary_Source', 'Second_coder'])
        for l in chosen:
            w.writerow([l['ID'], l['Name'], l['Family'], l['Primary_Source'], ''])
            with open(DIR / 'sheets' / f"{l['ID']}.csv", 'w', newline='', encoding='utf-8') as g:
                wg = csv.writer(g, lineterminator='\n')
                wg.writerow(['Parameter_ID', 'Question', 'Value', 'Source', 'Comment'])
                for p in PIDS:
                    wg.writerow([p, params[p], '', '', ''])
    print(f'{len(chosen)} languages from {len({l["Family"] for l in chosen})} families -> {DIR}')


def score():
    released = collections.defaultdict(dict)
    for r in read(ROOT / 'cldf' / 'values.csv'):
        released[r['Language_ID']][r['Parameter_ID']] = r['Value'] or '?'
    per = collections.defaultdict(list)
    unk = collections.Counter()
    for sheet in sorted((DIR / 'sheets').glob('*.csv')):
        gc = sheet.stem
        for r in read(sheet):
            v2 = r['Value'].strip()
            if not v2:
                continue
            v1 = released[gc][r['Parameter_ID']]
            if v1 in '01' and v2 in '01':
                per[r['Parameter_ID']].append((v1, v2))
            else:
                unk['one_unknown' if (v1 == '?') != (v2 == '?') else 'both_unknown'] += 1
    rows, allp = [], []
    for p in PIDS:
        pairs = per[p]
        allp += pairs
        rows.append(dict(Parameter_ID=p, n=len(pairs),
                         agreement=round(sum(a == b for a, b in pairs) / len(pairs), 3) if pairs else '',
                         kappa=kappa(pairs)))
    with open(DIR / 'agreement.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    summary = dict(cells=len(allp), agreement=round(sum(a == b for a, b in allp) / len(allp), 3) if allp else None,
                   kappa=kappa(allp), **unk)
    json.dump(summary, open(DIR / 'summary.json', 'w'), indent=1)
    print(summary)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['sample', 'score'])
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--seed', type=int, default=2026)
    a = ap.parse_args()
    sample(a.n, a.seed) if a.mode == 'sample' else score()
