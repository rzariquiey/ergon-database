"""
cldfbench build script for the ERGON dataset.

Source data:
  ERGON_data/Ergative/curated/<glottocode>_curated.csv  — preferred source
  ERGON_data/Ergative/original/<glottocode>.csv         — fallback
  ERGON_data/Non_ergative/original/<glottocode>.csv     — non-ergative languages

CLDF output (StructureDataset):
  cldf/languages.csv   — one row per language
  cldf/parameters.csv  — one row per feature (GB409_1 … GB409_24)
  cldf/values.csv      — one row per language × feature
  cldf/sources.bib     — bibliography
"""

import pathlib
import csv
import re
import collections

import cldfbench


DATA_DIR = pathlib.Path(__file__).parent / "ERGON_data"

# Which column to use as the final coded value
CURATED_VALUE_COL = "final_value"
ORIGINAL_VALUE_COL = "Value"

# Feature descriptions extracted from the data files
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

VALID_FEATURE_IDS = set(FEATURE_DESCRIPTIONS.keys())


def _read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _is_valid_glottocode(code):
    return bool(re.match(r"^[a-z]{4}\d{4}$", str(code).strip()))


def _collect_language_info(rows, glottocode):
    """Return (name, family) from the first row with valid data."""
    for row in rows:
        name = row.get("Language", "").strip()
        family = row.get("Family", "").strip()
        if name and name != "VERIFICAR" and family and family != "VERIFICAR":
            return name, family
    # Fall back to whatever is there
    if rows:
        return rows[0].get("Language", "").strip(), rows[0].get("Family", "").strip()
    return "", ""


def _ergative_flag(glottocode):
    """Return 'Ergative' or 'Non-ergative' for a given Glottocode."""
    curated = DATA_DIR / "Ergative" / "curated" / f"{glottocode}_curated.csv"
    original_erg = DATA_DIR / "Ergative" / "original" / f"{glottocode}.csv"
    if curated.exists() or original_erg.exists():
        return "Ergative"
    return "Non-ergative"


def _collect_all_sources():
    """Scan all data files and collect (source_key, raw_citation) pairs."""
    seen = {}
    for csv_path in sorted(DATA_DIR.rglob("*_curated.csv")):
        for row in _read_csv(csv_path):
            src = row.get("Source_comment", "").strip()
            if src:
                key = re.sub(r"[^a-zA-Z0-9_]", "", src)[:40]
                if key and key not in seen:
                    seen[key] = src
    for csv_path in sorted(DATA_DIR.rglob("original/*.csv")):
        if csv_path.name == "curation_report.csv":
            continue
        for row in _read_csv(csv_path):
            src = row.get("Source", "").strip()
            if src:
                key = re.sub(r"[^a-zA-Z0-9_]", "", src)[:40]
                if key and key not in seen:
                    seen[key] = src
    return seen


class Dataset(cldfbench.Dataset):
    metadata_cls = cldfbench.Metadata
    dir = pathlib.Path(__file__).parent

    def cldf_specs(self):
        return cldfbench.CLDFSpec(
            dir=self.cldf_dir,
            module="StructureDataset",
        )

    def cmd_makecldf(self, args):
        with self.cldf_writer(args) as writer:
            self._build(writer)

    def _build(self, writer):
        ds = writer.cldf

        # ── add extra columns ──────────────────────────────────────────────
        ds["LanguageTable"].tableSchema.columns.append(
            {"name": "Family", "datatype": "string"}
        )
        ds["LanguageTable"].tableSchema.columns.append(
            {"name": "Ergative_type", "datatype": "string",
             "dc:description": "Whether the language is classified as Ergative or Non-ergative in ERGON"}
        )
        ds["ValueTable"].tableSchema.columns.append(
            {"name": "Comment", "datatype": "string"}
        )
        ds["ValueTable"].tableSchema.columns.append(
            {"name": "Curated", "datatype": "boolean",
             "dc:description": "True if the value comes from a manually curated file"}
        )

        # ── parameters ────────────────────────────────────────────────────
        for pid in sorted(FEATURE_DESCRIPTIONS, key=lambda x: int(x.split("_")[1])):
            ds.add_component("ParameterTable")
            writer["ParameterTable"].append({
                "ID": pid,
                "Name": pid,
                "Description": FEATURE_DESCRIPTIONS[pid],
            })

        # ── collect language data ─────────────────────────────────────────
        # Map glottocode → {name, family, ergative_type, rows}
        languages = {}

        # 1. Curated ergative files (highest priority)
        for csv_path in sorted((DATA_DIR / "Ergative" / "curated").glob("*_curated.csv")):
            glottocode = csv_path.stem.replace("_curated", "")
            if not _is_valid_glottocode(glottocode):
                continue
            rows = _read_csv(csv_path)
            name, family = _collect_language_info(rows, glottocode)
            languages[glottocode] = {
                "name": name,
                "family": family,
                "ergative_type": "Ergative",
                "rows": rows,
                "curated": True,
            }

        # 2. Original ergative files (fallback for languages without curated version)
        for csv_path in sorted((DATA_DIR / "Ergative" / "original").glob("*.csv")):
            if csv_path.name == "curation_report.csv":
                continue
            glottocode = csv_path.stem
            if not _is_valid_glottocode(glottocode):
                continue
            if glottocode in languages:
                continue  # already have curated version
            rows = _read_csv(csv_path)
            name, family = _collect_language_info(rows, glottocode)
            languages[glottocode] = {
                "name": name,
                "family": family,
                "ergative_type": "Ergative",
                "rows": rows,
                "curated": False,
            }

        # 3. Non-ergative files
        for csv_path in sorted((DATA_DIR / "Non_ergative" / "original").glob("*.csv")):
            glottocode = csv_path.stem
            if not _is_valid_glottocode(glottocode):
                continue
            rows = _read_csv(csv_path)
            name, family = _collect_language_info(rows, glottocode)
            languages[glottocode] = {
                "name": name,
                "family": family,
                "ergative_type": "Non-ergative",
                "rows": rows,
                "curated": False,
            }

        # ── write languages ───────────────────────────────────────────────
        for glottocode, lang in sorted(languages.items()):
            ds["LanguageTable"].append({
                "ID": glottocode,
                "Name": lang["name"],
                "Glottocode": glottocode,
                "Family": lang["family"],
                "Ergative_type": lang["ergative_type"],
            })

        # ── write values ──────────────────────────────────────────────────
        value_id = 0
        for glottocode, lang in sorted(languages.items()):
            seen_features = set()
            for row in lang["rows"]:
                pid = str(row.get("Ergon_ID", "")).strip()
                if pid not in VALID_FEATURE_IDS:
                    continue
                if pid in seen_features:
                    continue
                seen_features.add(pid)

                # Choose value column
                if lang["curated"]:
                    raw_val = str(row.get(CURATED_VALUE_COL, "")).strip()
                    if not raw_val:
                        raw_val = str(row.get(ORIGINAL_VALUE_COL, "")).strip()
                    source = str(row.get("Source_comment", "")).strip()
                    comment = str(row.get("Comment", "")).strip()
                else:
                    raw_val = str(row.get(ORIGINAL_VALUE_COL, "")).strip()
                    source = str(row.get("Source", "")).strip()
                    comment = str(row.get("Comment", "")).strip()

                # Normalize value: accept 0/1/?, skip empty
                if raw_val in ("0", "1", "?"):
                    coded_value = raw_val
                elif raw_val == "":
                    continue
                else:
                    coded_value = "?"

                value_id += 1
                ds["ValueTable"].append({
                    "ID": str(value_id),
                    "Language_ID": glottocode,
                    "Parameter_ID": pid,
                    "Value": coded_value,
                    "Comment": comment,
                    "Curated": lang["curated"],
                    "Source": [source] if source else [],
                })

        args.log.info(
            f"Written {len(languages)} languages and {value_id} values."
        )
