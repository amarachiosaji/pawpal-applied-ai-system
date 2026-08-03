# Model Card: PawPal+ RAG Layer

## What This Component Does

A TF-IDF-based retriever (`rag_retriever.py`) that searches a small,
hand-written pet-care knowledge base and returns a relevant tip for a
scheduled task, or explicitly declines to answer if nothing clears a
confidence threshold.

## Limitations and Biases

- **No semantic understanding.** TF-IDF matches on literal character overlap,
  not meaning. During testing, a single broad paragraph mentioning both
  "dogs" and "cats" and "meals" out-scored more specific, topically precise
  paragraphs simply because it shared more surface vocabulary with a wider
  range of queries. A semantic embedding model would likely handle this
  better, at the cost of needing external dependencies/API calls.
- **Knowledge base coverage is incomplete and hand-authored by me.** It only
  covers six topics (dog walking, cat grooming, feeding, medication, senior
  care, vet visits, hygiene). Task categories outside this scope will always
  fall back to "no guidance found" — this is a coverage gap, not a smart
  system recognizing its own limits.
- **No threshold cleanly separates good from bad matches.** Testing showed
  overlapping score ranges: a correct match (0.168) and a plausible-but-wrong
  match (0.144) for different queries sat close enough together that no
  single cutoff handled both cases perfectly. The current threshold (0.10)
  was chosen empirically based on this project's specific test queries and
  may not generalize to a larger knowledge base.
- **Content is general veterinary/care guidance, not verified medical
  advice**, and should not be treated as a substitute for an actual
  veterinarian, especially for the medication and health-related content.

## Could This Be Misused?

The main risk is a user treating a retrieved "tip" as authoritative pet-care
or medical guidance rather than general informational content, particularly
around `medication_safety.md`. Mitigation: the system always shows its source
file and confidence score alongside any tip, rather than presenting it as an
unattributed, confident answer — this is why the guardrail and source
citation were treated as required features, not nice-to-haves.

## What Surprised Me During Testing

The biggest surprise was that my own attempted "fix" (repeating task category
and species words in the retrieval query to weight them more heavily) made
results measurably *worse*, not better — it caused "Morning walk" (an
exercise task) to incorrectly match a feeding document, because the word
"exercise" happened to appear verbatim inside an unrelated feeding paragraph.
I only caught this by re-running the same test queries after the change and
comparing scores directly, rather than assuming the change was safe because
it seemed logical. It reinforced that with TF-IDF, any change to query
construction needs to be empirically re-tested against the full query set,
not reasoned about in the abstract.

## AI Collaboration

I used Claude throughout this project to plan the architecture, debug
retrieval issues, and iterate on the RAG implementation.

**Helpful suggestion:** When my first retriever version completely missed
"dog walking duration" against my own `dog_walking.md` file, Claude correctly
diagnosed it as a word-tokenization mismatch (singular "dog" vs. plural
"dogs" in the source text) and suggested switching to character n-grams
(`analyzer="char_wb", ngram_range=(3,5)`), which fixed the issue without
needing a separate stemming library.

**Flawed suggestion:** Claude's suggestion to repeat task category/species
terms in the query to weight them more heavily actually broke two previously
correct matches (Morning walk, Grooming) by diluting the query vector and
accidentally triggering an unrelated keyword collision. This was only caught
because we re-ran the debug script after the change instead of assuming it
worked — a good reminder that AI-suggested "improvements" still need to be
verified against real output, not accepted on the strength of the
explanation alone.

## Reliability Summary

9/9 automated tests passed (`tests/test_rag.py`). 7/7 sample queries
retrieved the correct knowledge source. Two categories (vet appointments,
litter box hygiene) required adding new knowledge content after initial
testing revealed they had no matching documents. Threshold tuning went
through three values (0.18 → 0.15 → 0.10) before settling on one that
preserved all known-correct matches without reintroducing known-bad ones.