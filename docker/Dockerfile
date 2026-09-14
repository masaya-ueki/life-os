# syntax=docker/dockerfile:1
#
# life-os テスト実行用イメージ（ローカル開発用）
# 設計根拠: docs/adr/0006-docker-test-environment.md
#
# uv 公式イメージ（Python 3.12 + uv 同梱）をベースに、uv workspace を同期して
# pytest / lint-imports を実行できる状態にする。pyproject.toml は requires-python
# >=3.12 のため、ベースの Python バージョンと一致させること。

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# 追加 CA（任意）: TLS 傍受プロキシが挟まる環境向け。
# docker/certs/ に *.crt があれば信頼ストアへ導入する。証明書が無ければ no-op。
# 詳細と配置手順: docker/certs/README.md
COPY docker/certs/ /usr/local/share/ca-certificates/extra/
RUN update-ca-certificates

# uv 設定:
#   UV_LINK_MODE=copy        … キャッシュからのハードリンク不可警告を避ける
#   UV_COMPILE_BYTECODE=1    … .pyc を事前生成し起動を速くする
#   UV_PROJECT_ENVIRONMENT   … 仮想環境をソースツリー外の固定パスに置く
#                              （compose でソースをマウントしても venv が消えない）
#   UV_NATIVE_TLS=1          … uv は既定でバンドル済みルート証明書を使い OS の信頼ストアを
#                              見ない。上の追加 CA を効かせるために OS 側を使わせる。
#                              追加 CA が無い環境では標準のルート証明書を使うだけで影響しない。
#   UV_HTTP_TIMEOUT=120      … プロキシ経由だと既定の 30 秒では大きな wheel が落ちきらない。
ENV UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=120 \
    UV_COMPILE_BYTECODE=1 \
    UV_NATIVE_TLS=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# 1) 依存解決に必要なマニフェストとロックのみ先にコピーし、
#    dev 依存（pytest / import-linter）の install レイヤをキャッシュする。
#    （ソース変更ではこのレイヤを再実行しない）
COPY pyproject.toml uv.lock ./
COPY shared/pyproject.toml shared/
COPY domains/task/pyproject.toml domains/task/
COPY domains/content-sales/pyproject.toml domains/content-sales/
COPY domains/media/pyproject.toml domains/media/
COPY domains/travel/pyproject.toml domains/travel/
COPY domains/english/pyproject.toml domains/english/
COPY domains/tools/pyproject.toml domains/tools/
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
