#!/bin/bash

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Stampa SaaS - Docker Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Install Docker Desktop (includes Compose)"
    exit 1
fi

echo "✅ Docker: $(docker --version)"
echo "✅ Docker Compose: $(docker-compose --version)"
echo ""

# Build
echo "🔨 Building image..."
docker build -t stampa-saas:latest .
echo "✅ Build complete"
echo ""

# Create volume
echo "📦 Creating data volume..."
docker volume create stampa-data 2>/dev/null || true
echo "✅ Volume ready"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "  ✨ Setup complete!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Next steps:"
echo "    1. GUI mode:       docker-compose up"
echo "    2. Dev mode:       docker-compose -f docker-compose.dev.yml up"
echo "    3. CLI/setup:      docker-compose run stampa-saas cli"
echo "    4. Bash shell:     docker-compose run stampa-saas shell"
echo ""
echo "  📖 Full docs: README_DOCKER.md"
echo ""
