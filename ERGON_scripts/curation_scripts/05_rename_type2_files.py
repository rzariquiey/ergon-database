#!/usr/bin/env python3
"""
Renombra los 16 archivos xlsx de Tipo 2 (VERIFICAR resueltos por PDF) al formato:
    X_glottocode_inicial=glottocode_corregido.xlsx

"glottocode_corregido" es el código Glottolog real de la lengua identificada.
Cuando el código del archivo ya era correcto, inicial == corregido.
Los casos marcados con [ESTIMAR] son estimaciones que el investigador debe verificar en Glottolog.
"""

import os
import openpyxl

FOLDER = '/sessions/compassionate-lucid-gauss/mnt/Ergon/fichas_ergon/'

# Mapeo: glottocode_inicial → (glottocode_corregido, lengua, confianza)
# Confianza: "confirmado" = mismo código, "alto", "estimar" = verificar en Glottolog
TIPO2 = {
    'ahin1234': ('kala1373', 'Kalanguya',           'estimar'),   # PDF: kalanguya grammar
    'aime1238': ('eibe1237', 'Eibela',               'estimar'),   # PDF: eibela grammar
    'akun1241': ('akun1241', 'Akuntsu',              'confirmado'), # akun1241 = Akuntsu en Glottolog
    'amam1246': ('amam1246', 'Amam',                 'confirmado'), # amam1246 = Amam en Glottolog
    'ango1257': ('uuwa1243', 'U\'wa',                'alto'),      # PDF: uwa grammar; ango1257 ≠ U'wa
    'bala1316': ('nele1239', 'Nêlêmwa',              'alto'),      # PDF: nelemwa; bala1316 = Balangao (distinto)
    'bamb1270': ('pitu1241', 'Pitu Ulunna Salu',     'estimar'),   # PDF: pitu grammar
    'bara1357': ('than1259', 'Thangmi',              'estimar'),   # PDF: thangmi grammar
    'bayb1234': ('utud1238', 'Utudnon',              'estimar'),   # PDF: utudnon grammar
    'bilb1241': ('bilb1241', 'Bilibili',             'confirmado'), # bilb1241 = Bilibili en Glottolog
    'boun1245': ('kuwa1244', 'Ku Waru',              'estimar'),   # PDF: ku waru grammar
    'cuti1242': ('katu1274', 'Katukina-Kanamari',    'estimar'),   # PDF: katukina grammar
    'dhar1248': ('dhar1248', 'Dharumbal',            'confirmado'), # dhar1248 = Dharumbal en Glottolog
    'fran1266': ('fran1266', 'Francisco León Zoque', 'confirmado'), # fran1266 = Zoque en Glottolog
    'gana1278': ('gana1278', 'Ganai',                'estimar'),   # PDF: ganai/ganalbingu — verificar
    'kara1476': ('kara1476', 'Karajarri',            'confirmado'), # kara1476 = Karajarri en Glottolog
}

def rename_and_report():
    renamed = []
    same_code = []
    errors = []

    for inicial, (corregido, lengua, confianza) in TIPO2.items():
        old_path = os.path.join(FOLDER, f'{inicial}.xlsx')
        new_name = f'X_{inicial}={corregido}.xlsx'
        new_path = os.path.join(FOLDER, new_name)

        if not os.path.exists(old_path):
            print(f'  [NO ENCONTRADO] {inicial}.xlsx')
            errors.append(inicial)
            continue

        try:
            os.rename(old_path, new_path)
            marker = '(mismo código)' if inicial == corregido else f'→ {corregido}'
            tag = '[ESTIMAR]' if confianza == 'estimar' else '[OK]'
            print(f'  {tag} {inicial}.xlsx → {new_name}  [{lengua}] {marker}')
            if inicial == corregido:
                same_code.append((inicial, lengua))
            else:
                renamed.append((inicial, corregido, lengua, confianza))
        except Exception as e:
            print(f'  [ERROR] {inicial}: {e}')
            errors.append(inicial)

    print(f'\n=== Resumen ===')
    print(f'  Archivos renombrados (código cambia): {len(renamed)}')
    for ini, cor, lng, conf in renamed:
        tag = '[ESTIMAR]' if conf == 'estimar' else ''
        print(f'    {ini} → {cor}  ({lng}) {tag}')
    print(f'  Archivos marcados con X (código confirmado, no cambia): {len(same_code)}')
    for ini, lng in same_code:
        print(f'    X_{ini}={ini}  ({lng})')
    if errors:
        print(f'  Errores: {len(errors)} — {errors}')

if __name__ == '__main__':
    rename_and_report()
