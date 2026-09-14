#!/bin/bash
#
# SessionStart フック: クラウドセッションで `docker compose run --rm test/lint` を
# 実行できる状態にする。
#
# クラウド環境（Claude Code on the web）では次の2点が毎セッション必要になる:
#   1. Docker デーモンの起動
#      セットアップスクリプトのキャッシュはファイルシステムのスナップショットで、
#      起動中のプロセスは保存されない。イメージはディスクに残るがデーモンは残らない。
#   2. TLS 傍受プロキシの CA 配置
#      ホストのシステム信頼ストアには CA が導入済みだが、ビルドコンテナは
#      素のベースイメージのため持っておらず `uv sync` が
#      `invalid peer certificate: UnknownIssuer` で失敗する。
#      詳細: docker/certs/README.md
#
# ローカル開発では何もしない（Docker Desktop 等が既に動いている前提）。
# 設計根拠: docs/adr/0006-docker-test-environment.md

set -euo pipefail

# ローカルセッションでは対象外
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
# ホストのシステム信頼ストア。傍受プロキシの CA が 1ファイル 1証明書 で置かれている。
# `update-ca-certificates` は 1ファイルに複数証明書があるとスキップするため、
# 束ねられた /root/.ccr/ca-bundle.crt ではなくこちらを使う。
HOST_CA_DIR="/usr/local/share/ca-certificates"
CA_DEST_DIR="${PROJECT_DIR}/docker/certs"
DOCKERD_LOG="/tmp/dockerd.log"

log() { echo "[session-start] $*"; }

# --- 1. プロキシ CA をビルドコンテキストへ配置（毎セッション: リポジトリは再 clone される） ---
mkdir -p "$CA_DEST_DIR"
ca_count=0
shopt -s nullglob
for src in "$HOST_CA_DIR"/*.crt; do
  dest="${CA_DEST_DIR}/$(basename "$src")"
  cmp -s "$src" "$dest" || cp "$src" "$dest"
  ca_count=$((ca_count + 1))
done
shopt -u nullglob

if [ "$ca_count" -gt 0 ]; then
  log "プロキシ CA を ${ca_count} 件配置: docker/certs/"
else
  log "追加 CA が見つからないためスキップ: ${HOST_CA_DIR}"
fi

# --- 2. Docker デーモンを起動 ---
if ! command -v dockerd >/dev/null 2>&1; then
  log "dockerd が無いためスキップ"
  exit 0
fi

start_dockerd() {
  # 前回の異常終了で PID ファイルが残っていると dockerd は起動を拒否する。
  # プロセスが実在しない場合だけ掃除する（動作中のデーモンは消さない）。
  if [ -f /var/run/docker.pid ]; then
    stale_pid="$(cat /var/run/docker.pid 2>/dev/null || true)"
    if [ -z "$stale_pid" ] || ! kill -0 "$stale_pid" 2>/dev/null; then
      rm -f /var/run/docker.pid
    fi
  fi

  setsid dockerd >"$DOCKERD_LOG" 2>&1 </dev/null &

  for _ in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

if docker info >/dev/null 2>&1; then
  log "Docker デーモンは起動済み"
else
  log "Docker デーモンを起動中..."
  if start_dockerd; then
    log "Docker デーモンを起動した"
  elif start_dockerd; then
    # 直前のデーモンの終了処理と競合した場合に備えて 1 度だけ再試行する
    log "Docker デーモンを起動した（再試行）"
  else
    # デーモンが上がらなくてもセッション自体は継続させる（テスト以外の作業は可能なため）
    log "警告: Docker デーモンの起動に失敗した。詳細は $DOCKERD_LOG"
    exit 0
  fi
fi

# --- 3. テスト用イメージを用意（環境キャッシュに無い初回のみビルド） ---
if docker image inspect life-os-test:local >/dev/null 2>&1; then
  log "life-os-test:local は準備済み"
else
  log "life-os-test:local をビルド中（初回のみ・数分かかる）..."
  if (cd "$PROJECT_DIR" && docker compose build >/tmp/compose-build.log 2>&1); then
    log "ビルド完了"
  else
    log "警告: ビルドに失敗した。詳細は /tmp/compose-build.log"
  fi
fi
