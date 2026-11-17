# Aggregate Earnings Yield

This repository calculates the monthly aggregate earnings yield of U.S. stocks using CRSP and Compustat data from WRDS, beginning in January 2000.

## Methodology

Aggregate earnings yield is calculated as:

$$
\text{Aggregate Earnings Yield} = \frac{\text{Total TTM Earnings}}{\text{Total Market Capitalization}}
$$

- **CRSP:** Monthly stock prices and shares outstanding, used to calculate market capitalization.
- **Compustat:** Quarterly net income, used to calculate trailing twelve-month (TTM) earnings.
- **CCM:** Links CRSP securities to Compustat companies.

TTM earnings are calculated by summing the most recent four quarters of net income. Earnings are matched to monthly stock observations using their announcement dates to avoid look-ahead bias.

Companies with multiple share classes have their market capitalizations combined, while their earnings are counted only once. Companies reporting negative earnings remain included.

## Reproducing the Results

The project uses Python and `uv` for dependency management.

Install dependencies:

```bash
uv sync
```

With WRDS access configured, run:

```bash
uv run python src/pull_crsp.py
uv run python src/pull_compustat.py
uv run python src/pull_ccm.py
uv run python src/calculate_earnings_yield.py
```

The final dataset is saved as `aggregate_earnings_yield.csv`.

## Output

The dataset contains 321 monthly observations from January 2000 through September 2026, with two columns:

- `date`: Monthly observation date.
- `earnings_yield`: Aggregate earnings yield expressed as a decimal (e.g., `0.0375` represents 3.75%).

The final aggregate series is included in the repository. Raw WRDS data is excluded.