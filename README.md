# 🍐 Pearnament

A tool for evaluation of model outputs, primarily translation but also various other NLP tasks.
Supports multimodality (text, video, audio, images) and a variety of annotation protocols (DA, ESA, MQM, paired ESA, etc).

<img width="1334" height="614" alt="image" src="https://github.com/user-attachments/assets/dde04b98-c724-4226-b926-011a89e9ce31" />


## Starting a campaign

First, install the server package:
```bash
pip install pearnament          # NOTE: this will fail for now as package is not live yet
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
        ...                            # any other keys that will be stored, useful for analysis andfurther identification
    },
    {
        "src": "toto je pokračování stejného dokumentu",
        "tgt": "this is a continuation of the same document",
        ...
    },
    ...
]
```

We also support dynamic allocation of annotations, which is more complex and can be ignored for now:
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
It will also output a secret management link.
```bash
pearnament add my_campaign_4.json
```

Finally, you can launch the server with:
```bash
pearnament run
```

The frontend is detached from the server and only receives an address that it should use to communicate.
For this reason, you can use https://vilda.net/s/pearnament/ while supplying your own server connection.
NOTE: this will fail for now as website is not live yet.

## Development

For the frontend locally run:

```bash
cd web
npm install
npm run dev    # will automatically open your browser
npm run build  # will output in dist/ that can be statically served
```

For the server locally run:

```bash
pip3 install -e server/ # install editable
# add existing data from WMT25, this generates annotation links that you should click
pearnament add server/examples/wmt25_#_en-cs_CZ.json
pearnament run
```


## Misc

If you use this work in your paper, please cite as:
```bibtex
@misc{pearnament,
    author={Vilém Zouhar and others},
    title={Pearnament: Annotating Multilinguality Pointwise and Pairwise},
    url={https://github.com/zouharvi/pearnament/},
    year={2025},
}