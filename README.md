# Pearmut 🍐

Pearmut is a **Platform for Evaluation and Reviewing of Multilingual Tasks**.
It evaluates model outputs, primarily translation but also various other NLP tasks.
Supports multimodality (text, video, audio, images) and a variety of annotation protocols (DA, ESA, MQM, paired ESA, etc).

[![PyPi version](https://badgen.net/pypi/v/pearmut/)](https://pypi.org/project/pearmut)
&nbsp;
[![PyPI download/month](https://img.shields.io/pypi/dm/pearmut.svg)](https://pypi.python.org/pypi/pearmut/)
&nbsp;
[![PyPi license](https://badgen.net/pypi/license/pearmut/)](https://pypi.org/project/pearmut/)
&nbsp;
[![build status](https://github.com/zouharvi/pearmut/actions/workflows/ci.yml/badge.svg)](https://github.com/zouharvi/pearmut/actions/workflows/ci.yml)

<img width="1334" alt="Screenshot of ESA/MQM interface" src="https://github.com/user-attachments/assets/dde04b98-c724-4226-b926-011a89e9ce31" />

## Quick start
```bash
# install the package
pip install pearmut
# download two campaign definitions
wget https://raw.githubusercontent.com/zouharvi/pearmut/refs/heads/main/examples/wmt25_%23_en-cs_CZ.json
wget https://raw.githubusercontent.com/zouharvi/pearmut/refs/heads/main/examples/wmt25_%23_cs-de_DE.json
# load them into pearmut
pearmut add wmt25_#_en-cs_CZ.json
pearmut add wmt25_#_cs-de_DE.json
# start pearmut (will show management links)
pearmut run
```

## Starting a campaign

First, install the package
```bash
pip install pearmut
```

A campaign is described in a single JSON file (see [examples/](examples/)!).
One of the simplest ones, where each user has a pre-defined list of tasks (`task-based`), is:
```python
{
  "info": {
    "type": "task-based",
    "template": "pointwise",
    "protocol_score": true,                 # we want scores [0...100] for each segment
    "protocol_error_spans": true,           # we want error spans
    "protocol_error_categories": false,     # we do not want error span categories
    "status_message": "Evaluate translation from en to cs_CZ",  # message to show to users
    "url": "http://localhost:8001"          # where the server will be accessible
  },
  "campaign_id": "wmt25_#_en-cs_CZ",
  "data": [
    # data for first task/user
    [
      {
        # each evaluation item is a document
        "src": [
          "This will be the year that Guinness loses its cool. Cheers to that!",
          "I'm not sure I can remember exactly when I sensed it. Maybe it was when some...",
        ],
        "tgt": [
          "Tohle bude rok, kdy Guinness přijde o svůj „cool“ faktor. Na zdraví!",
          "Nevím přesně, kdy jsem to poprvé zaznamenal. Možná to bylo ve chvíli, ...",
        ]
      },
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
{   # single document definition
    "src": ["A najednou se všechna tato voda naplnila dalšími lidmi a dalšími věcmi.", "toto je pokračování stejného dokumentu"],       # mandatory for ESA/MQM/DA
    "tgt": ["And suddenly all the water became full of other people and other people.", "this is a continuation of the same document"], # mandatory for ESA/MQM/DA
    ...  # all other keys that will be stored, useful for your analysis
},
... # definition of another item
```

We also support a super simple allocation of annotations (`task-single`, not yet ⚠️), where you simply pass a list of all examples to be evaluated and they are processed in parallel by all annotators:
```python
{
    "campaign_id": "my campaign 6",
    "info": {
        "type": "task-single",
        "template": "pointwise",
        "protocol_score": True,                # collect scores
        "protocol_error_spans": True,          # collect error spans
        "protocol_error_categories": False,    # do not collect MQM categories, so ESA
        "users": 50,
    },
    "data": [...], # list of all items
}
```


We also support dynamic allocation of annotations (`dynamic`, not yet ⚠️), which is more complex and can be ignored for now:
```python
{
    "campaign_id": "my campaign 6",
    "info": {
        "type": "dynamic",
        "template": "kway",
        "protocol_k": 5,
        "users": 50,
    },
    "data": [...], # list of all items
}
```

To load a campaign into the server, run the following.
It will fail if an existing campaign with the same `campaign_id` already exists, unless you specify `-o/--overwrite`.
It will also output a secret management link. Then, launch the server:
```bash
pearmut add my_campaign_4.json
pearmut run
```

## Campaign management

When adding new campaigns or launching pearmut, a management link is shown that gives an overview of annotator progress but also an easy access to the annotation links or resetting the task progress (no data will be lost).

<img width="800" alt="Management dashboard" src="https://github.com/user-attachments/assets/057899d7-2291-46c7-876f-407c4050a9cb" />

Additionally, at the end of an annotation, a token of completion is shown which can be compared to the correct one that you can download in metadat from the dashboard.
An intentionally incorrect token can be shown if the annotations don't pass quality control.

<img width="500" alt="Token on completion" src="https://github.com/user-attachments/assets/4b4d2aa9-7bab-44d6-894b-6c789cd3bc6e" />

## Multimodal Annotations

We also support anything HTML-compatible both on the input and on the output.
This includes embedded YouTube videos, or even simple `<video ` tags that point to some resource somewhere.
For an example, try [examples/mock_multimodal.json](examples/mock_multimodal.json).
Tip: make sure the elements are already appropriately styled.

## Development

For the server and frontend locally run:

```bash
# watch the frontend for changes (in a separate terminal)
npm install web/ --prefix web/
npm run watch --prefix web/

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

## Citation

If you use this work in your paper, please cite as:
```bibtex
@misc{zouhar2025pearmut,
    author={Vilém Zouhar and others},
    title={Pearmut🍐 Platform for Evaluation and Reviewing of Multilingual Tasks},
    url={https://github.com/zouharvi/pearmut/},
    year={2025},
}
