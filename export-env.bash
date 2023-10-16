#!/bin/bash
# Output commands to export docker .env file into shell environment. Handles quoting strings and comments
# bash usage: eval $(./export-env.bash)
set -e

DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVFILE="${DIRECTORY}/.env"

perl -ne 'chomp; /^[^#]/ && /([^=]+)=([^#]*)/ && print "export $1=\"$2\"\n"' $ENVFILE