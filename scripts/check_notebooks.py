"""Validate and optionally execute every public notebook in a fresh kernel."""

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient

parser = argparse.ArgumentParser()
parser.add_argument("--execute", action="store_true")
parser.add_argument("--save-outputs", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]

for path in sorted(root.glob("module*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    if args.execute:
        NotebookClient(notebook, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(root)}}).execute()
        if args.save_outputs:
            nbformat.write(notebook, path)
    print(f"{path.name}: {'executed' if args.execute else 'validated'} {len(notebook.cells)} cells")
