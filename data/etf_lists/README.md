Place ETF holdings CSV files in this folder.

Current parser assumptions:
- The first two lines are metadata and are skipped.
- The third line contains headers such as `Ticker`, `Name`, `Sector`, `Weight (%)`, `Location`, `Exchange`.
- Numeric fields can use comma decimals (for example `1 234,56`).

Each CSV filename is used as the ETF name in the dashboard selector.
