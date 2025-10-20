#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import hashlib
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
ORCH_DIR = HERE / "orchestrations"


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd):
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    out_lines = []
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        if line:
            print(line, end="")
            out_lines.append(line)
    return proc.returncode, "".join(out_lines)


def latest_run_dir(base: Path) -> Path:
    if not base.exists():
        return None
    dirs = sorted(
        [p for p in base.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return dirs[0] if dirs else None


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_artifacts(run_dir: Path):
    files = {
        "manifest": run_dir / "manifest_def14a.json",
        "log": run_dir / "extraction.log",
        "xlsx": run_dir / "DEF14A_Artifacts.xlsx",
    }
    out = {"run_dir": str(run_dir), "files": {}}
    for k, v in files.items():
        if v and v.exists():
            out["files"][k] = {"path": str(v)}
            if k == "xlsx":
                out["files"][k]["sha256"] = sha256_file(v)
        else:
            out["files"][k] = None
    return out


def write_agreement(record: dict):
    ORCH_DIR.mkdir(exist_ok=True)
    out = ORCH_DIR / f"agreement_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out, "w") as f:
        json.dump(record, f, indent=2)
    print(f"\nAgreement written: {out}\n")


def main():
    parser = argparse.ArgumentParser(
        description="DEF 14A orchestration with governance gates"
    )
    parser.add_argument("--tickers", type=str, required=True)
    parser.add_argument("--user-agent", type=str, required=True)
    parser.add_argument("--throttle", type=float, default=1.5)
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split() if t.strip()]
    out_base = HERE / "def14a_deterministic"

    # Scrape/fetch
    print(f"\n=== DEF14A: Fetch {tickers} ===")
    rc, _ = run_cmd([
        "python3",
        str(HERE / "sec_def14a_deterministic.py"),
        "--tickers",
        " ".join(tickers),
        "--user-agent",
        args.user_agent,
        "--throttle",
        str(args.throttle),
    ])
    if rc != 0:
        die("DEF 14A fetch failed")
    run_dir = latest_run_dir(out_base)
    if not run_dir:
        die("No run directory in def14a_deterministic/")

    # Audit
    print(f"\n=== Derek Audit (DEF14A): {run_dir.name} ===")
    rc, _ = run_cmd(["python3", str(HERE / "derek_def14a_verifier.py"), str(run_dir)])
    audit_pass = (rc == 0)
    print("\nDerek audit pass = ", audit_pass)

    # Record
    art = collect_artifacts(run_dir)
    record = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "pipeline": "def14a",
        "inputs": {
            "tickers": tickers,
            "user_agent": args.user_agent,
            "throttle": args.throttle,
        },
        "runs": [{"tickers": tickers, "artifacts": art}],
        "result": {"accepted_by_derek": audit_pass},
    }
    write_agreement(record)
    sys.exit(0 if audit_pass else 2)


if __name__ == "__main__":
    main()

