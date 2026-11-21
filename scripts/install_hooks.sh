#!/bin/sh
# Instalacja jest jawna, ponieważ zmienia lokalną konfigurację Git.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
chmod +x .githooks/pre-commit .githooks/pre-push
git config core.hooksPath .githooks
printf '%s\n' 'OK: lokalne hooki aktywne (.githooks).'
