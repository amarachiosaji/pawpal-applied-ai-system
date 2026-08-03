# PawPal+ - Applied AI System (Project 4)

## Base Project

This project extends **PawPal+ (Project 2, Module 2)**, a Streamlit app that helps
a pet owner plan daily care tasks for their pet(s). The original system let an
owner track tasks (walks, feeding, meds, grooming), set an availability window,
and generate a conflict-free daily schedule via a `Planner` class that handled
sorting (priority, then time), filtering, conflict detection, and recurring
tasks. It included a 19-test pytest suite and a Streamlit UI for adding pets,
tasks, and generating schedules.

## What's New: Retrieval-Augmented Generation (RAG)

PawPal+'s scheduler could tell you *when* to do a task, but had no way to tell
you anything about *how* to do it well. This project adds a RAG layer: a small
pet-care knowledge base, a TF-IDF retriever, and a guardrail that only surfaces
a care tip when the system is actually confident it found something relevant —
otherwise it says so, rather than guessing.

This is fully integrated into the existing `Planner`, not a bolted-on demo:
`Planner.generate_plan_with_context()` builds on the same `generate_plan()`
used everywhere else in the app, and the resulting tips appear in both the CLI
(`main.py`) and the Streamlit UI (`app.py`).

## Architecture

See [`diagrams/architecture.mmd`](diagrams/architecture.mmd) for the full
Mermaid source. In short:

User Input → Planner (collect/sort/detect conflicts/generate plan)
→ RAGRetriever.retrieve(task title + category + species)
→ Knowledge Base (TF-IDF vector space over knowledge/*.md)
→ similarity threshold check
├─ pass → tip + source + confidence score
└─ fail → "no specific guidance found"
→ CLI (main.py) and Streamlit UI (app.py)

The knowledge base (`knowledge/`) contains six markdown files covering dog
walking, cat grooming, feeding schedules, medication safety, senior pet care,
vet visits, and general hygiene. `rag_retriever.py` chunks each file into
paragraphs and builds a TF-IDF vector space over all chunks using character
n-grams (explained in Design Decisions below).

## Setup

```bash
git clone https://github.com/amarachiosaji/pawpal-applied-ai-system.git
cd pawpal-applied-ai-system
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the CLI demo
```bash
python main.py
```

### Running the Streamlit UI
```bash
python -m streamlit run app.py
```

### Running tests
```bash
python -m pytest
```

## Sample Interactions

### 1. CLI: Full daily plan with RAG-enriched tips

Running `python main.py` builds a schedule for two pets (Rex the dog, Luna
the cat) and enriches each task with retrieved guidance:

========================================
PLAN WITH CONTEXTUAL GUIDANCE (RAG)

Daily care plan with contextual guidance for Amarachi:
07:30 — Morning walk (30 min) [pet: Rex, priority: high]

💡 Tip (dog_walking.md): Morning and evening walks are generally preferable to midday walks in hot
climates, both to avoid pavement burns on paw pads and heat exhaustion....
08:00 — Feed & fresh water (10 min) [pet: Luna, priority: high]

💡 Tip (feeding_schedules.md): Always ensure fresh water is available at all times regardless of feeding
schedule — dehydration risk is separate from and just as important as
feedin...
09:00 — Vet appointment (30 min) [pet: Rex, priority: high]

💡 Tip (vet_visits.md): Adult dogs and cats generally benefit from an annual wellness exam, even when
they appear healthy, since many conditions (dental disease, early kidney...
09:30 — Grooming (30 min) [pet: Luna, priority: medium]

💡 Tip (cat_grooming.md): Senior cats and overweight cats often lose flexibility and struggle to groom
hard-to-reach spots like the lower back and hindquarters, making them pro...
18:00 — Dinner (15 min) [pet: Rex, priority: medium]

💡 Tip (feeding_schedules.md): Always ensure fresh water is available at all times regardless of feeding
schedule — dehydration risk is separate from and just as important as
feedin...
18:15 — Litter box cleaning (10 min) [pet: Luna, priority: low]

💡 Tip (pet_hygiene.md): Litter boxes should be scooped at least once daily, and ideally twice for
multi-cat households, since cats are prone to avoiding a dirty box entirely...


### 2. Streamlit UI: retrieved tip with confidence score

After adding a pet (Mochi, dog) and a "Morning walk" task, then clicking
**Generate schedule**, the UI shows an expandable care tip card:

Morning walk (Mochi)
Morning and evening walks are generally preferable to midday walks in hot
climates, both to avoid pavement burns on paw pads and heat exhaustion.
Source: dog_walking.md · confidence: 0.24

### 3. Guardrail in action: no confident match

For a nonsense query with no relevant content in the knowledge base, the
retriever correctly returns nothing rather than forcing a bad match:

Query: 'asdkjqwe nonsense gibberish'
No relevant guidance found.

## Design Decisions

- **Character n-grams over word-level TF-IDF.** The first retriever version
  used standard word-tokenized TF-IDF, which completely missed matches like
  "dog walking duration" against a knowledge base written with "dogs" and
  "walks" — plural/tense mismatches meant zero token overlap. Switching to
  `analyzer="char_wb", ngram_range=(3,5)` fixed this without needing a
  stemming library.
- **Threshold tuning was iterative, not a single guess.** An initial 0.1
  threshold let a wrong match through (a "vet appointment" query matching a
  generic feeding paragraph at 0.15). Raising to 0.18 fixed that but also
  rejected a legitimately correct "dog walking" match (0.136). The real fix
  was adding missing knowledge content (`vet_visits.md`, `pet_hygiene.md`)
  and trimming an overly broad chunk — after that, a lower 0.10 threshold
  preserved all correct matches without reintroducing bad ones.
- **Query construction: simpler was better.** An attempt to weight retrieval
  by repeating task category/species words in the query actually made
  results *worse* — it caused a walking task to match a feeding document
  because the literal word "exercise" happened to appear in a feeding
  paragraph. Reverted to the simpler `title + category + species` query.
- **Paragraph-level chunking.** Each knowledge doc is split on blank lines
  into paragraph chunks, small enough to be topically coherent but large
  enough to retain useful context per retrieval.

## Testing Summary

- **Original PawPal+ suite:** 19/19 tests passing (`tests/test_pawpal.py`),
  covering sorting, filtering, conflict detection, and recurrence.
- **RAG evaluation suite:** 9/9 tests passing (`tests/test_rag.py`), including
  7/7 sample queries retrieving the correct knowledge source, a guardrail
  test confirming no result is ever returned below the confidence threshold,
  and a documented gray-zone case (vet appointment queries sit near the
  threshold boundary).
- Full quantitative summary: **9/9 automated tests passed; 7/7 sample queries
  retrieved the correct knowledge source.** See `model_card.md` for what this
  process revealed about the retriever's real limitations.

