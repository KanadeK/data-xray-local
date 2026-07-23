#!/usr/bin/env sh
set -eu
python -m build
python "$(dirname "$0")/demo.py"
python "$(dirname "$0")/package_release.py"

