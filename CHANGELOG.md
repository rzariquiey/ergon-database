# Changelog

## 1.1.0 (2026-10, revision for *Scientific Data*)

Single, harmonised source format, rebuilt CLDF, automated validation, and regenerated
statistics, tables and figures. Every value change is listed in `raw/curation_log.csv`.

### Data
- **Language status.** Six languages released as ergative in v1.0.1 had no ergative flagging on any nominal
  category after verification and are now `non-ergative` (all values 0): Bugis (bugi1244), Pitu Ulunna Salu
  (bamb1270), Kamula (kamu1260), Iaai (iaai1238), Karajá (kara1500), Karitiana (kari1311). Four entries
  coded from a single description of Lisu (Yu 2007), which describes split-S flagging, are now `problematic`:
  Lisu (lisu1250), Lipo (lipo1242), Lisu Dechang (dech1234), Lisu Central/Lipo (hual1240).
  Totals: 167 ergative, 19 non-ergative, 10 problematic.
- **Glottocodes.** caca1251 (invalid) → cash1251 (Kakataibo); yami1258 (invalid) → yami1256 (Yaminawa);
  bala1316 → kuma1276 (the coded source, Bril 2002, describes Nêlêmwa).
- **Invalid and missing values.** Two values coded `2` (Kabardian GB409_12–13) and a spurious parameter `all`
  (Nhanda) removed; 20 values missing from the v1.0.1 build (Mparntwe Arrernte) added.
- **Coding harmonisation** under the explicit rules of `docs/coding_protocol.md` (C2: default when no split is
  documented; C3: grammatical category absent; C5: no inference from areal expectations); see rules H1–H5, P1, V1.
- **Optional ergative marking** counts as ergative flagging (Futuna-Aniwa GB409_5 restored to 1).
- **Comments** translated into English (91 comments), workflow notes removed from value comments;
  language-level notes moved to `raw/curation_notes.csv`.
- **Sources.** Free-text citations resolved to a BibTeX bibliography (201 references) and given as
  CLDF source references with pages; citation as written by the coder kept in `Source_comment`.
- **Metadata.** Language names, families, macroareas and coordinates from Glottolog 5.3 for all languages;
  `Language_level_Glottocode` for joins with Grambank; `Status_comment` for every non-ergative/problematic
  language; parameter `Domain`, `Subdomain`, `Paired_with`; code table; contributors table; coder/reviewer columns.

### Repository
- Legacy folders (`ERGON_data/` with duplicate CSV/XLSX/TXT files, `etc/` working files, `latex*/`, `presentation/`)
  are not part of the release; they remain available in v1.0.1 (Zenodo) and in the git history.
- New: `scripts/validate.py` (automated checks, `docs/validation_checks.md`), `scripts/technical_validation.py`
  (all numbers, tables and figures of the Data Descriptor), `scripts/intercoder_reliability.py`, `Makefile`,
  pinned `requirements.txt`, MIT licence for code.

## 1.0.1 (2026-07)
Zenodo release accompanying the first submission (doi:10.5281/zenodo.21107436).
