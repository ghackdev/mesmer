# JBFuzz Paper Example

This folder maps `2503.08990v1`, "JBFuzz: Jailbreaking LLMs Efficiently and
Effectively Using Fuzzing", onto Mesmer's generic iterative search primitives.

The implementation follows the paper's fuzzing lifecycle:

```text
initialize seed templates -> select seed -> mutate template -> query target
-> classify response -> update seed rewards -> stop on success
```

The reusable primitives live in `mesmer.search.fuzzing`; this example only
configures them for JBFuzz.

## Dataset Provenance

JBFuzz does not publish a dedicated dataset repository in the paper. It cites
GPTFuzz `[98]` for the 100 harmful questions and labeled response examples.
This example therefore uses pinned GPTFuzz raw URLs by default and records the
source details in `datasets.toml`.

The data is not copied into Mesmer. Runtime downloads are cached under
`.mesmer/`.

## Optional Dependencies

Mesmer core does not install NLP or ML dependencies by default. Install by
primitive capability:

The default example uses LLM-backed template mutation and embedding+MLP
evaluation, so install:

```bash
uv sync --extra embedding-classifier
```

If you choose the lexical mutator with `--mutator lexical`, install both extras
in one command:

```bash
uv sync --extra lexical-nlp --extra embedding-classifier
```

For the Hugging Face sequence classifier evaluator:

```bash
uv sync --extra hf-sequence-classifier
```

Or install all fuzzing-related extras:

```bash
uv sync --extra fuzzing
```

Important: pass all needed extras in the same `uv sync` command. Running one
extra and then another separately makes the environment match only the latest
command.

The optional lexical mutator automatically downloads missing NLTK data into
`.mesmer/nltk_data` on first use. For explicit preflight setup:

```bash
uv run python examples/papers/jbfuzz/run_jbfuzz.py --download-nltk-data --rows 1 --iterations 1
```

That command downloads to `.mesmer/nltk_data` by default. You can also install
the data directly:

```bash
uv run python -m nltk.downloader -d .mesmer/nltk_data wordnet omw-1.4 averaged_perceptron_tagger_eng
```

If a primitive is used without its dependency, it raises an explicit error with
the matching install command. It does not auto-install Python packages.

## Run

Default run with LLM-generated seeds, LLM template mutation, GPTFuzz questions,
and embedding+MLP evaluation:

```bash
export GEMINI_API_KEY=...
uv run python examples/papers/jbfuzz/run_jbfuzz.py --rows 1 --iterations 1 --branching-factor 1
```

For a lighter smoke run that avoids embedding training, use the LLM evaluator:

```bash
uv run python examples/papers/jbfuzz/run_jbfuzz.py \
  --rows 1 \
  --iterations 1 \
  --branching-factor 1 \
  --seed-mode builtin \
  --evaluator llm
```

Useful controls:

```bash
export MESMER_ATTACKER_MODEL=gemini/gemini-2.5-flash
export MESMER_EVALUATOR_MODEL=gemini/gemini-2.5-flash
export MESMER_TARGET_MODEL=gemini/gemini-2.5-flash
export MESMER_JBFUZZ_ROWS=1
export MESMER_JBFUZZ_ITERATIONS=10
export MESMER_JBFUZZ_BRANCHING_FACTOR=1
export MESMER_JBFUZZ_SELECTOR=weighted-random
export MESMER_JBFUZZ_SEED_MODE=llm
export MESMER_JBFUZZ_MUTATOR=llm
export MESMER_JBFUZZ_EVALUATOR=embedding-classifier
```

The paper's selected settings are represented by the defaults where practical:
weighted-random seed selection and the embedding evaluator. The JBFuzz paper
uses synonym/POS mutation with `p=0.25`; use `--mutator lexical` to reproduce
that ablation. The default `--mutator llm` is the developer-friendly Mesmer
composition because it preserves fluent templates. The paper reports
`intfloat/e5-base-v2` embeddings with a 3-layer MLP classifier; the script
exposes `--embedding-model` and `--mlp-hidden-sizes` because hidden sizes are
not specified in the PDF.
