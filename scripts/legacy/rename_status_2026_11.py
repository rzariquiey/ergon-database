"""
Step 5 of the v1.0.1 -> v1.1.0 migration: rename the status value `non-ergative` to
`no-ergative-flagging` and reword the curation notes that use the old label.

The languages concerned are coded 1 for GB409 in Grambank, but ergative flagging was not
confirmed in the sources. The new label states what was checked (flagging) and leaves open
other ergative patterns, such as ergative indexing, which several of these languages have.

Run once after apply_review_2026_11.py. Running it again changes nothing.
"""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
OLD, NEW = 'non-ergative', 'no-ergative-flagging'

TEXT = [
    ('Language reclassified as non-ergative after verification (no ergative flagging on any nominal category)',
     'Ergative flagging not confirmed after verification (no nominal category is flagged ergatively)'),
    ('Language reclassified as non-ergative in the 2026 review (no ergative flagging on any nominal category)',
     'Ergative flagging not confirmed in the 2026 review (no nominal category is flagged ergatively)'),
    ('(Marori is non-ergative)', '(Marori has no ergative flagging)'),
]


def rewrite(path, fix):
    with open(path, encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())
    n = sum(fix(r) for r in rows)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    print(f'{path.relative_to(ROOT)}: {n} rows changed')


def status(r):
    if r['Status'] == OLD:
        r['Status'] = NEW
        return 1
    return 0


def notes(r):
    changed = 0
    for k, v in r.items():
        if not v:
            continue
        for a, b in TEXT:
            if a in v:
                v = v.replace(a, b)
        if v != r[k]:
            r[k], changed = v, 1
    return changed


if __name__ == '__main__':
    rewrite(ROOT / 'raw' / 'languages.csv', status)
    rewrite(ROOT / 'raw' / 'curation_log.csv', notes)
    rewrite(ROOT / 'raw' / 'curation_history_v1_0.csv', notes)
