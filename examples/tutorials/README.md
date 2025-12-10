# Pearmut Tutorial Examples

This directory contains tutorial item files that can be used to train annotators on how to use the Pearmut annotation interface.

## Available Tutorials

### `esa_deen.json` - German→English Error Span Annotation Tutorial

A comprehensive tutorial for teaching annotators how to evaluate German-to-English translations using the Error Span Annotation (ESA) protocol.

**Structure:**
- **6 Tutorial Items** (with `allow_skip: true`): Progressive lessons teaching core annotation skills
- **2 Loud Attention Checks** (with warning): Verify annotator understanding with feedback
- **2 Silent Attention Checks** (no warning): Quality control without user notification

**Tutorial Progression:**

1. **Perfect Translation** - Learn to recognize and score correct translations (100%)
2. **Minor Error** - Practice marking a single word error with light pink highlighting (75-85%)
3. **Major Error** - Learn to mark severe errors with dark pink highlighting (10-20%)
4. **No Markings** - Rate naturally awkward but technically correct translations (70-80%)
5. **Missing Content** - Mark missing words using the [MISSING] marker (5-15%)
6. **Removing Errors** - Practice removing incorrect error markings (100%)

**Attention Checks:**
- Verify annotators can identify perfect translations
- Ensure annotators can detect and mark major semantic errors
- Silent checks for quality control without disrupting workflow

## Usage

These tutorial files contain **only the items array** and are meant to be loaded into a campaign configuration. They are not complete campaign files.

### Option 1: Load into a Campaign File

```python
import json

# Load tutorial items
with open('examples/tutorials/esa_deen.json', 'r') as f:
    tutorial_items = json.load(f)

# Create a campaign that uses them
campaign = {
    "info": {
        "assignment": "task-based",
        "protocol": "ESA",
        "shuffle": False  # Keep tutorial in order
    },
    "campaign_id": "my_campaign_with_tutorial",
    "data": [
        [
            tutorial_items  # Add as first document
        ],
        # ... rest of your evaluation items
    ]
}
```

### Option 2: Prepend to Existing Campaign Data

```python
import json

# Load tutorial
with open('examples/tutorials/esa_deen.json', 'r') as f:
    tutorial_items = json.load(f)

# Load your campaign
with open('my_campaign.json', 'r') as f:
    campaign = json.load(f)

# Add tutorial as first document for each annotator
for task_data in campaign['data']:
    task_data.insert(0, tutorial_items)

# Save updated campaign
with open('my_campaign_with_tutorial.json', 'w') as f:
    json.dump(campaign, f, indent=2)
```

### Option 3: Use Programmatically

```python
import json

tutorial_items = json.load(open('examples/tutorials/esa_deen.json'))

# Filter by type
tutorials = [item for item in tutorial_items 
             if item.get('validation', {}).get('Translation', {}).get('allow_skip')]
loud_checks = [item for item in tutorial_items 
               if 'validation' in item and 'warning' in item['validation'].get('Translation', {}) 
               and not item['validation']['Translation'].get('allow_skip')]
silent_checks = [item for item in tutorial_items
                 if 'validation' in item and 'warning' not in item['validation'].get('Translation', {})]

# Mix them into your annotation tasks as needed
```

## Creating Your Own Tutorials

Tutorial items follow the standard Pearmut item format with additional `validation` fields:

```json
{
  "doc_id": "tutorial-example-1",
  "src": "Source text in German",
  "tgt": {
    "Translation": "Target text in English"
  },
  "instructions": "<b>Detailed HTML instructions for the annotator</b>",
  "validation": {
    "Translation": {
      "warning": "Feedback message shown when validation fails",
      "score": [70, 80],
      "error_spans": [
        {
          "start_i": 10,
          "end_i": 20,
          "severity": "minor"
        }
      ],
      "allow_skip": true
    }
  }
}
```

**Key Fields:**
- `instructions`: HTML-formatted guidance shown above the item
- `validation`: Rules to check annotator's work
  - `warning`: Message shown on validation failure (omit for silent checks)
  - `score`: Expected score range `[min, max]`
  - `error_spans`: Expected error markings with character positions
  - `allow_skip`: If true, shows "Skip Tutorial" button (for tutorial items)
  - `score_greaterthan`: Ensure one translation scores higher than another

**Error Span Format:**
- `start_i` and `end_i`: Character indices (0-based, inclusive)
- Use `"missing"` for both to indicate the [MISSING] marker
- `severity`: `"minor"` (light pink) or `"major"` (dark pink)

## Best Practices

1. **Progressive Difficulty**: Start with simple perfect/bad translations, then introduce complexity
2. **Clear Instructions**: Use bold, color, and formatting to highlight key information
3. **Consistent Feedback**: Provide specific, actionable feedback in warnings
4. **Mix Check Types**: Combine tutorial items (skippable), loud checks (retry), and silent checks (logging)
5. **Real Examples**: Use realistic translation scenarios relevant to your domain
6. **Test Thoroughly**: Validate your tutorial items with real annotators before deployment

## References

- Inspired by the [Appraise ErrorSpanAnnotation tutorial](https://github.com/wmt-conference/ErrorSpanAnnotation)
- See [Pearmut documentation](../../README.md) for more information on validation rules
- Check [examples/attention_checks.json](../attention_checks.json) for more validation examples
