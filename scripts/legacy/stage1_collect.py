# Provenance script used once to prepare ERGON v1.1.0 from the v1.0.1 archive (see README.md in this folder).
# Paths refer to the working copies used at the time (v1.0.1 checkout; Grambank v1.0 and Glottolog 5.3 clones).
"""Collect legacy v1.0.1 material into one JSON for migration."""
import sys, json, csv, collections
sys.path.insert(0,'.')
from legacy_loader import *
cl_vals = list(csv.DictReader(open(REPO/'cldf/values.csv')))
cl_langs = {r['ID']:r for r in csv.DictReader(open(REPO/'cldf/languages.csv'))}
paths=collections.defaultdict(list)
for kind,stage,gc,p in all_sheets(): paths[gc].append((kind,stage,p))
paths['yami1258']=paths['yami1256']
out={}
for gc,L in cl_langs.items():
    kind={'ergative':'Ergative','non_ergative':'Non_ergative','problematic':'Problematic'}[L['Ergative_type']]
    cands=[x for x in paths[gc] if x[0]==kind] or paths[gc]
    cur=[x for x in cands if x[1]=='curated']; org=[x for x in paths[gc] if x[1]=='original']
    cur_recs = sheet_records(cur[0][2])[0] if cur else {}
    org_recs = sheet_records(org[0][2])[0] if org else {}
    vals={}
    for r in cl_vals:
        if r['Language_ID']!=gc or not r['Parameter_ID'].startswith('GB409_'): continue
        pid=r['Parameter_ID']
        c=cur_recs.get(pid,{}); o=org_recs.get(pid,{})
        vals[pid]=dict(value=r['Value'],source=(r['Source'].strip() or c.get('source','').strip() or o.get('source','').strip()),source_backfilled=not r['Source'].strip() and bool(c.get('source','').strip() or o.get('source','').strip()),comment=r['Comment'],
                       curated_comment=c.get('curated_comment',''),
                       original_value=o.get('value', c.get('orig_value','')),
                       original_comment=o.get('comment',''))
    out[gc]=dict(name=L['Name'],family=L['Family'],status=L['Ergative_type'],
                 sheet=str(cur[0][2].relative_to(REPO)) if cur else (str(org[0][2].relative_to(REPO)) if org else ''),
                 values=vals)
json.dump(out,open('legacy.json','w'),ensure_ascii=False,indent=1)
print(len(out))
