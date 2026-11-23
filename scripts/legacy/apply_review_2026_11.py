"""
Apply the November 2026 review round to raw/ (provenance script; run once).

Inputs: the team's working sheets of the review round (revised cells, the Coders sheet and the
answers to the review issues). They are kept by the authors and are not part of the public
release; set ERGON_REVIEW_DIR to the folder that holds them (rasgos_revisados.csv, coders.csv,
responses_to_issues.csv). The effect of the review on the data is recorded in raw/language_sheets/
and, cell by cell, in raw/curation_log.csv (rules R1 and S1).

Decisions applied (Roberto Zariquiey, 2026-11-16):
  * Emai, Fulnio and Huastec reclassified as non-ergative (team review); all values 0 (protocol s.3).
  * Non-ergative languages keep all values 0 even where a reviewed row says '?' or '1'
    (Momu, Kamula, Marori; Marori stays non-ergative: split-S is out of scope).
  * Duplicate rows for the same cell: the first row is the substantive review; later rows
    ("there's no evidence on source") were a second pass over '?' cells and are used only if
    the first row has no source.
  * A generic "no evidence" comment does not overwrite an existing substantive comment.
Every value change is written to raw/curation_log.csv with rule R1.
"""
import csv, collections, os, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
REV = pathlib.Path(os.environ.get('ERGON_REVIEW_DIR', pathlib.Path(__file__).resolve().parent / 'review_2026_11'))
SHEETS = ROOT / 'raw' / 'language_sheets'

NEW_NON_ERGATIVE = {
    'emai1242': ('LL', 'No ergative alignment of flagging; the "subject concord" marker of imperfective transitive clauses '
                 'is not a case marker (Schaefer & Egbokhare 2017:37-42).'),
    'fuln1247': ('CA', 'Ergative alignment is found only in indexing (third-person singular pronominal clitics on the verb); '
                 'pronouns and full NPs show no ergative flagging (Costa 1999:145-146, 309).'),
    'huas1242': ('CA', 'Person marking on the verb resembles an inverse system; there is no flagging of nouns or pronouns, '
                 'hence no ergative flagging (Kondić 2012).'),
}
# English translations of the Spanish comments entered for Georgian in the review sheet (reviewer JM).
# The sheet cites the source as "Hewitt 1990"; the work is Hewitt (1995) (confirmed in responses_to_issues.csv).
NUCL1302 = {
    'GB409_2': 'The source states that first- and second-person pronouns, singular and plural, do not change form (no case marking).',
    'GB409_3': 'The source states that first- and second-person pronouns, singular and plural, do not change form (no case marking).',
    'GB409_8': 'The past corresponds to Series II, which is ergative.',
    'GB409_9': 'Present and future correspond to Series I, which is nominative.',
    'GB409_10': 'Ergative marking occurs in the indicative whenever the verb form belongs to Series II.',
    'GB409_11': 'Ergative marking occurs in non-indicative moods whenever the verb form belongs to Series II.',
    'GB409_12': 'The realis corresponds to Series II, which is ergative.',
    'GB409_13': 'The irrealis corresponds to Series I, which is nominative.',
    'GB409_14': 'Agentive subjects are marked in Series II. Agentivity does not by itself trigger ergative marking, however; see for example Series III (Hewitt 1995:338).',
    'GB409_16': 'There is no evidence that topicality affects case marking; ergative marking occurs in both contexts.',
    'GB409_17': 'There is no evidence that topicality affects case marking; ergative marking occurs in both contexts.',
    'GB409_18': 'The source mentions no split in ergative marking based on the animacy of A.',
    'GB409_19': 'The source mentions no split in ergative marking based on the animacy of A; the examples given for GB409_15 also apply.',
    'GB409_21': 'The source mentions no exclusion of ergative marking from non-main clauses: factual clauses (Hewitt 1995:614), speech reporting (614), direct quotation (615).',
    'GB409_22': 'The source mentions no other factor conditioning ergative case marking. Hewitt (1995:446-490) discusses some irregular verbs, notably "know", which historically belongs to Series II: gmrot-mav (0-)i-c-i-s God-ERG (3rd.PER-)SV-know--PRS.INDIC-he "God knows", where the subject takes ergative marking with a present-tense third-person form, outside Series II.',
    'GB409_23': 'In general -ma/-n is the ergative marker, whereas -s/-is mark the genitive.',
    'GB409_24': 'In general -ma/-n is the ergative marker, whereas -it marks the instrumental; no other marker is identical to the ergative.',
}

BERGSLAND = '''@book{g_Bergsland_Aleut,
    author = {Bergsland, Knut},
    address = {Fairbanks},
    isbn = {9781555000646},
    pages = {xiii+360},
    publisher = {Fairbanks: Alaska Native Language Center, University of Alaska},
    series = {Research Paper},
    title = {Aleut Grammar: Unangam Tunuganann Achixaasix\u0302},
    volume = {10},
    year = {1997}
}'''
DELMER = '''@mastersthesis{Delmer2018,
    author = {Delmer, Jean-Fran\u00e7ois},
    year = {2018},
    title = {Manobo Verbs and Their Arguments},
    school = {Payap University}
}'''
HENDERSON = '''@phdthesis{Henderson2022,
    author = {Henderson, Claire Emma},
    year = {2022},
    title = {Ergativity in East Futunan Oral Narratives},
    school = {University of California, Davis},
    url = {https://escholarship.org/uc/item/6h69f1zc}
}'''
GENERIC = re.compile(r"^\s*(there'?s no evidence( on (the )?source)?|no evidence)\.?\s*$", re.I)


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def write(p, rows, fields):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def clean_source(s):
    s = (s or '').strip()
    s = s.replace('Routamma', 'Routamaa').replace('Kondić2012', 'Kondić 2012')
    s = re.sub(r'\bDe Queiroz\b', 'de Queiroz', s)
    s = re.sub(r':\s*in passim', ': passim', s)
    s = re.sub(r'^([^\d,]+),\s*(\d{4}),\s*p\.\s*', r'\1 \2: ', s)   # 'Fesl, 1985, p. 117'
    s = re.sub(r',\s*(\d{4}):', r' \1:', s)          # 'Fesl, 1985:' -> 'Fesl 1985:'
    # several works separated by commas: 'A 1981: 17-18, B 1997: 56' -> 'A 1981: 17-18; B 1997: 56'
    s = re.sub(r"\s*,\s*(?=[A-Z][\w'\-]+(?:\s+(?:and|&|[A-Z][\w'\-]+))*\s+(?:1[89]|20)\d\d\b)", '; ', s)
    return s


def clean_comment(c):
    c = (c or '').strip()
    if GENERIC.match(c):
        return 'No relevant evidence in the source.'
    return c


WORKFLOW = [   # editing notes that do not belong in a released comment
    (r'^Original coding uncertain; not re-verified during curation because no legible copy of the source was available\.$',
     'No relevant evidence in the source.'),
    (r'\s*CORRECTED from original annotation [^.]*?\.', ''),
    (r'\s*Corrected from original annotation [^.]*\.', ''),
    (r'\s*Corrected from (?:original value of )?\S+(?: to \S+)?\.', ''),
    (r'\s*Original annotation \(value=\d\) was a coding error[^.]*\.', ''),
    (r'\s*Changed from original annotation [^.]*\.', ''),
    (r'[;,]?\s*changed from original annotation [^.]*\.', '.'),
    (r'\s*Original annotation of \S+ was incorrect\.', ''),
    (r'Original annotation cited nɛ³³ as both ergative and instrumental, but PDF verification \(Yu 2007\) confirms that nɛ³³ is',
     'In Yu (2007), nɛ³³ is'),
    (r'original annotation 0 lacks specific citation for Dechang; ', ''),
]


def clean_workflow(c):
    for a, b in WORKFLOW:
        c = re.sub(a, b, c)
    return c.strip()


def fix_cell(gc, pid, old, new):
    path = SHEETS / f'{gc}.csv'
    sheet = read(path)
    for row in sheet:
        if row['Parameter_ID'] == pid and row['Source'].strip() == old:
            row['Source'] = new
    write(path, sheet, list(sheet[0].keys()))


def main():
    langs = read(ROOT / 'raw' / 'languages.csv')
    lfields = list(langs[0].keys())
    L = {l['Glottocode']: l for l in langs}
    log = read(ROOT / 'raw' / 'curation_log.csv')
    logfields = list(log[0].keys())
    logged = {(r['Glottocode'], r['Parameter_ID']): r for r in log}

    # ---------------------------------------------------------------- reviewed cells
    rows = read(REV / 'rasgos_revisados.csv')
    first = collections.OrderedDict()
    for r in rows:
        k = (r['Glottocode'].strip(), r['Ergon_ID'].strip())
        if k not in first:
            first[k] = r
        elif not (first[k].get('Source') or '').strip():
            first[k] = r

    for gc, (rev, why) in NEW_NON_ERGATIVE.items():
        L[gc]['Status'] = 'non-ergative'
        L[gc]['Status_comment'] = why

    changes = []
    by_lang = collections.defaultdict(dict)
    for (gc, pid), r in first.items():
        by_lang[gc][pid] = r
    for gc in sorted(set(by_lang) | set(NEW_NON_ERGATIVE)):
        path = SHEETS / f'{gc}.csv'
        sheet = read(path)
        fields = list(sheet[0].keys())
        status = L[gc]['Status']
        for row in sheet:
            pid = row['Parameter_ID']
            old = row['Value']
            r = by_lang[gc].get(pid)
            new_src = clean_source(r['Source']) if r else ''
            new_com = clean_comment(r['Comment']) if r else ''
            new_val = (r['Value'] or '').strip() if r else old
            if status == 'non-ergative':
                new_val = '0'
                if new_com == 'No relevant evidence in the source.' or (r and (r['Value'] or '').strip() != '0'):
                    new_com = ''          # stale context coding; the language-level comment explains the 0s
            if new_val not in ('0', '1', '?'):
                raise SystemExit(f'bad value {gc} {pid} {new_val!r}')
            if new_src and (new_val != old or not row['Source'].strip() or 'passim' not in new_src):
                row['Source'] = new_src
            if new_com and (new_val != old or not row['Comment'].strip() or new_com != 'No relevant evidence in the source.'):
                row['Comment'] = new_com
            elif new_val != old and not new_com and status != 'non-ergative':
                row['Comment'] = ''
            if gc in NEW_NON_ERGATIVE and new_val != old:
                row['Comment'] = ''
            if new_val != old:
                row['Value'] = new_val
                changes.append((gc, pid, old, new_val))
        write(path, sheet, fields)

    sheet = read(SHEETS / 'nucl1302.csv')
    for row in sheet:
        if row['Parameter_ID'] in NUCL1302:
            row['Comment'] = NUCL1302[row['Parameter_ID']]
        row['Comment'] = row['Comment'].replace('Hewitt (1990, pp.', 'Hewitt (1995, pp.')
    write(SHEETS / 'nucl1302.csv', sheet, list(sheet[0].keys()))

    # two Spanish comments missed by the first translation pass
    for gc, pid, old, new in [('darl1243', 'GB409_1', 'unmarked/doble marcación', 'Unmarked (double marking).'),
                              ('guiq1238', 'GB409_17', 'indexación al adjetivo', 'Indexing on the adjective.')]:
        sh = read(SHEETS / f'{gc}.csv')
        for row in sh:
            if row['Parameter_ID'] == pid and row['Comment'].strip() == old:
                row['Comment'] = new
        write(SHEETS / f'{gc}.csv', sh, list(sh[0].keys()))

    # remove editing notes from all comments
    for path in sorted(SHEETS.glob('*.csv')):
        sh = read(path)
        new = [dict(r, Comment=clean_workflow(r['Comment'])) for r in sh]
        if new != sh:
            write(path, new, list(sh[0].keys()))

    # Apinaje: the review recodes all TAM contexts as 1 (ergative flagging in subordinate clauses of
    # every TAM value), so the documented exception to check L2 is no longer needed.
    exc = read(ROOT / 'etc' / 'validation_exceptions.csv')
    exc_fields = list(exc[0].keys())
    write(ROOT / 'etc' / 'validation_exceptions.csv', [e for e in exc if e['Glottocode'] != 'apin1244'], exc_fields)

    # ---------------------------------------------------------------- curation log
    for gc, pid, old, new in changes:
        k = (gc, pid)
        if gc in NEW_NON_ERGATIVE:
            rule, why = 'S1', 'Language reclassified as non-ergative in the 2026 review (no ergative flagging on any nominal category); all GB409 sub-features are 0 by definition.'
        else:
            rule, why = 'R1', 'Recoded in the 2026 review round against the source (reviewer sheet, comment and pages in the coding sheet).'
        if k in logged:
            # the final value decides the rule, except for cells that were missing in v1.0.1 (M1)
            e = logged[k]
            e['Value_v1_1_0'] = new
            if e['Rule'] == 'M1':
                e['Rationale'] += ' Coded in the 2026 review round.'
            else:
                e['Rule'], e['Rationale'] = rule, why
        else:
            e = dict(Glottocode=gc, Parameter_ID=pid, Value_v1_0_1=old, Value_v1_1_0=new, Rule=rule, Rationale=why)
            log.append(e)
            logged[k] = e
    log = [e for e in log if e['Value_v1_0_1'] != e['Value_v1_1_0']]
    for e in log:   # rule H3 is coding rule C5 (no inference from expectations)
        e['Rationale'] = e['Rationale'].replace('(coding rule C4)', '(coding rule C5)')
    log.sort(key=lambda e: (e['Glottocode'], int(e['Parameter_ID'].split('_')[1])))
    write(ROOT / 'raw' / 'curation_log.csv', log, logfields)

    # ---------------------------------------------------------------- coders
    names = {'Manuel Olórtegui': 'MO', 'Amy Trujillo': 'AT', 'Josué Nuñez': 'JN', 'Gerson Vizcarra': 'GV'}
    for r in read(REV / 'coders.csv'):
        parts = [p.strip() for p in (r['Coders'] or '').split(',')]
        L[r['Glottocode']]['Coders'] = ';'.join(names.get(p, p) for p in parts if p and p != '?')
    L['mati1255']['Coders'] = 'RZ'     # Matis: coded by RZ (author, 2026-11-17)
    write(ROOT / 'raw' / 'languages.csv', langs, lfields)

    # ---------------------------------------------------------------- sources (responses_to_issues.csv)
    fix_cell('east2379', 'GB409_17', 'Wilkins 1989165', 'Wilkins 1989: 165')
    fix_cell('iwam1256', 'GB409_22', 'Conrad, 1999', 'Conrad 1971; Conrad 1993')   # "We used Conrad 1971 and Conrad 1993, not 1999"
    smap = read(ROOT / 'raw' / 'source_map.csv')
    sfields = list(smap[0].keys())
    smap = [r for r in smap if (r['Glottocode'], r['Citation']) != ('iwam1256', 'Conrad 1999')]
    notes = {('kara1487', 'Brainard 1993'): 'Cited as 1993 in the coding sheet; confirmed as Brainard (1994) in the 2026 review.',
             ('nucl1302', 'Hewitt 1990'): 'Cited as Hewitt 1990 in the coding sheet; confirmed as Hewitt (1995) in the 2026 review.',
             ('east2447', 'Henderson 2022'): 'Record completed in the 2026 review (UC Davis dissertation).',
             ('ayiw1239', 'N\ufffdss 2015'): 'Confirmed in the 2026 review: Naess (2015), The Aiwoo verb phrase, Journal of Linguistics 51(1).'}
    for r in smap:
        if (r['Glottocode'], r['Citation']) in notes:
            r['Note'] = notes[(r['Glottocode'], r['Citation'])]
    for gc, cit, key, match in [
            ('agus1235', 'Verstraelen 1968', 's_Verstraelen_Manobo', 'Grambank v1.0 sources.bib'),
            ('agus1235', 'Delmer 2018', 'Delmer2018', 'manual'),
            ('aleu1260', 'Bergsland 1997', 'g_Bergsland_Aleut', 'Grambank v1.0 sources.bib'),
            ('kamu1260', 'Routamaa 1994', 's_Routamaa_Kamula', 'Grambank v1.0 sources.bib'),
            ('kara1487', 'Brainard 1994', 'styp_Brainard_Karao', 'Grambank v1.0 sources.bib'),
            ('kari1254', 'de Queiroz 2012', 'g_deQueiroz_Dzubukua', 'Grambank v1.0 sources.bib'),
            ('nucl1302', 'Hewitt 1995', 'g_Hewitt_Georgian', 'Grambank v1.0 sources.bib')]:
        smap.append(dict(Glottocode=gc, Citation=cit, BibKey=key, Match=match,
                         Note='Added in the 2026 review.' + (' MA thesis, Payap University (reference supplied by the authors).' if match == 'manual' else '')))
    bib = (ROOT / 'raw' / 'sources.bib').read_text(encoding='utf-8')
    bib = re.sub(r'@misc\{Conrad1999,.*?\n\}\n*', '', bib, flags=re.S)
    bib = re.sub(r'@misc\{Henderson2022,.*?\n\}', lambda m: HENDERSON, bib, flags=re.S)
    if 'g_Bergsland_Aleut' not in bib:
        bib = bib.rstrip() + '\n\n' + BERGSLAND + '\n\n' + DELMER + '\n'
    (ROOT / 'raw' / 'sources.bib').write_text(bib, encoding='utf-8')
    smap.sort(key=lambda r: (r['Glottocode'], r['Citation']))
    write(ROOT / 'raw' / 'source_map.csv', smap, sfields)

    c = collections.Counter((o, n) for _, _, o, n in changes)
    print(f'{len(changes)} value changes in {len({g for g, *_ in changes})} languages: {dict(c)}')


if __name__ == '__main__':
    main()
