# docker/certs

TLS 傍受プロキシ（Claude Code on the web のクラウド環境や、社内ネットワークの
SSL インスペクション等）が挟まる環境で、ビルドコンテナに信頼させたい CA 証明書の置き場。

- このディレクトリの `*.crt` は [`docker/Dockerfile`](../Dockerfile) が
  `/usr/local/share/ca-certificates/extra/` へコピーし `update-ca-certificates` を実行する。
- **空でよい。** 証明書が無い環境（通常のローカル開発）では実質 no-op になる。
- `*.crt` は環境ごとに異なり失効もするため `.gitignore` 済み。コミットしない。

## クラウドセッションでの配置

[`.claude/hooks/session-start.sh`](../../.claude/hooks/session-start.sh) が
セッション開始時にホストのシステム信頼ストアの証明書をここへコピーする。手動で行う場合:

```bash
cp /usr/local/share/ca-certificates/*.crt docker/certs/
```

**束ねられた `/root/.ccr/ca-bundle.crt` は使わないこと。** `update-ca-certificates` は
1ファイルに複数の証明書が入っているとそのファイルをスキップするため、
`rehash: warning: skipping ..., it does not contain exactly one certificate or CRL`
となり信頼ストアに入らない。1ファイル 1証明書 で置く必要がある。

## 経緯

クラウド環境ではホストのシステム信頼ストアにプロキシの CA が導入済みだが、
コンテナは素のベースイメージのため持っておらず、`uv sync` が
`invalid peer certificate: UnknownIssuer` で失敗する。`--network host` でも解決しない
（傍受はネットワークモードに依らない）。ベースイメージを同じタグで差し替える回避策も、
BuildKit がリモートのダイジェストで解決するため効かない。
