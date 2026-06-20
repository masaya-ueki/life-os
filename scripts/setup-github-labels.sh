#!/bin/bash
set -uo pipefail

#########################################
# GitHub Issue ラベル一括作成・更新スクリプト
# - 補助 / type / system の 3 カテゴリのラベルを idempotent に作成・更新
# - 廃止予定ラベルの削除にも対応（--cleanup）
# - 設計根拠: guides/development-policy/issue-operation-rules.md
#########################################

# === 出力用のカラー設定
RED="\033[0;31m"
YELLOW="\033[33m"
GREEN="\033[32m"
BLUE="\033[0;34m"
BOLD="\033[1m"
NC="\033[0m"

REPO="${GH_REPO:-masaya-ueki/life-os}"

#########################################
# ヘルプ表示
#########################################
show_help() {
  cat <<EOF
# 使い方：
  $(basename "$0")              全ラベルを作成・更新
  $(basename "$0") --dry-run    実行せず作成計画のみ表示
  $(basename "$0") --cleanup    廃止予定ラベルを削除（要確認プロンプト）
  $(basename "$0") --help       このヘルプを表示

# 環境変数：
  GH_REPO    対象リポジトリ（デフォルト: masaya-ueki/life-os）

# 例：
  $(basename "$0")
  $(basename "$0") --dry-run
  GH_REPO=owner/repo $(basename "$0")

# 関連ドキュメント：
  guides/development-policy/issue-operation-rules.md  ラベル運用ルール
EOF
}

#########################################
# 作成・更新するラベル定義
# 形式: "name|color|description"
#########################################
LABELS=(
  # === 種別ラベル（4 件、旧 Issue Type 相当） ===
  "bug|d73a4a|バグ修正対応"
  "task|fef2c0|一般タスク"
  "product-backlog|bf5b17|複数フェーズの親 Issue"
  "on-hold|cccccc|保留中（着手判断・要件確定待ち等）"

  # === 補助ラベル（2 件） ===
  "no-product-backlog|cfd3d7|ProductBacklog なしの単発 Task Issue"
  "investigation|8a3ffc|調査目的の Issue"

  # === type ラベル（9 件、ブランチプレフィックスと一致） ===
  "type: feat|0e8a16|新機能追加"
  "type: fix|d73a4a|バグ修正"
  "type: design|c5def5|設計作業"
  "type: test|fbca04|テスト追加・修正"
  "type: docs|0075ca|ドキュメント"
  "type: refactor|d93f0b|リファクタリング"
  "type: chore|bfd4f2|ビルド設定・ツール変更"
  "type: ci|1d76db|CI/CD 設定"
  "type: perf|a4f2a4|パフォーマンス改善"

  # === system ラベル（7 件、Conventional Commits の scope と一致） ===
  "system: task|7e57c2|タスク管理"
  "system: travel|7e57c2|旅行の行先管理"
  "system: media|7e57c2|画像・動画管理"
  "system: english|7e57c2|英語学習"
  "system: common|7e57c2|横断的・共通基盤"
  "system: content-sales|7e57c2|自作ツール等の販売管理"
  "system: deps|7e57c2|依存パッケージ"

  # === priority ラベル（3 件、派生課題・改善 Issue の緊急度） ===
  "priority: high|b60205|既存の正しさ・健全性・回帰検知に関わる/他作業の前提"
  "priority: medium|fbca04|機能の実用性・保守性に直結"
  "priority: low|c2e0c6|付加価値的な拡張"
)

#########################################
# 削除する旧ラベル
#########################################
DEPRECATED_LABELS=(
  "documentation"
  "enhancement"
  "duplicate"
  "good first issue"
  "help wanted"
  "invalid"
  "question"
  "wontfix"
  "epic"
  "design"
  "implementation"
  # === データ基盤リポジトリ由来の旧ラベル（life-os では不使用） ===
  "type: hotfix"
  "type: infra"
  "system: data"
  "system: modeling"
  "system: etl"
  "system: terraform-aws"
  "system: terraform-snowflake"
)

#########################################
# 前提チェック
#########################################
check_prerequisites() {
  if ! command -v gh >/dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} gh コマンドが見つかりません。GitHub CLI をインストールしてください。"
    exit 1
  fi

  if ! gh auth status >/dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} GitHub CLI に認証されていません。'gh auth login' を実行してください。"
    exit 1
  fi
}

#########################################
# ラベル作成・更新
#########################################
apply_labels() {
  local dry_run="${1:-false}"

  echo -e "${BOLD}${BLUE}=== ラベル作成・更新 ===${NC}"
  echo -e "対象リポジトリ: ${BOLD}${REPO}${NC}"
  echo ""

  for entry in "${LABELS[@]}"; do
    IFS='|' read -r name color description <<<"${entry}"

    if [[ "${dry_run}" == "true" ]]; then
      printf "  ${YELLOW}[DRY-RUN]${NC} %-35s color=#%s desc=\"%s\"\n" "${name}" "${color}" "${description}"
    else
      if gh label create "${name}" \
        --repo "${REPO}" \
        --color "${color}" \
        --description "${description}" \
        --force >/dev/null 2>&1; then
        printf "  ${GREEN}[OK]${NC}     %-35s color=#%s\n" "${name}" "${color}"
      else
        printf "  ${RED}[FAIL]${NC}   %-35s\n" "${name}"
      fi
    fi
  done
  echo ""
}

#########################################
# 廃止ラベル削除
#########################################
cleanup_labels() {
  local dry_run="${1:-false}"

  echo -e "${BOLD}${YELLOW}=== 廃止ラベル削除 ===${NC}"
  echo -e "対象リポジトリ: ${BOLD}${REPO}${NC}"
  echo ""

  if [[ "${dry_run}" != "true" ]]; then
    echo -e "${YELLOW}以下のラベルを削除します。既存 Issue から該当ラベルが外れます。${NC}"
    for label in "${DEPRECATED_LABELS[@]}"; do
      echo "  - ${label}"
    done
    echo ""
    read -rp "本当に削除しますか? [y/N]: " confirm
    if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
      echo -e "${BLUE}[INFO]${NC} 削除をキャンセルしました。"
      return
    fi
  fi

  for label in "${DEPRECATED_LABELS[@]}"; do
    if [[ "${dry_run}" == "true" ]]; then
      printf "  ${YELLOW}[DRY-RUN]${NC} delete %-35s\n" "${label}"
    else
      if gh label delete "${label}" --repo "${REPO}" --yes >/dev/null 2>&1; then
        printf "  ${GREEN}[OK]${NC}     deleted %-35s\n" "${label}"
      else
        printf "  ${BLUE}[SKIP]${NC}   not found %-35s\n" "${label}"
      fi
    fi
  done
  echo ""
}

#########################################
# メイン
#########################################
main() {
  local mode="apply"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h | --help)
        show_help
        exit 0
        ;;
      --dry-run)
        mode="dry-run"
        shift
        ;;
      --cleanup)
        mode="cleanup"
        shift
        ;;
      *)
        echo -e "${RED}[ERROR]${NC} 不明なオプション: $1"
        show_help
        exit 1
        ;;
    esac
  done

  check_prerequisites

  case "${mode}" in
    apply)
      apply_labels "false"
      echo -e "${GREEN}[INFO]${NC} ラベル作成・更新が完了しました。"
      echo -e "${BLUE}[HINT]${NC} 廃止ラベルを削除する場合は '--cleanup' を指定してください。"
      ;;
    dry-run)
      apply_labels "true"
      cleanup_labels "true"
      echo -e "${BLUE}[INFO]${NC} dry-run を実行しました。実際のラベルは変更されていません。"
      ;;
    cleanup)
      cleanup_labels "false"
      echo -e "${GREEN}[INFO]${NC} 廃止ラベル削除処理が完了しました。"
      ;;
  esac
}

main "$@"
