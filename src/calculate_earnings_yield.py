
from pathlib import Path

import pandas as pd


DATA_DIR = Path("_data")


# load data
crsp = pd.read_parquet(DATA_DIR / "crsp_monthly.parquet")
comp = pd.read_parquet(DATA_DIR / "compustat_quarterly.parquet")
ccm = pd.read_parquet(DATA_DIR / "ccm_links.parquet")


# calculate trailing twelve-month earnings
"""
Compustat reports net income quarterly, but we want annual earnings
to compare against each company's market capitalization.

For each company, we add net income from the most recent four quarters.
The first three observations will be missing because we do not yet have
four quarters of earnings.
"""
comp = comp.sort_values(["gvkey", "datadate"])

comp["ttm_earnings"] = (
    comp.groupby("gvkey")["niq"]
    .transform(lambda x: x.rolling(window=4, min_periods=4).sum())
)


# validate reporting periods
"""
We need to make sure the four observations used in our TTM calculation
actually represent four consecutive quarters.

Although TTM earnings cover twelve months, the distance between the
first and fourth quarter-end dates should be approximately nine months.

We exclude observations outside 260 to 290 days to avoid including
earnings from irregular reporting periods.
"""
comp["ttm_span_days"] = (
    comp["datadate"]
    - comp.groupby("gvkey")["datadate"].shift(3)
).dt.days

comp.loc[
    ~comp["ttm_span_days"].between(260, 290),
    "ttm_earnings"
] = float("nan")


# avoid look-ahead bias
"""
The end of a financial quarter is not necessarily when its earnings
become public.

For example, a company might end its quarter on March 31 but not
announce earnings until May 5. We cannot use those earnings when
calculating the market's earnings yield for April.

We therefore use rdq, the earnings announcement date, to determine
when each observation becomes available.
"""
comp = comp.dropna(subset=["ttm_earnings", "rdq"]).copy()
comp = comp[comp["rdq"] >= comp["datadate"]].copy()


# match CRSP stocks to Compustat companies
"""
CRSP identifies stocks using permno, while Compustat identifies
companies using gvkey.

The CCM linking table connects these identifiers. Because these
relationships can change over time, we only keep links that were
valid on the date of each CRSP observation.
"""
crsp = crsp.merge(ccm, on="permno", how="inner")

crsp = crsp[
    (crsp["mthcaldt"] >= crsp["linkdt"])
    & (
        crsp["linkenddt"].isna()
        | (crsp["mthcaldt"] <= crsp["linkenddt"])
    )
].copy()


# resolve duplicate CCM links
"""
Some stocks have multiple valid CCM links for the same month.

We prioritize LC links, followed by LU and LD, so that each stock
appears only once per month and its market capitalization is not
accidentally counted multiple times.
"""
crsp["link_priority"] = crsp["linktype"].map({
    "LC": 0,
    "LU": 1,
    "LD": 2
}).fillna(3)

crsp = (
    crsp.sort_values(["link_priority", "permno", "mthcaldt"])
    .drop_duplicates(subset=["permno", "mthcaldt"], keep="first")
    .drop(columns="link_priority")
)


# match monthly stock data with the latest available earnings
"""
For each stock-month observation, we find the most recent TTM
earnings that had already been announced.

The backward merge ensures that we never use an earnings announcement
from after the stock's observation date.
"""
crsp = crsp.sort_values("mthcaldt")
comp = comp.sort_values("rdq")

merged = pd.merge_asof(
    crsp,
    comp[["gvkey", "rdq", "ttm_earnings"]],
    left_on="mthcaldt",
    right_on="rdq",
    by="gvkey",
    direction="backward"
)


# keep observations with usable earnings and market capitalization
merged = merged.dropna(subset=["ttm_earnings", "market_cap"])
merged = merged[merged["market_cap"] > 0].copy()


# aggregate stocks to the company level
"""
Some companies have multiple publicly traded share classes.

We add the market capitalizations of these stocks together, but
only count the company's earnings once. Otherwise, companies with
multiple share classes would have their earnings double-counted.
"""
company_monthly = (
    merged.groupby(["mthcaldt", "gvkey"], as_index=False)
    .agg(
        market_cap=("market_cap", "sum"),
        ttm_earnings=("ttm_earnings", "first")
    )
)


# calculate aggregate earnings yield
"""
Rather than averaging individual companies' earnings yields, we
calculate the earnings yield of the market as a whole.

Aggregate earnings yield = total TTM earnings / total market cap

Both earnings and market capitalization are measured in millions
of dollars, so no additional unit conversion is necessary.

We include negative earnings because loss-making companies still
contribute to the market's aggregate profitability.
"""
monthly = (
    company_monthly.groupby("mthcaldt", as_index=False)
    .agg(
        total_earnings=("ttm_earnings", "sum"),
        total_market_cap=("market_cap", "sum")
    )
)

monthly["earnings_yield"] = (
    monthly["total_earnings"] / monthly["total_market_cap"]
)


# save final dataset
output = (
    monthly[["mthcaldt", "earnings_yield"]]
    .rename(columns={"mthcaldt": "date"})
)

output.to_csv("aggregate_earnings_yield.csv", index=False)

print(f"Saved {len(output)} monthly observations.")
print(output.tail())
