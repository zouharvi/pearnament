# 🍐 Pearnament

A tool for evaluation of model outputs, primarily translation but also various other NLP tasks.
Supports multimodality (text, video, audio, images) and a variety of annotation protocols (DA, ESA, MQM, paired ESA, etc).

## Starting a campaign

First, install the server package:
```bash
pip install pearnament          # NOTE: this will fail for now as package is not live yet
```

A campaign is described in a single JSON file.
The simplest one is:
```python
{
    "protocol": "ESA",
    "campaign_id": "my campaign 4",
    "meta": {...},
    "data": [...],
}
```

However, we also support dynamic allocation of annotations:
```python
{
    "protocol": "PearTournament",
    "campaign_id": "my campaign 6",
    "meta": {...},
    "data": [...],
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
npm install
npm run dev    # will automatically open your browser
npm run build  # will output in dist/ that can be statically served
```

For the server locally run:

```bash
cd server
python3 install -e . # install editable
pearnament run
```