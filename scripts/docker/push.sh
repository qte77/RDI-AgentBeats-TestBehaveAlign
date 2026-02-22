#!/bin/bash
# Push Docker images to GitHub Container Registry (GHCR)
#
# Authenticates with GHCR using GHCR_PAT token and pushes both
# Green and Purple agent images with :latest tag.
#
# Prerequisites:
#   - GHCR_PAT environment variable must be set with a GitHub Personal Access Token
#   - Images must be built first (run ./build.sh)
#
# Usage:
#   export GHCR_PAT=<your-github-pat>
#   export GH_USERNAME=<your-github-username>
#   bash ./push.sh

set -e

# Source common utilities (DRY principle)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo ""
echo "Pushing Docker Images to GHCR"
echo "=============================="
echo ""

# Validate required environment variables
GH_USERNAME="${GH_USERNAME:-}"
GHCR_PAT="${GHCR_PAT:-}"
GREEN_AGENT_IMAGE_NAME="testbehavealign-green"
PURPLE_AGENT_IMAGE_NAME="testbehavealign-purple"

if [ -z "$GH_USERNAME" ]; then
  error "GH_USERNAME environment variable is not set"
  echo ""
  echo "Usage:"
  echo "  export GH_USERNAME=<your-github-username>"
  echo "  export GHCR_PAT=<your-github-pat>"
  echo "  bash ./push.sh"
  echo ""
  exit 1
fi

if [ -z "$GHCR_PAT" ]; then
  error "GHCR_PAT environment variable is not set"
  echo ""
  echo "The GHCR_PAT token is required for GHCR authentication."
  echo ""
  echo "To create a Personal Access Token (PAT):"
  echo "  1. Go to https://github.com/settings/tokens"
  echo "  2. Click 'Generate new token (classic)'"
  echo "  3. Select scopes: write:packages, read:packages, delete:packages"
  echo "  4. Copy the generated token"
  echo ""
  echo "Usage:"
  echo "  export GH_USERNAME=<your-github-username>"
  echo "  export GHCR_PAT=<your-github-pat>"
  echo "  bash ./push.sh"
  echo ""
  exit 1
fi

info "GitHub username: $GH_USERNAME"
info "Registry: ghcr.io"
echo ""

# Authenticate with GHCR
info "[1/3] Authenticating with GitHub Container Registry..."
echo "$GHCR_PAT" | docker login ghcr.io -u "$GH_USERNAME" --password-stdin

success "Authentication successful"
echo ""

# Push Green Agent
info "[2/3] Pushing ${GREEN_AGENT_IMAGE_NAME}..."
docker push ghcr.io/${GH_USERNAME}/${GREEN_AGENT_IMAGE_NAME}:latest

success "Green agent pushed successfully"
echo ""

# Push Purple Agent
info "[3/3] Pushing ${PURPLE_AGENT_IMAGE_NAME}..."
docker push ghcr.io/${GH_USERNAME}/${PURPLE_AGENT_IMAGE_NAME}:latest

success "Purple agent pushed successfully"
echo ""

# Display summary
success "Push Complete!"
echo ""
echo "Images pushed to GHCR:"
echo "  - ghcr.io/${GH_USERNAME}/${GREEN_AGENT_IMAGE_NAME}:latest"
echo "  - ghcr.io/${GH_USERNAME}/${PURPLE_AGENT_IMAGE_NAME}:latest"
echo ""
echo "View your packages at:"
echo "  https://github.com/${GH_USERNAME}?tab=packages"
echo ""
echo "To use these images, update scenario.toml with:"
echo "  ghcr_url = \"ghcr.io/${GH_USERNAME}/${GREEN_AGENT_IMAGE_NAME}:latest\""
echo ""
