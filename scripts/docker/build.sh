#!/bin/bash
# Build Docker images for GHCR deployment
#
# Builds both Bulletproof Green and Purple agents for linux/amd64 platform.
# Images are tagged locally and ready for push to GitHub Container Registry.

set -e

# Source common utilities (DRY principle)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo ""
echo "Building Docker Images for GHCR"
echo "==============================="
echo ""

# Get the GitHub username for image naming (use GH_USERNAME for consistency)
GH_USERNAME="${GH_USERNAME:-}"

if [ -z "$GH_USERNAME" ]; then
  info "GH_USERNAME not set, using 'local' as default"
  GH_USERNAME="local"
fi

info "Building for platform: linux/amd64"
info "GitHub username: $GH_USERNAME"
echo ""

# Build Green Agent
info "[1/2] Building Bulletproof Green Agent..."
docker build \
  --platform linux/amd64 \
  -f Dockerfile.green \
  -t ghcr.io/${GH_USERNAME}/bulletproof-green:latest \
  .

success "Green agent built successfully"
echo ""

# Build Purple Agent
info "[2/2] Building Bulletproof Purple Agent..."
docker build \
  --platform linux/amd64 \
  -f Dockerfile.purple \
  -t ghcr.io/${GH_USERNAME}/bulletproof-purple:latest \
  .

success "Purple agent built successfully"
echo ""

# Display summary
success "Build Complete!"
echo ""
echo "Images built:"
echo "  - ghcr.io/${GH_USERNAME}/bulletproof-green:latest"
echo "  - ghcr.io/${GH_USERNAME}/bulletproof-purple:latest"
echo ""
echo "Next step: Run scripts/push.sh to push images to GHCR"
echo ""
