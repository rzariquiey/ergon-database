"""
Write a spreadsheet version of the CLDF dataset (outputs/ERGON_v1.1.0.xlsx).

The CLDF tables in cldf/ are the canonical release; this workbook is a convenience copy
for users who prefer a spreadsheet. Run after scripts/build_cldf.py.
"""
import csv
import pathlib

import pycldf
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLDF = ROOT / 'cldf'
OUT = ROOT / 'outputs' / 'ERGON_v1.1.0.xlsx'
VERSION = '1.1.0'
PIDS = [f'GB409_{i}' for i in range(1, 25)]

FONT = Font(name='Arial', size=10)
BOLD = Font(name='Arial', size=10, bold=True)
HEAD_FILL = PatternFill('solid', start_color='D9D9D9')


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def sheet(wb, title, header, rows, widths=None, wrap=()):
    ws = wb.create_sheet(title)
    ws.append(header)
    for r in rows:
        ws.append(r)
    for c in ws[1]:
        c.font, c.fill = BOLD, HEAD_FILL
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = FONT
            if c.column in wrap:
                c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = 'B2' if title == 'Matrix' else 'A2'
    ws.auto_filter.ref = ws.dimensions
    for i, w in enumerate(widths or [], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    return ws


def main():
    langs = read(CLDF / 'languages.csv')
    params = read(CLDF / 'parameters.csv')
    values = read(CLDF / 'values.csv')
    contributors = read(CLDF / 'contributors.csv')
    log = read(ROOT / 'raw' / 'curation_log.csv')
    lname = {l['ID']: l['Name'] for l in langs}
    pname = {p['ID']: p['Name'] for p in params}
    val = {(v['Language_ID'], v['Parameter_ID']): (v['Value'] or '?') for v in values}

    wb = Workbook()
    ws = wb.active
    ws.title = 'README'
    readme = [
        f'ERGON v{VERSION}',
        '',
        'Spreadsheet copy of the CLDF dataset in the folder cldf/ of the release. The CLDF tables are the',
        'reference version; this file contains the same values.',
        '',
        'Matrix: languages in rows, the 24 features in columns.',
        'Values: one row per value, with source, pages and comment.',
        'Languages: metadata, status and reason for the status, coders and reviewer.',
        'Features: the 24 features.',
        'Sources: references cited in the Values sheet.',
        'Contributors: the initials used in the Coders and Reviewer columns.',
        'Curation log: values that differ from version 1.0.1, with the rule applied.',
        '',
        '1 = ergative flagging documented in the context; 0 = absence documented; ? = the source does not',
        'allow a decision. The coding rules are in docs/coding_protocol.md. Languages with status',
        'non-ergative have all values 0. Problematic languages should not be included in analyses of',
        'ergative languages.',
        '',
        'Licence CC BY 4.0.',
    ]
    for line in readme:
        ws.append([line])
    for row in ws.iter_rows():
        for c in row:
            c.font = FONT
    ws['A1'].font = Font(name='Arial', size=12, bold=True)
    ws.column_dimensions['A'].width = 120

    order = sorted(langs, key=lambda l: ({'ergative': 0, 'problematic': 1, 'non-ergative': 2}[l['Status']], l['Name']))
    sheet(wb, 'Matrix', ['Language', 'Glottocode', 'Family', 'Macroarea', 'Status'] + [f'{p} {pname[p]}' for p in PIDS],
          [[l['Name'], l['ID'], l['Family'], l['Macroarea'], l['Status']] + [val[(l['ID'], p)] for p in PIDS] for l in order],
          widths=[26, 11, 18, 14, 13] + [9] * 24)
    m = wb['Matrix']
    for c in m[1][5:]:
        c.alignment = Alignment(text_rotation=90, wrap_text=True)
    m.row_dimensions[1].height = 260
    for row in m.iter_rows(min_row=2, min_col=6):
        for c in row:
            c.alignment = Alignment(horizontal='center')

    sheet(wb, 'Values', ['ID', 'Language', 'Glottocode', 'Feature', 'Feature name', 'Value', 'Source', 'Comment', 'Citation as written by the coder'],
          [[v['ID'], lname[v['Language_ID']], v['Language_ID'], v['Parameter_ID'], pname[v['Parameter_ID']], v['Value'] or '?',
            v['Source'], v['Comment'], v['Source_comment']] for v in values],
          widths=[18, 24, 11, 10, 40, 7, 40, 70, 40], wrap=(8,))
    sheet(wb, 'Languages', ['Glottocode', 'Name', 'Glottolog name', 'Family', 'Family Glottocode', 'Macroarea', 'Latitude', 'Longitude',
                            'ISO 639-3', 'Status', 'Status comment', 'Coders', 'Reviewer', 'Primary source'],
          [[l['ID'], l['Name'], l['Glottolog_Name'], l['Family'], l['Family_Glottocode'], l['Macroarea'],
            float(l['Latitude']) if l['Latitude'] else None, float(l['Longitude']) if l['Longitude'] else None,
            l['ISO639P3code'], l['Status'], l['Status_comment'], l['Coders'], l['Reviewer'], l['Primary_Source']] for l in langs],
          widths=[11, 24, 24, 18, 12, 14, 9, 9, 8, 13, 60, 10, 9, 22], wrap=(11,))
    sheet(wb, 'Features', ['ID', 'Name', 'Description', 'Domain', 'Subdomain', 'Paired with', 'Grambank parent'],
          [[p['ID'], p['Name'], p['Description'], p['Domain'], p['Subdomain'], p['Paired_with'], p['Grambank_parent']] for p in params],
          widths=[10, 40, 80, 18, 18, 11, 11], wrap=(3,))

    ds = pycldf.Dataset.from_metadata(CLDF / 'StructureDataset-metadata.json')
    srcs = []
    for s in ds.sources:
        f = {k.lower(): v for k, v in s.items()}
        srcs.append([s.id, s.genre, f.get('author', f.get('editor', '')), f.get('year', ''), f.get('title', ''),
                     f.get('journal', f.get('booktitle', f.get('school', ''))), f.get('publisher', ''), f.get('pages', ''),
                     f.get('doi', ''), f.get('url', '')])
    sheet(wb, 'Sources', ['BibTeX key', 'Type', 'Author', 'Year', 'Title', 'Journal / book / school', 'Publisher', 'Pages', 'DOI', 'URL'],
          sorted(srcs), widths=[28, 12, 30, 7, 60, 30, 25, 10, 22, 30], wrap=(5,))
    sheet(wb, 'Contributors', ['ID', 'Name', 'Affiliation', 'Roles'],
          [[c['ID'], c['Name'], c['Affiliation'], c['Roles']] for c in contributors], widths=[6, 26, 50, 30])
    sheet(wb, 'Curation log', ['Glottocode', 'Language', 'Feature', 'Value v1.0.1', 'Value v1.1.0', 'Rule', 'Rationale'],
          [[r['Glottocode'], lname[r['Glottocode']], r['Parameter_ID'], r['Value_v1_0_1'] or '?', r['Value_v1_1_0'] or '?',
            r['Rule'], r['Rationale']] for r in log],
          widths=[11, 24, 10, 11, 11, 7, 90], wrap=(7,))
    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    print(f'{OUT}: {len(langs)} languages, {len(values)} values, {len(srcs)} sources')


if __name__ == '__main__':
    main()
