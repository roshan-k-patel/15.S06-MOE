# Which Expert, When? Alpha Models Across Market Regimes

MIT 15.S06, Fall 2026, Project 5.

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

## Repository structure

```
15.S06-MOE/
├── data/
│   ├── raw/
│   │   ├── jkp_us/                1990.parquet … 2025.parquet
│   │   └── theme_map.csv
│   ├── interim/
│   └── processed/
├── notebooks/
│   └── 01_initial_analysis.ipynb
├── src/                           # example
│   └── moe/
│       ├── __init__.py
│       ├── data.py
│       ├── experts.py
│       ├── gates.py
│       └── evaluate.py
├── scripts/
│   ├── get_jkp_us.py
│   ├── get_ctf_data.py
│   └── train_experts.py
├── outputs/
│   ├── figures/
│   ├── tables/
│   ├── models/
│   ├── predictions/
│   ├── metrics/
│   └── runs/
│       └── 2026-10-08_ridge_experts/
│           ├── config.yaml
│           ├── predictions.parquet
│           ├── metrics.csv
│           └── figures/
├── reports/
│   └── moe_progress_report_overleaf.pdf
├── references/
│   ├── papers/
│   │   └── jkp/
│   └── course/
│       └── projects2026.pdf
└── docs/
    └── concepts-glossary.md
```
