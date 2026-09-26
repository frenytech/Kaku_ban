#!/usr/bin/env python3
# --- kaku_wa_checker.py ---
# Bulk WhatsApp number status checker. Passive reads only.

import argparse
import csv
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

WA_CHECK_URL = "https://v.whatsapp.net/v2/exist"

DEFAULT_HEADERS = {
    "User-Agent": "WhatsApp/2.24.9.78 Android/14 Device/Pixel-6",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

CC_POOL = ["1", "44", "49", "33", "34", "39", "62", "91", "234", "27"]


def normalize_number(raw, default_cc="1"):
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None
    if len(digits) <= 11 and not digits.startswith(tuple(CC_POOL)):
        digits = default_cc + digits
    return digits


def load_numbers(path):
    if path.endswith(".csv"):
        with open(path, newline="") as f:
            return [row[0] for row in csv.reader(f) if row]
    with open(path) as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def check_number(number, session, retries=2, timeout=8.0):
    payload = {
        "cc": CC_POOL[hash(number) % len(CC_POOL)],
        "in": number,
        "lg": "en",
        "lc": "US",
        "id": "".join(random.choices("0123456789abcdef", k=32)),
        "mistyped": "6",
        "network_radio_type": "1",
        "simnum": "1",
        "s": "",
        "changed_pin_md5": "",
        "feo2_query_status": "0",
        "authkey": "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=32)),
    }
    for attempt in range(retries + 1):
        try:
            r = session.post(WA_CHECK_URL, data=payload, timeout=timeout, verify=True)
            if r.status_code == 429:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            if r.status_code != 200:
                return {"number": number, "status": "http_error", "code": r.status_code}
            try:
                data = r.json()
            except ValueError:
                return {"number": number, "status": "parse_error", "raw": r.text[:200]}
            return classify(number, data)
        except requests.RequestException as e:
            if attempt == retries:
                return {"number": number, "status": "network_error", "error": str(e)}
            time.sleep(1.5 ** attempt)
    return {"number": number, "status": "unknown"}


def classify(number, data):
    status = data.get("status", "")
    if status == "1":
        return {"number": number, "status": "registered",
                "wa_id": data.get("wa_id", ""), "biz": data.get("biz", False)}
    if status == "2":
        reason = data.get("reason", "")
        if "ban" in str(reason).lower() or data.get("ban", False):
            return {"number": number, "status": "banned", "reason": reason}
        return {"number": number, "status": "not_registered", "reason": reason}
    if status == "3":
        return {"number": number, "status": "invalid", "reason": data.get("reason")}
    if status == "6":
        return {"number": number, "status": "temp_banned", "reason": data.get("reason")}
    if status == "7":
        return {"number": number, "status": "bad_country", "reason": data.get("reason")}
    return {"number": number, "status": "unknown", "raw": data}


def run(numbers, workers=8, delay=0.4):
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    results = []

    def worker(num):
        time.sleep(random.uniform(0, delay))
        res = check_number(num, session)
        print(f"[{res.get('status','?'):>15}] {num}")
        return res

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker, n): n for n in numbers}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def summarize(results):
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("\n=== SUMMARY ===")
    for status, n in sorted(counts.items()):
        print(f"  {status:<20} {n}")


def main():
    ap = argparse.ArgumentParser(description="Kaku WhatsApp number checker.")
    ap.add_argument("input", help="numbers.txt or numbers.csv")
    ap.add_argument("-w", "--workers", type=int, default=8)
    ap.add_argument("-d", "--delay", type=float, default=0.4)
    ap.add_argument("-o", "--output", default="wa_results.json")
    ap.add_argument("--default-cc", default="1")
    args = ap.parse_args()

    raw = load_numbers(args.input)
    numbers = [n for n in (normalize_number(r, args.default_cc) for r in raw) if n]
    if not numbers:
        print("[!] No valid numbers.")
        sys.exit(1)

    print(f"[*] Checking {len(numbers)} numbers, {args.workers} workers...")
    results = run(numbers, args.workers, args.delay)
    summarize(results)

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "results": results,
    }
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    buckets = {}
    for r in results:
        buckets.setdefault(r["status"], []).append(r["number"])
    for status, nums in buckets.items():
        with open(f"wa_{status}.txt", "w") as f:
            f.write("\n".join(nums))

    print(f"\n[+] Saved: {args.output}")
    for status, nums in buckets.items():
        print(f"[+] {len(nums):>5} -> wa_{status}.txt")


if __name__ == "__main__":
    main()
