#!/bin/bash
# === 未定義変数参照、パイプ中のエラーで即止める
set -uo pipefail

#########################################
# worktree 削除スクリプト
# - 第1引数: ブランチ名（例: feature/issue-99-add-feature）
# - help 対応
#########################################

# === 出力用のカラー設定
RED="\033[0;31m"
YELLOW="\033[33m"
GREEN="\033[32m"
BLUE="\033[0;34m"
BOLD="\033[1m"
NC="\033[0m"

#########################################
# ヘルプ表示関数
#########################################
show_help() {
  cat <<EOF
# 使い方：
  $(basename "$0") <BRANCH_NAME>

  引数：
    <BRANCH_NAME>  削除するブランチ名を指定
                   例: feature/issue-99-add-feature
                       fix/issue-100-bug-fix

  オプション：
    -h, --help   このヘルプを表示

# 処理内容：
  1. git worktree remove ../{BRANCH_NAME のスラッシュをハイフン置換したパス} で worktree を削除
     例: feature/issue-99-foo → ../feature-issue-99-foo を削除
  2. git branch -D {BRANCH_NAME} でローカルブランチを削除

# 例：
  ./scripts/delete_worktree.sh feature/issue-15-worktree-env-sync
  ./scripts/delete_worktree.sh fix/issue-100-bug-fix

EOF
}

#########################################
# パス設定（共通）
#########################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# main worktree のパスを git から取得（worktree list の先頭行が main）
MAIN_DIR="$(git -C "${SCRIPT_DIR}" worktree list | head -1 | awk '{print $1}')"
REPO_ROOT="$(cd "${MAIN_DIR}/.." && pwd)"

#########################################
# 引数チェック
#########################################
if [ $# -lt 1 ]; then
  echo -e "${RED}[ERROR]${NC} 引数が不足しています。削除するブランチ名を指定してください。"
  show_help
  exit 1
fi

if [[ "${1}" == "-h" || "${1}" == "--help" ]]; then
  show_help
  exit 0
fi

#########################################
# 通常モード: worktree 削除
#########################################
BRANCH="${1}"
# ブランチ名のスラッシュをハイフンに変換してフラットなディレクトリ名を生成
# 例: feature/issue-99-add-feature → feature-issue-99-add-feature
WORKTREE_DIRNAME="${BRANCH//\//-}"
WORKTREE_PATH="${REPO_ROOT}/${WORKTREE_DIRNAME}"

echo -e "${BLUE}[INFO]${NC} === Worktree 削除開始 ==="
echo -e "${BLUE}[INFO]${NC} ブランチ: ${GREEN}${BOLD}${BRANCH}${NC}"
echo -e "${BLUE}[INFO]${NC} パス: ${WORKTREE_PATH}"

#########################################
# worktree の存在確認
#########################################
if ! git -C "${MAIN_DIR}" worktree list | awk '{print $1}' | grep -qx "${WORKTREE_PATH}"; then
  echo -e "${RED}[ERROR]${NC} worktree が存在しません: ${WORKTREE_PATH}"
  echo -e "${BLUE}[INFO]${NC} 現在の worktree 一覧:"
  git -C "${MAIN_DIR}" worktree list
  exit 1
fi

#########################################
# worktree 削除
#########################################
echo -e "${BLUE}[INFO]${NC} git worktree を削除中..."

if ! git -C "${MAIN_DIR}" worktree remove "${WORKTREE_PATH}"; then
  echo -e "${RED}[ERROR]${NC} worktree の削除に失敗しました"
  echo -e "${YELLOW}[HINT]${NC}  未コミットの変更がある場合は --force オプションを使用してください:"
  echo -e "${YELLOW}[HINT]${NC}    git worktree remove --force ${WORKTREE_PATH}"
  exit 1
fi

echo -e "${GREEN}[SUCCESS]${NC} worktree を削除しました: ${WORKTREE_PATH}"

#########################################
# ローカルブランチ削除
#########################################
echo -e "${BLUE}[INFO]${NC} ローカルブランチを削除中..."

if ! git -C "${MAIN_DIR}" branch -D "${BRANCH}"; then
  echo -e "${RED}[ERROR]${NC} ブランチの削除に失敗しました: ${BRANCH}"
  exit 1
fi

echo -e "${GREEN}[SUCCESS]${NC} ブランチを削除しました: ${BRANCH}"

#########################################
# 完了
#########################################
echo ""
echo -e "${GREEN}[SUCCESS]${NC} === Worktree 削除完了 ==="
echo -e "${BLUE}[INFO]${NC}   ブランチ: ${GREEN}${BOLD}${BRANCH}${NC}"
