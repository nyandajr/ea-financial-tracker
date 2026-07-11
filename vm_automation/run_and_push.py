"""VM-side replacement for the GitHub Actions workflow -- run from the VM's
own crontab, not GitHub Actions (see hormuz-strait-monitor for why: GitHub's
schedule trigger delivers a fraction of its configured cadence for anything
sub-hourly, measured repeatedly across this account's repos).

Usage: python run_and_push.py --crypto | --fx
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_FILES = ["data/exchange_rates.csv", "data/crypto_prices.csv", "data/predictions.json"]


def _last_row(csv_path):
    try:
        with open(REPO_DIR / csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[-1] if rows else None
    except FileNotFoundError:
        return None


def build_commit_message(is_crypto):
    if is_crypto:
        row = _last_row("data/crypto_prices.csv")
        if not row:
            return "data: crypto update"
        return (
            "data: crypto update — "
            f"BTC ${float(row['BTC_USD']):,.0f} | "
            f"ETH ${float(row['ETH_USD']):,.0f} | "
            f"BNB ${float(row['BNB_USD']):,.0f}"
        )

    row = _last_row("data/exchange_rates.csv")
    if not row:
        return "data: fx update"
    return (
        "data: fx update — "
        f"USD/TZS {float(row['USD_TZS']):,.2f} | "
        f"USD/KES {float(row['USD_KES']):,.2f} | "
        f"USD/UGX {float(row['USD_UGX']):,.2f}"
    )


def run(*args, cwd=REPO_DIR, check=True):
    return subprocess.run(list(args), cwd=str(cwd), check=check)


def sync_with_remote():
    # --hard, not --soft, and BEFORE any data files are regenerated: reset
    # --soft only moves HEAD, leaving stale index entries for any file this
    # script doesn't explicitly `git add` (e.g. source files edited from
    # another machine), which then get silently recommitted on the next
    # force-push. Learned this the hard way on hormuz-strait-monitor.
    run("git", "fetch", "origin", "main")
    run("git", "reset", "--hard", "origin/main")


def git_commit_and_push(is_crypto):
    # freddynyanda@proton.me is Fred's real, verified GitHub email --
    # a synthetic bot email here would push real commits that silently
    # never count toward his contribution graph
    run("git", "config", "user.name", "nyandajr")
    run("git", "config", "user.email", "freddynyanda@proton.me")
    run("git", "add", *DATA_FILES, check=False)

    diff = run("git", "diff", "--cached", "--quiet", check=False)
    if diff.returncode == 0:
        print("[run_and_push] no changes to commit")
        return

    run("git", "commit", "-m", build_commit_message(is_crypto))
    run("git", "push", "--force", "origin", "HEAD:main")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fx", action="store_true")
    parser.add_argument("--crypto", action="store_true")
    args = parser.parse_args()

    if not args.fx and not args.crypto:
        print("[run_and_push] specify --fx or --crypto", file=sys.stderr)
        sys.exit(1)

    sync_with_remote()

    fetch_args = [sys.executable, "src/fetch_data.py"]
    fetch_args.append("--fx" if args.fx else "--crypto")
    run(*fetch_args)

    run(sys.executable, "src/predict.py")

    git_commit_and_push(args.crypto)
    print("[run_and_push] done")


if __name__ == "__main__":
    main()
