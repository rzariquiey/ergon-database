"""
Build the ERGON CLDF StructureDataset directly with pycldf.
Run: python3 build_cldf.py
Output: cldf/
"""

import pathlib
import csv
import re

import pycldf

ROOT = pathlib.Path(__file__).parent
DATA_DIR = ROOT / "ERGON_data"
CLDF_DIR = ROOT / "cldf"
CLDF_DIR.mkdir(exist_ok=True)

FEATURE_DESCRIPTIONS = {
    "GB409_1":  "Is there an overt marker for the absolutive?",
    "GB409_2":  "Is there ergative alignment of flagging on first person pronouns?",
    "GB409_3":  "Is there ergative alignment of flagging on second person pronouns?",
    "GB409_4":  "Is there ergative alignment of flagging on third person pronouns?",
    "GB409_5":  "Is there ergative alignment of flagging on full NPs?",
    "GB409_6":  "Is there ergative alignment of flagging in the imperfective aspect?",
    "GB409_7":  "Is there ergative alignment of flagging in the perfective aspect?",
    "GB409_8":  "Is there ergative alignment of flagging in the past tense?",
    "GB409_9":  "Is there ergative alignment of flagging in non-past tenses?",
    "GB409_10": "Is there ergative alignment of flagging in the indicative mood?",
    "GB409_11": "Is there ergative alignment of flagging in non-indicative moods?",
    "GB409_12": "Is there ergative alignment of flagging in the realis status?",
    "GB409_13": "Is there ergative alignment of flagging in the irrealis status?",
    "GB409_14": "Is there ergative alignment of flagging in the context of an agentive A?",
    "GB409_15": "Is there ergative alignment of flagging in the context of a non-agentive A?",
    "GB409_16": "Is there ergative alignment of flagging in the context of a topical A?",
    "GB409_17": "Is there ergative alignment of flagging in the context of a non-topical A?",
    "GB409_18": "Is there ergative alignment of flagging in the context of an animate A?",
    "GB409_19": "Is there ergative alignment of flagging in the context of an inanimate A?",
    "GB409_20": "Is there ergative alignment of flagging in main clauses?",
    "GB409_21": "Is there ergative alignment of flagging in non-main clauses?",
    "GB409_22": "Is ergative alignment of flagging conditioned by any other factor?",
    "GB409_23": "Are the ergative and the genitive expressed by the same marker?",
    "GB409_24": "Are the ergative and the instrumental/comitative expressed by the same marker?",
}

VALID_PIDS = set(FEATURE_DESCRIPTIONS)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def is_glottocode(s):
    return bool(re.match(r"^[a-z]{4}\d{4}$", s.strip()))


def best_name_family(rows):
    for row in rows:
        n = row.get("Language", "").strip()
        f = row.get("Family", "").strip()
        if n and n != "VERIFICAR" and f and f != "VERIFICAR":
            return n, f
    if rows:
        return rows[0].get("Language", "").strip(), rows[0].get("Family", "").strip()
    return "", ""


# ── collect languages ────────────────────────────────────────────────────────
languages = {}

for p in sorted((DATA_DIR / "Ergative" / "curated").glob("*_curated.csv")):
    gc = p.stem.replace("_curated", "")
    if not is_glottocode(gc):
        continue
    rows = read_csv(p)
    name, family = best_name_family(rows)
    languages[gc] = dict(name=name, family=family, etype="Ergative", rows=rows, curated=True)

for p in sorted((DATA_DIR / "Ergative" / "original").glob("*.csv")):
    if p.name == "curation_report.csv":
        continue
    gc = p.stem
    if not is_glottocode(gc) or gc in languages:
        continue
    rows = read_csv(p)
    name, family = best_name_family(rows)
    languages[gc] = dict(name=name, family=family, etype="Ergative", rows=rows, curated=False)

for p in sorted((DATA_DIR / "Non_ergative" / "original").glob("*.csv")):
    gc = p.stem
    if not is_glottocode(gc):
        continue
    rows = read_csv(p)
    name, family = best_name_family(rows)
    languages[gc] = dict(name=name, family=family, etype="Non-ergative", rows=rows, curated=False)

# ── build values ─────────────────────────────────────────────────────────────
value_rows = []
vid = 0
for gc, lang in sorted(languages.items()):
    seen = set()
    for row in lang["rows"]:
        pid = row.get("Ergon_ID", "").strip()
        if pid not in VALID_PIDS or pid in seen:
            continue
        seen.add(pid)

        if lang["curated"]:
            raw = row.get("final_value", "").strip() or row.get("Value", "").strip()
            source = row.get("Source_comment", "").strip()
        else:
            raw = row.get("Value", "").strip()
            source = row.get("Source", "").strip()

        comment = row.get("Comment", "").strip()
        coded = raw if raw in ("0", "1", "?") else ("?" if raw else None)
        if coded is None:
            continue

        vid += 1
        value_rows.append(dict(
            ID=str(vid),
            Language_ID=gc,
            Parameter_ID=pid,
            Value=coded,
            Comment=comment,
            Source=source if source else "",
            Curated=str(lang["curated"]),
        ))

# ── write CLDF ───────────────────────────────────────────────────────────────
ds = pycldf.StructureDataset.in_dir(CLDF_DIR)

# languages.csv
with open(CLDF_DIR / "languages.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["ID", "Name", "Glottocode", "Family", "Ergative_type"])
    w.writeheader()
    for gc, lang in sorted(languages.items()):
        w.writerow(dict(ID=gc, Name=lang["name"], Glottocode=gc,
                        Family=lang["family"], Ergative_type=lang["etype"]))

# parameters.csv
with open(CLDF_DIR / "parameters.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["ID", "Name", "Description"])
    w.writeheader()
    for pid in sorted(VALID_PIDS, key=lambda x: int(x.split("_")[1])):
        w.writerow(dict(ID=pid, Name=pid, Description=FEATURE_DESCRIPTIONS[pid]))

# values.csv
with open(CLDF_DIR / "values.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["ID", "Language_ID", "Parameter_ID",
                                      "Value", "Comment", "Source", "Curated"])
    w.writeheader()
    w.writerows(value_rows)

# StructureDataset-metadata.json
import json
metadata = {
    "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
    "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#StructureDataset",
    "dc:title": "ERGON: A Cross-Linguistic Database of Ergativity",
    "dc:description": (
        "ERGON is a typological database covering 24 binary features (GB409_1–GB409_24) "
        "related to ergative case marking across approximately 200 languages worldwide."
    ),
    "dc:license": "https://creativecommons.org/licenses/by/4.0/",
    "tables": [
        {
            "url": "values.csv",
            "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#ValueTable",
            "tableSchema": {
                "columns": [
                    {"name": "ID", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#id"},
                    {"name": "Language_ID", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#languageReference"},
                    {"name": "Parameter_ID", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#parameterReference"},
                    {"name": "Value", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#value"},
                    {"name": "Comment", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#comment"},
                    {"name": "Source", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
                     "separator": ";"},
                    {"name": "Curated", "dc:description": "True if value comes from a manually curated file"}
                ],
                "foreignKeys": [
                    {"columnReference": "Language_ID",
                     "reference": {"resource": "languages.csv", "columnReference": "ID"}},
                    {"columnReference": "Parameter_ID",
                     "reference": {"resource": "parameters.csv", "columnReference": "ID"}}
                ]
            }
        },
        {
            "url": "languages.csv",
            "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#LanguageTable",
            "tableSchema": {
                "columns": [
                    {"name": "ID", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#id"},
                    {"name": "Name", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#name"},
                    {"name": "Glottocode", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#glottocode"},
                    {"name": "Family", "dc:description": "Top-level language family"},
                    {"name": "Ergative_type", "dc:description": "Ergative or Non-ergative classification in ERGON"}
                ]
            }
        },
        {
            "url": "parameters.csv",
            "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#ParameterTable",
            "tableSchema": {
                "columns": [
                    {"name": "ID", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#id"},
                    {"name": "Name", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#name"},
                    {"name": "Description", "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#description"}
                ]
            }
        }
    ]
}

with open(CLDF_DIR / "StructureDataset-metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"Done: {len(languages)} languages, {len(value_rows)} values, {len(VALID_PIDS)} parameters")
print(f"Output: {CLDF_DIR}/")
