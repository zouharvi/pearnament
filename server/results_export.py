import collections
import json
import os
import statistics
import tempfile

import typst

from .utils import get_db_log


def compute_model_scores(campaign_id):
    """
    Compute model scores from annotations for a campaign.
    
    Returns:
        List of dicts with keys: model, score, count
        Sorted by score in descending order
    """
    # Compute model scores from annotations
    model_scores = collections.defaultdict(dict)

    # Iterate through all tasks to find items with 'models' field (basic template)
    log = get_db_log(campaign_id)
    for entry in log:
        if "item" not in entry or "annotation" not in entry:
            continue
        for item, annotation in zip(entry["item"], entry["annotation"]):
            for model, annotation in annotation.items():
                if "score" in annotation and annotation["score"] is not None:
                    model_scores[model][json.dumps(item)] = annotation["score"]

    results = [
        {
            "model": model,
            "score": statistics.mean(scores.values()),
            "count": len(scores),
        }
        for model, scores in model_scores.items()
    ]
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def generate_typst_table(results):
    """
    Generate Typst code for a two-column table with results.
    
    Args:
        results: List of dicts with keys: model, score, count
        
    Returns:
        String containing Typst table markup
    """
    if not results:
        return "// No results available"
    
    typst_code = """#table(
  columns: (auto, auto),
  align: (left, right),
  stroke: none,
  table.hline(),
  [*Model*], [*Score*],
  table.hline(),
"""
    
    for result in results:
        # Escape Typst special characters
        model = result["model"]
        model = model.replace("\\", "\\\\")
        model = model.replace("#", "\\#")
        model = model.replace("*", "\\*")
        model = model.replace("_", "\\_")
        model = model.replace("`", "\\`")
        model = model.replace("[", "\\[")
        model = model.replace("]", "\\]")
        
        score = f"{result['score']:.1f}"
        typst_code += f"  [{model}], [{score}],\n"
    
    typst_code += "  table.hline(),\n"
    typst_code += ")\n"
    return typst_code


def generate_latex_table(results):
    """
    Generate LaTeX code for a booktabs two-column table with results.
    
    Args:
        results: List of dicts with keys: model, score, count
        
    Returns:
        String containing LaTeX table markup
    """
    if not results:
        return "% No results available"
    
    latex_code = """\\begin{table}[h]
\\centering
\\begin{tabular}{lr}
\\toprule
\\textbf{Model} & \\textbf{Score} \\\\
\\midrule
"""
    
    for result in results:
        # Escape LaTeX special characters
        model = result["model"]
        model = model.replace("\\", "\\textbackslash ")
        model = model.replace("_", "\\_")
        model = model.replace("&", "\\&")
        model = model.replace("%", "\\%")
        model = model.replace("$", "\\$")
        model = model.replace("#", "\\#")
        model = model.replace("{", "\\{")
        model = model.replace("}", "\\}")
        model = model.replace("~", "\\textasciitilde ")
        model = model.replace("^", "\\textasciicircum ")
        
        score = f"{result['score']:.1f}"
        latex_code += f"{model} & {score} \\\\\n"
    
    latex_code += """\\bottomrule
\\end{tabular}
\\caption{Model ranking results}
\\label{tab:results}
\\end{table}
"""
    return latex_code


def generate_pdf(results):
    """
    Generate PDF from Typst code using typst-py.
    
    Args:
        results: List of dicts with keys: model, score, count
        
    Returns:
        bytes containing the PDF
    """
    if not results:
        # Return empty PDF with message
        typst_code = "[No results available]"
    else:
        typst_code = generate_typst_table(results)
    
    # Create a temporary file for the typst source
    with tempfile.NamedTemporaryFile(mode='w', suffix='.typ', delete=False) as f:
        f.write(typst_code)
        typst_file = f.name
    
    try:
        # Compile to PDF
        pdf_bytes = typst.compile(typst_file)
        return pdf_bytes
    finally:
        # Clean up
        os.unlink(typst_file)
