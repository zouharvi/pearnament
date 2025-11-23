# 🍐 Pearnament

A tool for pairwise tournament of model outputs, such as for WMT.

## Starting a campaign

A campaign is described in a single JSON file.
The simplest one is:
```json
{
    "protocol": "ESA",
    "campaign_id": "my campaign 4",
    "meta": {...},
    "data": [...],
}
```

However, we also support dynamic allocation of annotations:
```json
{
    "protocol": "pear",
    "campaign_id": "my campaign 6",
    "meta": {...},
    "data": [...],
}
```

To load a campaign into the server, run the following.
It will fail if an existing campaign with the same `campaign_id` already exists, unless you specify `-o/--overwrite`.
It will also output a secret management link.
```bash
python3 server/start_campaign.py my_campaign_4.json
```

## Development

For the frontend run:

```bash
npm install
npm run dev    # will automatically open your browser
npm run build  # will output in dist/ that can be statically served
```

For the server run:

```bash
cd server
pip install fastapi uvicorn
uvicorn main:app --reload --port 8001
```