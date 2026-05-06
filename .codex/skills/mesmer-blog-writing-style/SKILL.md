---
name: mesmer-blog-writing-style
description: Write Mesmer-facing blog posts, research notes, docs essays, and launch-style articles in the Mesmer project voice. Use when drafting or editing Mesmer content that should explain AI safety, LLM red-team, jailbreak research, prompt patterns, reproducible experiments, or Mesmer architecture with a practical, story-led engineering tone instead of generic marketing or academic summary.
---

# Mesmer Blog Writing Style

## Core Voice

Write as Mesmer, not as a detached paper summarizer. The voice is practical, curious, and engineering-minded. It should feel like the team is explaining a hard topic through concrete evidence, not promoting Mesmer as the main subject.

Use a natural Indonesian-engineer English rhythm where it helps the writing feel human: direct explanations, occasional conversational bridges, and simple phrasing. Keep it readable and professional; do not intentionally add grammar mistakes.

Prefer "we" only when it is natural for a project post. Use "I" only when the article is explicitly a personal essay. Do not make the post feel personal unless the user asks for a personal essay. For Mesmer blog posts, the author is usually "Mesmer AI".

## Article Shape

Start from a concrete situation before theory. A small example, product problem, experiment trace, or surprising behavior should open the article before introducing paper terminology.

Use the story logic from *Talk Like TED* at a high level: open with a concrete moment, make the reader care emotionally and intellectually, teach one memorable new idea, use contrast or surprise, keep a conversational rhythm, and end with a useful takeaway. Do not copy the book's wording; apply the presentation principles to technical writing.

Move in this order:

1. Concrete observation.
2. Why the observation matters.
3. The research idea or technical concept.
4. A practical experiment or implementation consequence, with Mesmer used as the code vehicle when relevant.
5. What we learned and where readers can inspect more.

Avoid turning posts into setup tutorials unless the user explicitly asks for a guide. For Mesmer research posts, show the experiment shape and observations, then link readers to GitHub for commands and source code. Do not over-promote Mesmer in the prose; discuss the topic, paper, concept, or failure mode first. Mesmer should appear naturally in code examples, reproducibility notes, and the final GitHub invitation.

## Tone Rules

- Explain hard concepts with small analogies and plain language.
- Use rhetorical questions when transitioning into a new idea.
- Let curiosity and slight unease appear when the topic is surprising or risky.
- Prefer normal paragraphs with two to four connected sentences. Avoid excessive one-line paragraphs unless the line is a deliberate beat, quote, or transition.
- Use phrases like "the problem is", "the interesting part is", "to be clear", "in this case", "so", and "that is the scary part" when they fit naturally.
- Avoid corporate launch language, heavy hype, and "this solves everything" framing.
- Avoid over-polishing into native-speaker marketing prose; keep some directness and learning-in-public texture.
- Use headings, blockquotes, figures, and lists intentionally. Do not leave long stretches that look like raw paragraphs without visual rhythm, but also do not break every sentence into its own paragraph.
- When including code, prefer real runnable examples over pseudo schemas. The code should be readable and directly tied to the concept being explained.
- Assume readers may not know Mesmer internals. Do not explain internal library mechanics unless they are necessary to understand the concept. Make code declarative enough that readers can infer the idea from names and structure.

## Research Post Guidance

When explaining a paper, use the paper as a lens. Do not make the post a chapter-by-chapter summary.

Do not overload the article with paper metrics, tables, and exact rates. Use numbers only when they materially change the reader's understanding. The default should be: explain the concept clearly, mention the paper's empirical direction in plain language, and let readers open the paper for full quantitative details.

For each paper idea:

- State the idea in plain language.
- Connect it to a small example.
- Explain the experiment consequence without sounding like a product pitch. It is fine to say that a concept can become a prompt pattern, transform, evaluator, or replay artifact, but keep the paper topic as the center of gravity.
- Be clear about responsible boundaries: do not publish actionable harmful payloads; use redaction for sensitive prompts and responses.
- In Mesmer code examples, prefer explicit prompt-pattern IDs such as `paper.jailbroken.competing_objectives` over broad implicit selectors such as generic tags. Explicit IDs make the paper concept visible without requiring readers to know the prompt library internals.

## Content Quality Guardrails

- If a post uses a meme, screenshot, or concrete example as the hook, explain the real subtext of that artifact. Do not flatten it into a generic example.
- If discussing jailbreaks, avoid publishing operational harmful payloads. Use harmless canaries, redactions, or authorized boundary tests.
- Code blocks should not visually look like nested cards. If the docs renderer wraps code blocks, avoid adding another heavy frame through custom CSS.
- End with an invitation to inspect the GitHub repository when useful, but do not turn the ending into marketing copy.

For style observations from existing ghack.dev posts, read `references/source-style-notes.md` when drafting or heavily editing a post.
