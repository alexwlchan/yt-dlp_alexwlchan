#!/usr/bin/env bash

set -o errexit
set -o nounset

# Print a command in blue, then run the command
run_command() {
    echo ""
    echo -e "\033[34m-> $@\033[0m"
    bash -c "$@"
}

run_command 'ruff format'
run_command 'ruff check *.py'
run_command 'ty check *.py'
run_command 'python3 -m pytest --cov=. test_yt-dlp_alexwlchan.py'
