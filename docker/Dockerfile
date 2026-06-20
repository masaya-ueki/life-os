# syntax=docker/dockerfile:1
#
# life-os テスト実行用イメージ（ローカル開発用）
# 設計根拠: docs/adr/0004-docker-test-environment.md
#
# uv 公式イメージ（Python 3.12 + uv 同梱）をベースに、uv workspace を同期して
# pytest / lint-imports を実行できる状態にする。pyproject.toml は requires-python
# >=3.12 のため、ベースの Python バージョンと一致させること。

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# uv 設定:
#   UV_LINK_MODE=copy        … キャッシュからのハードリンク不可警告を避ける
#   UV_COMPILE_BYTECODE=1    … .pyc を事前生成し起動を速くする
#   UV_PROJECT_ENVIRONMENT   … 仮想環境をソースツリー外の固定パスに置く
#                              （compose でソースをマウントしても venv が消えない）
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# 1) 依存解決に必要なマニフェストとロックのみ先にコピーし、
#    dev 依存（pytest / import-linter）の install レイヤをキャッシュする。
#    （ソース変更ではこのレイヤを再実行しない）
COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/
COPY task/pyproject.toml task/
COPY content-sales/pyproject.toml content-sales/
COPY media/pyproject.toml media/
COPY travel/pyproject.toml travel/
COPY english/pyproject.toml english/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --dev

# 2) ワークスペース本体をコピーして同期（各領域を editable で導入）
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --dev

# 既定はスモークテスト実行。compose 側で lint-imports に切り替える。
# --no-sync: 実行時に再同期しない（依存はビルド時に確定済み。実行時のネットワーク不要、
#            かつ compose でソースをマウントしても editable のまま即反映される）。
CMD ["uv", "run", "--no-sync", "pytest"]
