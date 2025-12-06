# Pearmut 🍐

Pearmut is a **Platform for Evaluation and Reviewing of Multilingual Tasks**.
It evaluates model outputs, primarily translation but also various other NLP tasks.
Supports multimodality (text, video, audio, images) and a variety of annotation protocols ([DA](https://aclanthology.org/N15-1124/), [ESA](https://aclanthology.org/2024.wmt-1.131/), [ESA<sup>AI</sup>](https://aclanthology.org/2025.naacl-long.255/), [MQM](https://doi.org/10.1162/tacl_a_00437), paired ESA, etc).

[![PyPi version](https://badgen.net/pypi/v/pearmut/)](https://pypi.org/project/pearmut)
&nbsp;
[![PyPI download/month](https://img.shields.io/pypi/dm/pearmut.svg)](https://pypi.python.org/pypi/pearmut/)
&nbsp;
[![PyPi license](https://badgen.net/pypi/license/pearmut/)](https://pypi.org/project/pearmut/)
&nbsp;
[![build status](https://github.com/zouharvi/pearmut/actions/workflows/test.yml/badge.svg)](https://github.com/zouharvi/pearmut/actions/workflows/test.yml)

<img width="1000" alt="Screenshot of ESA/MQM interface" src="https://github.com/user-attachments/assets/4fb9a1cb-78ac-47e0-99cd-0870a368a0ad" />

## Quick start

You do not need to clone this repository. Simply install with pip and run locally:
```bash
# install the package
pip install pearmut
# download two campaign definitions
wget https://raw.githubusercontent.com/zouharvi/pearmut/refs/heads/main/examples/esa_encs.json
wget https://raw.githubusercontent.com/zouharvi/pearmut/refs/heads/main/examples/da_enuk.json
# load them into pearmut
pearmut add esa_encs.json
pearmut add da_enuk.json
# start pearmut (will show management links)
pearmut run
```

## Starting a campaign

First, install the package
```bash
pip install pearmut
```

A campaign is described in a single JSON file (see [examples/](examples/)).
One of the simplest ones, where each user has a pre-defined list of tasks (`task-based`), is:
```python
{
  "info": {
    "assignment": "task-based",
    "template": "pointwise",
    "protocol_score": true,                 # we want scores [0...100] for each segment
    "protocol_error_spans": true,           # we want error spans
    "protocol_error_categories": false,     # we do not want error span categories
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
In general, the task item can be anything and is handled by the specific protocol template.
For the standard ones (ESA, DA, MQM), we expect each item to be a dictionary (corresponding to a single document unit) that looks as follows:
```python
# single document definition
[
  {
    "src": "A najednou se všechna tato voda naplnila dalšími lidmi a dalšími věcmi.", # mandatory for ESA/MQM/DA
    "tgt": "And suddenly all the water became full of other people and other people." # mandatory for ESA/MQM/DA
  },
  {
    "src": "toto je pokračování stejného dokumentu",
    "tgt": "this is a continuation of the same document",
    ...  # all other keys that will be stored, useful for your analysis
  }
],
... # definition of another item (document)
```

## Pre-filled Error Spans (ESA<sup>AI</sup> Support)

For workflows where you want to provide pre-filled error annotations (e.g., ESA<sup>AI</sup>), you can include an `error_spans` key in each item.
These spans will be loaded into the interface as existing annotations that users can review, modify, or delete.

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

For **listwise** template, `error_spans` is a 2D array where each inner array corresponds to error spans for that candidate.

See [examples/esaai_prefilled.json](examples/esaai_prefilled.json) for a complete example.

## Tutorial and Attention Checks

You can add validation rules to items for tutorials or attention checks. Items with `validation` field will be checked before submission:

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

- Tutorial items: Include `allow_skip: true` and `warning` to let users skip after seeing the feedback
- Loud attention checks: Include `warning` without `allow_skip` to force users to retry
- Silent attention checks: Omit `warning` to silently log failures without user notification (useful for quality control with bad translations)

For listwise template, `validation` is an array where each element corresponds to a candidate. 
The dashboard shows failed/total validation checks per user, and ✅/❌ based on whether they pass the threshold.
Set `validation_threshold` in `info` to control pass/fail: integer for max failed count, float in [0,1) for max failed proportion.
See [examples/tutorial_pointwise.json](examples/tutorial_pointwise.json) and [examples/tutorial_listwise.json](examples/tutorial_listwise.json) for complete examples.

## Single-stream Assignment

We also support a simple allocation where all annotators draw from the same pool (`single-stream`). Items are randomly assigned to annotators from the pool of unfinished items:
```python
{
    "campaign_id": "my campaign 6",
    "info": {
        "assignment": "single-stream",
        "template": "pointwise",
        "protocol_score": True,                # collect scores
        "protocol_error_spans": True,          # collect error spans
        "protocol_error_categories": False,    # do not collect MQM categories, so ESA
        "users": 50,                           # number of annotators (can also be a list, see below)
    },
    "data": [...], # list of all items (shared among all annotators)
}
```


We also support dynamic allocation of annotations (`dynamic`, not yet ⚠️), which is more complex and can be ignored for now:
```python
{
    "campaign_id": "my campaign 6",
    "info": {
        "assignment": "dynamic",
        "template": "listwise",
        "protocol_k": 5,
        "users": 50,
    },
    "data": [...], # list of all items
}
```

## Pre-defined User IDs and Tokens

By default, user IDs and completion tokens are automatically generated. The `users` field can be:
- A number (e.g., `50`) to generate that many random user IDs
- A list of strings (e.g., `["alice", "bob"]`) to use specific user IDs
- A list of dictionaries to specify user IDs with custom tokens:
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

To load a campaign into the server, run the following.
It will fail if an existing campaign with the same `campaign_id` already exists, unless you specify `-o/--overwrite`.
It will also output a secret management link. Then, launch the server:
```bash
pearmut add my_campaign_4.json
pearmut run
```

## Campaign options

In summary, you can select from the assignment types

- `task-based`: each user has a predefined set of items
- `single-stream`: all users are annotating together the same set of items
- `dynamic`: WIP ⚠️

and independently of that select your protocol template:

- `pointwise`: evaluate a single output given a single output
  - `protocol_score`: ask for score 0 to 100
  - `protocol_error_spans`: ask for highlighting error spans
  - `protocol_error_categories`: ask for highlighting error categories
- `listwise`: evaluate multiple outputs at the same time given a single output ⚠️
  - `protocol_score`: ask for score 0 to 100
  - `protocol_error_spans`: ask for highlighting error spans
  - `protocol_error_categories`: ask for highlighting error categories

## Campaign management

When adding new campaigns or launching pearmut, a management link is shown that gives an overview of annotator progress but also an easy access to the annotation links or resetting the task progress (no data will be lost).
This is also the place where you can download all progress and collected annotations (these files exist also locally but this might be more convenient).

<img width="800" alt="Management dashboard" src="https://github.com/user-attachments/assets/800a1741-5f41-47ac-9d5d-5cbf6abfc0e6" />

Additionally, at the end of an annotation, a token of completion is shown which can be compared to the correct one that you can download in metadat from the dashboard.
An intentionally incorrect token can be shown if the annotations don't pass quality control.

<img width="500" alt="Token on completion" src="https://github.com/user-attachments/assets/40eb904c-f47a-4011-aa63-9a4f1c501549" />


## Multimodal Annotations

We also support anything HTML-compatible both on the input and on the output.
This includes embedded YouTube videos, or even simple `<video ` tags that point to some resource somewhere.
For an example, try [examples/multimodal.json](examples/multimodal.json).
Tip: make sure the elements are already appropriately styled.

<img width="1000" alt="Preview of multimodal elements in Pearmut" src="https://github.com/user-attachments/assets/77c4fa96-ee62-4e46-8e78-fd16e9007956" />

## CLI Commands

Pearmut provides the following commands:

- `pearmut add <file(s)>`: Add one or more campaign JSON files. Supports wildcards (e.g., `pearmut add examples/*.json`).
  - `-o/--overwrite`: Overwrite existing campaigns with the same ID.
  - `--server <url>`: Prefix server URL for protocol links (default: `http://localhost:8001`).
- `pearmut run`: Start the Pearmut server.
  - `--port <port>`: Port to run the server on (default: 8001).
  - `--server <url>`: Prefix server URL for protocol links.
- `pearmut purge [campaign]`: Remove campaign data.
  - Without arguments: Purges all campaigns (tasks, outputs, progress).
  - With campaign name: Purges only the specified campaign's data.


## Hosting Assets

To host local assets (e.g., audio files, images, videos), use the `assets` key in your campaign file:

```python
{
    "campaign_id": "my_campaign",
    "info": { 
      "assets": {
        "source": "videos",              # path to directory containing assets
        "destination": "assets/my_videos"  # where to mount (must start with "assets/")
      },
      ...
    },
    "data": [ ... ]
}
```

Files in `videos/` become accessible at `localhost:8001/assets/my_videos/`.

**Important**: This creates a symlink, so the source directory must exist throughout the annotation period.
If another campaign already uses the destination path, the add command will fail.

## Development

Pearmut works by running a server that responds to requests from the frontend.
These requests are not template-based but rather carry only data (which gives flexibility in designing new protocols and interfaces).
By default, the frontend is served from `static/` which is pre-built when you `pip install pearmut`.
To make changes locally, clone the repository and run the following, which will recompile the frontend on changes (server changes need server restart):
```bash
cd pearmut
# watch the frontend for changes (in a separate terminal)
npm install web/ --prefix web/
npm run build --prefix web/ # `watch` for rebuild on code change

# install local package as editable
pip3 install -e .
# add existing data from WMT25, this generates annotation links
# sets up progress/log files in current working folder
pearmut add examples/wmt25_#_en-cs_CZ.json
pearmut add examples/wmt25_#_cs-de_DE.json
# shows a management link for all loaded campaigns and reload on change
pearmut run
```

Optionally, you can specify `--server` in `pearmut add` and `pearmut run` to show correct URL prefixes.
The `pearmut run` also accepts `--port` (default 8001). 

If you wish to create a new protocol (referenceable from `info->template`), simply create a new HTML and TS file in `web/src` and add a rule to `webpack.config.js` so that your template gets built.
A template can call the server for data etc (see [web/src/pointwise.ts](web/src/pointwise.ts) as an exmple).

To run the platform, you need to run this on some publicly-facing server, or run it locally and tunnel your port to a public IP/domain.

## Citation

If you use this work in your paper, please cite as:
```bibtex
@misc{zouhar2025pearmut,
    author={Vilém Zouhar},
    title={Pearmut: Platform for Evaluating and Reviewing of Multilingual Tasks},
    url={https://github.com/zouharvi/pearmut/},
    year={2025},
}
