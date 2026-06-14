#!/bin/bash
# =============================================================================
# Snowflake用 RSA鍵ペア生成スクリプト
# - 秘密鍵（PKCS8形式、パスフレーズ付き暗号化）
# - 公開鍵
# =============================================================================

set -e

# デフォルト設定
KEY_SIZE=2048
OUTPUT_DIR="${HOME}/.snowflake/keys"
KEY_NAME="snowflake_key"

# 使用方法
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -o, --output-dir DIR    出力ディレクトリ (default: ${OUTPUT_DIR})"
    echo "  -n, --name NAME         鍵ファイル名 (default: ${KEY_NAME})"
    echo "  -s, --key-size SIZE     鍵サイズ (default: ${KEY_SIZE})"
    echo "  -h, --help              このヘルプを表示"
    echo ""
    echo "Example:"
    echo "  $0 -o ./keys -n terraform_user"
    exit 1
}

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -n|--name)
            KEY_NAME="$2"
            shift 2
            ;;
        -s|--key-size)
            KEY_SIZE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# 出力ファイルパス
PRIVATE_KEY_PEM="${OUTPUT_DIR}/${KEY_NAME}.pem"
PRIVATE_KEY_P8="${OUTPUT_DIR}/${KEY_NAME}.p8"
PUBLIC_KEY="${OUTPUT_DIR}/${KEY_NAME}.pub"

echo "=============================================="
echo "Snowflake RSA鍵ペア生成スクリプト"
echo "=============================================="
echo ""
echo "設定:"
echo "  出力ディレクトリ: ${OUTPUT_DIR}"
echo "  鍵ファイル名: ${KEY_NAME}"
echo "  鍵サイズ: ${KEY_SIZE} bits"
echo ""

# 出力ディレクトリ作成
mkdir -p "${OUTPUT_DIR}"
chmod 700 "${OUTPUT_DIR}"

# パスフレーズの入力
echo "秘密鍵を保護するパスフレーズを入力してください。"
echo "（パスフレーズはSnowflakeの認証時に必要になります）"
echo ""
read -s -p "パスフレーズ: " PASSPHRASE
echo ""
read -s -p "パスフレーズ（確認）: " PASSPHRASE_CONFIRM
echo ""
echo ""

# パスフレーズ確認
if [ "${PASSPHRASE}" != "${PASSPHRASE_CONFIRM}" ]; then
    echo "エラー: パスフレーズが一致しません。"
    exit 1
fi

if [ -z "${PASSPHRASE}" ]; then
    echo "エラー: パスフレーズは必須です。"
    exit 1
fi

echo "鍵ペアを生成中..."
echo ""

# Step 1: 秘密鍵を生成（PEM形式）
echo "[1/3] RSA秘密鍵を生成..."
openssl genrsa -out "${PRIVATE_KEY_PEM}" "${KEY_SIZE}"

# Step 2: 秘密鍵をPKCS8形式に変換（パスフレーズ付き暗号化）
echo "[2/3] 秘密鍵をPKCS8形式に変換（パスフレーズ付き暗号化）..."
openssl pkcs8 -topk8 \
    -inform PEM \
    -outform PEM \
    -in "${PRIVATE_KEY_PEM}" \
    -out "${PRIVATE_KEY_P8}" \
    -v2 aes-256-cbc \
    -passout pass:"${PASSPHRASE}"

# Step 3: 公開鍵を生成
echo "[3/3] 公開鍵を生成..."
openssl rsa -in "${PRIVATE_KEY_PEM}" -pubout -out "${PUBLIC_KEY}"

# 元のPEM秘密鍵を削除（PKCS8形式のみ保持）
rm -f "${PRIVATE_KEY_PEM}"

# パーミッション設定
chmod 600 "${PRIVATE_KEY_P8}"
chmod 644 "${PUBLIC_KEY}"

echo ""
echo "=============================================="
echo "鍵ペアの生成が完了しました"
echo "=============================================="
echo ""
echo "生成されたファイル:"
echo "  秘密鍵 (PKCS8, 暗号化): ${PRIVATE_KEY_P8}"
echo "  公開鍵:                  ${PUBLIC_KEY}"
echo ""
echo "----------------------------------------------"
echo "Snowflakeユーザーへの公開鍵登録コマンド:"
echo "----------------------------------------------"
echo ""

# 公開鍵の内容を取得（ヘッダー/フッターを除去）
PUBLIC_KEY_CONTENT=$(grep -v "PUBLIC KEY" "${PUBLIC_KEY}" | tr -d '\n')

echo "ALTER USER <ユーザー名> SET RSA_PUBLIC_KEY='${PUBLIC_KEY_CONTENT}';"
echo ""
echo "----------------------------------------------"
echo "重要:"
echo "----------------------------------------------"
echo "1. 秘密鍵(${PRIVATE_KEY_P8})は安全に保管してください"
echo "2. パスフレーズは忘れないように記録してください"
echo "3. 秘密鍵とパスフレーズはAWS Secrets Manager等に保存することを推奨します"
echo ""
