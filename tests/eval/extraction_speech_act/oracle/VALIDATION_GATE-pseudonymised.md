<!-- DERIVED COPY — NOT THE FROZEN ARTIFACT -->

> **This is a PSEUDONYMISED COPY of `paper2/freeze/VALIDATION_GATE.md`, published
> so a reviewer can verify 0038 §6b's claims about the gate this spec does NOT
> meet.**
>
> * **The frozen original is UNCHANGED and is not this file.** Its sha256 is
>   `a11755dbe4c82362b2b60e9e35bb0806486ad275ba71f446cef6ce580d10bed1`
>   (sha16 `a11755dbe4c82362`). Anyone holding the original can verify this copy by
>   applying the single transformation below and re-digesting.
> * **The only change: 3 occurrence(s) of the owner's given name → "the project
>   owner".** The gate names him in the RATER role (§1, "one labeller … blind"),
>   which is exactly the role the owner's 2026-09-07 pseudonymisation ruling
>   covers. Nothing else is altered — not a threshold, not a requirement, not a
>   word of §1's blindness condition.
> * **A frozen document cannot be edited to suit a later publication**, so it is
>   not edited: the freeze stays intact and this copy declares itself a copy.
>   *(A digest names a copy, not a filename.)*

---

# §8 semantic-label validation — acceptance gate, frozen

*A5, 2026-08-03. Closes review finding 6. §8 required agreement "by relation
class" and repair of ambiguous probes, but froze no threshold — so it was a
measurement exercise, not a gate. Frozen here before either labeller's results
are examined.*

---

## 1. Labellers

- **Human:** one labeller (the project owner), blind — intended labels stripped, items
  shuffled under seed `20260801`, opaque ids assigned **after** shuffling.
- **Model:** `gpt-4.1-2025-04-14`, temperature 0.0, max_tokens 60, the rubric
  copied **verbatim** from `validation/PACK.md`, single attempt, no retry on a
  parseable reply; an unparseable reply is retried **once** then recorded
  `unparsed`. **Already executed 2026-08-01**; 104/104 parsed.

**The model pass ran before this gate was written.** That is disclosed rather
than hidden: its configuration was fixed and recorded at the time, and it
labels *probe semantics*, not system outcomes, so it exposes nothing about any
evaluated system.

## 2. Statistic

- **Per relation class** (`equivalent`, `entails`, `overlapping`, `distinct`):
  **one-vs-rest Cohen's κ**, human against model.
- **Reported alongside κ in every case:** the confusion matrix, raw agreement,
  and n. *(κ alone conceals arm heterogeneity — the finding of our own JUDGe
  work, applied to ourselves.)*
- **Computed BEFORE adjudication**, on first-pass labels.

## 3. Thresholds

| | |
|---|---|
| **class passes** | one-vs-rest κ **≥ 0.60** *and* n ≥ 10 in that class |
| **class fails** | κ < 0.60, or n < 10 |
| **corpus gate** | **every class must pass** |

**A failing class does not fail the corpus** — it triggers §4's repair on that
class only.

## 4. Item-level ambiguity and repair

- An item is **ambiguous** if the human labelled it `ambiguous`, **or** human
  and model disagree **and** the project owner, re-reading blind to both, declines to
  choose.
- **Ambiguous → DISCARDED**, not rewritten. Rewriting an item after seeing that
  it was contested is how a corpus acquires the labels its author expected.
- A disagreement the project owner resolves on re-reading is **relabelled to the resolved
  value**, and the resolution is logged with both original labels.

## 5. Attrition cap

**≤ 10% of the 104 pairs (≤ 10 items) may be discarded.** Above that, the
corpus is regenerated rather than pruned — a corpus that loses more than a tenth
of its pairs to ambiguity has a generator problem, not an item problem.

## 6. Cell-balance preservation

**A discard removes the semantic pair from every cell it appears in**, so the
48-cell matrix stays balanced at a lower per-cell n. **Per-cell n must remain
equal across cells**, and **no discard may reduce the §7.2 mandatory set below
72 probes**; if it would, the mandatory pair is regenerated rather than
discarded.

## 7. Re-registration

**After repair the corpus is regenerated, re-hashed, and the new hashes recorded
as a §15 amendment** with the discard list and the reason for each. The
pre-repair hashes remain in the record.

## 8. Prediction, recorded before κ is computed

Per A2: the **`numeric` form on non-functional relations** will show the lowest
class agreement. **Recorded before the statistic exists so it cannot be claimed
afterwards.**
