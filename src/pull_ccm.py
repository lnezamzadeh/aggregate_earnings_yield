from pathlib import Path

import wrds

WRDS_USERNAME = "lnezamza"


def pull_ccm():
    db = wrds.Connection(wrds_username=WRDS_USERNAME)

    query = """
        SELECT
            gvkey,
            lpermno AS permno,
            linktype,
            linkprim,
            linkdt,
            linkenddt
        FROM crsp.ccmxpf_linktable
        WHERE SUBSTR(linktype, 1, 1) = 'L'
            AND linkprim IN ('P', 'C')
    """

    df = db.raw_sql(query, date_cols=["linkdt", "linkenddt"])
    db.close()

    return df


if __name__ == "__main__":
    df = pull_ccm()

    data_dir = Path("_data")
    data_dir.mkdir(exist_ok=True)

    df.to_parquet(data_dir / "ccm_links.parquet", index=False)

    print(f"Saved {len(df):,} CCM links.")