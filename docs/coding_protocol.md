# ERGON coding protocol (v1.1.0)

This document states the operational definitions and decision rules behind every value in
ERGON. It consolidates the coding guidelines used by the coders (Zariquiey & Montoya,
*ERGON: a granular coding of split ergativity based on GB409*, 2025) and the decisions
taken during curation. Section numbers are referred to in the Data Descriptor and in
`raw/curation_log.csv`.

## 1. Object of description: ergative alignment of flagging

* **Flagging** is argument marking on the argument itself: case affixes, case clitics,
  adpositions and particles attached to or phrasally associated with a noun phrase or a
  personal pronoun (Haspelmath 2019). The marker can be phonologically free or bound,
  overt or zero.
* **Indexing** is the marking of argument person/number on the predicate by bound person
  forms. Ergative alignment of indexing is *not* coded in ERGON, and neither is behavioural
  (syntactic) ergativity (pivots in coordination, relativisation, control, etc.).
* **Ergative alignment of flagging** holds in a given domain when the sole argument of an
  intransitive clause (S) is flagged like the patient-like argument of a transitive clause
  (P) and differently from the agent-like argument (A): S = P ≠ A. The comparison is made
  for the default (major) class of intransitive and transitive verbs.
* A language is classified as having ergative flagging (`Status = ergative`) if S = P ≠ A
  holds in at least one domain, i.e. for at least one nominal category (GB409_2–5) in at
  least one clausal context.

### 1.1 What does and does not count

| Pattern | Treatment |
|---|---|
| Ergative pattern restricted to some persons, NP types, TAM values, clause types, etc. (split ergativity) | In scope; the restriction is what the sub-features record. |
| **Optional ergative marking** (the A flag may be omitted under pragmatic or semantic conditions but never appears on S) | In scope: counts as ergative flagging. The conditioning is recorded in GB409_14–19/22 and in the comments. |
| Marker that also appears on S (agentive / "marked nominative" marker; e.g. Kamula *-ta*) | Not ergative flagging (S = A). |
| **Tripartite** domain (S ≠ A ≠ P) | Not ergative in that domain (S ≠ P): coded 0 for that nominal category. Note that Grambank GB409 asks only whether A ≠ S, so tripartite domains are 1 in Grambank but 0 in ERGON. |
| **Split-S / active-stative** flagging (A = S_a ≠ S_o = P) | Out of scope as *ergative flagging* when the default intransitive class patterns with A. Under a decompositional analysis (Witzlack-Makarevich et al. 2016) such systems contain an ergative sub-pattern for S_o; users interested in that analysis should use AUTOTYP or ATLAs (Align-11, Align-12). Languages with split-S flagging are classified `no-ergative-flagging` or `problematic`, with the reason in `Status_comment`. Minor intransitive classes with A-like or P-like marking inside an otherwise ergative system are recorded with GB409_22 = 1. |
| Hierarchical / inverse systems, voice-conditioned (Philippine-type, Salish) patterns | Coded as ergative only if the S = P ≠ A pattern can be established for flags on NPs or free pronouns; otherwise `problematic`. |
| Person forms on the verb (see §1.2) | Indexing; not coded. |

### 1.2 Pronouns, clitics and indexes

Features GB409_2–4 concern **personal pronouns that are in complementary distribution with
a coreferential noun phrase in the same clause**, whether phonologically free or clitic
(e.g. Philippine second-position pronominal clitics). Bound person forms that can co-occur
with a coreferential NP or free pronoun in the same clause (cross-indexing) are treated as
**indexes** and are not coded, whatever the source calls them ("ergative proclitics",
"absolutive enclitics", "actancial indices"). This criterion follows Haspelmath (2013)
and is the one used to recode Bugis and Pitu Ulunna Salu.

Case markers that are themselves clitics (phrasal enclitics such as Kakataibo *=nën*,
Jaminjung *=ni*) are flags: their bound status is irrelevant.

## 2. Values

| Value | Meaning |
|---|---|
| `1` | The consulted source(s) document ergative flagging in the context named by the feature (explicit statement or examples), or the default rule C2/C3 applies. |
| `0` | The source documents that ergative flagging does **not** occur in that context (statement, paradigm or examples with A flagged like S, or no flag at all), or the language has no ergative flagging at all. |
| `?` | **Not known**: the source was consulted but its description of argument marking in that context is insufficient to decide (no relevant examples, a possible but undescribed split, contradictory information). |

### 2.1 Decision rules for the context features (GB409_6–21)

* **C1 – explicit evidence.** Use the statement or examples in the source.
* **C2 – default when no split is documented.** When the source describes ergative
  flagging as a general property of the relevant nominal categories, describes argument
  marking in enough detail (a section on case and examples of transitive clauses), and
  mentions no restriction along the dimension in question, both members of the pair are
  coded `1`. This mirrors Grambank practice of relying on general statements in grammars.
  If the description of argument marking is too short to exclude a split, or the author
  hints at a possible conditioning factor without describing it, code `?`.
* **C3 – category not grammaticalised.** If the language lacks a grammatical category
  (e.g. no grammatical aspect, no realis/irrealis distinction), the contexts are identified
  semantically (clauses describing completed vs. ongoing events, etc.). If ergative flagging
  is invariant across these contexts, both members are coded `1`. A category's absence is
  never coded `0` or `?` on its own.
* **C4 – zero.** `0` requires positive evidence that ergative flagging is absent in that
  context (e.g. present-tense clauses with A unmarked like S in a tense-split language).
* **C5 – no inference from expectations.** Values may not be inferred from what is typical
  of the family or area. Such values found during curation were reset to `?` (rule H3 in
  `raw/curation_log.csv`).
* **Combination with other conditions.** If ergative flagging is restricted by some other
  condition (e.g. only in the past tense), a context feature is `1` if ergative flagging
  occurs in that context in *any* of the environments allowed by the other condition.
* **Pairs.** For a language with ergative flagging, at least one member of each context pair
  must be `1` or `?`. Documented exceptions would be listed in `etc/validation_exceptions.csv`; there are
  none in v1.1.0 (Apinajé, the former exception, was recoded from its source in the 2026 review round).

### 2.2 Notes on specific features

* **GB409_1 (overt absolutive):** a phonologically non-empty marker shared by S and P and
  distinct from the A flag, in any domain; suppletive ABS forms of free pronouns count.
* **GB409_2–5 (nominal categories):** code `1` if *any* subset of the category shows
  ergative flagging (e.g. only 1SG, only inclusive, only proper names); the subset is
  described in the comment. Number, gender and clusivity restrictions are therefore
  recoverable from the comments but not from separate features (planned for v2).
* **GB409_10–11 (mood)** concern sentence-type/mood paradigms (declarative/indicative vs.
  imperative, interrogative, optative, subjunctive…). **GB409_12–13 (reality status)**
  concern the realis/irrealis distinction (Mithun 1999; Michael 2014). In languages with a
  grammaticalised mood paradigm but no reality-status category (or vice versa), rule C3
  applies to the other pair. The two pairs are therefore highly correlated in the data and
  should not be treated as independent evidence.
* **GB409_14–15 (agentivity):** agentive A = volitional, instigating participant (Næss 2007);
  experiencers of psych verbs and natural forces/instruments in A function count as
  non-agentive A.
* **GB409_16–17 (topicality):** topical A = an A that the source identifies as topic,
  given/anaphoric, definite or pivot/trigger, or that occurs in the topic position; the
  binary coding records whether ergative flagging occurs with such A's (16) and with A's
  that are not (17). Gradient topicality effects are described in the comments.
* **GB409_18–19 (animacy):** humanness effects are coded here and described in the comments.
* **GB409_20–21 (clause type):** non-main clauses include complement, relative and adverbial
  clauses and grammatical nominalisations.
* **GB409_22 (other conditioning):** `1` if a factor not covered by GB409_2–21 conditions
  ergative flagging (verb class, properties of P, number, word order, …); `0` if the source's
  description of argument marking is detailed and mentions no other factor; `?` otherwise.
* **GB409_23–24 (syncretism):** `1` if the A flag is identical to, or shares allomorphs with,
  the genitive (23) or the instrumental or comitative (24), or if the source states that one
  derives from the other. Other syncretisms (e.g. with ablative or locative) are noted in
  the comments.

## 3. Language status

| Status | Definition | Values |
|---|---|---|
| `ergative` | Ergative flagging attested for at least one nominal category (at least one `1` in GB409_2–5). | coded as above |
| `no-ergative-flagging` | Language sampled because Grambank codes GB409 = 1, but no ergative flagging (as defined in §1) after verification against the source. The label refers to flagging only; ergative patterns in indexing or elsewhere are not excluded. | all `0` |
| `problematic` | Classification unresolved (conflicting descriptions, voice-conditioned or split-S systems, insufficient evidence). Excluded from all analyses of ergative languages. | as coded; to be read with `Status_comment` |

## 4. Sources and provenance

Each value cites the source(s) and pages used (`Source`, BibTeX keys with page ranges) and the
citation as written by the coder (`Source_comment`). For 118 coded values the coding sheet did
not record a page; these cite the principal source of the language without pages and say so in
`Source_comment`. The bibliography (`sources.bib`) was resolved against Grambank v1.0 and
Glottolog 5.3 (`raw/source_map.csv`).

## References

Haspelmath, M. 2013. Argument indexing: a conceptual framework for the syntactic status of bound person forms. In D. Bakker & M. Haspelmath (eds.), *Languages across boundaries*, 197–226. De Gruyter Mouton.
Haspelmath, M. 2019. Indexing and flagging, and head and dependent marking. *Te Reo* 62(1), 93–115.
Michael, L. 2014. The Nanti reality status system. *Linguistic Typology* 18(2), 251–288.
Mithun, M. 1999. *The languages of native North America*. Cambridge University Press.
Næss, Å. 2007. *Prototypical transitivity*. John Benjamins.
Witzlack-Makarevich, A., Zakharko, T., Bierkandt, L., Zúñiga, F. & Bickel, B. 2016. Decomposing hierarchical alignment: co-arguments as conditions on alignment and the limits of referential hierarchies as explanations in verb agreement. *Linguistics* 54(3), 531–561.
