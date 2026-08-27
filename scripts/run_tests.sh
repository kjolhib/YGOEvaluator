#!/usr/bin/env bash
set -euo pipefail

# Backend
cd "$(dirname "$0")/../backend"
pytest -q "$@"