# ERGON

ERGON is a dataset on the distribution and conditioning of ergative flagging. It takes Grambank
feature GB409 ("Is there any ergative alignment of flagging?") and divides it into 24 binary
features (GB409_1 to GB409_24). These features record the nominal categories that show ergative
flagging, the clausal and semantic contexts in which it occurs, and the syncretism of the ergative
marker with the genitive and the instrumental or comitative. The values were coded from published
grammars and are released as a [CLDF](https://cldf.clld.org) StructureDataset.

Version 1.1.0. Data under CC BY 4.0, code under the MIT licence. The previous version (1.0.1) is
archived at Zenodo, https://doi.org/10.5281/zenodo.21107436.

## Contents

The dataset covers 196 languages (Glottolog 5.3). Of these, 164 have ergative flagging (34 families,
5 isolates, 5 macroareas). A further 22 languages are coded 1 for GB409 in Grambank but ergative
flagging was not confirmed in the sources (status `no-ergative-flagging`), and 10 languages could not be
classified (status `problematic`). There are 4,704 values, of which 4,197 are coded 0 or 1 and 507
are `?`. The values cite 201 references.

The folders are:

- `cldf/`: the dataset. Load `cldf/StructureDataset-metadata.json`.
- `raw/`: the coding sheets (one per language), the language list, the bibliography and the curation
  log, which lists every value that changed between versions 1.0.1 and 1.1.0.
- `etc/`: feature definitions, contributors and the Glottolog snapshot used for the build.
- `docs/`: the coding protocol and the list of automated checks.
- `scripts/`: build, validation and analysis scripts.
- `outputs/`: validation report, statistics, tables and figures of the Data Descriptor, and a copy of
  the data as a spreadsheet (`ERGON_v1.1.0.xlsx`).

## Features

| ID | Question |
|---|---|
| GB409_1 | Is there an overt marker for the absolutive? |
| GB409_2 | Is there ergative alignment of flagging on first person pronouns? |
| GB409_3 | Is there ergative alignment of flagging on second person pronouns? |
| GB409_4 | Is there ergative alignment of flagging on third person pronouns? |
| GB409_5 | Is there ergative alignment of flagging on full NPs? |
| GB409_6 | Is there ergative alignment of flagging in the imperfective aspect? |
| GB409_7 | Is there ergative alignment of flagging in the perfective aspect? |
| GB409_8 | Is there ergative alignment of flagging in the past tense? |
| GB409_9 | Is there ergative alignment of flagging in non-past tenses? |
| GB409_10 | Is there ergative alignment of flagging in the indicative mood? |
| GB409_11 | Is there ergative alignment of flagging in non-indicative moods? |
| GB409_12 | Is there ergative alignment of flagging in the realis status? |
| GB409_13 | Is there ergative alignment of flagging in the irrealis status? |
| GB409_14 | Is there ergative alignment of flagging in the context of an agentive A? |
| GB409_15 | Is there ergative alignment of flagging in the context of a non-agentive A? |
| GB409_16 | Is there ergative alignment of flagging in the context of a topical A? |
| GB409_17 | Is there ergative alignment of flagging in the context of a non-topical A? |
| GB409_18 | Is there ergative alignment of flagging in the context of an animate A? |
| GB409_19 | Is there ergative alignment of flagging in the context of an inanimate A? |
| GB409_20 | Is there ergative alignment of flagging in main clauses? |
| GB409_21 | Is there ergative alignment of flagging in non-main clauses? |
| GB409_22 | Is ergative alignment of flagging conditioned by any other factor? |
| GB409_23 | Are the ergative and the genitive expressed by the same marker? |
| GB409_24 | Are the ergative and the instrumental/comitative expressed by the same marker? |

A value of 1 means that the source documents ergative flagging in the context, 0 that it documents
its absence, and `?` that the source was consulted but does not allow a decision. The coding rules are
in `docs/coding_protocol.md`.

## Using the data

```python
from pycldf import Dataset
ds = Dataset.from_metadata('cldf/StructureDataset-metadata.json')
```

Analyses of ergative languages should use only the languages with `Status = ergative`. To combine ERGON
with Grambank or other datasets, use the column `Language_level_Glottocode` in `languages.csv`, since
ten entries are dialects in Glottolog.

## Rebuilding the dataset

```bash
pip install -r requirements.txt
make all
```

`make all` rebuilds `cldf/` from `raw/`, runs the checks described in `docs/validation_checks.md` and
regenerates `outputs/`. The comparison with Grambank, WALS, AUTOTYP and ATLAs needs these datasets,
which `make external` downloads.

## Citation

Zariquiey, R., Montoya, J., Gomez, L., Alvarado, C., Chau Príncipe, S., Lanasca-Moura, L., Almendra, A.,
Poblete, M., Vásquez-Aguilar, A., Greenhill, S. J. & Gray, R. D. ERGON (v1.1.0) [Data set]. Zenodo.
https://doi.org/10.5281/zenodo.24484168
