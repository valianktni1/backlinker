#!/bin/bash
# =============================================================
# TrueNAS Scale - Backlinker Setup Script
# =============================================================
# Dataset: /mnt/apps/backlinkgen
# Repo: https://github.com/valianktni1/backlinker
# Port: 3333
# =============================================================

set -e

DATASET_PATH="/mnt/apps/backlinkgen"
REPO_URL="https://github.com/valianktni1/backlinker.git"
REPO_PATH="$DATASET_PATH/repo"

echo "=========================================="
echo "Backlinker - TrueNAS Scale Setup"
echo "=========================================="

# Create directories
echo "[1/5] Creating directories..."
mkdir -p "$DATASET_PATH/mongodb"
mkdir -p "$DATASET_PATH/backend_logs"

# Clone or update repo
if [ -d "$REPO_PATH/.git" ]; then
    echo "[2/5] Updating repository..."
    cd "$REPO_PATH"
    git pull origin main
else
    echo "[2/5] Cloning repository..."
    git clone "$REPO_URL" "$REPO_PATH"
fi

# Create .env file if it doesn't exist
if [ ! -f "$DATASET_PATH/.env" ]; then
    echo "[3/5] Creating .env file..."
    cat > "$DATASET_PATH/.env" << 'EOF'
# TrueNAS Backlinker Configuration
JWT_SECRET=CHANGE_THIS_TO_A_RANDOM_STRING_AT_LEAST_32_CHARS_LONG

# Your TrueNAS IP address (change this!)
EXTERNAL_URL=http://YOUR_TRUENAS_IP:3333

# SerpAPI - 100 free Google searches/month
SERPAPI_API_KEY=21372238b614ac864de8dd246672e9014daa8586878e9b5d58e9f4ff3f52bbcc

# SendGrid (optional) - for email outreach
SENDGRID_API_KEY=
SENDER_EMAIL=
EOF
    echo "   >>> IMPORTANT: Edit $DATASET_PATH/.env with your settings!"
else
    echo "[3/5] .env file exists, skipping..."
fi

# Build frontend
echo "[4/5] Building frontend..."
cd "$REPO_PATH/frontend"
if command -v yarn &> /dev/null; then
    yarn install
    REACT_APP_BACKEND_URL=$(grep EXTERNAL_URL "$DATASET_PATH/.env" | cut -d '=' -f2) yarn build
elif command -v npm &> /dev/null; then
    npm install
    REACT_APP_BACKEND_URL=$(grep EXTERNAL_URL "$DATASET_PATH/.env" | cut -d '=' -f2) npm run build
else
    echo "ERROR: yarn or npm not found. Install Node.js first."
    exit 1
fi

# Copy docker-compose to dataset
echo "[5/5] Setting up docker-compose..."
cp "$REPO_PATH/docker-compose.yml" "$DATASET_PATH/docker-compose.yml"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit your settings: nano $DATASET_PATH/.env"
echo "2. Start the app:"
echo "   cd $DATASET_PATH"
echo "   docker-compose up -d"
echo ""
echo "3. Access at: http://YOUR_TRUENAS_IP:3333"
echo ""
