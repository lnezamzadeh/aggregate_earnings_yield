from pathlib import Path
import pandas as pd
import wrds

START_DATE = "2000-01-01"
END_DATE = "2026-10-31"
WRDS_USERNAME = "lnezamza"


def pull_crsp_monthly():
    db = wrds.Connection(wrds_username=WRDS_USERNAME)

    query = f"""
        SELECT
            msf.permno,
            msf.mthcaldt,
            msf.mthprc,
            msf.shrout
        FROM crspm.msf_v2 AS msf
        INNER JOIN crspm.stksecurityinfohist AS info
            ON msf.permno = info.permno
            AND msf.mthcaldt BETWEEN info.secinfostartdt AND info.secinfoenddt
        WHERE msf.mthcaldt BETWEEN '{START_DATE}' AND '{END_DATE}'
            AND info.securitytype = 'EQTY'
            AND info.securitysubtype = 'COM'
            AND info.sharetype = 'NS'
            AND info.usincflg = 'Y'
    """

    df = db.raw_sql(query, date_cols=["mthcaldt"])
    db.close()

    # Calculate market capitalization in millions of dollars
    df["market_cap"] = df["mthprc"].abs() * df["shrout"] / 1000

    return df


if __name__ == "__main__":
    df = pull_crsp_monthly()

    data_dir = Path("_data")
    data_dir.mkdir(exist_ok=True)

    df.to_parquet(data_dir / "crsp_monthly.parquet", index=False)

    print(f"Saved {len(df):,} rows of CRSP data.")