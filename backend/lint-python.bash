#!/usr/bin/env bash

set -o errexit -o noclobber -o nounset -o pipefail

directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mapfile -t files < <(find $directory -path $directory/.venv -prune -false -o -wholename "${directory}/*.py")

echo "flake8"
poetry run flake8 "${files[@]}"

echo "mypy"
poetry run mypy "${files[@]}"

echo "black"
poetry run black --check "${files[@]}"

echo "isort"
poetry run isort --check-only "${files[@]}"
