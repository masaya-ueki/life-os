# ADR-0001: Claude Code の複数セッション管理を自作フレームワークからネイティブ機能へ移行する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-14
- **決定者**: masaya_ueki
- **関連タスク**: -
- **置き換え**: -

---

## コンテキスト

別リポジトリ（データ基盤）で構築した自作の Claude Code 複数セッション運用フレームワーク一式（`scripts/cc-*` ＋ `create_worktree.sh` / `delete_worktree.sh`）を life-os にもコピーしていた。このフレームワークは以下を担っていた。

| 自作スクリプト | 役割 |
|---|---|
| `cc-queue.sh` | ファイルベース JSON（`~/.claude/queue/queue.json`）でタスクをキューイング |
| `cc-daemon.sh` | 常駐デーモンがキューを pop し、最大 N 並列で起動（既定 N=10） |
| `cc-launch.sh` | worktree 作成 + tmux セッション（`cc-<issue>`）+ headless 起動 |
| `cc-run.sh` | `claude` の headless 実行ラッパー（`--model` 切替等） |
| `cc-status.sh` / `cc-status.py` | 複数セッションのステータスダッシュボード |
| `create_worktree.sh` / `delete_worktree.sh` | Issue 単位の git worktree 作成・削除 |

これらは Claude Code に複数セッション・並列実行のネイティブ機能が乏しかった時期に作られたもの。その後（〜2026年中盤）Claude Code 本体が worktree・headless・並列エージェント運用を公式サポートしたため、自作フレームワークの大半が重複・陳腐化した。

加えて life-os では次の問題があった。

- `create_worktree.sh` は Docker Compose（`COMPOSE_PROJECT_NAME=data-platform-*`）・AWS MFA（`setup_mfa_to_env/`）・`local/.env` を前提にしており、**life-os には存在しない依存のため動作しない**。
- 常駐デーモン + 自作キューは、単独開発の個人リポジトリに対して運用負荷・複雑性が過剰。
- 保守対象（合計 ~3000 行のシェル/Python）を、ネイティブ機能と二重に抱える状態だった。

## 決定事項

**自作の複数セッション管理フレームワーク（`cc-*` ＋ worktree スクリプト）を全廃し、Claude Code のネイティブ機能に全面移行する。** `scripts/` には life-os 固有で必要なもの（`setup-github-labels.sh` 等）のみを残す。

## 検討した選択肢

### 選択肢A: ネイティブ機能へ全面移行（採用）

自作フレームワークを退役し、用途を Claude Code 本体の機能に対応づける。

- **メリット**: 保守コストゼロ。公式アップデートに追従。個人利用に対して複雑度が適正。データ基盤依存（Docker/MFA）から解放。
- **デメリット**: 自前キュー（永続タスク行列）の完全等価物はネイティブには無い。一部機能は research preview / 実験的。

### 選択肢B: 自作フレームワークを life-os 向けに改修して維持（不採用）

`create_worktree.sh` の Docker/MFA 依存を剥がし、キュー/デーモンを残す。

- **メリット**: 既存の運用感を維持できる。
- **デメリット**: ネイティブ機能と重複する資産を保守し続ける。単独個人プロジェクトに対し明らかに過剰。**不採用理由**: 維持コストに見合う固有価値が無い。

### 選択肢C: 何もしない（不採用）

- **デメリット**: 動かない `create_worktree.sh`、SKILL からの dead reference が残る。陳腐化したコードが温存される。**不採用理由**: 技術的負債を放置するだけ。

## 結果・トレードオフ

### 自作機能 → ネイティブ機能の対応表（移行ガイド）

| 自作機能 | ネイティブの代替 | 備考 |
|---|---|---|
| worktree 作成/削除 | `claude --worktree <name>`（自動作成・自動クリーンアップ）。セッション内なら subagent の worktree 隔離 | git worktree 運用が公式パターン |
| headless 起動 | `claude -p`（print mode）＋ `--output-format json` / `--json-schema` / `--allowedTools` / `--permission-mode` | スクリプトからの呼び出しはこれが標準 |
| 複数セッションの監視ダッシュボード | **Agent View**（`claude agents`）／デスクトップ版のセッション一覧 | research preview。VSCode/WSL のターミナルで動作（デスクトップアプリ不要・v2.1.139+） |
| キュー + 並列デーモン | ・単純並列: `claude -p ... --worktree ... &` のシェルループ<br>・協調並列: **Agent Teams**（実験的・`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`、2〜16体が共有タスクリストで協調）<br>・定期実行: **Routines**（クラウド cron）／ローカルは `/loop` | 常駐デーモンの自作は不要 |
| 1セッション内の作業分担 | **subagents（Task ツール）/ `/agents`** | 本体コンテキストを汚さず並行 |

### 運用方針（用途別の推奨・運用負荷の低い順）

1. 並行で別タスク → 別ターミナルで `claude --worktree <name>`（1作業=1 worktree）
2. 1セッション内の調査・検証分担 → subagent（Task ツール）
3. 独立タスクを投げて後で確認 → Agent View（`claude agents`）
4. Issue を自律的に並列消化 → Agent Teams（実験的）または `claude -p` の薄いシェルループ
5. 定期実行 → Routines（クラウド）/ ローカルは `/loop`

### Agent View（`claude agents`）の動作環境と使い方（実機確認済み）

life-os 環境（WSL2 上の Claude Code v2.1.177・VSCode 統合ターミナル）で動作を確認した。

- **デスクトップアプリは不要。** VSCode の統合ターミナルから `claude agents` で起動できる（前提: Claude Code v2.1.139 以降、`claude --version` で確認）。WSL2・標準的な POSIX ターミナルで動作し、tmux/iTerm2 等の特定ターミナル依存は無い。
- 起動直後はセッション 0 件の空ダッシュボード（上部に `N awaiting input · N working · N completed`、下部に「Describe a task for a new session」入力欄）。通常チャットと見た目が似ているが別物。
- 使い方: 入力欄にタスクを書いて `Enter` → 上に行が追加されバックグラウンド実行。`Space` で peek、`Enter`/`→` でアタッチ、`←` でデタッチ、`Ctrl+X` で停止、`?` でショートカット一覧。
- 各セッションは `.claude/worktrees/` に自動で worktree を作って隔離する。ターミナルを閉じても走り続ける（シャットダウンで停止）。

### トレードオフ・注意点

- **永続キューの等価物が無い**: 「未処理タスクを行列で溜める」挙動が必要なら、CI/CD（GitHub Actions）や薄い `claude -p` グルー、もしくは Agent Teams の共有タスクリストで代替する。
- **鮮度リスク**: Agent View・Agent Teams・Routines は research preview / 実験的機能。採用前に使用中の Claude Code バージョンで有効か（例: `claude agents` が存在するか、`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` が効くか）を確認すること。
- **~~2026-06-15 の料金変更~~（訂正・2026-06-17）**: 当初「Agent SDK / `claude -p` の利用が対話の上限とは別の月次クレジットから消費される」と記載していたが、**この課金変更は実施直前に撤回・保留された**。現在 `claude -p` / Agent SDK は引き続き通常のサブスク上限から消費される（Anthropic は変更前に改めて告知するとしている）。一方、GitHub Actions を `ANTHROPIC_API_KEY` で動かす場合は元来 API クレジット（トークン従量）課金であり、本保留とは無関係（[ADR-0005](./0005-directory-governance-daily-keeper.md) 参照）。

### 他リポジトリへの移行手順（このADRの再利用）

別案件で同じ自作フレームワークを使っている場合、本ADRを参照して以下を実施する。

1. 上表で各自作スクリプトの代替を確認する。
2. `cc-*`・`create_worktree.sh`・`delete_worktree.sh` を `git rm` で退役。
3. ドキュメント/スキル内の `./scripts/create_worktree.sh ...` 等の参照を素の `git switch -c` / `git worktree add` に置換。
4. 自律運用が必須の場合のみ、`claude -p` ベースの最小グルー（Issue番号 → worktree名 → headless 実行）を新規作成。

## 関連ドキュメント・リンク

- Worktrees: https://code.claude.com/docs/en/worktrees
- Headless mode（`claude -p`）: https://code.claude.com/docs/en/headless
- Subagents: https://code.claude.com/docs/en/sub-agents
- Agent teams（実験的）: https://code.claude.com/docs/en/agent-teams
- 並列エージェントの選択（比較表）: https://code.claude.com/docs/en/agents
- Routines（クラウド定期実行）: https://code.claude.com/docs/en/routines
- 開発運用ルール: [`guides/development-policy/issue-operation-rules.md`](../../guides/development-policy/issue-operation-rules.md)
