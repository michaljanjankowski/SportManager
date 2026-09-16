#!/bin/sh
set -eu

# Uruchom Compose z katalogu projektu, niezależnie od bieżącego katalogu.
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"

if ! command -v docker >/dev/null 2>&1; then
    echo "Brak Dockera. Zainstaluj Docker z Docker Compose v2." >&2
    exit 1
fi

docker compose version >/dev/null
exec docker compose up --build -d --wait "$@"
