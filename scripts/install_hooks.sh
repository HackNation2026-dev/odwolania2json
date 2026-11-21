#!/bin/sh
# Jeden właściciel hooków: framework pre-commit, także dla pre-push.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python="${PYTHON:-python3}"
"$python" -m pre_commit --version
hooks_path="$(git config --local --get core.hooksPath || true)"
case "$hooks_path" in
  .githooks) git config --local --unset core.hooksPath ;;
  '') ;;
  *) printf '%s\n' "FAIL: obce core.hooksPath=$hooks_path; uzgodnij konfigurację." >&2; exit 1 ;;
esac
"$python" -m pre_commit install --install-hooks --hook-type pre-commit --hook-type pre-push
printf '%s\n' 'OK: pre-commit zarządza pre-commit i pre-push.'
printf '%s\n' 'Hooki wołają python3; ci.py użyje CI_PYTHON albo .venv/bin/python z narzędziami.'
