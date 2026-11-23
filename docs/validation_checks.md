# Automated validation checks (`scripts/validate.py`)

Run with `make validate` (or `python scripts/validate.py`). Errors fail the build; warnings
are reported in `outputs/validation_report.md`.

| ID | Check | Severity |
|---|---|---|
| S0 | CLDF conformance (`pycldf` validation: schema, datatypes, primary and foreign keys, source references) | error |
| S1 | The parameter table contains exactly GB409_1–GB409_24 | error |
| S2 | Exactly one value per language and parameter (24 × number of languages) | error |
| S3 | Values restricted to `0`, `1`, `?` | error |
| S4 | Language IDs are well-formed Glottocodes present in Glottolog 5.3 at language or dialect level; coordinates present | error / warning |
| S5 | Every coded value (0/1) cites at least one source; every source key resolves in `sources.bib`; incomplete bibliographic records flagged | error / warning |
| L1 | A language with `Status = ergative` has at least one `1` among GB409_2–5 | error |
| L2 | For an ergative language, the two members of a context pair (perfective/imperfective, past/non-past, indicative/non-indicative, realis/irrealis, agentive/non-agentive, topical/non-topical, animate/inanimate, main/non-main) are not both `0` (unless listed in `etc/validation_exceptions.csv`) | error |
| L3 | A `no-ergative-flagging` language has `0` for all 24 features | error |
| L4 | Every `no-ergative-flagging` and `problematic` language has a `Status_comment` | error |
| C1 | Comments are in English (heuristic) | error |
| C2 | Comments contain no workflow notes (e.g. "researcher must", "TODO") | error |
| A1 | Every language has coder attribution | warning |
| I1 | Languages deviating from the referential-hierarchy implication 1st ≤ 2nd ≤ 3rd ≤ NP (information only; deviations are not errors) | info |

Manual checks are described in the Data Descriptor (Methods, Curation) and recorded value by
value in `raw/curation_log.csv` and `raw/curation_history_v1_0.csv`.
