# Pearmut 🍐

**Platform for Evaluation and Reviewing of Multilingual Tasks** — Evaluate model outputs for translation and NLP tasks with support for multimodal data (text, video, audio, images) and multiple annotation protocols ([DA](https://aclanthology.org/N15-1124/), [ESA](https://aclanthology.org/2024.wmt-1.131/), [ESA<sup>AI</sup>](https://aclanthology.org/2025.naacl-long.255/), [MQM](https://doi.org/10.1162/tacl_a_00437), and more!).

[![PyPi version](https://badgen.net/pypi/v/pearmut/)](https://pypi.org/project/pearmut)
&nbsp;
[![PyPI download/month](https://img.shields.io/pypi/dm/pearmut.svg)](https://pypi.python.org/pypi/pearmut/)
&nbsp;
[![PyPi license](https://badgen.net/pypi/license/pearmut/)](https://pypi.org/project/pearmut/)
&nbsp;
[![build status](https://github.com/zouharvi/pearmut/actions/workflows/test.yml/badge.svg)](https://github.com/zouharvi/pearmut/actions/workflows/test.yml)

<img width="1000" alt="Screenshot of ESA/MQM interface" src="https://github.com/user-attachments/assets/4fb9a1cb-78ac-47e0-99cd-0870a368a0ad" />

## Table of Contents

- [Quick Start](#quick-start)
- [Campaign Configuration](#campaign-configuration)
  - [Basic Structure](#basic-structure)
  - [Assignment Types](#assignment-types)
  - [Protocol Templates](#protocol-templates)
- [Advanced Features](#advanced-features)
  - [Pre-filled Error Spans (ESA<sup>AI</sup>)](#pre-filled-error-spans-esaai)
  - [Tutorial and Attention Checks](#tutorial-and-attention-checks)
  - [Pre-defined User IDs and Tokens](#pre-defined-user-ids-and-tokens)
  - [Multimodal Annotations](#multimodal-annotations)
  - [Hosting Assets](#hosting-assets)
- [Campaign Management](#campaign-management)
- [CLI Commands](#cli-commands)
- [Development](#development)
- [Citation](#citation)

## Quick Start

Install and run locally without cloning:
```bash
pip install pearmut
# Download example campaigns
wget https://raw.githubusercontent.com/zouharvi/pearmut/refs/heads/main/examples/esa_encs.json
wget https://raw.githubusercontent.com/zouharvi/pearmut/refs/heads/main/examples/da_enuk.json
# Load and start
pearmut add esa_encs.json da_enuk.json
pearmut run
```

## Campaign Configuration

### Basic Structure

Campaigns are defined in JSON files (see [examples/](examples/)). The simplest configuration uses `task-based` assignment where each user has pre-defined tasks:
```python
{
  "info": {
    "assignment": "task-based",
    "template": "pointwise",
    "annotation_score": true,                 # we want scores [0...100] for each segment
    "annotation_error_spans": true,           # we want error spans
    "annotation_error_categories": false,     # we do not want error span categories
  },
  "campaign_id": "wmt25_#_en-cs_CZ",
  "data": [
    # data for first task/user
    [
      [
        # each evaluation item is a document
        {
          "instructions": "Evaluate translation from en to cs_CZ",  # message to show to users above the first item
          "src": "This will be the year that Guinness loses its cool. Cheers to that!",
          "tgt": "Nevím přesně, kdy jsem to poprvé zaznamenal. Možná to bylo ve chvíli, ..."
        },
        {
          "src": "I'm not sure I can remember exactly when I sensed it. Maybe it was when some...",
          "tgt": "Tohle bude rok, kdy Guinness přijde o svůj „cool“ faktor. Na zdraví!"
        }
        ...
      ],
      # more document
      ...
    ],
    # data for second task/user
    [
        ...
    ],
    # arbitrary number of users (each corresponds to a single URL to be shared)
  ]
}
```
Task items are protocol-specific. For ESA/DA/MQM protocols, each item is a dictionary representing a document unit:
```python
[
  {
    "src": "A najednou se všechna tato voda naplnila dalšími lidmi a dalšími věcmi.",  # required
    "tgt": "And suddenly all the water became full of other people and other people."  # required
  },
  {
    "src": "toto je pokračování stejného dokumentu",
    "tgt": "this is a continuation of the same document"
    # Additional keys stored for analysis
  }
]
```

Load campaigns and start the server:
```bash
pearmut add my_campaign.json  # Use -o/--overwrite to replace existing
pearmut run
```

### Assignment Types

- **`task-based`**: Each user has predefined items
- **`single-stream`**: All users draw from a shared pool (random assignment)
- **`dynamic`**: work in progress ⚠️

### Protocol Templates

- **Pointwise**: Evaluate single output against single input
  - `annotation_score`: Collect scores [0-100]
  - `annotation_error_spans`: Collect error span highlights
  - `annotation_error_categories`: Collect MQM category labels
- **Listwise**: Evaluate multiple outputs simultaneously
  - Same protocol options as pointwise

## Advanced Features

### Pre-filled Error Spans (ESA<sup>AI</sup>)

Include `error_spans` to pre-fill annotations that users can review, modify, or delete:

```python
{
  "src": "The quick brown fox jumps over the lazy dog.",
  "tgt": "Rychlá hnědá liška skáče přes líného psa.",
  "error_spans": [
    {
      "start_i": 0,         # character index start (inclusive)
      "end_i": 5,           # character index end (inclusive)
      "severity": "minor",  # "minor", "major", "neutral", or null
      "category": null      # MQM category string or null
    },
    {
      "start_i": 27,
      "end_i": 32,
      "severity": "major",
      "category": null
    }
  ]
}
```

For **listwise** template, `error_spans` is a 2D array (one per candidate). See [examples/esaai_prefilled.json](examples/esaai_prefilled.json).

### Tutorial and Attention Checks

Add `validation` rules for tutorials or attention checks:

```python
{
  "src": "The quick brown fox jumps.",
  "tgt": "Rychlá hnědá liška skáče.",
  "validation": {
    "warning": "Please set score between 70-80.",  # shown on failure (omit for silent logging)
    "score": [70, 80],                             # required score range [min, max]
    "error_spans": [{"start_i": [0, 2], "end_i": [4, 8], "severity": "minor"}],  # expected spans
    "allow_skip": true                             # show "skip tutorial" button
  }
}
```

**Types:**
- **Tutorial**: Include `allow_skip: true` and `warning` to let users skip after feedback
- **Loud attention checks**: Include `warning` without `allow_skip` to force retry
- **Silent attention checks**: Omit `warning` to log failures without notification (quality control)

For listwise, `validation` is an array (one per candidate). Dashboard shows ✅/❌ based on `validation_threshold` in `info` (integer for max failed count, float \[0,1\) for max proportion, default 0).
See [examples/tutorial_pointwise.json](examples/tutorial_pointwise.json) and [examples/tutorial_listwise.json](examples/tutorial_listwise.json).

### Single-stream Assignment

All annotators draw from a shared pool with random assignment:
```python
{
    "campaign_id": "my campaign 6",
    "info": {
        "assignment": "single-stream",
        "template": "pointwise",
        "annotation_score": True,                # collect scores
        "annotation_error_spans": True,          # collect error spans
        "annotation_error_categories": False,    # do not collect MQM categories, so ESA
        "users": 50,                           # number of annotators (can also be a list, see below)
    },
    "data": [...], # list of all items (shared among all annotators)
}
```


### Pre-defined User IDs and Tokens

The `users` field accepts:
- **Number** (e.g., `50`): Generate random user IDs
- **List of strings** (e.g., `["alice", "bob"]`): Use specific user IDs
- **List of dictionaries**: Specify custom tokens:
```python
{
    "info": {
        ...
        "users": [
            {"user_id": "alice", "token_pass": "alice_done", "token_fail": "alice_fail"},
            {"user_id": "bob", "token_pass": "bob_done"}  # missing tokens are auto-generated
        ],
    },
    ...
}
```

### Multimodal Annotations

Support for HTML-compatible elements (YouTube embeds, `<video>` tags, images). Ensure elements are pre-styled. See [examples/multimodal.json](examples/multimodal.json).

<img width="1000" alt="Preview of multimodal elements in Pearmut" src="https://github.com/user-attachments/assets/77c4fa96-ee62-4e46-8e78-fd16e9007956" />

### Hosting Assets

Host local assets (audio, images, videos) using the `assets` key:

```python
{
    "campaign_id": "my_campaign",
    "info": { 
      "assets": {
        "source": "videos",                    # Source directory
        "destination": "assets/my_videos"      # Mount path (must start with "assets/")
      }
    },
    "data": [ ... ]
}
```

Files from `videos/` become accessible at `localhost:8001/assets/my_videos/`. Creates a symlink, so source directory must exist throughout annotation. Destination paths must be unique across campaigns.

## CLI Commands

- **`pearmut add <file(s)>`**: Add campaign JSON files (supports wildcards)
  - `-o/--overwrite`: Replace existing campaigns with same ID
  - `--server <url>`: Server URL prefix (default: `http://localhost:8001`)
- **`pearmut run`**: Start server
  - `--port <port>`: Server port (default: 8001)
  - `--server <url>`: Server URL prefix
- **`pearmut purge [campaign]`**: Remove campaign data
  - Without args: Purge all campaigns
  - With campaign name: Purge specific campaign only

## Campaign Management

Management link (shown when adding campaigns or running server) provides:
- Annotator progress overview
- Access to annotation links
- Task progress reset (data preserved)
- Download progress and annotations

<img width="1000" alt="Management dashboard" src="https://github.com/user-attachments/assets/8953252c-d7b1-428c-a974-5bc7501457c7" />

Completion tokens are shown at annotation end for verification (download correct tokens from dashboard). Incorrect tokens can be shown if quality control fails.

<img width="500" alt="Token on completion" src="https://github.com/user-attachments/assets/40eb904c-f47a-4011-aa63-9a4f1c501549" />

### Model Results Display

Add `&results` to dashboard URL to show model rankings (requires valid token).
Items need `model` field (pointwise) or `models` field (listwise) and the `annotation_score` needs to be enable such that the `score` can be used for the ranking:
```python
{"doc_id": "1", "model": "CommandA", "src": "...", "tgt": "..."}
{"doc_id": "2", "models": ["CommandA", "Claude"], "src": "...", "tgt": ["...", "..."]}
```
See an example in [Campaign Management](#campaign-management)

## Development

Server responds to data-only requests from frontend (no template coupling). Frontend served from pre-built `static/` on install.

### Local development:
```bash
cd pearmut
# Frontend (separate terminal, recompiles on change)
npm install web/ --prefix web/
npm run build --prefix web/
# optionally keep running indefinitely to auto-rebuild
npm run watch --prefix web/

# Install as editable
pip3 install -e .
# Load examples
pearmut add examples/wmt25_#_en-cs_CZ.json examples/wmt25_#_cs-de_DE.json
pearmut run
```

### Creating new protocols:
1. Add HTML and TS files to `web/src`
2. Add build rule to `webpack.config.js`
3. Reference as `info->template` in campaign JSON

See [web/src/pointwise.ts](web/src/pointwise.ts) for example.

### Deployment

Run on public server or tunnel local port to public IP/domain and run locally.

## Misc.

If you use this work in your paper, please cite as following.
```bibtex
@misc{zouhar2025pearmut,
    author={Vilém Zouhar},
    title={Pearmut: Platform for Evaluating and Reviewing of Multilingual Tasks},
    url={https://github.com/zouharvi/pearmut/},
    year={2025},
}
```

Contributions are welcome! Please reach out to [Vilém Zouhar](mailto:vilem.zouhar@gmail.com).
