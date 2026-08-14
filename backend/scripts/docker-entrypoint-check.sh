#!/bin/sh
set -eu
case "${1:-}" in
  api|migrate) exec "$@";;
  *) echo "usage: docker-entrypoint-check.sh api|migrate" >&2; exit 64;;
esac
