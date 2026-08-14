#!/bin/sh
set -eu

docker compose -f docker-compose.yml -f docker-compose.integration.yml build migrate integration
docker compose -f docker-compose.yml -f docker-compose.integration.yml up -d mysql
cleanup() {
  docker compose -f docker-compose.yml -f docker-compose.integration.yml down -v --remove-orphans
}
trap cleanup EXIT

docker compose -f docker-compose.yml -f docker-compose.integration.yml run --rm migrate
docker compose -f docker-compose.yml -f docker-compose.integration.yml run --rm integration
