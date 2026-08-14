# Project 2 — HTML textbook preprocessing for RAG

`data-preprocessing.ipynb` converts the local *Lessons In Electric Circuits — Volume I (DC)* HTML mirror into structured data for a future RAG application.

## Project purpose

The purpose of this project is to prepare an electronics textbook for a Retrieval-Augmented Generation (RAG) system. The problem is that raw HTML is difficult to search reliably: it contains navigation controls, layout markup, long sections, and images mixed with the educational text. This project cleans that source, preserves its chapter and section context, and creates searchable JSON chunks with metadata. The resulting data can later be embedded and retrieved to help an AI answer electronics questions using the textbook as its source.

## What the preprocessing does

1. Loads every `*.html` file from `data/DC-html-vol-1`.
2. Inspects the legacy HTML before parsing it. The relevant structure is chapter `h1` headings, section/subsection `h2`/`h3` headings, paragraphs, lists, and images.
3. Excludes the navigation-only index page and Previous / Contents / Next image controls. It preserves the 16 chapters and three appendices.
4. Builds section-level documents before chunking. Each document keeps chapter, section, optional subsection, ordered content blocks, source location, and images.
5. Represents every educational image with its original location, local path, source URL, optional alt text, a future `description` field, and an in-text `[IMAGE: ...]` placeholder. No OCR or multimodal embedding is used in this first version.
6. Conservatively normalizes whitespace while retaining formulas, units, punctuation, and paragraph boundaries.
7. Keeps small semantic sections intact. Only large sections are split at content-block boundaries with an approximate 75-token overlap. Every chunk repeats volume/chapter/section context so it is understandable when retrieved independently.
8. Validates section/chunk counts, token estimates, images, empty or very short chunks, navigation-only chunks, and duplicate text before export.

## Outputs

Run the notebook from the `Project_2` directory. It creates:

- `data/processed/chunks.json` — a readable JSON array.
- `data/processed/chunks.jsonl` — one JSON chunk per line for ingestion tools.

Each chunk includes a stable ID, contextual text, source metadata, image metadata, and an estimated token count. The current token estimator is intentionally model-agnostic; it should be swapped for the eventual embedding model's tokenizer before applying a strict production token limit.

## Learning notes

The notebook is ordered as a guided preprocessing exercise: load, inspect, clean, parse structure, inspect intermediate documents, chunk, validate, then export. The “Try it yourself” cells point out what to check at each stage and why the parser makes each choice.
