# Pearmut Tutorial Examples

## `esa_deen.json` - German→English ESA Tutorial

Tutorial items for teaching Error Span Annotation (ESA) of German-English translations. Contains 6 progressive tutorial items, 2 loud attention checks, and 2 silent quality control checks.

## Usage

Load tutorial items into your campaign:

```python
import json

with open('examples/tutorials/esa_deen.json', 'r') as f:
    tutorial_items = json.load(f)

# Add as first document for each annotator
for task_data in campaign['data']:
    task_data.insert(0, tutorial_items)
```
