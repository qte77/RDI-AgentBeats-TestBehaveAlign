#!/bin/bash
################################################################################
# COMMON TEST UTILITIES
################################################################################
#
# Shared functions and utilities for E2E test scripts.
# Source this file in test scripts: source "$(dirname "$0")/common.sh"
#
################################################################################

# Color codes for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export NC='\033[0m' # No Color

# A2A standard paths
export AGENT_CARD_PATH="/.well-known/agent-card.json"

#
# Load settings from Python settings.py in ONE call (DRY principle)
#
# Returns space-separated values: host port url
# Usage: read -r HOST PORT URL < <(load_purple_agent_settings)
#
load_purple_agent_settings() {
    python -c "
from bulletproof_purple.settings import settings as purple_settings
from bulletproof_green.settings import settings as green_settings
print(purple_settings.host, purple_settings.port, green_settings.purple_agent_url)
" 2>/dev/null || echo "localhost 8001 http://localhost:8001"
}

#
# Check if Purple agent is responding at given URL
#
# Args:
#   $1: Purple agent URL (e.g., http://localhost:8001)
#
# Returns:
#   0 if agent is available, 1 otherwise
#
check_purple_agent_available() {
    local url="$1"
    curl -s -f "${url}${AGENT_CARD_PATH}" > /dev/null 2>&1
}

#
# Wait for Purple agent to be ready with retries
#
# Args:
#   $1: Purple agent URL
#   $2: Max retries (default: 10)
#   $3: Retry delay in seconds (default: 1)
#
# Returns:
#   0 if agent became ready, 1 if timeout
#
wait_for_purple_agent() {
    local url="$1"
    local max_retries="${2:-10}"
    local retry_delay="${3:-1}"
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if check_purple_agent_available "$url"; then
            return 0
        fi
        retry_count=$((retry_count + 1))
        echo -e "${YELLOW}  Waiting for Purple agent... (attempt $retry_count/$max_retries)${NC}" >&2
        sleep "$retry_delay"
    done

    return 1
}

#
# Cleanup function for Purple agent processes
#
# Requires: PURPLE_PID environment variable set to agent PID
#
cleanup_purple_agent() {
    if [ ! -z "$PURPLE_PID" ]; then
        echo -e "${YELLOW}Stopping Purple agent (PID: $PURPLE_PID)...${NC}" >&2
        kill $PURPLE_PID 2>/dev/null || true
        wait $PURPLE_PID 2>/dev/null || true
    fi
}

#
# Print colored status messages
#
info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

#
# Docker Compose utilities
#

# Check if docker-compose is available
is_docker_available() {
    command -v docker-compose >/dev/null 2>&1
}

# Start Purple agent via docker-compose
# Returns: 0 on success, 1 on failure
start_purple_docker() {
    local purple_url="$1"
    local compose_file="${2:-docker-compose-local.yml}"

    info "Starting Purple agent via docker-compose..."
    docker-compose -f "$compose_file" up -d purple || return 1

    info "Waiting for Purple agent to be ready..."
    if wait_for_purple_agent "$purple_url" 20 2; then
        success "Purple agent ready (Docker)"
        return 0
    else
        error "Purple agent failed to start (Docker)"
        return 1
    fi
}

# Stop Purple agent via docker-compose
stop_purple_docker() {
    local compose_file="${1:-docker-compose-local.yml}"
    info "Stopping Purple agent (Docker)..."
    docker-compose -f "$compose_file" stop purple
}

# Cleanup Docker containers
cleanup_purple_docker() {
    local compose_file="${1:-docker-compose-local.yml}"
    if [ ! -z "$PURPLE_DOCKER" ]; then
        stop_purple_docker "$compose_file"
    fi
}
