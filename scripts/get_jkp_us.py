"""
Download US stocks from the full JKP panel (contrib.global_factor) on WRDS.

- US only, with JKP's four standard screens
- only the 153 JKP characteristics + identifiers + target (not all ~400 columns)
- one query per year, saved as its own parquet file, so a crash or Ctrl-C
  loses at most one year and re-running skips years already downloaded

Setup (once):
    pip install wrds pandas pyarrow openpyxl
    python scripts/get_jkp_us.py      # prompts for WRDS username/password the first
                                      # time; answer 'y' to create .pgpass so you're
                                      # not asked again. Approve the Duo push.
"""
from pathlib import Path

import pandas as pd
import wrds

OUT = Path("data/raw/jkp_us")
OUT.mkdir(parents=True, exist_ok=True)

START_YEAR, END_YEAR = 1990, 2026   # characteristics are sparse before the 1960s

GH = "https://github.com/bkelly-lab/"
FACTOR_DETAILS = GH + "jkp-data/raw/main/src/jkp/data/resources/factor_details.xlsx"
CLUSTER_LABELS = GH + "ReplicationCrisis/raw/master/GlobalFactors/Cluster%20Labels.csv"

ID_COLS = ["id", "eom", "excntry", "gvkey", "permno", "size_grp", "me", "ret_exc_lead1m"]
EXTRA_COLS: list[str] = []          # add any non-JKP columns you want as gate inputs

SCREENS = "common = 1 AND exch_main = 1 AND primary_sec = 1 AND obs_main = 1"


def load_metadata() -> tuple[list[str], pd.DataFrame]:
    details = pd.read_excel(FACTOR_DETAILS)
    details = details[details["abr_jkp"].notna()]
    chars = details["abr_jkp"].tolist()                       # the 153 characteristics

    themes = pd.read_csv(CLUSTER_LABELS)                      # characteristic, cluster
    themes = themes.merge(
        details[["abr_jkp", "name_new", "direction"]],
        left_on="characteristic", right_on="abr_jkp", how="left",
    ).drop(columns="abr_jkp")
    return chars, themes


def download(chars: list[str]) -> None:
    cols = ", ".join(ID_COLS + EXTRA_COLS + chars)
    db = wrds.Connection()
    try:
        for year in range(START_YEAR, END_YEAR + 1):
            out = OUT / f"{year}.parquet"
            if out.exists():
                continue
            sql = f"""
                SELECT {cols}
                FROM contrib.global_factor
                WHERE excntry = 'USA'
                  AND {SCREENS}
                  AND eom BETWEEN '{year}-01-01' AND '{year}-12-31'
            """
            df = db.raw_sql(sql, date_cols=["eom"])
            if df.empty:
                print(f"{year}: no rows")
                continue
            # float32 halves memory/disk; ids stay exact
            df[chars] = df[chars].astype("float32")
            df.to_parquet(out, index=False)
            print(f"{year}: {len(df):>7,} rows, {df['id'].nunique():>5,} stocks")
    finally:
        db.close()


def load_panel() -> pd.DataFrame:
    """Read all saved years back into one DataFrame."""
    return pd.concat(
        (pd.read_parquet(p) for p in sorted(OUT.glob("*.parquet"))), ignore_index=True
    )


if __name__ == "__main__":
    chars, themes = load_metadata()
    themes.to_csv("data/raw/theme_map.csv", index=False)
    print(f"{len(chars)} characteristics, {themes['cluster'].nunique()} themes")

    download(chars)

    panel = load_panel()
    print(f"\npanel: {panel.shape[0]:,} rows, {panel['eom'].min().date()} -> {panel['eom'].max().date()}")
    print("rows by size group:\n", panel["size_grp"].value_counts(dropna=False).to_string())
