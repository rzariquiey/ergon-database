#!/usr/bin/env python3
"""
Add Glottocode, Language, and Family columns to all CSV fichas in fichas_ergon/.
The three new columns are inserted at the beginning (before Ergon_ID).
"""

import os
import csv
import glob
import re
import io

FOLDER = '/sessions/compassionate-lucid-gauss/mnt/Ergon/fichas_ergon/'

# Complete GLOTTOLOG lookup for all 38 CSV glottocodes
# Language names and families identified from PDF filenames and Glottolog training knowledge
GLOTTOLOG_CSV = {
    'lamj1247': ('Lamjung Yolmo',       'Trans-Himalayan'),    # Gawne 2016
    'lemb1266': ('Lembena',             'Trans-New Guinea'),   # Heineman 1998
    'lepc1244': ('Lepcha',              'Trans-Himalayan'),    # Plaisier 2007
    'lezg1247': ('Lezgian',             'Nakh-Daghestanian'),  # Haspelmath 1993
    'lihi1237': ('Lihir',               'Austronesian'),       # Neuhaus 2015
    'liji1238': ('VERIFICAR',           'VERIFICAR'),          # PDF: Migili (stofberg 1978); revisar glottocode
    'limb1266': ('Limbu',               'Trans-Himalayan'),    # van Driem 1987
    'limo1248': ('Limos Kalinga',       'Austronesian'),       # Ferreirinho 1993
    'lipo1242': ('Lipo',                'Trans-Himalayan'),    # No PDF; Tibeto-Burman (Yunnan)
    'lush1249': ('Mizo',                'Trans-Himalayan'),    # Chhangte 1986 (Mizo/Lushai)
    'lush1252': ('Lushootseed',         'Salishan'),           # Zahir 2018
    'macu1259': ('Macushi',             'Cariban'),            # Carson 1982 (Macuxi)
    'madn1237': ('Matngele',            'Daly'),               # Zandvoort 1999
    'maga1263': ('Mag-anchi Agta',      'Austronesian'),       # Kitano & Pangilinan 2003
    'mail1248': ('Magi',                'Trans-New Guinea'),   # Thomson 1975
    'mais1250': ('Maisin',              'Trans-New Guinea'),   # Frampton 2020
    'mana1288': ('Manange',             'Trans-Himalayan'),    # Hildebrandt 2004
    'mang1381': ('Mangarayi',           'Gunwinyguan'),        # Merlan 1989
    'mang1405': ('Manggarai',           'Austronesian'),       # Semiun 1993
    'maor1246': ('Maori',               'Austronesian'),       # Harlow 2007
    'mara1378': ('Marathi',             'Indo-European'),      # Dhongde & Wali 2009
    'mara1379': ('Maram Naga',          'Trans-Himalayan'),    # Singh 1984
    'mara1404': ('Maranao',             'Austronesian'),       # McKaughan & Macaraya 1967
    'marg1253': ('Margany',             'Pama-Nyungan'),       # Breen 1981 (Margany-Gunya)
    'mari1416': ('Maring',              'Trans-New Guinea'),   # Kanshouwa 2016
    'mari1424': ('Marrithiyel',         'Daly'),               # Green 1989
    'masb1238': ('Masbatenyo',          'Austronesian'),       # Rosero 2014
    'maxa1247': ('Maxakalí',            'Maxakalían'),         # Campos 2009
    'mayk1239': ('Mayi-Kulan',          'Pama-Nyungan'),       # Breen 1981
    'melp1238': ('Melpa',               'Trans-New Guinea'),   # Berthold 2008
    'mono1273': ('Mono-Alu',            'Austronesian'),       # Fagan 1986 / Meier 2020
    'moro1289': ('Marori',              'Trans-New Guinea'),   # Arka 2012
    'munc1235': ('Mün Chin',            'Trans-Himalayan'),    # Mang 2006 (K\'cho Chin)
    'muru1266': ('Muruwari',            'Pama-Nyungan'),       # Oates (Muruwari language)
    'nalc1240': ('Nalca',               'Trans-New Guinea'),   # Svard 2013
    'namb1293': ('Nmbo',                'Trans-New Guinea'),   # Kashima 2020
    'naru1238': ('Narungga',            'Pama-Nyungan'),       # Eira 2010
    'natc1249': ('Natchez',             'Natchez'),            # Kimball 2005 (language isolate)
}


def add_columns_to_csv(filepath, glottocode, lang, family):
    """Insert Glottocode, Language, Family as the first three columns of a CSV file."""
    # Read the original file (handle BOM if present)
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        content = f.read()

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        print(f'  [EMPTY] {os.path.basename(filepath)}')
        return False

    new_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            # Header row
            new_rows.append(['Glottocode', 'Language', 'Family'] + row)
        else:
            # Data rows: add values if the row has any non-empty content
            if any(cell.strip() for cell in row):
                new_rows.append([glottocode, lang, family] + row)
            else:
                # Blank rows: prepend empty cells
                new_rows.append(['', '', ''] + row)

    # Write back (UTF-8 without BOM, Windows-compatible line endings)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    return True


def main():
    csv_files = sorted(glob.glob(FOLDER + '*.csv'))
    print(f'Found {len(csv_files)} CSV files.\n')

    ok = 0
    verif = 0
    err = 0

    for fpath in csv_files:
        stem = os.path.basename(fpath).replace('.csv', '')
        # Extract glottocode from filename
        m = re.search(r'[a-z]{4}[0-9]{4}', stem)
        gc = m.group(0) if m else stem

        if gc not in GLOTTOLOG_CSV:
            lang, fam = f'VERIFICAR ({gc})', 'VERIFICAR'
            print(f'  [NO DICT] {stem} → {gc}')
            verif += 1
        else:
            lang, fam = GLOTTOLOG_CSV[gc]
            if 'VERIFICAR' in lang:
                verif += 1

        try:
            success = add_columns_to_csv(fpath, gc, lang, fam)
            if success:
                status = 'VERIFICAR' if 'VERIFICAR' in lang else 'OK'
                print(f'  [{status}] {stem} → {gc} | {lang} | {fam}')
                ok += 1
        except Exception as e:
            print(f'  [ERROR] {stem}: {e}')
            err += 1

    print(f'\n=== Resultado ===')
    print(f'  Procesados: {ok}')
    print(f'  VERIFICAR:  {verif}')
    print(f'  Errores:    {err}')


if __name__ == '__main__':
    main()
