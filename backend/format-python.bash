#!/usr/bin/env bash

set -o errexit -o noclobber -o nounset -o pipefail

directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mapfile -t files < <(find $directory -path $directory/.venv -prune -false -o -wholename "${directory}/*.py")

echo "black"
poetry run black "${files[@]}"

echo "isort"
poetry run isort "${files[@]}"