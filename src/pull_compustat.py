import pandas as pd
import wrds
from pathlib import Path

WRDS_USERNAME = "lnezamza"
START_DATE = "1999-01-01"
END_DATE = "2026-10-31"

def pull_compustat_quarterly():
    db = wrds.Connection(wrds_username=WRDS_USERNAME)

    query = f"""
        SELECT
            gvkey,
            datadate,
            niq,
            rdq,
            fic
        FROM comp.fundq
        WHERE datadate BETWEEN '{START_DATE}' AND '{END_DATE}'
            AND indfmt = 'INDL'
            AND datafmt = 'STD'
            AND consol = 'C'
            AND popsrc = 'D'
            AND fic = 'USA'
    """

    df = db.raw_sql(query, date_cols=["datadate", "rdq"])
    db.close()

    return df


if __name__ == "__main__":
    df = pull_compustat_quarterly()

    data_dir = Path("_data")
    data_dir.mkdir(exist_ok=True)

    df.to_parquet(data_dir / "compustat_quarterly.parquet", index=False)

    print(f"Saved {len(df):,} rows of Compustat data.")