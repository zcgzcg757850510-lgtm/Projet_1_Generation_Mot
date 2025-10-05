#!/usr/bin/env bash
set -e

# 目标路径（mmh_pipeline 根）
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RAW_DIR="$ROOT_DIR/data/mmh_raw"
REPO_URL="https://github.com/skishore/makemeahanzi.git"

mkdir -p "$RAW_DIR"

if [ -d "$RAW_DIR/.git" ]; then
  echo "==> Updating makemeahanzi..."
  git -C "$RAW_DIR" pull --ff-only
else
  echo "==> Cloning makemeahanzi..."
  git clone --depth 1 "$REPO_URL" "$RAW_DIR"
fi

echo "==> Done. Raw data at: $RAW_DIR"
