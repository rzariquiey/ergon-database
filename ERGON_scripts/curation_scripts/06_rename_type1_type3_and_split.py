#!/usr/bin/env python3
"""
Paso 1: Renombra los archivos de Tipo 1 y Tipo 3 al formato X_inicial=propuesto.
Paso 2: Crea subcarpetas 'correctos/' y 'por_revisar/' dentro de fichas_ergon/.
Paso 3: Mueve todos los archivos (xlsx, csv, pdf) a la subcarpeta correspondiente.

Criterio de 'por_revisar':
  - Tipo 1 (metadato inicial incorrecto): nucl1302, guan1266, kala1399, fass1245, gure1255, alba1269
  - Tipo 2 (VERIFICAR resueltos, ya renombrados con X_): ahin1234, aime1238, akun1241,
    amam1246, ango1257, bala1316, bamb1270, bara1357, bayb1234, bilb1241, boun1245,
    cuti1242, dhar1248, fran1266, gana1278, kara1476
  - Tipo 3 (errores graves VERIFICAR): dech1234, hual1240, aben1249, liji1238
  - Contaminación de plantilla (nombres de hoja incorrectos): caca1251, mati1255,
    mats1244, yami1258, dara1250, darl1243, darm1243
"""

import os
import shutil
import glob

FOLDER = '/sessions/compassionate-lucid-gauss/mnt/Ergon/fichas_ergon/'

# ─── PASO 1: Renombrado Tipo 1 y Tipo 3 ─────────────────────────────────────
# (gc_original, gc_propuesto, lengua, confianza)
TIPO1 = [
    ('nucl1302', 'geon1241', 'Georgian',           'alto'),     # PDF: hewitt_georgian; nucl1302 = Malagasy ≠ Georgian
    ('guan1266', 'wobz1235', 'Wobzi Khroskyabs',   'estimar'),  # PDF: lai_wobzi; guan1266 = Guanano ≠ Wobzi
    ('kala1399', 'kala1399', 'Kalaallisut',        'confirmado'),# kala1399 = Kalaallisut; mi ID inicial era errónea
    ('fass1245', 'momu1235', 'Momu',               'estimar'),  # PDF: momu grammar; fass1245 = Fassano ≠ Momu
    ('gure1255', 'gure1255', 'Gureng Gureng',      'confirmado'),# gure1255 = Gureng Gureng; mi ID inicial era errónea
    ('alba1269', 'alba1269', 'Bikol',              'confirmado'),# alba1269 = Albay Bikol; mi ID inicial era errónea
]

TIPO3_XLSX = [
    ('dech1234', 'dadi1250', 'Dadibi',   'alto'),    # Hoja dice dadi1250; contenido = Dadibi
    ('hual1240', 'lisu1250', 'Lisu',     'estimar'), # PDF: yu_lisu; hual1240 = Hualapai ≠ Lisu
    ('aben1249', 'aben1249', 'VERIFICAR','pendiente'),# Fuente: Nitsch 2009; lengua no identificada
]

TIPO3_CSV = [
    ('liji1238', 'migi1234', 'Migili', 'estimar'),   # PDF: stofberg_migili; liji1238 = Liji ≠ Migili
]

# ─── PASO 2: Conjuntos de glottocodes problemáticos ─────────────────────────
TIPO1_GC    = {t[0] for t in TIPO1}
TIPO2_GC    = {
    'ahin1234','aime1238','akun1241','amam1246','ango1257','bala1316',
    'bamb1270','bara1357','bayb1234','bilb1241','boun1245','cuti1242',
    'dhar1248','fran1266','gana1278','kara1476',
}
TIPO3_GC    = {t[0] for t in TIPO3_XLSX} | {t[0] for t in TIPO3_CSV}
PLANTILLA_GC = {'caca1251','mati1255','mats1244','yami1258',
                'dara1250','darl1243','darm1243'}

POR_REVISAR_GC = TIPO1_GC | TIPO2_GC | TIPO3_GC | PLANTILLA_GC


def rename_file(old_gc, new_gc, ext):
    """Renombra gc.ext → X_gc=propuesto.ext. Devuelve el nuevo nombre de archivo."""
    old_path = os.path.join(FOLDER, f'{old_gc}{ext}')
    new_name = f'X_{old_gc}={new_gc}{ext}'
    new_path = os.path.join(FOLDER, new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        return new_name
    else:
        print(f'  [NO ENCONTRADO] {old_gc}{ext}')
        return None


def step1_rename():
    print('═' * 60)
    print('PASO 1 — Renombrando Tipo 1 y Tipo 3')
    print('═' * 60)

    for (ini, prop, lengua, conf) in TIPO1:
        tag = '[ESTIMAR]' if conf == 'estimar' else '[OK]'
        new = rename_file(ini, prop, '.xlsx')
        marker = '(mismo código)' if ini == prop else f'→ {prop}'
        print(f'  {tag} TIPO1 {ini}.xlsx → {new}  [{lengua}] {marker}')

    for (ini, prop, lengua, conf) in TIPO3_XLSX:
        tag = '[ESTIMAR]' if conf == 'estimar' else '[ALTO]' if conf == 'alto' else '[PENDIENTE]'
        new = rename_file(ini, prop, '.xlsx')
        marker = '(mismo código)' if ini == prop else f'→ {prop}'
        print(f'  {tag} TIPO3 {ini}.xlsx → {new}  [{lengua}] {marker}')

    for (ini, prop, lengua, conf) in TIPO3_CSV:
        tag = '[ESTIMAR]'
        new = rename_file(ini, prop, '.csv')
        print(f'  {tag} TIPO3 {ini}.csv  → {new}  [{lengua}]')


def step2_split():
    print('\n' + '═' * 60)
    print('PASO 2 — Creando subcarpetas y moviendo archivos')
    print('═' * 60)

    dir_ok  = os.path.join(FOLDER, 'correctos')
    dir_rev = os.path.join(FOLDER, 'por_revisar')
    os.makedirs(dir_ok,  exist_ok=True)
    os.makedirs(dir_rev, exist_ok=True)

    all_files = [f for f in os.listdir(FOLDER)
                 if os.path.isfile(os.path.join(FOLDER, f))
                 and f.lower().endswith(('.xlsx', '.csv', '.pdf'))]

    n_ok = n_rev = 0
    for fname in sorted(all_files):
        fpath = os.path.join(FOLDER, fname)

        # Determinar glottocode base del archivo (ignorar prefijo X_ y sufijo =xxx)
        stem = fname.rsplit('.', 1)[0]          # sin extensión
        if stem.startswith('X_'):
            stem = stem[2:]                     # quitar "X_"
        base_gc = stem.split('=')[0]            # tomar parte antes del "="

        is_problematic = base_gc in POR_REVISAR_GC

        dest_dir = dir_rev if is_problematic else dir_ok
        shutil.move(fpath, os.path.join(dest_dir, fname))
        if is_problematic:
            n_rev += 1
        else:
            n_ok += 1

    return n_ok, n_rev


def main():
    step1_rename()
    n_ok, n_rev = step2_split()

    print(f'\n  → correctos/:   {n_ok} archivos')
    print(f'  → por_revisar/: {n_rev} archivos')

    # Verificación rápida
    print('\n' + '═' * 60)
    print('VERIFICACIÓN — Contenido de por_revisar/ (X_ files):')
    print('═' * 60)
    for f in sorted(os.listdir(os.path.join(FOLDER, 'por_revisar'))):
        if f.startswith('X_'):
            print(f'  {f}')

    print(f'\nTotal por_revisar/ (todos):',
          len(os.listdir(os.path.join(FOLDER, 'por_revisar'))))
    print(f'Total correctos/  (todos):',
          len(os.listdir(os.path.join(FOLDER, 'correctos'))))


if __name__ == '__main__':
    main()
