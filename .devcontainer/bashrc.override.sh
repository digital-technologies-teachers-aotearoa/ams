
#
# .bashrc.override.sh
#

# persistent bash history
HISTFILE=~/.bash_history
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

# IMPORTANT: Do NOT source /entrypoint here.
# /entrypoint sets 'set -o errexit -o pipefail -o nounset' and then 'exec "$@"'.
# When sourced with no arguments, that 'exec' triggers an error under 'errexit',
# leaving the interactive shell with 'errexit' still enabled. Any failing command
# would then terminate your login shell (and VS Code interprets that as container exit).
# Instead, we (re)construct only the env vars we practically need for dev.

# Recreate DATABASE_URL (entrypoint normally does this). All POSTGRES_* vars
# already come from docker-compose env_file. Provide defaults where sensible.
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -n "${POSTGRES_DB:-}" ]; then
	: "${POSTGRES_USER:=postgres}"
	: "${POSTGRES_HOST:=postgres}"
	: "${POSTGRES_PORT:=5432}"
	export POSTGRES_USER POSTGRES_HOST POSTGRES_PORT
	export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
fi

# Ensure relaxed interactive shell (in case image/base changed defaults)
set +o errexit +o pipefail +o nounset 2>/dev/null || true

# start ssh-agent
# https://code.visualstudio.com/docs/remote/troubleshooting
eval "$(ssh-agent -s)"

alias runserver='python manage.py runserver 0.0.0.0:8000'
