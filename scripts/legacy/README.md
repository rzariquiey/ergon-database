# Legacy migration (v1.0.1 → v1.1.0)

These scripts were run **once** to convert the legacy coding sheets and the v1.0.1 CLDF
release (Zenodo 10.5281/zenodo.21107436, GitHub commit b93a06a) into the harmonised
sources in `raw/`. They are kept for provenance only; the regular build starts from
`raw/` (`make all`).

| Step | Script | Output |
|---|---|---|
| 1 | `stage1_collect.py` (uses `legacy_loader.py`) | one JSON file with all v1.0.1 values plus the original coding and curation notes from the legacy sheets |
| 2 | `migrate_v1_0_to_v1_1.py` | `raw/language_sheets/*.csv`, `raw/languages.csv`, `raw/curation_log.csv`, `raw/curation_history_v1_0.csv`, `raw/curation_notes.csv` |
| 3 | `stage3_bib.py` (uses `bibmatch.py`, `../citations.py`) | `raw/sources.bib`, `raw/source_map.csv` |
| 4 | `apply_review_2026_11.py` (inputs: the team's working sheets of the November 2026 review, kept by the authors; see the docstring) | updates `raw/language_sheets/`, `raw/languages.csv`, `raw/curation_log.csv`, `raw/source_map.csv`, `raw/sources.bib`, `etc/validation_exceptions.csv` |
| 5 | `rename_status_2026_11.py` | renames the status `non-ergative` to `no-ergative-flagging` in `raw/languages.csv` and rewords the notes that used it in `raw/curation_log.csv` and `raw/curation_history_v1_0.csv` |

Inputs that are not part of this repository: the v1.0.1 archive, Grambank v1.0
(`grambank/grambank`, `cldf/sources.bib`, `cldf/values.csv`), Glottolog 5.3
(`glottolog/glottolog-cldf` v5.3, `cldf/sources.bib`), and the team's working files, which
are kept by the authors: the English translations of the Spanish comments of v1.0.1 (step 2),
the assignment of coding sheets to team members in the 2026 review (source of the `Reviewer`
column) and the sheets of the November 2026 review (step 4).

Every value change between v1.0.1 and v1.1.0 is listed, with its rule and rationale,
in `raw/curation_log.csv`. The rules are:

| Rule | Meaning |
|---|---|
| G | Glottocode corrected (see `raw/languages.csv`, `Glottocode_note`) |
| S1 | Ergative flagging not confirmed after verification (status `no-ergative-flagging`); all sub-features set to 0 |
| V1 | Invalid code (`2`) recoded under coding rule C3 |
| M1 | Value absent from the v1.0.1 build added (as `?` = not coded, unless documented) |
| H1 | `?` → default value: source documents ergative flagging and no split along this dimension (rule C2) |
| H2 | Category not grammaticalised; invariant ergative flagging (rule C3) |
| H3 | Value inferred from areal/genealogical expectation, not from the source → `?` (rule C5) |
| H4 | Subset rule for GB409_5 (proper names flagged ergatively) |
| H5 | Logically impossible, unsourced pair of 0s → `?` |
| P1 | Optional A-only marking restored as ergative flagging (scope definition, §2 of docs/coding_protocol.md) |
| R1 | Recoded in the November 2026 review round against the source (step 4) |
