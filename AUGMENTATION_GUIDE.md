# Dataset Augmentation Guide

This guide explains how to install a local LLM with Ollama and generate
realistic, messy user prompts that map to existing CadQuery outputs using
`src/augment_dataset.py`.

## Quick Start

```bash
# 1) Install Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# 2) Pull a model (matches script default)
ollama pull llama3:8b

# 3) Verify the service is running
ollama serve &>/dev/null &  # if not already running
curl -s http://localhost:11434/v1/models | jq . # optional

# 4) Python deps
pip install "openai>=1.0.0" "tqdm>=4.0.0"

# 5) Run augmentation
python src/augment_dataset.py --limit 10
```

## What This Does

- Reads clean entries from `data/seed_dataset.jsonl`
- For each entry, generates multiple “messy” prompts that should produce the
  exact same CadQuery output
- Writes the original entry + all variations to `data/augmented_dataset.jsonl`

## Installing Ollama

### Linux (incl. WSL2)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama --version
```

If the service is not running automatically:

```bash
ollama serve
```

Keep this running in a terminal, or start it in the background with a process
manager (e.g., `systemctl --user enable --now ollama` on systems that support
it) or run `ollama serve &`.

### macOS

```bash
brew install ollama
ollama --version
ollama serve
```

### Windows

- Install Ollama from the official website or Microsoft Store, then ensure it is
  running.
- If you work inside WSL2, you can either:
  - run Ollama on Windows and access it from WSL2 at `http://localhost:11434`,
    or
  - install Linux Ollama inside WSL2 using the Linux instructions above.

## Pulling a Model

The augmentation script defaults to `llama3:8b`:

```bash
ollama pull llama3:8b
```

Alternative smaller model (faster, lower quality):

```bash
ollama pull phi3:mini
```

Ensure at least one model is available:

```bash
ollama list
```

## Python Environment

From your project root:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt || pip install "openai>=1.0.0" "tqdm>=4.0.0"
```

## Running the Augmentation

```bash
python src/augment_dataset.py --limit 50
```

- `--limit` limits how many source lines to process (use `-1` for all).
- The script writes outputs to `data/augmented_dataset.jsonl`.

By default, the script is configured as follows (see constants at the top of
`src/augment_dataset.py`):

- `SOURCE_FILE = "data/seed_dataset.jsonl"`
- `DESTINATION_FILE = "data/augmented_dataset.jsonl"`
- `MODEL_TO_USE = "llama3:8b"`
- `VARIATIONS_PER_ENTRY = 4`

## Customization

Edit `src/augment_dataset.py` to change:

- Model: set `MODEL_TO_USE = "phi3:mini"` (or any local model you pulled)
- Number of variations per entry: `VARIATIONS_PER_ENTRY = 4`
- Input/output files: `SOURCE_FILE`, `DESTINATION_FILE`

The script uses the OpenAI Python client pointed at Ollama’s OpenAI-compatible
endpoint:

```python
OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
```

No external OpenAI API key is required; the placeholder value is sufficient for
local use with Ollama.

## Troubleshooting

- Connection refused / timeout:
  - Ensure `ollama serve` is running and reachable at `http://localhost:11434`.
- Model not found:
  - Run `ollama pull llama3:8b` (or whichever model you configured).
- Very slow generations:
  - Try a smaller model (e.g., `phi3:mini`) or reduce
    `VARIATIONS_PER_ENTRY`.
- JSON parse warnings in the script output:
  - The script extracts a JSON array from the model response. If the model
    outputs extra text, a warning is printed and that variation is skipped. Try
    lowering temperature or using a more capable model.

## Performance Notes

- Larger models yield higher-quality variations but are slower and use more
  memory.
- The script sleeps briefly between requests to be gentle on the local server.

---

With Ollama running and a model pulled, you can quickly augment your dataset to
improve model robustness to typos, slang, and informal phrasing.


