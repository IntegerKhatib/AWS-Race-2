#!/usr/bin/env python3
"""Targeted public-repository scan; no third-party dependencies.

Scans tracked Git files in the current checkout; does NOT scan history or
provide a comprehensive secret-discovery guarantee.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RULES = {
    "private application name": re.compile(r"\bEMP\b|Enterprise Media Platform|emp-source-reference|emp-mediaconvert|Ask\s+EMP", re.I),
    "private source path": re.compile(r"/home/ec2-user/|backend/src/services/|frontend/src/components/"),
    "AWS access key ID": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "private key block": re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC |DSA )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "Stripe secret": re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{10,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    "production private IP": re.compile(r"\b(?:172\.31\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b"),
    "12-digit AWS account number": re.compile(r"(?<!\d)\d{12}(?!\d)"),
    "possible hardcoded credential": re.compile(
        r"(?i)\b(?:password|secret|api[_-]?key|access[_-]?key|auth[_-]?token)\b"
        r"\s*[=:]\s*[\"'][^$\"'\\\n]{16,}[\"']"
    ),
}

def tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], check=True, stdout=subprocess.PIPE)
    return [path.decode("utf-8", "surrogateescape") for path in result.stdout.split(b"\0") if path]

def main() -> int:
    failures = []
    scanned = 0
    for name in tracked_files():
        path = Path(name)
        # Scanner rules contain the very signatures being searched.
        if name == "scripts/security_scan.py":
            continue
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\0" in raw[:4096]:
            continue
        content = raw.decode("utf-8", errors="replace")
        scanned += 1
        for title, rule in RULES.items():
            for match in rule.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                failures.append((name, line, title))
    for name, line, reason in failures:
        print(f"REVIEW: {name}:{line} — {reason}")
    print(f"Checked {scanned} text files; {len(failures)} finding(s).")
    if failures:
        print("Do not publish until findings are investigated.")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
