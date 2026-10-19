#!/usr/bin/env python3
"""
Tool Name   : kloner.py (Pipeline Backend Engine)
Description : Audits HTML input zones, traces where they submit, and rewrites
              endpoints into the export folder.
"""

import argparse
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# --- Terminal ANSI Colors ---
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

JS_PATTERNS = [
    ("fetch()", re.compile(r"""((?:fetch)\s*\(\s*['"`])([^'"`]+)(['"`])""", re.IGNORECASE)),
    ("axios", re.compile(r"""((?:axios\.(?:get|post|put|delete|patch))\s*\(\s*['"`])([^'"`]+)(['"`])""", re.IGNORECASE)),
    ("jQuery AJAX", re.compile(r"""(\$\.(?:post|get|ajax)\s*\(\s*(?:\{[^}]*url\s*:\s*)?['"`])([^'"`]+)(['"`])""", re.IGNORECASE)),
]

def resolve_url(raw_url: str, base_url: str) -> str:
    if not raw_url or raw_url.startswith(("#", "javascript:")):
        return f"{raw_url or '(self)'} [Local DOM]"
    if base_url:
        return urljoin(base_url, raw_url)
    return raw_url

def build_new_endpoint(old_url: str, new_base: str, keep_path: bool) -> str:
    if not keep_path:
        return new_base
    parsed_old = urlparse(old_url)
    path = parsed_old.path.lstrip("/")
    if parsed_old.query:
        path = f"{path}?{parsed_old.query}"
    return urljoin(new_base.rstrip("/") + "/", path)

def process_file_pipeline(filepath: Path, base_url: str, new_url: str, keep_path: bool, rewrite_js: bool):
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"{RED}[!] Error reading {filepath}: {e}{RESET}")
        return None

    soup = BeautifulSoup(content, "html.parser")
    file_audit = {"file": str(filepath), "forms": [], "rewrites_performed": []}

    # Audit & Rewrite Forms and Inputs
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

        resolved_dest = resolve_url(raw_action, base_url)
        file_audit["forms"].append({
            "form_index": idx,
            "id": form.get("id", "-"),
            "method": method,
            "original_destination": resolved_dest,
            "fields": fields
        })

        # Rewrite form action endpoint
        new_action = build_new_endpoint(raw_action, new_url, keep_path)
        form["action"] = new_action
        file_audit["rewrites_performed"].append(f"Form #{idx} action: '{raw_action or '(empty)'}' -> '{new_action}'")

        # Check button formaction overrides
        for btn in form.find_all(["button", "input"]):
            if btn.has_attr("formaction"):
                old_fa = btn["formaction"]
                new_fa = build_new_endpoint(old_fa, new_url, keep_path)
                btn["formaction"] = new_fa
                file_audit["rewrites_performed"].append(f"  └── Button formaction override: '{old_fa}' -> '{new_fa}'")

    # Rewrite JS endpoints if requested
    if rewrite_js:
        for script in soup.find_all("script"):
            if script.string:
                js_text = script.string
                updated_js = js_text
                for label, pattern in JS_PATTERNS:
                    def js_replacer(match):
                        prefix, old_ep, suffix = match.groups()
                        new_ep = build_new_endpoint(old_ep, new_url, keep_path)
                        if old_ep != new_ep:
                            file_audit["rewrites_performed"].append(f"JS {label} endpoint: '{old_ep}' -> '{new_ep}'")
                        return f"{prefix}{new_ep}{suffix}"
                    updated_js = pattern.sub(js_replacer, updated_js)
                if updated_js != js_text:
                    script.string.replace_with(updated_js)

    filepath.write_text(str(soup), encoding="utf-8")
    return file_audit

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("-u", "--new-url", required=True)
    parser.add_argument("-out", "--output-dir", default="changed")
    parser.add_argument("-b", "--base-url", default="")
    parser.add_argument("-k", "--keep-path", action="store_true")
    parser.add_argument("--js", action="store_true")
    args = parser.parse_args()

    src_path = Path(args.target)
    out_path = Path(args.output_dir)

    if out_path.exists():
        shutil.rmtree(out_path)
    
    if src_path.is_dir():
        shutil.copytree(src_path, out_path)
        target_work_path = out_path
    else:
        out_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, out_path / src_path.name)
        target_work_path = out_path / src_path.name

    files = list(target_work_path.rglob("*.html")) + list(target_work_path.rglob("*.htm"))
    if args.js:
        files += list(target_work_path.rglob("*.js"))

    print(f"{YELLOW}[*] Auditing input zones and rewriting endpoints in: {BOLD}{out_path}{RESET}\n")

    all_audits = []
    for fpath in sorted(files):
        audit_res = process_file_pipeline(fpath, args.base_url, args.new_url, args.keep_path, args.js)
        if audit_res and audit_res["forms"]:
            all_audits.append(audit_res)
            print(f"{GREEN}[+] Audited File:{RESET} {CYAN}{fpath}{RESET}")
            for form in audit_res["forms"]:
                print(f"    ├── Form #{form['form_index']} | Destination was: {YELLOW}{form['original_destination']}{RESET}")
                print(f"    └── Input Fields Discovered:")
                for f in form["fields"]:
                    print(f"        └── <{f['tag']} type=\"{f['type']}\"> name=\"{f['name']}\" id=\"{f['id']}\"")
            for rev in audit_res["rewrites_performed"]:
                print(f"    {MAGENTA}--> {rev}{RESET}")
            print("-" * 65)

    report_path = out_path / "input_audit_report.json"
    report_path.write_text(json.dumps(all_audits, indent=2), encoding="utf-8")
    print(f"\n{BOLD}{GREEN}[+] Done! Audit report saved to: {CYAN}{report_path}{RESET}")

if __name__ == "__main__":
    main()