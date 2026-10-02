"""Parsing of free-text citations ("Author Year: pages") used in the coding sheets."""
import re, csv, pathlib, collections
CIT = re.compile(r"""^\s*(?P<auth>[^\d;]*?[\w'’\.\-])[\s,\(]*(?P<year>(1[89]|20)\d\d(\s*[-–]\s*\d{2,4})?[a-z]?)\)?\s*(?:[:,]\s*(?:pp?\.?\s*)?(?P<pages>.*))?$""")
def split_sources(s):
    s = s.strip().strip(';').strip()
    if not s: return []
    # split on ';' but keep page lists like "p. 76; 59" attached to previous citation
    parts=[p.strip() for p in s.split(';') if p.strip()]
    out=[]
    for p in parts:
        if out and not re.search(r'[A-Za-z]{3,}.*(1[89]|20)\d\d', p):
            out[-1]+= '; '+p
        else: out.append(p)
    return out
def parse(c):
    m = CIT.match(c)
    if not m: return None
    a = m.group('auth').strip(' ,.(')
    a = re.sub(r'\s+(and|&|y|e)\s+', ' & ', a)
    a = re.sub(r'\bet al\.?', 'et al.', a)
    pages = (m.group('pages') or '').strip().strip('.').replace('p. ','').replace('pp. ','')
    return dict(authors=a, year=m.group('year').replace(' ',''), pages=pages)
def surnames(a):
    a=a.replace('et al.','')
    return [re.sub(r"[^A-Za-zÀ-ÿ'\- ]","",x).strip().split()[-1] for x in re.split(r'&|,| and ',a) if re.sub(r"[^A-Za-zÀ-ÿ]","",x)]

def normalize_source(s):
    """Return list of (authors, year, pages) from a free-text Source cell."""
    s = s.replace('\n', '; ')
    s = re.sub(r'^1(?=[A-Z])', '', s.strip())                      # '1Whereat'
    s = re.sub(r'(\w):(\d{4})', r'\1 \2', s)                         # 'Gomez:1990'
    s = re.sub(r'([A-Za-z]),\s*[A-Z]\.\s*\((\d{4})\)\.?', r'\1 \2:', s)   # 'Fleck, D. (2010).'
    s = re.sub(r'Neuhaus 1954 \(2015\)', 'Neuhaus 2015', s)
    s = re.sub(r'(\d{4}),\s*(vol\d)', r'\1: \2', s)
    s = re.sub(r'(\d{4});\s*(\d)', r'\1: \2', s)                     # 'Whereat 1996; 6'
    s = re.sub(r'(\d{4}):\s*[:.]', r'\1:', s)
    out=[]
    for c in split_sources(s):
        p = parse(c)
        if p: out.append(p)
        elif out:                                                     # bare pages -> previous
            out[-1]['pages'] += '; ' + c
        else:
            out.append(dict(authors='', year='', pages=c))
    return out
