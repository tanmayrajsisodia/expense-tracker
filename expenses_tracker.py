"""
Expenses Tracker (Python + SQLite)

Usage examples:
    python expenses_tracker.py add 250 Food "Lunch with team"
    python expenses_tracker.py add 1200 Transport "Cab to airport" --date 2026-11-10
    python expenses_tracker.py list
    python expenses_tracker.py list --month 2026-11 --category Food
    python expenses_tracker.py summary
    python expenses_tracker.py monthly
    python expenses_tracker.py top --n 3
    python expenses_tracker.py delete 2
    python expenses_tracker.py export expenses.csv

Requires Python 3.8+ (SQLite 3.25+ for the window functions). No packages to install.
"""

import argparse
import csv
import sqlite3
from datetime import date

DB_FILE = "expenses.db"


# ---------- Database ----------

def get_conn(db_file=DB_FILE):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            amount      REAL    NOT NULL CHECK (amount > 0),
            category    TEXT    NOT NULL,
            description TEXT,
            spent_on    TEXT    NOT NULL   -- stored as YYYY-MM-DD
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_spent_on ON expenses(spent_on)")
    return conn


def valid_date(text):
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' is not a valid date (use YYYY-MM-DD)")


# ---------- Commands ----------

def cmd_add(args, conn):
    cur = conn.execute(
        "INSERT INTO expenses (amount, category, description, spent_on) VALUES (?, ?, ?, ?)",
        (args.amount, args.category.title(), args.description, args.date),
    )
    conn.commit()
    print(f"Added expense #{cur.lastrowid}: {args.amount:.2f} on {args.category.title()} ({args.date})")


def cmd_list(args, conn):
    query = "SELECT id, spent_on, category, amount, description FROM expenses WHERE 1=1"
    params = []
    if args.month:
        query += " AND strftime('%Y-%m', spent_on) = ?"
        params.append(args.month)
    if args.category:
        query += " AND category = ?"
        params.append(args.category.title())
    query += " ORDER BY spent_on DESC, id DESC"

    rows = conn.execute(query, params).fetchall()
    if not rows:
        print("No expenses found.")
        return

    print(f"{'ID':<4} {'Date':<12} {'Category':<14} {'Amount':>10}  Description")
    print("-" * 60)
    for r in rows:
        print(f"{r['id']:<4} {r['spent_on']:<12} {r['category']:<14} {r['amount']:>10.2f}  {r['description'] or ''}")
    print("-" * 60)
    noun = "expense" if len(rows) == 1 else "expenses"
    print(f"Total: {sum(r['amount'] for r in rows):.2f}  ({len(rows)} {noun})")


def cmd_summary(args, conn):
    """Totals per category with share of overall spending."""
    rows = conn.execute(
        """
        SELECT category,
               COUNT(*)                                          AS n,
               SUM(amount)                                       AS total,
               ROUND(100.0 * SUM(amount) / SUM(SUM(amount)) OVER (), 1) AS pct
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    ).fetchall()
    if not rows:
        print("No expenses yet.")
        return

    print(f"{'Category':<14} {'Count':>5} {'Total':>12} {'Share':>7}")
    print("-" * 42)
    for r in rows:
        print(f"{r['category']:<14} {r['n']:>5} {r['total']:>12.2f} {r['pct']:>6.1f}%")


def cmd_monthly(args, conn):
    """Monthly totals with month-over-month change (window function)."""
    rows = conn.execute(
        """
        WITH m AS (
            SELECT strftime('%Y-%m', spent_on) AS month, SUM(amount) AS total
            FROM expenses
            GROUP BY month
        )
        SELECT month,
               total,
               total - LAG(total) OVER (ORDER BY month) AS change
        FROM m
        ORDER BY month
        """
    ).fetchall()
    if not rows:
        print("No expenses yet.")
        return

    print(f"{'Month':<9} {'Total':>12} {'Change':>12}")
    print("-" * 35)
    for r in rows:
        change = "-" if r["change"] is None else f"{r['change']:+.2f}"
        print(f"{r['month']:<9} {r['total']:>12.2f} {change:>12}")


def cmd_top(args, conn):
    rows = conn.execute(
        "SELECT id, spent_on, category, amount, description FROM expenses ORDER BY amount DESC LIMIT ?",
        (args.n,),
    ).fetchall()
    if not rows:
        print("No expenses yet.")
        return
    print(f"Top {len(rows)} expenses:")
    for r in rows:
        print(f"  #{r['id']}  {r['spent_on']}  {r['category']:<12} {r['amount']:>10.2f}  {r['description'] or ''}")


def cmd_delete(args, conn):
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (args.id,))
    conn.commit()
    print(f"Deleted expense #{args.id}." if cur.rowcount else f"No expense with id {args.id}.")


def cmd_export(args, conn):
    rows = conn.execute(
        "SELECT id, spent_on, category, amount, description FROM expenses ORDER BY spent_on"
    ).fetchall()
    with open(args.filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "category", "amount", "description"])
        writer.writerows([tuple(r) for r in rows])
    print(f"Exported {len(rows)} expenses to {args.filename}")


# ---------- CLI ----------

def build_parser():
    p = argparse.ArgumentParser(description="Expenses tracker")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="add an expense")
    a.add_argument("amount", type=float)
    a.add_argument("category")
    a.add_argument("description", nargs="?", default="")
    a.add_argument("--date", type=valid_date, default=date.today().isoformat())
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="list expenses")
    l.add_argument("--month", help="filter by month, e.g. 2026-11")
    l.add_argument("--category", help="filter by category")
    l.set_defaults(func=cmd_list)

    sub.add_parser("summary", help="totals by category").set_defaults(func=cmd_summary)
    sub.add_parser("monthly", help="monthly totals with change").set_defaults(func=cmd_monthly)

    t = sub.add_parser("top", help="largest expenses")
    t.add_argument("--n", type=int, default=5)
    t.set_defaults(func=cmd_top)

    d = sub.add_parser("delete", help="delete an expense by id")
    d.add_argument("id", type=int)
    d.set_defaults(func=cmd_delete)

    e = sub.add_parser("export", help="export to CSV")
    e.add_argument("filename")
    e.set_defaults(func=cmd_export)

    return p


def main():
    args = build_parser().parse_args()
    conn = get_conn()
    try:
        args.func(args, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
