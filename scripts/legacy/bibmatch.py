# Provenance script used once to prepare ERGON v1.1.0 from the v1.0.1 archive (see README.md in this folder).
# Paths refer to the working copies used at the time (v1.0.1 checkout; Grambank v1.0 and Glottolog 5.3 clones).
import re, csv, json, unicodedata, collections, sys
sys.path.insert(0,'.')
from cites import surnames
def fold(s): return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c)).lower()
def parse_bib(path, keep=lambda k,f: True):
    txt=open(path,encoding='utf-8').read()
    out={}
    for m in re.finditer(r'@(\w+)\{([^,]+),\n(.*?)\n\}\n', txt, re.S):
        typ,key,body=m.groups()
        f={}
        for fm in re.finditer(r'^\s*(\w+) = \{(.*?)\},?$', body, re.M): f[fm.group(1).lower()]=fm.group(2)
        if keep(key,f): out[key]=dict(type=typ,fields=f,raw=m.group(0))
    return out
def bib_surnames(author):
    names=[a.strip() for a in author.split(' and ') if a.strip()]
    return [fold(n.split(',')[0].strip().split()[-1]) if ',' in n else fold(n.split()[-1]) for n in names]
