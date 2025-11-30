# Pearmut 🍐

Pearmut is a **Platform for Evaluation and Reviewing of Multilingual Tasks**.
It evaluates model outputs, primarily translation but also various other NLP tasks.
Supports multimodality (text, video, audio, images) and a variety of annotation protocols (DA, ESA, MQM, paired ESA, etc).
[![build status](https://github.com/zouharvi/pearmut/actions/workflows/ci.yml/badge.svg)](https://github.com/zouharvi/pearmut/actions/workflows/ci.yml)


<img width="1334" alt="Screenshot of ESA/MQM interface" src="https://github.com/user-attachments/assets/dde04b98-c724-4226-b926-011a89e9ce31" />


## Starting a campaign

First, install the package
```bash
pip install pearmut
```

A campaign is described in a single JSON file.
The simplest one, where each user has a pre-defined list of tasks (`task-based`) is:
```python
{
    "campaign_id": "my campaign 4",
    "info": {
        "type": "task-based",
        "template": "pointwise",
        "protocol_score": True,                # collect scores
        "protocol_error_spans": True,          # collect error spans
        "protocol_error_categories": False,    # do not collect MQM categories, so ESA
    },
    "data": [
        [...],  # tasks for first user
        [...],  # tasks for second user
        [...],  # tasks for third user
        ...
    ],
}
```
In general, the task item can be anything and is handled by the specific protocol template.
For the standard ones (ESA, DA, MQM), we expect each item to be a list (i.e. document unit) that looks as follows:
```python
[
    {
        "src": "A najednou se všechna tato voda naplnila dalšími lidmi a dalšími věcmi.",       # mandatory for ESA/MQM/DA
        "tgt": "And suddenly all the water became full of other people and other people.",      # mandatory for ESA/MQM/DA
        ...  # all other keys that will be stored, useful for your analysis
    },
    {
        "src": "toto je pokračování stejného dokumentu",
        "tgt": "this is a continuation of the same document",
        ...
    },
    ...
]
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

To load a campaign into the server, run the following.
It will fail if an existing campaign with the same `campaign_id` already exists, unless you specify `-o/--overwrite`.
It will also output a secret management link.
```bash
pearmut add my_campaign_4.json
```

Finally, you can launch the server with:
```bash
pearmut run
```

You can see examples in `data/examples/`.

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
pearmut add data/examples/wmt25_#_en-cs_CZ.json
pearmut add data/examples/wmt25_#_cs-de_DE.json
# shows a management link for all loaded campaigns
pearmut run
```

## Misc

If you use this work in your paper, please cite as:
```bibtex
@misc{zouhar2025pearmut,
    author={Vilém Zouhar and others},
    title={Pearmut🍐 Platform for Evaluation and Reviewing of Multilingual Tasks},
    url={https://github.com/zouharvi/pearmut/},
    year={2025},
}