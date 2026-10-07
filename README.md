# Which Expert, When? Alpha Models Across Market Regimes

## Environment setup

1. Install uv:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Restart your terminal so the `uv` command is found.

3. Create the environment (from the repo root):

   ```bash
   uv sync
   ```

4. Select the environment as your Python interpreter / notebook kernel:

   - **PyCharm:** Python Interpreter → Add New Interpreter → Add Local Interpreter → Select existing →
     Type: uv → Environment: this repo's `.venv`
   - **VS Code:** Select Kernel → Python Environments → `.venv`
     (if not listed: Enter interpreter path… → `.venv/bin/python`)

5. Optional: activate the environment in your terminal (or prefix commands with `uv run`):

   ```bash
   source .venv/bin/activate
   ```

## Repository structure (to follow)

```
15.S06-MOE/
├── data/
│   ├── raw/           jkp_us/ (1990–2025.parquet), theme_map.csv
│   ├── interim/
│   └── processed/
├── notebooks/         01_initial_analysis.ipynb
├── src/moe/           __init__.py, data.py, experts.py, gates.py, evaluate.py   # example
├── scripts/           get_jkp_us.py, get_ctf_data.py, train_experts.py
├── outputs/           figures/, tables/, models/, predictions/, metrics/, runs/<date>_<name>/
├── reports/           moe_progress_report_overleaf.pdf
├── references/        papers/jkp/, course/projects2026.pdf
└── docs/              concepts-glossary.md
```
