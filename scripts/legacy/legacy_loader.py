# Provenance script used once to prepare ERGON v1.1.0 from the v1.0.1 archive (see README.md in this folder).
# Paths refer to the working copies used at the time (v1.0.1 checkout; Grambank v1.0 and Glottolog 5.3 clones).
import csv, io, re, pathlib, collections
import os
# a checkout of the v1.0.1 tree of rzariquiey/ergon-database (set ERGON_V1_REPO to override)
REPO = pathlib.Path(os.environ.get('ERGON_V1_REPO', pathlib.Path(__file__).resolve().parents[3] / 'ergon-database-v1.0.1'))
DATA = REPO/'ERGON_data'
GC = re.compile(r'^[a-z]{4}\d{4}$')

def read_any(p):
    raw = p.read_bytes()
    for enc in ('utf-8-sig','cp1252','latin-1'):
        try: t = raw.decode(enc); break
        except UnicodeDecodeError: continue
    first = t.splitlines()[0]
    if first.startswith('"') and ';' in first and first.count(',')==0:
        # whole line quoted with ; inside
        lines=[l[1:-1] if l.startswith('"') and l.endswith('"') else l for l in t.splitlines()]
        t='\n'.join(lines)
    delim = ';' if first.count(';') > first.count(',') else ','
    rdr = csv.reader(io.StringIO(t), delimiter=delim)
    rows = list(rdr)
    hdr = [h.strip() for h in rows[0]]
    out=[]
    for r in rows[1:]:
        if not any(x.strip() for x in r): continue
        d={}
        for i,h in enumerate(hdr):
            if h and i < len(r): d[h]=r[i].strip()
        out.append(d)
    return out, enc, hdr

def sheet_records(p):
    rows, enc, hdr = read_any(p)
    recs={}
    for d in rows:
        pid = d.get('Ergon_ID','').strip()
        if not re.match(r'^GB409_\d+$', pid): continue
        src = d.get('Source_comment') or d.get('Source') or ''
        val = (d.get('final_value') or '').strip()
        if val == '': val = d.get('Value','').strip()
        recs.setdefault(pid, dict(value=val, orig_value=d.get('Value','').strip(), source=src,
                                  comment=d.get('Comment',''), curated_flag=d.get('curated',''),
                                  curated_comment=d.get('curated_comment',''),
                                  language=d.get('Language',''), family=d.get('Family','')))
    return recs, enc, hdr

def all_sheets():
    """yield (folder_kind, stage, glottocode, path)"""
    for kind in ('Ergative','Non_ergative'):
        for stage in ('curated','original'):
            for p in sorted((DATA/kind/stage).glob('*.csv')):
                gc = p.stem.replace('_curated','')
                if GC.match(gc): yield kind, stage, gc, p
    for p in sorted((DATA/'Problematic').glob('*.csv')):
        gc=p.stem.replace('_curated','')
        if GC.match(gc): yield 'Problematic','curated',gc,p
