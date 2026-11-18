# ERGON: sub-features of ergative flagging for 196 languages

ERGON is a cross-linguistic dataset that expands Grambank feature GB409 (*Is there any ergative
alignment of flagging?*) into 24 binary sub-features (GB409_1–GB409_24). They record on which
nominal categories ergative flagging occurs, in which clausal and semantic contexts, and with
which other cases the ergative marker is syncretic. Values were coded from published
grammatical descriptions and are distributed as a [CLDF](https://cldf.clld.org) StructureDataset.

**Version 1.1.0** · Data licence CC BY 4.0 · Code licence MIT ·
Archive: Zenodo, v1.0.1 [doi:10.5281/zenodo.21107436](https://doi.org/10.5281/zenodo.21107436); v1.1.0 DOI assigned on deposit

| | |
|---|---|
| Languages | 196 (Glottolog 5.3 languoids) |
| – with ergative flagging (`Status = ergative`) | 164 languages, 34 families + 5 isolates, 5 macroareas |
| – Grambank GB409 = 1 but ergative flagging not confirmed (`non-ergative`) | 22 |
| – classification unresolved (`problematic`) | 10 |
| Features | 24 |
| Values | 4,704 (4,183 coded 0/1; 521 `?` = not known) |
| Sources | 201 references (`cldf/sources.bib`) |

## Repository layout

```
cldf/                 the dataset (CLDF StructureDataset) - this is what users should load
  StructureDataset-metadata.json
  languages.csv       language metadata (Glottolog 5.3), ERGON status and its justification, coders
  parameters.csv      the 24 features, with Domain / Subdomain / Paired_with columns
  codes.csv           code table (0 = no, 1 = yes)
  values.csv          one row per language x feature, with comment and page-level sources
  contributors.csv    team members
  sources.bib         bibliography
raw/                  harmonised sources from which cldf/ is built
  language_sheets/    one coding sheet per language (Parameter_ID, Value, Source, Comment)
  languages.csv       language list, status, coder/reviewer attribution
  sources.bib, source_map.csv   bibliography and citation-to-key mapping
  curation_log.csv    every value change between v1.0.1 and v1.1.0, with rule and rationale
  curation_history_v1_0.csv     changes made during expert curation before v1.0 (original coding -> v1.0 value)
  curation_notes.csv  language-level curation notes
etc/                  feature definitions, contributors, Glottolog snapshot, validation exceptions (none at present)
docs/                 coding protocol and description of the automated checks
scripts/              build, validation, technical validation, inter-coder reliability; legacy/ = one-off migration from v1.0.1
outputs/              validation report, statistics, tables and figures of the Data Descriptor,
                      and ERGON_v1.1.0.xlsx, a spreadsheet copy of the CLDF tables
intercoder/           sample and blank sheets for the inter-coder reliability study
```

## Features

| ID | Question | Domain | Subdomain |
|---|---|---|---|
| GB409_1 | Is there an overt marker for the absolutive? | Form of the marker | Absolutive marking |
| GB409_2 | Is there ergative alignment of flagging on first person pronouns? | Nominal category | Person/NP type |
| GB409_3 | Is there ergative alignment of flagging on second person pronouns? | Nominal category | Person/NP type |
| GB409_4 | Is there ergative alignment of flagging on third person pronouns? | Nominal category | Person/NP type |
| GB409_5 | Is there ergative alignment of flagging on full NPs? | Nominal category | Person/NP type |
| GB409_6 | Is there ergative alignment of flagging in the imperfective aspect? | Clausal context | Aspect |
| GB409_7 | Is there ergative alignment of flagging in the perfective aspect? | Clausal context | Aspect |
| GB409_8 | Is there ergative alignment of flagging in the past tense? | Clausal context | Tense |
| GB409_9 | Is there ergative alignment of flagging in non-past tenses? | Clausal context | Tense |
| GB409_10 | Is there ergative alignment of flagging in the indicative mood? | Clausal context | Mood |
| GB409_11 | Is there ergative alignment of flagging in non-indicative moods? | Clausal context | Mood |
| GB409_12 | Is there ergative alignment of flagging in the realis status? | Clausal context | Reality status |
| GB409_13 | Is there ergative alignment of flagging in the irrealis status? | Clausal context | Reality status |
| GB409_14 | Is there ergative alignment of flagging in the context of an agentive A? | Properties of A | Agentivity |
| GB409_15 | Is there ergative alignment of flagging in the context of a non-agentive A? | Properties of A | Agentivity |
| GB409_16 | Is there ergative alignment of flagging in the context of a topical A? | Properties of A | Topicality |
| GB409_17 | Is there ergative alignment of flagging in the context of a non-topical A? | Properties of A | Topicality |
| GB409_18 | Is there ergative alignment of flagging in the context of an animate A? | Properties of A | Animacy |
| GB409_19 | Is there ergative alignment of flagging in the context of an inanimate A? | Properties of A | Animacy |
| GB409_20 | Is there ergative alignment of flagging in main clauses? | Clausal context | Clause type |
| GB409_21 | Is there ergative alignment of flagging in non-main clauses? | Clausal context | Clause type |
| GB409_22 | Is ergative alignment of flagging conditioned by any other factor? | Other conditioning | Other |
| GB409_23 | Are the ergative and the genitive expressed by the same marker? | Form of the marker | Syncretism |
| GB409_24 | Are the ergative and the instrumental/comitative expressed by the same marker? | Form of the marker | Syncretism |

Values: `1` = yes, `0` = no, `?` = not known (insufficient information in the consulted sources).
In CLDF, `?` in the `Value` column is read as null by `pycldf`. The decision rules distinguishing
`0` from `?` are given in [docs/coding_protocol.md](docs/coding_protocol.md).

## Usage

```python
from pycldf import Dataset
ds = Dataset.from_metadata('cldf/StructureDataset-metadata.json')
for v in ds.iter_rows('ValueTable'):
    ...
```

To join ERGON with Grambank or other language-level datasets, use
`languages.csv:Language_level_Glottocode` (10 ERGON entries are Glottolog dialects).
Analyses of ergative languages should be restricted to `Status == "ergative"`.

## Reproducibility

```bash
pip install -r requirements.txt      # Python >= 3.10; tested with 3.13
make all                             # rebuild cldf/, run all checks, regenerate outputs/
make external && make analysis       # optional: also compare with Grambank, WALS, AUTOTYP and ATLAs
```

`make all` regenerates every file in `cldf/` and `outputs/`; the build is deterministic and works offline
(Glottolog metadata are read from the snapshot in `etc/`). The checks run by `scripts/validate.py`
are listed in [docs/validation_checks.md](docs/validation_checks.md).

## How to cite

Zariquiey, R., Montoya, J., Gomez, L., Alvarado, C., Chau Príncipe, S., Lanasca-Moura, L., Almendra, A.,
Poblete, M., Vásquez-Aguilar, A., Greenhill, S. J. & Gray, R. D. ERGON (v1.1.0) [Data set]. Zenodo.
https://doi.org/10.5281/zenodo.XXXXXXX <!-- VERIFY: DOI of the v1.1.0 record -->

Please also cite the Data Descriptor (in preparation) and, where relevant, the sources of individual values.
