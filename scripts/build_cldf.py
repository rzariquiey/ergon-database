"""
Build the ERGON CLDF StructureDataset from the harmonised sources in raw/ and etc/.

    python scripts/build_cldf.py

Inputs
  raw/languages.csv              language list, ERGON status, coders/reviewers
  raw/language_sheets/*.csv      one coding sheet per language (Parameter_ID, Value, Source, Comment)
  raw/sources.bib                bibliography (BibTeX)
  raw/source_map.csv             maps citations as written in the sheets to BibTeX keys
  etc/parameters.csv             feature definitions, domains and pairings
  etc/contributors.csv           team members
  etc/glottolog_5.3_languoids.csv  Glottolog 5.3 metadata (names, families, macroareas, coordinates)
Output
  cldf/  (StructureDataset-metadata.json, languages.csv, parameters.csv, codes.csv,
          values.csv, contributors.csv, sources.bib)

The build is deterministic and offline: all external metadata are read from the
snapshot in etc/ (see etc/README.md for how the snapshot was made).
"""
import collections
import csv
import pathlib
import re
import sys

import pycldf
from pycldf.sources import Source, Sources

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from citations import normalize_source  # noqa: E402

VERSION = '1.1.0'
PIDS = [f'GB409_{i}' for i in range(1, 25)]


def read(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main(outdir=ROOT / 'cldf'):
    langs = read(ROOT / 'raw' / 'languages.csv')
    glot = {r['Glottocode']: r for r in read(ROOT / 'etc' / 'glottolog_5.3_languoids.csv')}
    params = read(ROOT / 'etc' / 'parameters.csv')
    contributors = read(ROOT / 'etc' / 'contributors.csv')
    smap = {(r['Glottocode'], r['Citation']): r['BibKey'] for r in read(ROOT / 'raw' / 'source_map.csv')}
    sources = Sources.from_file(ROOT / 'raw' / 'sources.bib')

    # ------------------------------------------------------------- values
    values, primary = [], {}
    for lang in langs:
        gc = lang['Glottocode']
        sheet = read(ROOT / 'raw' / 'language_sheets' / f'{gc}.csv')
        # principal source of the language = most frequently cited work
        cnt = collections.Counter()
        for row in sheet:
            for c in normalize_source(row['Source']):
                if c['authors']:
                    cnt[smap[(gc, f"{c['authors']} {c['year']}")]] += 1
        primary[gc] = cnt.most_common(1)[0][0] if cnt else None
        for row in sheet:
            refs = []
            for c in normalize_source(row['Source']):
                key = smap[(gc, f"{c['authors']} {c['year']}")]
                pages = re.sub(r'\s*;\s*', ', ', c['pages']).replace('[', '(').replace(']', ')').strip(' ,')
                refs.append(f'{key}[{pages}]' if pages else key)
            source_comment = row['Source']
            if not refs and row['Value'] in ('0', '1') and primary[gc]:
                refs = [primary[gc]]
                source_comment = '[no page reference recorded in the coding sheet; principal source of the language]'
            values.append(dict(
                ID=f"{row['Parameter_ID']}-{gc}",
                Language_ID=gc,
                Parameter_ID=row['Parameter_ID'],
                Value=row['Value'],
                Code_ID=f"{row['Parameter_ID']}-{row['Value']}" if row['Value'] in ('0', '1') else None,
                Comment=row['Comment'] or None,
                Source=refs,
                Source_comment=source_comment or None,
            ))

    # ------------------------------------------------------------- dataset
    ds = pycldf.StructureDataset.in_dir(outdir)
    ds.add_component('LanguageTable',
                     {'name': 'Glottolog_Name', 'dc:description': 'Name of the languoid in Glottolog 5.3'},
                     {'name': 'Level', 'dc:description': 'Glottolog level of the languoid (language or dialect)'},
                     {'name': 'Language_level_Glottocode',
                      'dc:description': 'Glottocode of the language-level languoid; use this column to join ERGON with Grambank and other language-level datasets'},
                     {'name': 'Family', 'dc:description': 'Top-level genealogical unit in Glottolog 5.3 ("Isolate" for isolates)'},
                     {'name': 'Family_Glottocode'},
                     {'name': 'Status', 'datatype': {'base': 'string', 'format': 'ergative|non-ergative|problematic'},
                      'dc:description': 'ergative: ergative flagging (S=P≠A) attested for at least one nominal category; non-ergative: no ergative flagging after verification against the source; problematic: classification unresolved (see Status_comment)'},
                     {'name': 'Status_comment', 'dc:description': 'Justification of the non-ergative or problematic classification'},
                     {'name': 'Coders', 'separator': ';', 'dc:description': 'Initials of the original coder(s); see contributors.csv'},
                     {'name': 'Reviewer', 'separator': ';', 'dc:description': 'Initials of the team member(s) who re-verified the coding sheet in the 2026 review round'},
                     {'name': 'Primary_Source', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source', 'separator': ';'})
    ds.add_component('ParameterTable',
                     {'name': 'Domain', 'dc:description': 'Top-level thematic domain of the feature'},
                     {'name': 'Subdomain', 'dc:description': 'Second-level grouping (e.g. Aspect, Tense)'},
                     {'name': 'Paired_with', 'dc:description': 'ID of the complementary context feature (e.g. perfective/imperfective)'},
                     {'name': 'Grambank_parent', 'dc:description': 'Grambank feature of which this is a sub-feature'})
    ds.add_component('CodeTable')
    ds.add_table('contributors.csv',
                 {'name': 'ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id'},
                 {'name': 'Name', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name'},
                 {'name': 'Affiliation'}, {'name': 'Roles'},
                 primaryKey=['ID'])
    ds.add_columns('ValueTable', {'name': 'Source_comment',
                                  'dc:description': 'Bibliographic reference as written by the coder in the coding sheet'})
    ds['ValueTable', 'Value'].datatype.format = r'0|1|\?'
    ds['ValueTable', 'Value'].common_props['dc:description'] = '1 = yes; 0 = no; ? = not known (insufficient information in the consulted sources)'

    ds.properties['dc:title'] = 'ERGON: sub-features of ergative flagging (Grambank GB409) for 196 languages'
    ds.properties['dc:description'] = (
        'Cross-linguistic dataset of 24 binary sub-features (GB409_1-GB409_24) of Grambank feature GB409 '
        '"Is there any ergative alignment of flagging?", coded from published grammatical descriptions.')
    ds.properties['dc:license'] = 'https://creativecommons.org/licenses/by/4.0/'
    ds.properties['dcat:accessURL'] = 'https://github.com/rzariquiey/ergon-database'
    # VERIFY: replace with the DOI of the v1.1.0 Zenodo record once it is minted
    # (the v1.0.1 record is https://doi.org/10.5281/zenodo.21107436).
    ds.properties['dc:identifier'] = 'https://github.com/rzariquiey/ergon-database/tree/v1.1.0'
    ds.properties['dc:bibliographicCitation'] = (
        'Zariquiey, R., Montoya, J., Gomez, L., Alvarado, C., Chau Príncipe, S., Lanasca-Moura, L., Almendra, A., '
        f'Poblete, M., Vásquez-Aguilar, A., Greenhill, S. J. & Gray, R. D. ERGON (v{VERSION}). '
        'https://github.com/rzariquiey/ergon-database')
    ds.properties['schema:version'] = VERSION
    ds.properties['prov:wasDerivedFrom'] = [
        {'rdf:about': 'https://github.com/grambank/grambank', 'dc:title': 'Grambank v1.0 (language sample; feature GB409)'},
        {'rdf:about': 'https://github.com/glottolog/glottolog-cldf/tree/v5.3', 'dc:title': 'Glottolog 5.3'},
    ]

    lang_rows = []
    for lang in langs:
        g = glot[lang['Glottocode']]
        lang_rows.append(dict(
            ID=lang['Glottocode'], Name=lang['Name'], Glottocode=lang['Glottocode'],
            ISO639P3code=g['ISO639P3code'] or None, Macroarea=g['Macroarea'],
            Latitude=float(g['Latitude']) if g['Latitude'] else None,
            Longitude=float(g['Longitude']) if g['Longitude'] else None,
            Glottolog_Name=g['Glottolog_Name'], Level=g['Level'],
            Language_level_Glottocode=g['Language_level_Glottocode'],
            Family=g['Family'], Family_Glottocode=g['Family_Glottocode'] or None,
            Status=lang['Status'], Status_comment=lang['Status_comment'] or None,
            Coders=[x for x in lang['Coders'].split(';') if x.strip()],
            Reviewer=[x for x in lang['Reviewer'].split(';') if x.strip()],
            Primary_Source=[primary[lang['Glottocode']]] if primary[lang['Glottocode']] else [],
        ))
    codes = []
    for p in params:
        codes.append(dict(ID=f"{p['ID']}-0", Parameter_ID=p['ID'], Name='0', Description='No'))
        codes.append(dict(ID=f"{p['ID']}-1", Parameter_ID=p['ID'], Name='1', Description='Yes'))
    param_rows = [dict(ID=p['ID'], Name=p['Name'], Description=p['Description'], Domain=p['Domain'],
                       Subdomain=p['Subdomain'], Paired_with=p['Paired_with'] or None,
                       Grambank_parent=p['Grambank_parent']) for p in params]
    contrib_rows = [dict(ID=c['ID'], Name=c['Name'], Affiliation=c['Affiliation'], Roles=c['Roles'])
                    for c in contributors]

    used = {r.split('[')[0] for v in values for r in v['Source']}
    ds.add_sources(*[s for s in sources if s.id in used])
    ds.write(LanguageTable=lang_rows, ParameterTable=param_rows, CodeTable=codes,
             ValueTable=values, **{'contributors.csv': contrib_rows})
    print(f'ERGON v{VERSION}: {len(lang_rows)} languages, {len(param_rows)} parameters, '
          f'{len(values)} values, {len(used)} sources')
    return ds


if __name__ == '__main__':
    main()
