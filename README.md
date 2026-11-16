# Expenses Tracker

A command-line expense tracker built with Python and SQLite. No packages to install.

## Requirements
- Python 3.8 or newer
- SQLite 3.25 or newer (bundled with Python; needed for window functions)

Check your versions:

    python --version
    python -c "import sqlite3; print(sqlite3.sqlite_version)"

## How to run
1. Put `expenses_tracker.py` in a folder.
2. Open a terminal in that folder.
3. Run a command (use `python3` instead of `python` on Mac/Linux, or `py` on Windows if needed).

Data is saved in `expenses.db`, created in the folder you run the script from.
Always run from the same folder to keep using the same database.

## Commands

    python expenses_tracker.py add 250 food "Lunch"
    python expenses_tracker.py add 3000 rent "Rent" --date 2026-11-01
    python expenses_tracker.py list
    python expenses_tracker.py list --month 2026-11
    python expenses_tracker.py list --category food
    python expenses_tracker.py summary
    python expenses_tracker.py monthly
    python expenses_tracker.py top --n 3
    python expenses_tracker.py delete 2
    python expenses_tracker.py export expenses.csv
    python expenses_tracker.py --help

| Command   | What it does                                          |
|-----------|-------------------------------------------------------|
| `add`     | Add an expense (amount, category, optional description, optional `--date YYYY-MM-DD`) |
| `list`    | Show expenses, optionally filtered by `--month` / `--category` |
| `summary` | Total, count and % share per category                 |
| `monthly` | Monthly totals with change vs the previous month      |
| `top`     | Largest expenses (`--n` sets how many)                |
| `delete`  | Remove an expense by its ID                           |
| `export`  | Write all expenses to a CSV file                      |

## SQL concepts used
`CREATE TABLE` with `CHECK`, indexes, parameterized queries, `GROUP BY`,
window functions (`SUM() OVER ()`, `LAG()`), CTEs, and `strftime` date grouping.

## Ideas to extend
- Monthly budgets per category with over-budget warnings
- An `update` command to edit an expense
- A pie chart of `summary` using matplotlib
- Unit tests using an in-memory database (`:memory:`)
