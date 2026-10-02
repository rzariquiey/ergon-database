"""
One-off migration of the ERGON v1.0.1 release (Zenodo 10.5281/zenodo.21107436,
GitHub tag/commit b93a06a) to the harmonised v1.1.0 source format in raw/.

This script documents, in executable form, every change made between v1.0.1
and v1.1.0. It is kept for provenance; it is NOT part of the regular build,
which starts from raw/ (see scripts/build_cldf.py).

Inputs (from the v1.0.1 archive):
  cldf/values.csv, cldf/languages.csv          released values (authoritative)
  ERGON_data/**/<glottocode>[_curated].csv      legacy coding sheets
                                                (original coding + curation notes)
  ERGON_documentation/control de revisiones-silverstein.xlsx (exported to CSV)
Outputs (this repository):
  raw/language_sheets/<glottocode>.csv  one sheet per language
  raw/languages.csv                     language metadata and status
  raw/curation_log.csv                  value-level change history
  raw/curation_notes.csv                language-level curation notes
"""
import csv, json, re, sys, pathlib, collections

LEGACY_JSON = pathlib.Path(sys.argv[1])          # produced by stage1_collect.py
TRANSLATIONS = pathlib.Path(sys.argv[2])         # Spanish -> English map
REVIEW_CONTROL = pathlib.Path(sys.argv[3])       # review-round assignments
OUT = pathlib.Path(sys.argv[4])                  # repository root

D = json.load(open(LEGACY_JSON, encoding='utf-8'))
TR = json.load(open(TRANSLATIONS, encoding='utf-8'))
PIDS = [f'GB409_{i}' for i in range(1, 25)]

# ---------------------------------------------------------------- language-level decisions
GLOTTOCODE_FIX = {
    'caca1251': ('cash1251', 'caca1251 is not a valid Glottocode; Kakataibo is cash1251 (Cashibo-Cacataibo) in Glottolog 5.3.'),
    'yami1258': ('yami1256', 'yami1258 is not a valid Glottocode (typo in v1.0.1 CLDF build); Yaminawa (Yaminahua) is yami1256.'),
    'bala1316': ('kuma1276', 'The coded source (Bril 2002) describes Nêlêmwa; bala1316 (Balade/Nyelâyu) was a mis-assignment. Nêlêmwa-Nixumwak is kuma1276.'),
}
# Languages whose v1.0.1 status was "ergative" but whose released values show no ergative
# flagging on any nominal category (GB409_2-5 all 0) after verification.
TO_NON_ERGATIVE = {
    'bugi1244': 'Ergative-absolutive alignment is realised by pronominal proclitics/enclitics on the verb (indexing), not by flagging; free pronouns and NPs are not case-marked (Hanson 2003:59-60, 126, 153).',
    'bamb1270': "Campbell (1989:47): 'absolutive/ergative case inflections are limited to the arguments represented by pronominal affixes on the verb stem. There are no case markings on nouns.' Ergative alignment is a property of indexing only.",
    'kamu1260': "The putative ergative -ta is optional, also marks intransitive subjects and attaches to non-argument elements; Routamaa (1994:75) states it 'cannot be described as' ergative.",
    'iaai1238': 'Personal markers of the agent series mark both S and A; no ergative flagging on pronouns or NPs (Ozanne-Rivierre 1976:148-149, §4.37-4.39).',
    'kara1500': 'Free pronouns are identical for S and A (nominative pattern) and full NPs are not case-marked; S and A are distinguished from P by word order and verbal morphology (Ribeiro 2012:51, 54, 174, 191-192).',
    'kari1311': 'No case morphology exists (Everett 2006:304); Everett explicitly rejects an ergative analysis of free pronouns (p. 365).',
}
TO_PROBLEMATIC = {
    'lisu1250': 'Coded from Yu (2007), which describes the agentive marker le on A and on agentive S (split-S flagging; see dech1234 and hual1240). Four ERGON entries (lisu1250, lipo1242, dech1234, hual1240) derive from this source; their classification and identity must be resolved together.',
    'lipo1242': 'Coded from Yu (2007), a description of Lisu, which describes the agentive marker le on A and on agentive S (split-S flagging). Four ERGON entries derive from this source; whether Yu (2007) describes Lipo at all must be checked.',
    'dech1234': 'Active-stative (split-S) flagging: le33 marks A and agentive S, non-agentive S is unmarked like P (Yu 2007). Split-S systems fall outside the operational definition used in this release (ERG flagging on the default intransitive class), and the coding is derived from the same source as hual1240.',
    'hual1240': 'Active-stative (split-S) flagging: le33 marks A and agentive S, non-agentive S is unmarked like P (Yu 2007). Split-S systems fall outside the operational definition used in this release, and the coding is derived from the same source as dech1234.',
}
PROBLEMATIC_NOTES = {
    'bilb1241': "An optional postposition mos occurs on subjects, especially when the object is fronted; the few available examples show it on A only, which is insufficient to establish an ergative marker (Dempwolff 1909). Grambank codes GB409=1.",
    'coeu1236': "Full-NP A arguments take the 'oblique' marker only in some contexts (e.g. when an overt P is animate; Doak 1997, ex. 420, 433); person is otherwise expressed by verbal affixes and proclitics. Whether oblique-marked A constitutes ergative flagging is unresolved.",
    'lush1252': "Salish voice/person-hierarchy system: the oblique marker ?ə marks NPs in several semantic roles and S and A share the subject position (Zahir 2018, §2.1-2.3). Grambank codes GB409=1; the alignment of flagging could not be classified unambiguously.",
    'maxa1247': "Campos (2009, §9.2.1) analyses the system as tripartite-active: A and agentive S take the postposition -te, non-agentive S is marked by a person prefix, and P is unmarked. It does not instantiate S=P≠A flagging.",
    'nort2722': "An optional agentive suffix -wu marks non-topical A only and cannot mark S; the grammar describes the system as nominative-accusative (LaPolla & Huang 2003, §3.2.3). Under the v1.1 scope definition (optional A-only marking counts as ergative flagging) this pattern qualifies as optional ergative flagging; the sheet, coded under the earlier stricter criterion, must be recoded before the language can be classified.",
    'pend1242': "Ergative-like marking arises when the genitive marks the agent in inverted (undergoer-voice) clauses; pronouns are not flagged (Quick 2007). The status of this voice-conditioned pattern as ergative flagging is unresolved.",
}
NON_ERGATIVE_NOTES = {
    'achi1257': 'Pronominal clitics on the verb follow S=A≠P; no ergative flagging (Asyik 1987).',
    'apat1240': "Nominative (zero)-accusative ('mi') case system: A and S unmarked, P marked (Abraham 1985:35-38).",
    'bert1248': 'Absolutive/nominative distinction is positional, not based on transitivity; no ergative flagging (Andersen 2003).',
    'bier1244': 'S and A are marked identically (subject prefixes); no ergative flagging (Budd 2009:161).',
    'cemu1238': 'S and A are marked identically by personal modalities; no separate A flag (Rivierre 1980:65, 185).',
    'fass1245': 'Nominative-accusative; the clitic =m marks objects/obliques, not A (Honeyman 2016; Blake 2007).',
    'hula1239': 'No ergative case morphology described (Short 1938).',
    'lihi1237': 'No ergative alignment of flagging; the grammar notes only a historical connection with an ergative language (Neuhaus 2015).',
    'liji1238': 'Nominative-accusative; no ergative flagging (Stofberg 1978).',
    'limo1248': "The grammar analyses the language as an 'active language' (Shibatani's typology), not ergative; subject marking does not follow ergative alignment (Ferreirinho 1993, §1.3).",
    'mara1379': 'Nominative-accusative: S and A take -na, P takes -go (Singh 1984, §2.2.8).',
    'mara1404': "Philippine-type voice system; the topic particle 'so' marks the topic regardless of role; no A-specific flag (McKaughan & Macaraya 1967).",
    'moro1289': 'The clitic =i marks the undergoer (P and patientive S); A and agentive S are unmarked. This split-intransitive pattern is outside the operational definition of ergative flagging used here (Arka 2012:152-154).',
}

# ---------------------------------------------------------------- value-level rules
NOSPLIT = re.compile(r"(no (mention|evidence|information)[^.]*split|no [a-z/\- ]*(split|conditioning)[^.]*(documented|described|reported|mentioned|found)|there are no additional splits|no additional splits)", re.I)
NO_EXAMPLES = re.compile(r"(no examples|do not offer evidence of inanimate|there are no examples|but there are no examples|not enough examples)", re.I)
ABSENT = re.compile(r"(not (a )?(grammaticali[sz]ed|morphological category|grammatical category)|category absent|^tense is not marked|there is not indicative mood|ill-posed|no hay referencia[^.]*estatus)", re.I)
SPECULATIVE = re.compile(r"(no source[^.]*verify|verify in|likely has|typical of [A-Z]|no source\. value)", re.I)
ARTIFACT_COMMENTS = {
    'PDF source unreadable; value retained from original annotation.':
        'Value from the original coding; not re-verified during curation because no legible copy of the source was available.',
    'PDF source unreadable; original annotation uncertain.':
        'Original coding uncertain; not re-verified during curation because no legible copy of the source was available.',
    'PDF source (Fesl 1985) is corrupted and unreadable; value retained from original annotation.':
        'Value from the original coding; not re-verified during curation because no legible copy of Fesl (1985) was available.',
}
DROP_COMMENTS = {'La gramática está en francés', 'La gramática está en alemán'}

def tr(text):
    t = text.strip()
    if t in TR:
        return TR[t] or ''
    return t

log = []            # value-level change log v1.0.1 -> v1.1.0
def L(gc, pid, old, new, rule, why):
    log.append(dict(Glottocode=gc, Parameter_ID=pid, Value_v1_0_1=old, Value_v1_1_0=new, Rule=rule, Rationale=why))

langs_out, sheets, notes, history = [], {}, [], []

for old_gc, d in sorted(D.items()):
    gc, gc_note = GLOTTOCODE_FIX.get(old_gc, (old_gc, ''))
    status = {'ergative': 'ergative', 'non_ergative': 'non-ergative', 'problematic': 'problematic'}[d['status']]
    status_note = ''
    if old_gc in TO_NON_ERGATIVE:
        status, status_note = 'non-ergative', TO_NON_ERGATIVE[old_gc]
    elif old_gc in TO_PROBLEMATIC:
        status, status_note = 'problematic', TO_PROBLEMATIC[old_gc]
    elif old_gc in PROBLEMATIC_NOTES:
        status_note = PROBLEMATIC_NOTES[old_gc]
    elif old_gc in NON_ERGATIVE_NOTES:
        status_note = NON_ERGATIVE_NOTES[old_gc]

    vals = d['values']
    rows = []
    for pid in PIDS:
        n = int(pid.split('_')[1])
        v = vals.get(pid)
        if v is None:
            # value missing from the v1.0.1 build (east2379 was only partially coded)
            new = '?'; comment = 'Not coded: this feature was left blank in the coding sheet.'; source = ''
            if old_gc == 'east2379' and pid == 'GB409_5':
                new, source = '1', 'Henderson 2013: 13'
                comment = "In nominals other than pronouns the nominative and accusative are syncretised, while the ergative is distinct (Henderson 2013:13)."
            L(gc, pid, '(missing)', new, 'M1', 'Value absent from v1.0.1 CLDF build; added as "?" (not coded)' + (' / coded from curation report' if new != '?' else ''))
            rows.append(dict(Parameter_ID=pid, Value=new, Source=source, Comment=comment))
            continue
        old = v['value']; new = old
        comment = v['comment'].strip()
        source = v['source'].strip()
        full = comment + ' || ' + v['curated_comment']

        # --- source-cell fixes (formatting errors in the coding sheets)
        if old_gc == 'noct1238' and re.fullmatch(r'[\d,\s\-–;]+', source or 'x'):
            source = 'Boro 2017: ' + source            # author/year omitted in the sheet
        if old_gc == 'nucl1302':
            source = re.sub(r'Hewitt:?1990,?\s*', 'Hewitt 1990: ', source).replace('\n', '; ')
        if old_gc == 'madn1237' and pid == 'GB409_24' and source == '1':
            source, comment = comment, ''              # column shift in the coding sheet
        # --- comment hygiene
        if comment in DROP_COMMENTS:
            comment = ''
        comment = ARTIFACT_COMMENTS.get(comment, comment)
        comment = tr(comment)
        comment = comment.replace('Routamma (1994', 'Routamaa (1994')   # author name misspelt in the sheet

        # --- language status overrides
        if old_gc in TO_NON_ERGATIVE:
            if old != '0':
                new = '0'
                L(gc, pid, old, new, 'S1', 'Language reclassified as non-ergative after verification (no ergative flagging on any nominal category); all GB409 sub-features are 0 by definition.')
            if comment in ('erg es unmarked', 'erg es unmarked pero lo ponen dentro de 1sg', 'The ergative is unmarked, but the source glosses it as part of the 1sg form.'):
                comment = ''
        else:
            # --- invalid codes
            if old not in ('0', '1', '?'):
                new = '1'
                L(gc, pid, old, new, 'V1', f'Invalid code "{old}" (used to signal that the language lacks a realis/irrealis category). Recoded under coding rule C3 (category not grammaticalised; ergative flagging invariant across the corresponding contexts).')
            # --- speculative values without source evidence
            elif old in ('0', '1') and SPECULATIVE.search(v['curated_comment']) and not source:
                new = '?'
                L(gc, pid, old, new, 'H3', 'Value was inferred from areal/genealogical expectations rather than from the source; reset to "?" (coding rule C4).')
            # --- "no split documented" harmonisation
            elif old == '?' and 6 <= n <= 22 and NOSPLIT.search(comment) and not NO_EXAMPLES.search(comment):
                new = '0' if n == 22 else '1'
                L(gc, pid, old, new, 'H1', 'Source describes ergative flagging and documents no split along this dimension; harmonised with coding rule C2 (default value when no split is documented).')
            elif old in ('?', '0') and 6 <= n <= 21 and ABSENT.search(full):
                new = '1'
                L(gc, pid, old, new, 'H2', 'The language does not grammaticalise this distinction; contexts identified semantically and ergative flagging is invariant across them (coding rule C3).')
            elif old_gc == 'nina1238' and pid in ('GB409_16', 'GB409_17') and old == '0' and not source:
                new = '?'
                L(gc, pid, old, new, 'H5', 'Both members of the topical/non-topical pair were coded 0 without any source reference, which is logically incompatible with the presence of ergative flagging; reset to "?".')
            elif old_gc == 'futu1245' and pid == 'GB409_5' and old == '0':
                new = '1'
                comment = ("The marker 'e' marks A (not S or P) when A follows the verb or in topicalisation contexts; "
                           "its use is optional. Optional ergative marking counts as ergative flagging under the v1.1 scope definition.")
                L(gc, pid, old, new, 'P1', 'v1.0.1 had recoded this value 1->0 because the marker is optional. Under the v1.1 scope definition optionality is not an exclusion criterion (only markers that also flag S are excluded); original coding restored.')
            elif old_gc == 'agus1235' and pid == 'GB409_5' and old == '?':
                new = '1'
                L(gc, pid, old, new, 'H4', 'Proper names take ergative si/ni (comment); coding guideline for GB409_5: code 1 if a subset of non-pronominal NPs shows ergative flagging.')
        rows.append(dict(Parameter_ID=pid, Value=new, Source=source, Comment=comment))

        # --- history of original coding -> curated value (pre-v1.0.1)
        ov = (v.get('original_value') or '').strip()
        if ov and ov != old and ov in ('0', '1', '?'):
            history.append(dict(Glottocode=gc, Parameter_ID=pid, Value_original_coding=ov,
                                Value_v1_0_1=old, Note=tr(v['curated_comment'].strip())))
    sheets[gc] = rows

    # language-level curation note (GB409_1 curated comment used as sheet-level note in v1.0)
    cc1 = vals.get('GB409_1', {}).get('curated_comment', '').strip()
    if len(cc1) > 200:
        notes.append(dict(Glottocode=gc, Note=tr(cc1)))
    NAME_FIX = {'cash1251': 'Kakataibo', 'yami1256': 'Yaminawa', 'kuma1276': 'Nêlêmwa'}
    langs_out.append(dict(Glottocode=gc, Name=NAME_FIX.get(gc, d['name']), Coders='', Status=status, Status_comment=status_note,
                          Glottocode_v1_0_1=old_gc if old_gc != gc else '', Glottocode_note=gc_note))

# ---------------------------------------------------------------- reviewer assignments
rev = {}
for r in csv.DictReader(open(REVIEW_CONTROL, encoding='utf-8')):
    g = r['lang'].replace('_curated', '').strip()
    if g == 'hula': g = 'hula1239'
    g = GLOTTOCODE_FIX.get(g, (g, ''))[0]
    rev[g] = r['coder'].strip()
INITIALS = {'Roberto': 'RZ', 'Jaime': 'JM', 'Alonso': 'AVA', 'Claudia': 'CA', 'Luisa': 'LG', 'Leslie': 'LL', 'Santiago': 'SCP'}
for l in langs_out:
    l['Reviewer'] = INITIALS.get(rev.get(l['Glottocode'], ''), '')

# ---------------------------------------------------------------- write
def wcsv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)

for gc, rows in sheets.items():
    wcsv(OUT / 'raw' / 'language_sheets' / f'{gc}.csv', rows, ['Parameter_ID', 'Value', 'Source', 'Comment'])
wcsv(OUT / 'raw' / 'languages.csv', langs_out,
     ['Glottocode', 'Name', 'Status', 'Status_comment', 'Coders', 'Reviewer', 'Glottocode_v1_0_1', 'Glottocode_note'])
wcsv(OUT / 'raw' / 'curation_log.csv', log, ['Glottocode', 'Parameter_ID', 'Value_v1_0_1', 'Value_v1_1_0', 'Rule', 'Rationale'])
wcsv(OUT / 'raw' / 'curation_history_v1_0.csv', history, ['Glottocode', 'Parameter_ID', 'Value_original_coding', 'Value_v1_0_1', 'Note'])
wcsv(OUT / 'raw' / 'curation_notes.csv', notes, ['Glottocode', 'Note'])
print(len(langs_out), 'languages;', len(log), 'value changes;', len(history), 'history rows;', len(notes), 'notes')
print(collections.Counter(x['Rule'] for x in log))
print(collections.Counter(l['Status'] for l in langs_out))
