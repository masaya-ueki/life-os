#!/bin/bash
# === 未定義変数参照、パイプ中のエラーで即止める
set -uo pipefail

#########################################
# worktree 作成 + .env シンボリックリンク設定スクリプト
# - 第1引数: ブランチ名（例: feature/issue-99-add-feature）
#          または --apply-all（既存 worktree 全体に一括適用）
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
  $(basename "$0") --apply-all

  引数：
    <BRANCH_NAME>  新規ブランチ名を指定して worktree を作成
                   例: feature/issue-99-add-feature
                       fix/issue-100-bug-fix

  オプション：
    --apply-all  既存の全 worktree に .env シンボリックリンクを一括設定
                 ※ .env が既に存在する worktree はスキップ
    --init-main  main ブランチ用の local/.env.local を生成
                 ※ 初回セットアップ時に一度だけ実行する
    -h, --help   このヘルプを表示

# 処理内容（通常モード）：
  1. git worktree add で新規ブランチを作成
     ※ ブランチ名のスラッシュはハイフンに変換してフラットなディレクトリ名にする
        例: feature/issue-99-add-feature → ../feature-issue-99-add-feature
  2. main/local/.env が存在する場合、{worktree}/local/.env へのシンボリックリンクを作成
  3. main/local/.env が存在しない場合、警告を表示してリンク作成をスキップ

# 処理内容（--apply-all モード）：
  1. git worktree list で全 worktree を取得
  2. main worktree を除く全 worktree に .env シンボリックリンクを設定
  3. .env が既に存在する worktree はスキップ（上書きしない）

# 処理内容（--init-main モード）：
  1. main ブランチのブランチ名を取得
  2. main/local/.env.local を生成（COMPOSE_PROJECT_NAME=data-platform-main）
  ※ 初回セットアップ時に一度だけ実行する

# 例：
  ./scripts/create_worktree.sh feature/issue-15-worktree-env-sync
  ./scripts/create_worktree.sh fix/issue-100-bug-fix
  ./scripts/create_worktree.sh --apply-all
  ./scripts/create_worktree.sh --init-main

# セッション切れ後の運用：
  シンボリックリンクはセッション切れでは消えません。
  MFA 認証情報の期限切れ時は main/local で再実行するだけで全 worktree に反映されます:
    cd main/local
    . ./setup_mfa_to_env/iam_role/setup_mfa_to_env.sh dev <profile>

EOF
}

#########################################
# パス設定（共通）
#########################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# main worktree のパスを git から取得（worktree list の先頭行が main）
MAIN_DIR="$(git -C "${SCRIPT_DIR}" worktree list | head -1 | awk '{print $1}')"
REPO_ROOT="$(cd "${MAIN_DIR}/.." && pwd)"
MAIN_ENV="${MAIN_DIR}/local/.env"

#########################################
# .env.local 生成関数
#########################################
generate_env_local() {
  local worktree_path="$1"
  local branch="$2"
  local env_local_path="${worktree_path}/local/.env.local"

  # ブランチ名を正規化: 英数字とハイフン以外を除去し、連続ハイフンを単一化
  local branch_normalized
  branch_normalized=$(echo "${branch}" | sed 's/[^a-zA-Z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
  local compose_project_name="data-platform-${branch_normalized}"

  echo "COMPOSE_PROJECT_NAME=${compose_project_name}" > "${env_local_path}"
  echo -e "${GREEN}[SUCCESS]${NC} .env.local を生成しました: ${env_local_path}"
  echo -e "${BLUE}[INFO]${NC}   COMPOSE_PROJECT_NAME=${compose_project_name}"
}

#########################################
# .env シンボリックリンク設定関数
#########################################
setup_env_symlink() {
  local worktree_path="$1"
  local worktree_env="${worktree_path}/local/.env"

  if [ -L "${worktree_env}" ]; then
    # 既にシンボリックリンク → 参照先を確認
    local link_target
    link_target="$(readlink "${worktree_env}")"
    if [ "${link_target}" = "${MAIN_ENV}" ]; then
      echo -e "${BLUE}[SKIP]${NC}    既に設定済み: ${worktree_path##*/}"
    else
      echo -e "${YELLOW}[WARN]${NC}    別の場所へのリンクが存在します: ${worktree_path##*/} -> ${link_target}"
    fi
  elif [ -f "${worktree_env}" ]; then
    # 実ファイルが存在 → スキップ（上書きしない）
    echo -e "${YELLOW}[SKIP]${NC}    .env が既に存在します（実ファイル）: ${worktree_path##*/}"
  elif [ -f "${MAIN_ENV}" ]; then
    # リンク未作成 + main/.env あり → リンク作成
    ln -sf "${MAIN_ENV}" "${worktree_env}"
    echo -e "${GREEN}[SUCCESS]${NC} ${worktree_path##*/}/local/.env -> main/local/.env"
  else
    # main/.env もなし → 警告のみ
    echo -e "${YELLOW}[WARN]${NC}    main/local/.env が存在しません。MFA 認証後に再実行してください。"
  fi
}

#########################################
# 引数チェック
#########################################
if [ $# -lt 1 ]; then
  echo -e "${RED}[ERROR]${NC} 引数が不足しています。ブランチ名または --apply-all を指定してください。"
  show_help
  exit 1
fi

if [[ "${1}" == "-h" || "${1}" == "--help" ]]; then
  show_help
  exit 0
fi

#########################################
# --apply-all モード
#########################################
if [[ "${1}" == "--apply-all" ]]; then
  echo -e "${BLUE}[INFO]${NC} === 既存 worktree への .env シンボリックリンク一括設定 ==="
  echo -e "${BLUE}[INFO]${NC} main: ${MAIN_DIR}"
  echo ""

  # git worktree list から main 以外の worktree を取得
  while IFS= read -r line; do
    worktree_path="$(echo "${line}" | awk '{print $1}')"

    # main worktree 自体はスキップ
    if [ "${worktree_path}" = "${MAIN_DIR}" ]; then
      continue
    fi

    setup_env_symlink "${worktree_path}"
  done < <(git -C "${MAIN_DIR}" worktree list)

  echo ""
  echo -e "${GREEN}[SUCCESS]${NC} === 一括設定完了 ==="
  exit 0
fi

#########################################
# --init-main モード
#########################################
if [[ "${1}" == "--init-main" ]]; then
  echo -e "${BLUE}[INFO]${NC} === main ブランチ用 .env.local 生成 ==="
  generate_env_local "${MAIN_DIR}" "main"
  echo ""
  echo -e "${GREEN}[SUCCESS]${NC} === 生成完了 ==="
  echo -e "${BLUE}[INFO]${NC} ${MAIN_DIR}/local/.env.local"
  exit 0
fi

#########################################
# 通常モード: 新規 worktree 作成
#########################################
BRANCH="${1}"
# ブランチ名のスラッシュをハイフンに変換してフラットなディレクトリ名を生成
# 例: feature/issue-99-add-feature → feature-issue-99-add-feature
WORKTREE_DIRNAME="${BRANCH//\//-}"
WORKTREE_PATH="${REPO_ROOT}/${WORKTREE_DIRNAME}"
WORKTREE_ENV="${WORKTREE_PATH}/local/.env"

echo -e "${BLUE}[INFO]${NC} === Worktree 作成開始 ==="
echo -e "${BLUE}[INFO]${NC} ブランチ: ${GREEN}${BOLD}${BRANCH}${NC}"
echo -e "${BLUE}[INFO]${NC} パス: ${WORKTREE_PATH}"

#########################################
# ブランチ名の重複チェック
#########################################
if git -C "${MAIN_DIR}" worktree list | grep -q "${WORKTREE_PATH}"; then
  echo -e "${RED}[ERROR]${NC} worktree が既に存在します: ${WORKTREE_PATH}"
  exit 1
fi

if [ -d "${WORKTREE_PATH}" ]; then
  echo -e "${RED}[ERROR]${NC} ディレクトリが既に存在します: ${WORKTREE_PATH}"
  exit 1
fi

#########################################
# worktree 作成
#########################################
echo -e "${BLUE}[INFO]${NC} git worktree を作成中..."

if ! git -C "${MAIN_DIR}" worktree add "${WORKTREE_PATH}" -b "${BRANCH}"; then
  echo -e "${RED}[ERROR]${NC} worktree の作成に失敗しました"
  exit 1
fi

echo -e "${GREEN}[SUCCESS]${NC} worktree を作成しました"

#########################################
# .env.local 生成
#########################################
echo -e "${BLUE}[INFO]${NC} .env.local を生成中..."
generate_env_local "${WORKTREE_PATH}" "${BRANCH}"

#########################################
# .env シンボリックリンク作成
#########################################
echo -e "${BLUE}[INFO]${NC} .env シンボリックリンクを設定中..."

if [ -f "${MAIN_ENV}" ]; then
  ln -sf "${MAIN_ENV}" "${WORKTREE_ENV}"
  echo -e "${GREEN}[SUCCESS]${NC} .env シンボリックリンクを作成しました"
  echo -e "${BLUE}[INFO]${NC}   ${WORKTREE_ENV}"
  echo -e "${BLUE}[INFO]${NC}   -> ${MAIN_ENV}"
else
  echo -e "${YELLOW}[WARN]${NC} main/local/.env が存在しません（MFA 認証がまだの場合）"
  echo -e "${YELLOW}[WARN]${NC} MFA 認証後に以下のコマンドでリンクを作成してください:"
  echo -e "${YELLOW}[WARN]${NC}   ln -sf ${MAIN_ENV} ${WORKTREE_ENV}"
fi

#########################################
# 完了
#########################################
echo ""
echo -e "${GREEN}[SUCCESS]${NC} === Worktree セットアップ完了 ==="
echo -e "${BLUE}[INFO]${NC}   ブランチ: ${GREEN}${BOLD}${BRANCH}${NC}"
echo -e "${BLUE}[INFO]${NC}   パス: ${WORKTREE_PATH}"
