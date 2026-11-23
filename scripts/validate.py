"""
Automated validation of the ERGON CLDF dataset.

    python scripts/validate.py            # writes outputs/validation_report.md

Errors make the script exit with status 1; warnings are reported but do not
fail the build. The checks are documented in docs/validation_checks.md.
"""
import collections
import csv
import pathlib
import re
import sys

import pycldf

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIDS = [f'GB409_{i}' for i in range(1, 25)]
PAIRS = [(6, 7), (8, 9), (10, 11), (12, 13), (14, 15), (16, 17), (18, 19), (20, 21)]
SPANISH = re.compile(r'\b(el|los|las|del|que|una|está|según|página|gramática|ejemplos?|pero|también|marca|se marca|no hay|lengua|tiene|solo|sólo|glosad[oa]|part[ií]cula|sujeto|cuando|aunque|oración)\b', re.I)
ARTEFACTS = re.compile(r'(researcher (must|should)|recommend citing|VERIFICAR|value not resolved|TODO|FIXME|'
                       r'original (annotation|coding|value)|corrected from|changed from|not accessed|unreadable|'
                       r'\bpdf\b|legible copy|re-verified|curator|curation)', re.I)


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    errors, warnings, info = [], [], []
    md = ROOT / 'cldf' / 'StructureDataset-metadata.json'
    ds = pycldf.Dataset.from_metadata(md)

    # S0 CLDF schema, datatypes, foreign keys and source references
    try:
        ok = ds.validate(log=None)
        if not ok:
            errors.append('S0 CLDF validation failed (run `cldf validate` for details)')
    except Exception as e:  # pragma: no cover
        errors.append(f'S0 CLDF validation raised: {e}')

    langs = {r['ID']: r for r in ds.iter_rows('LanguageTable')}
    params = {r['ID']: r for r in ds.iter_rows('ParameterTable')}
    values = list(ds.iter_rows('ValueTable'))
    for v in values:  # in CLDF, '?' in the Value column is read as null (unknown)
        v['Value'] = '?' if v['Value'] is None else v['Value']
    bibkeys = {s.id for s in ds.sources}
    glot = {r['Glottocode']: r for r in read(ROOT / 'etc' / 'glottolog_5.3_languoids.csv')}
    exceptions = {(r['Glottocode'], r['Check']): r['Justification']
                  for r in read(ROOT / 'etc' / 'validation_exceptions.csv')}

    # S1 parameters
    if sorted(params, key=lambda x: int(x.split('_')[1])) != PIDS:
        errors.append('S1 parameter table does not contain exactly GB409_1-GB409_24')

    # S2 completeness and uniqueness: one value per language and parameter
    grid = collections.defaultdict(dict)
    for v in values:
        if v['Parameter_ID'] in grid[v['Language_ID']]:
            errors.append(f"S2 duplicate value {v['Language_ID']} {v['Parameter_ID']}")
        grid[v['Language_ID']][v['Parameter_ID']] = v
    for gc in langs:
        missing = set(PIDS) - set(grid[gc])
        if missing:
            errors.append(f'S2 {gc}: missing values for {sorted(missing)}')

    # S3 value domain
    for v in values:
        if v['Value'] not in ('0', '1', '?'):
            errors.append(f"S3 {v['ID']}: invalid value {v['Value']!r}")

    # S4 language identifiers
    for gc, l in langs.items():
        if not re.fullmatch(r'[a-z]{4}\d{4}', gc):
            errors.append(f'S4 {gc}: malformed Glottocode')
        elif gc not in glot:
            errors.append(f'S4 {gc}: not found in Glottolog 5.3 snapshot')
        elif glot[gc]['Level'] not in ('language', 'dialect'):
            errors.append(f'S4 {gc}: Glottolog level is {glot[gc]["Level"]}')
        if l['Latitude'] is None:
            warnings.append(f'S4 {gc}: no coordinates')

    # S5 provenance: every coded value cites at least one source; all keys resolve
    for v in values:
        if v['Value'] in ('0', '1') and not v['Source']:
            errors.append(f"S5 {v['ID']}: coded value without source")
        for ref in v['Source']:
            if ref.split('[')[0] not in bibkeys:
                errors.append(f"S5 {v['ID']}: unresolved source key {ref}")
    for s in ds.sources:
        if 'VERIFY' in str(s):
            warnings.append(f'S5 bibliography entry {s.id} is incomplete (marked VERIFY)')

    # L1-L4 logical consistency between language status and values
    for gc, l in langs.items():
        g = grid[gc]
        val = lambda i: g[f'GB409_{i}']['Value']
        nominal = [val(i) for i in range(2, 6)]
        if l['Status'] == 'ergative':
            if '1' not in nominal and (gc, 'L1') not in exceptions:
                errors.append(f'L1 {gc}: status ergative but no nominal category (GB409_2-5) coded 1: {nominal}')
            for a, b in PAIRS:
                if val(a) == '0' and val(b) == '0' and (gc, f'L2:{a}/{b}') not in exceptions:
                    errors.append(f'L2 {gc}: GB409_{a} and GB409_{b} both 0 although the language has ergative flagging')
        elif l['Status'] == 'no-ergative-flagging':
            bad = [p for p in PIDS if g[p]['Value'] != '0']
            if bad:
                errors.append(f'L3 {gc}: language without ergative flagging has non-zero values {bad}')
        if l['Status'] != 'ergative' and not l['Status_comment']:
            errors.append(f'L4 {gc}: {l["Status"]} language without Status_comment')

    # C1-C2 comment hygiene
    for v in values:
        c = v['Comment'] or ''
        if len(SPANISH.findall(c)) >= 2 or re.search(r'\w+ciones?\b|\w+ción\b', c) or re.search(r'\b(la|el) (marca|lengua|part[ií]cula)\b|sujeto pron', c, re.I):
            errors.append(f"C1 {v['ID']}: comment appears not to be in English: {c[:80]!r}")
        if ARTEFACTS.search(c):
            errors.append(f"C2 {v['ID']}: comment contains a workflow note: {c[:80]!r}")

    # A1 attribution
    no_coder = [gc for gc, l in langs.items() if not l['Coders']]
    if no_coder:
        warnings.append(f'A1 {len(no_coder)} languages without coder attribution (Coders column)')

    # I1 informational: referential-hierarchy implication (not an error: genuine exceptions exist)
    viol = []
    for gc, l in langs.items():
        if l['Status'] != 'ergative':
            continue
        p = [grid[gc][f'GB409_{i}']['Value'] for i in (2, 3, 4, 5)]
        if '?' in p:
            continue
        p = list(map(int, p))
        if not (p[0] <= p[1] <= p[2] <= p[3]):
            viol.append(f"{gc} {l['Name']} {tuple(p)}")
    info.append(f'I1 {len(viol)} ergative languages deviate from 1st<=2nd<=3rd<=NP: ' + '; '.join(viol))
    for (gc, chk), why in sorted(exceptions.items()):
        info.append(f'X documented exception {gc} {chk}: {why}')

    out = ROOT / 'outputs' / 'validation_report.md'
    out.parent.mkdir(exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        f.write('# ERGON validation report\n\n')
        f.write(f'Dataset: {md.relative_to(ROOT)} (version {ds.properties.get("schema:version")})\n\n')
        f.write(f'Languages: {len(langs)}; parameters: {len(params)}; values: {len(values)}; sources: {len(bibkeys)}\n\n')
        for title, items in (('Errors', errors), ('Warnings', warnings), ('Information', info)):
            f.write(f'## {title} ({len(items)})\n\n')
            f.write(''.join(f'- {x}\n' for x in items) or '- none\n')
            f.write('\n')
    print(f'{len(errors)} errors, {len(warnings)} warnings -> {out.relative_to(ROOT)}')
    for e in errors[:50]:
        print('ERROR', e)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
