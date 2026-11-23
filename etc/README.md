# etc/

| File | Content |
|---|---|
| `parameters.csv` | The 24 ERGON features: question, short name, domain, subdomain, paired context and Grambank parent feature. |
| `contributors.csv` | ERGON team (IDs used in `languages.csv`, columns `Coders` and `Reviewer`). |
| `glottolog_5.3_languoids.csv` | Snapshot of Glottolog 5.3 (glottolog/glottolog-cldf, tag v5.3, `cldf/languages.csv`) for the 196 ERGON languoids: name, level, language-level Glottocode, top-level family, macroarea, coordinates, ISO 639-3. Kept here so that the build is offline and deterministic. |
| `validation_exceptions.csv` | Documented exceptions to the logical checks in `scripts/validate.py`. |
| `status_short_reasons.csv` | One-line summary (LaTeX) of the reason for each `no-ergative-flagging` or `problematic` classification, used for Table 5 of the Data Descriptor. The full justification is `Status_comment` in `raw/languages.csv`. |
| `ne_110m_land.json` | Natural Earth 1:110m land polygons (public domain), used only to draw the map. |
