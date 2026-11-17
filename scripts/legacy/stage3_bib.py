# Provenance script used once to prepare ERGON v1.1.0 from the v1.0.1 archive (see README.md in this folder).
# Paths refer to the working copies used at the time (v1.0.1 checkout; Grambank v1.0 and Glottolog 5.3 clones).
import sys,csv,json,collections,re,unicodedata
sys.path.insert(0,'.')
from bibmatch import *
from cites import surnames
import pathlib as _p
ROOT=_p.Path(__file__).resolve().parents[2]
EXT=ROOT/'external'   # see 'make external'; glsrc = Glottolog 5.3 sources.bib
OUT=str(ROOT/'raw')+'/'
LC=json.load(open('lang_cites.json'))
G={r['ID']:r for r in csv.DictReader(open(EXT/'glottolog-cldf'/'cldf'/'languages.csv'))}
gbkeys=collections.defaultdict(set)
for r in csv.DictReader(open(EXT/'grambank'/'cldf'/'values.csv')):
    for k in re.findall(r'([^;\[]+)(?:\[[^\]]*\])?', r['Source']):
        if k.strip(): gbkeys[r['Language_ID']].add(k.strip())
allk=set().union(*gbkeys.values())
GB=parse_bib(EXT/'grambank'/'cldf'/'sources.bib', lambda k,f: k in allk)
# manual resolutions: (glottocode, author, year) -> ('gb', key) | ('gl', glottolog_ref_id) | ('manual', None), note
GLMAN={
 ('auye1238','Moxness','2011'):('gl','37733',''),
 ('ayiw1239','N�ss','2015'):('gl','556763','Two Næss (2015) publications on Äiwoo exist in Glottolog; the coding sheet does not say which was used. VERIFY.'),
 ('bara1357','Dhakal','2014'):('gl','586767',''),
 ('cash1251','Zariquiey','2018'):('gl','578861',''),
 ('cavi1250','Guillaume','2010'):('gl','518359',''),
 ('chan1313','Chor','2011'):('gl','469057',''),
 ('chep1245','Pons','2022'):('gl','666588',''),
 ('chuk1273','Kantarovich','2020'):('gl','587879',''),
 ('cuti1242','Queixalos','2007'):('gl','52048',''),
 ('dier1241','Austin','2021'):('gl','585921',''),
 ('diga1241','Jiang & Li & Sun','2013'):('gl','321507',''),
 ('dumi1241','Rai','2016'):('gl','576274',''),
 ('dyir1250','Dixon','2022'):('gl','660494',''),
 ('east2379','Henderson','2013'):('gl','694240','Cited by the curator (not in the original coding sheet).'),
 ('east2516','Yarapea','2013'):('gl','669241',''),
 ('fass1245','Honeyman','2016'):('gl','694415',''),
 ('iwam1256','Conrad','1993'):('gl','143348',''),
 ('kaga1256','Pebley & Macgregor','2024'):('gl','696246',''),
 ('kala1399','Sadock','2003'):('gl','115316',''),
 ('kara1476','McKelson','2004'):('gl','2965',''),
 ('lisu1250','Yu','2007'):('gl','311017',''),
 ('mais1250','Frampton','2020'):('gl','587141',''),
 ('mari1416','Kanshouwa','2016'):('gl','587878',''),
 ('mati1255','Fleck','2010'):('gl','85053',''),
 ('mats1244','Fleck','2010'):('gl','85053',''),
 ('namb1293','Kashima','2020'):('gl','587894',''),
 ('panj1256','Bashir & Conners','2019'):('gl','568752',''),
 ('pend1242','Quick','2008'):('gl','106287',''),
 ('ship1254','Valenzuela','2010'):('gl','542246',''),
 ('colu1241','Willet','2003'):('gb','g_Willett_Nxaamxcin','Author name misspelled in the coding sheet (Willet).'),
 ('djap1238','Murphy','1983'):('gb','g_Morphy_Djapu','Author name misspelled in the coding sheet (Murphy).'),
 ('limb1266','Direm','1987'):('gb','g_vanDriem_Limbu','Author name misspelled in the coding sheet (Direm).'),
 ('kamu1260','Routamma','1994'):('gb','s_Routamaa_Kamula','Author name misspelled in the coding sheet (Routamma).'),
 ('kara1487','Brainard','1993'):('gb','styp_Brainard_Karao','Cited as 1993 in the coding sheet; Grambank/Glottolog date this work to 1994. VERIFY.'),
 ('huas1242','Kondić','2012'):('gb','g_Kondic_Huastec',''),
 ('nucl1302','Hewitt','1990'):('gb','g_Hewitt_Georgian','Cited as Hewitt 1990 in the coding sheet; the page references match Hewitt (1995). VERIFY.'),
}
MANUAL={
 ('east2447','Henderson','2022'):'@misc{Henderson2022,\n    author = {Henderson, [VERIFY]},\n    year = {2022},\n    title = {[VERIFY: full reference of the East Futuna source cited as Henderson 2022]}\n}',
 ('iwam1256','Conrad','1999'):'@misc{Conrad1999,\n    author = {Conrad, Robert J. [VERIFY]},\n    year = {1999},\n    title = {[VERIFY: full reference of the Iwam source cited as Conrad 1999]}\n}',
}
need=set(GLMAN[k][1] for k in GLMAN if GLMAN[k][0]=='gl')
GL=parse_bib(EXT/'glsrc'/'sources.bib', lambda k,f: f.get('glottolog_ref_id') in need)
GLbyid={e['fields']['glottolog_ref_id']:(k,e) for k,e in GL.items()}
KEEP=['author','editor','year','title','booktitle','journal','volume','number','pages','series','publisher','address','school','howpublished','edition','note','doi','url','glottolog_ref_id']
def bibkey(e):
    a=e['fields'].get('author') or e['fields'].get('editor') or 'Anon'
    sn=re.sub(r'[^A-Za-z]','',fold(a.split(' and ')[0].split(',')[0]).title())
    y=re.sub(r'\D','',e['fields'].get('year',''))[:4]
    w=[x for x in re.findall(r'[A-Za-z]+',fold(e['fields'].get('title',''))) if len(x)>3 and x not in ('grammar','language','with','from','some','aspects','dialect')]
    return f"{sn}{y}{(w[0].title() if w else '')}"
def entry(key,e,extra_note=''):
    f=e['fields']; lines=[f'@{e["type"]}{{{key},']
    for k in KEEP:
        if k in f and f[k]: lines.append(f'    {k} = {{{f[k]}}},')
    lines[-1]=lines[-1].rstrip(',')
    return '\n'.join(lines)+'\n}'
entries={}; smap=[]; unresolved=[]
for g,cl in sorted(LC.items()):
    ll=(G[g]['Language_ID'] or g) if g in G else g
    cands=gbkeys.get(g,set())|gbkeys.get(ll,set())
    for a,y,n in cl:
        kind=None; note=''
        if (g,a,y) in GLMAN:
            kind,ref,note=GLMAN[(g,a,y)]
            if kind=='gb': e=GB[ref]; key=ref
            else: k0,e=GLbyid[ref]; key=bibkey(e)
        elif (g,a,y) in MANUAL:
            key=MANUAL[(g,a,y)].split('{')[1].split(',')[0]; entries[key]=MANUAL[(g,a,y)]; kind='manual'; note='Bibliographic record incomplete; VERIFY.'
            smap.append(dict(Glottocode=g,Citation=f'{a} {y}',BibKey=key,Match=kind,Note=note)); continue
        else:
            sn=[fold(s) for s in surnames(a)]
            for k in sorted(cands):
                e=GB.get(k)
                if not e: continue
                if y[:4] in e['fields'].get('year','') and sn and sn[0] in bib_surnames(e['fields'].get('author',e['fields'].get('editor',''))):
                    key=k; kind='gb'; break
        if not kind:
            unresolved.append((g,a,y)); continue
        if key not in entries: entries[key]=entry(key,e)
        smap.append(dict(Glottocode=g,Citation=f'{a} {y}',BibKey=key,Match={'gb':'Grambank v1.0 sources.bib','gl':'Glottolog 5.3 sources.bib'}.get(kind,kind),Note=note))
print('unresolved',unresolved)
with open(OUT+'sources.bib','w',encoding='utf-8') as f: f.write('\n\n'.join(entries[k] for k in sorted(entries))+'\n')
with open(OUT+'source_map.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['Glottocode','Citation','BibKey','Match','Note'],lineterminator='\n'); w.writeheader(); w.writerows(smap)
print(len(entries),'bib entries;',len(smap),'citations mapped')
