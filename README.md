# ERGON: A Cross-Linguistic Database of Ergativity

[![CLDF](https://img.shields.io/badge/CLDF-StructureDataset-blue)](https://cldf.clld.org)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

ERGON is a typological database of ergativity covering **195 languages** and **24 binary features** (GB409_1–GB409_24) related to ergative case marking. The dataset is distributed in [CLDF](https://cldf.clld.org) format (StructureDataset).

## Features

The 24 parameters code ergative alignment of flagging across the following dimensions:

| ID | Description |
|----|-------------|
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

Values: `1` = yes, `0` = no, `?` = unknown/insufficient data.

## CLDF Structure

```
cldf/
├── StructureDataset-metadata.json   # CLDF metadata
├── languages.csv                    # 195 languages (Glottocode, Name, Family, Ergative_type)
├── parameters.csv                   # 24 features
└── values.csv                       # 4582 coded values
```

Languages are identified by [Glottocode](https://glottolog.org) and classified as **Ergative** or **Non-ergative** in the `Ergative_type` column.

## Data curation

Raw data files are stored in `ERGON_data/`. Ergative languages have a manually curated version (`*_curated.csv`) reviewed against the primary sources. The `Curated` column in `values.csv` indicates whether a value comes from a curated file.

## Rebuild

```bash
pip install pycldf
python3 build_cldf.py
python3 -m pycldf validate cldf/StructureDataset-metadata.json
```

## License

Data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
