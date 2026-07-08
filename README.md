# BIOL 40B — Lab Practical 1 Trainer

A browser-based practice **lab practical** for BIOL 40B, Labs 1–4 (Nervous System & Special Senses).
It mirrors the real exam: you're shown a specimen as if under the microscope and must **type** what's
indicated by the target — or name the slide itself. Spelling counts. Missed items keep coming back until
every one is cleared, then you can run the whole thing again.

**Play it:** open `index.html` (or the GitHub Pages link).

## What it covers
- **Identify the indicated structure** — a target marks a structure on the slide; type its name (56 structures).
- **Name the slide** — identify the whole specimen / tissue (14 slides).
- **Cranial nerves** — numbers, names, and function, CN I–XII (recall).

Slides: peripheral nerve (osmium), spinal cord #27 & #28, cerebellum #30, cerebrum #31,
neuromuscular junction #25, lip #53, monkey eye #36, and the motor neuron enhanced view.

## How it works
- **Strict spelling.** Answers are graded after normalizing case/punctuation and accepting legitimate
  synonyms (e.g. *grey / gray*, *dorsal / posterior*). A near-miss gets one "check your spelling" nudge,
  then it's marked wrong.
- **Retry until mastery.** Anything you miss is re-queued into the next round. You keep going, round by
  round, until nothing is left — then "Take it again" reshuffles the full set.

## Structure
| File | Purpose |
|------|---------|
| `index.html` | page structure |
| `styles.css` | histology/microscopy visual identity, light + dark |
| `app.js` | exam engine: grading, spelling tolerance, retry-until-mastery loop |
| `questions.js` | generated slide/pin bank |
| `facts.js` | cranial-nerve recall bank |
| `images/` | clean specimen images |
| `build/` | extraction pipeline (PyMuPDF) that pulled label-free slides and pin coordinates from the course PDFs |

*Study aid — not for distribution. Specimen images are from the course histology decks.*
