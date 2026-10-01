"""
Download the JKP Common Task Framework (CTF) data from WRDS, attach the
JKP 13-theme labels, and run basic sanity checks.

Setup (once):
    pip install pandas pyarrow sqlalchemy psycopg2-binary keyring
    python -c "import keyring, getpass; keyring.set_password('wrds', 'YOUR_WRDS_USERNAME', getpass.getpass())"
    export WRDS_USERNAME=YOUR_WRDS_USERNAME     # or you'll be prompted

Usage:
    python get_ctf_data.py            # download + checks
    python get_ctf_data.py --skip-download   # checks only, on saved parquet files
"""
import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

CLUSTER_URL = (
    "https://raw.githubusercontent.com/bkelly-lab/ReplicationCrisis/"
    "master/GlobalFactors/Cluster%20Labels.csv"
)
TABLES = ["ctff_features", "ctff_chars", "ctff_daily_ret"]


# ---------------------------------------------------------------- download
def download_ctf():
    import keyring
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL

    # macOS Keychain can't look up a credential without a username,
    # so the username comes from an env var (or a prompt) and only the password from keyring.
    import os
    username = os.environ.get("WRDS_USERNAME") or input("WRDS username: ").strip()
    password = keyring.get_password("wrds", username)
    if password is None:
        raise RuntimeError(
            f"No password stored for '{username}'. Run:\n"
            "  python -c \"import keyring, getpass; "
            f"keyring.set_password('wrds', '{username}', getpass.getpass())\""
        )

    engine = create_engine(URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host="wrds-pgdata.wharton.upenn.edu",
        port=9737,
        database="wrds",
        query={"sslmode": "require"},
    ))

    for t in TABLES:
        out = RAW / f"{t}.parquet"
        if out.exists():
            print(f"{t}: already saved, skipping")
            continue
        print(f"{t}: downloading...")
        with engine.connect() as conn:
            parts = pd.read_sql_query(
                text(f"SELECT * FROM contrib_global_factor.{t};"),
                conn, chunksize=500_000,      # chunked so ctff_chars fits in memory
            )
            df = pd.concat(parts, ignore_index=True)
        df.to_parquet(out, index=False)
        print(f"{t}: {df.shape[0]:,} rows x {df.shape[1]} cols -> {out}")


# ------------------------------------------------------------ theme labels
def load_themes() -> pd.DataFrame:
    out = RAW / "cluster_labels.csv"
    if not out.exists():
        pd.read_csv(CLUSTER_URL).to_csv(out, index=False)
    return pd.read_csv(out)   # columns: characteristic, cluster


# ------------------------------------------------------------------ checks
def sanity_checks():
    chars = pd.read_parquet(RAW / "ctff_chars.parquet")
    feats = pd.read_parquet(RAW / "ctff_features.parquet")
    themes = load_themes()

    print("\n=== ctff_chars ===")
    print(chars.shape)
    print("non-characteristic columns:",
          [c for c in chars.columns if c not in set(feats["features"])])
    chars["eom"] = pd.to_datetime(chars["eom"])
    print("date range:", chars["eom"].min().date(), "->", chars["eom"].max().date())
    print("stocks per month (median):", int(chars.groupby("eom")["id"].nunique().median()))

    split = chars.groupby("ctff_test")["eom"].agg(["min", "max", "count"])
    print("\ntrain/test split:\n", split)

    # --- how the CTF feature list lines up with the 13 JKP themes
    feature_list = set(feats["features"])
    themed = set(themes["characteristic"])
    print(f"\nCTF features: {len(feature_list)} | JKP themed chars: {len(themed)}")
    print("in CTF but no theme:", sorted(feature_list - themed))
    print("themed but not in CTF:", sorted(themed - feature_list))

    mapping = themes[themes["characteristic"].isin(feature_list)]
    print("\nfeatures per theme (usable in CTF):")
    print(mapping["cluster"].value_counts().to_string())

    # --- missingness by theme (matters for how you impute before fitting experts)
    miss = chars[list(mapping["characteristic"])].isna().mean()
    print("\nmean missing share by theme:")
    print(miss.groupby(mapping.set_index("characteristic")["cluster"]).mean()
              .sort_values(ascending=False).round(3).to_string())

    mapping.to_csv(RAW / "theme_map_ctf.csv", index=False)
    print(f"\nsaved theme map -> {RAW / 'theme_map_ctf.csv'}")


if __name__ == "__main__":
    if "--skip-download" not in sys.argv:
        download_ctf()
    sanity_checks()
