# ADR-0005: ディレクトリ構成論を rule/ で統治し、日次 directory-keeper で維持する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-17
- **決定者**: masaya_ueki
- **関連タスク**: -
- **置き換え**: -

---

## コンテキスト

life-os は Modular Monolith × Bounded Context（[ADR-0002](./0002-modular-monolith-bounded-context.md)）で
領域を増やしていく個人モノレポ。領域・ドキュメント・設定が増えるほど「あるべき構成」が暗黙知のままになり、
README の重複・置き場所の揺れ・リンク切れ・空雛形の放置といった**散らかり**が蓄積する。

ここでの本質は「正しい構成を一度決めること」ではなく、**時間が経っても構成が崩れない仕組みにすること**である。
文章で書いただけのルールは必ず破られ腐る（research: architecture fitness functions）。

決めるべき構造的な論点は次の3つで、いずれも「一度決めると後から変えにくい」「複数の有力な選択肢があり自明でない」ため
ADR の対象（[ADR README の判断基準](./README.md#adr-の必要性判断基準)）に該当する。

1. **構成ルールをどこに置くか**（既存の `guides/` と二重化しないか）
2. **維持の自動化を何で・どう実行するか**（常時起動PCの要否がポイント）
3. **エージェントの自律度**（検知した乱れにどこまで自動で手を入れるか）

前提として、一般的なディレクトリ構成のベストプラクティスと、Claude Code の定期実行手段を調査した。

## 決定事項

**(1) あるべきディレクトリ構成論をトップレベル `rule/` に明文化し、(2) それを検査する directory-keeper
（Claude Code スキル ＋ 決定的チェック `scripts/check_structure.py`）を、(3) Claude Code Routines
（クラウド cron）で1日1回・無人実行し、「レポート＋安全な機械的修正の PR」を出す。**
ルールは文章だけにせず `scripts/check_structure.py`・[`.importlinter`](../../.importlinter)・日次 keeper で
検査して腐らせない（fitness functions）。**常時起動PCは不要。API キー不要で既存サブスク枠のみで動く（トークン従量の追加課金なし）。**

## 検討した選択肢

### 論点1: 構成ルールの配置

#### 選択肢A: トップレベル `rule/`（採用）
- **メリット**: 「構造ガバナンス（どうあるべきか）」を独立した第一級の関心事として可視化。`guides/`（プロセス＝どう働くか）と役割が明確に分かれる。トップで「叫ぶ」（Screaming Architecture）。
- **デメリット**: トップレベルディレクトリが1つ増える。
- **採用理由**: ルールは「人の作業手順」ではなく「リポジトリの不変条件」。プロセス文書と混在させない方が SSOT を保ちやすい。役割の境界を rule/README に明記して二重化を防ぐ。

#### 選択肢B: `guides/directory-policy/` に集約（不採用）
- **メリット**: 既存 `guides/` 慣習に統一でき、トップ階層が増えない。
- **デメリット**: 「手順（how-to）」と「構造規約（rule）」が同居し、Diátaxis の分離が崩れる。構造ルールの存在が埋もれる。
- **不採用理由**: 構造ガバナンスは how-to ではない。可視性と SSOT を優先した。

### 論点2: 実行基盤（1日1回・無人）

調査の結論：候補のうち**ローカル cron と `/loop` 以外は常時起動PC不要**。

#### 選択肢A: Claude Code Routines（クラウド cron）（採用）
- **メリット**: PC不要・設定が最も手軽。**API キー不要**で Anthropic クラウドが既存サブスク(Pro/Max)枠で実行する＝**トークン従量の別請求が発生しない**。リポジトリ整頓の定期実行という用途に最適。シークレット管理・ランナー運用が不要。
- **デメリット**: research preview（要 v2.1.81+）で仕様変動リスク。設定がリポジトリ外（バージョン管理されない）。毎回フレッシュクローンのためローカルファイル前提は効かない（本件はクローンした repo を対象にするので問題なし）。
- **採用理由**: ユーザー方針として**トークン従量課金になり得る経路を避けたい**（[ADR-0001](./0001-claude-code-native-multi-session.md) の課金注記のとおり、ヘッドレス/Actions 系の課金方針は将来変わり得る）。Routines は API キーを使わず純粋にサブスク枠で動く最も単純な無人実行で、PC も不要。preview リスクは受容し、不安定化したらフォールバック（選択肢B）へ。

#### 選択肢B: GitHub Actions（schedule cron）（不採用・フォールバックとして保持）
- **メリット**: GA で安定。常時起動PC不要。ワークフローがリポジトリ内に在りバージョン管理・監査ログが残る。
- **デメリット**: ワークフローとシークレットの管理が要る。`ANTHROPIC_API_KEY` 認証は API 従量課金。サブスク認証（`CLAUDE_CODE_OAUTH_TOKEN`）にすれば従量課金は避けられるが、これは「Agent SDK / Claude Code 自動実行」の課金方針変更（ADR-0001 で保留中と判明）の影響を将来受け得る経路にあたる。
- **不採用理由**: ユーザーが課金方針の不確実性を避けて Routines を選好したため。ただし Routines は preview のため、**GitHub Actions（サブスク認証）をフォールバックとして残す**（必要時はワークフローを再追加できるよう本 ADR に構成を記録）。

#### 選択肢C: ローカル cron / systemd + `claude -p`（不採用）
- **デメリット**: **常時起動PCが必要**。個人マシン依存で可搬性が無い。
- **不採用理由**: 「常時起動PC不要」という要件に反する。

#### 選択肢D: `/loop` コマンド（不採用）
- **デメリット**: 対話セッションを開いたまま PC を起動し続ける必要があり、無人定期実行には不適（タスクは端末を閉じると終了）。
- **不採用理由**: 無人運用の手段ではない。

#### 選択肢E: クラウドコンテナ定期起動（Fargate+EventBridge / Cloud Run Jobs）（不採用・将来余地）
- **メリット**: PC不要。ランタイムを完全制御できる。
- **デメリット**: Dockerfile・レジストリ・IAM・スケジューラ・シークレット管理と構築/運用が重い。個人利用に過剰。
- **不採用理由**: Routines（または GitHub Actions フォールバック）で足りる規模。独自ランタイムが要るようになったら検討。

### 論点3: 自律度

#### 選択肢A: レポート＋PR（採用）
- **メリット**: 安全・機械的な修正だけ PR にして人がレビュー。検知と修正を自動化しつつ、マージ判断は人に残す。安全と自動化のバランスが良い。
- **デメリット**: マージの一手間が残る。
- **採用理由**: 個人リポジトリの「掃除」に最適なバランス。

#### 選択肢B: レポートのみ（Issue 起票）（不採用）
- **メリット**: 最も安全・低リスク。
- **デメリット**: 機械的に直せるものまで毎回手作業になる。
- **不採用理由**: 自動化の旨味が薄い。

#### 選択肢C: 自動コミット（main 直押し）（不採用）
- **メリット**: 最も手間が少ない。
- **デメリット**: 人のレビューを挟まず main を変える。誤検知時のリスクが高い。
- **不採用理由**: 個人運用でも main への無人直 push は危険。

## 結果・トレードオフ

### 成果物
- `rule/`（README ＋ directory-structure / documentation / naming / maintenance）— 構成論ルールの正本。
- `scripts/check_structure.py` — 決定的チェック（fitness function）。CI でも終了コードで落とせる。
- `.claude/skills/directory-keeper/SKILL.md` — 監査手順（ネイティブ配置、[ADR-0003](./0003-presentation-system.md) に準拠）。Routines は repo をクローンしてこのスキルを実行する。
- 実行は Routines（リポジトリ外の設定）。実行プロンプトと手順は本 ADR「Routines セットアップ」に記録。

### コスト（トークン従量の追加課金なし）
- Routines は **API キー不要**で、Anthropic クラウドが**既存サブスク(Pro/Max)枠**で実行する。**トークン従量の別請求は発生しない**（サブスクの利用量を消費するのみ）。アカウント単位の1日あたり実行回数上限の範囲内。
- 抑制策: 既定 `claude-sonnet-4-6`、読む範囲を rule/＋README＋構造に限定、決定的チェックはスクリプトに逃がす、クリーン時は早期終了。
- フォールバックの GitHub Actions を使う場合: ランナー時間は public 無料 / private 無料枠内。認証は `CLAUDE_CODE_OAUTH_TOKEN`（サブスク・追加課金なし）推奨。従量 API（`ANTHROPIC_API_KEY`）を使う場合の月額目安（キャッシュ前提）は Haiku ~$5-10 / Sonnet ~$15-30 / Opus ~$25-50。

### Routines セットアップ（ユーザー操作）
1. Claude Code を更新（`claude update`、Routines は v2.1.81+ / research preview）。
2. `claude.ai/code/routines`・デスクトップ版・または CLI `/schedule` で Routine を作成し、対象に本リポジトリ（`masaya-ueki/life-os`）、トリガーを Daily（最小間隔1時間）、モデルを `claude-sonnet-4-6` に設定。
3. プロンプト（実行内容）:
   ```
   directory-keeper スキル（.claude/skills/directory-keeper/SKILL.md）を実行。rule/ に照らして
   このリポジトリを監査し、まず `python scripts/check_structure.py --json` を実行、判断系のみ内容を
   読む（読む範囲は rule/＋各README＋構造に限定、全ソースは読まない）。安全で機械的・可逆な修正のみを
   ブランチに適用して1つの PR を作成し、人の判断が必要な指摘は PR 本文にレポートする。違反ゼロなら
   何も作らず終了。破壊的変更・削除・設計判断は自動で行わない。
   ```
4. 本 PR をマージ後に作成する（Routines は `main` をフレッシュクローンするため、スキル・ルールが main に入ってから）。

### フォールバック構成（GitHub Actions・必要時のみ再追加）
Routines が preview ゆえに不安定化したら、以下を `.github/workflows/directory-keeper.yml` として復活させる
（Secrets `CLAUDE_CODE_OAUTH_TOKEN`＝サブスク認証で追加課金なし、Variables `DIRECTORY_KEEPER_ENABLED=true` で opt-in）。

```yaml
name: directory-keeper
on:
  schedule:
    - cron: "0 0 * * *"   # 00:00 UTC = 09:00 JST
  workflow_dispatch:
permissions:
  contents: write
  pull-requests: write
  issues: write
jobs:
  keep:
    if: ${{ github.event_name == 'workflow_dispatch' || vars.DIRECTORY_KEEPER_ENABLED == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - uses: anthropics/claude-code-action@v1
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}  # サブスク認証＝追加課金なし
          github_token: ${{ secrets.GITHUB_TOKEN }}
          claude_args: "--model claude-sonnet-4-6"
          prompt: "directory-keeper スキルを実行し、rule/ に照らして監査、安全な修正は PR、判断系はレポート。違反ゼロなら何もしない。"
```

### 注意点・将来の見直し条件
- **directory-keeper は掃除であって設計変更ではない**。破壊的・解釈を伴う変更は report に回す（自律度は段階的に上げられる）。
- Routines は research preview。仕様変更や不安定化に追従が必要。破綻時は上記 GitHub Actions フォールバックへ。
- 有効化（Routine 作成・定期実行ON）はユーザー操作。設定するまで実行されない。

### 関連する訂正（ADR-0001 の課金記載）
本件の調査で、[ADR-0001](./0001-claude-code-native-multi-session.md) の「2026-06-15 に `claude -p` / Agent SDK が
別クレジット課金へ移行した」という記載が**現在は誤り（実施直前に撤回・保留）**であることが判明したため、ADR-0001 に訂正注記を入れた。
この「ヘッドレス/自動実行系の課金方針はいつ変わるか不確実」という点こそが、本 ADR で**従量 API 経路を避け Routines（サブスク枠のみ）を選んだ理由**である。

## 関連ドキュメント・リンク

- [rule/README.md](../../rule/README.md) — 構成論ルールの正本
- [rule/maintenance.md](../../rule/maintenance.md) — 監査チェックリスト（keeper との契約）
- [.claude/skills/directory-keeper/SKILL.md](../../.claude/skills/directory-keeper/SKILL.md) — 監査手順
- [ADR-0002](./0002-modular-monolith-bounded-context.md) — Modular Monolith × Bounded Context（領域の構成根拠）
- [ADR-0003](./0003-presentation-system.md) — ネイティブ `.claude/` 配置の方針
- [ADR-0001](./0001-claude-code-native-multi-session.md) — Claude Code ネイティブ機能・定期実行（Routines）
- Architecture fitness functions: Ford/Parsons, *Building Evolutionary Architectures* ／ Diátaxis: diataxis.fr ／ Screaming Architecture: R.C. Martin
- Claude Code Routines / scheduled tasks: https://code.claude.com/docs/en/routines ／ anthropics/claude-code-action: https://github.com/anthropics/claude-code-action
