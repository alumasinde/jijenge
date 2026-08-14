#!/bin/sh
set -eu
test -f docker-compose.yml
test -f Dockerfile
test -f .env.example
grep -q "service_completed_successfully" docker-compose.yml
grep -q "service_healthy" docker-compose.yml
grep -q "target: migrate" docker-compose.yml
grep -q "target: api" docker-compose.yml
echo "Docker configuration structure: OK"
