---
name: claude-code-release-watcher
description: Claude Code の新リリースを確認し、Notion の ClaudeCodeReleases（リリース要約）・ClaudeCodeFeatureGuides（新機能・改善の説明書、最大5件）・Information Hub（1バージョン1行）に記録するスキル。取得・分類・重複チェック・書き込みは実行モデルが、説明書にする機能の選定と文章作成は Opus サブエージェントが担う。Use when Claude Code のアップデート内容を Notion にまとめたいとき、/claude-code-release-watcher 実行時、Routines（クラウド定期実行）時。Triggers on Claude Code リリース, 変更履歴を Notion に, アップデートの使い方, release watcher, 新機能の説明書.
---

# claude-code-release-watcher — Claude Code リリース記録スキル

Claude Code の新リリースを GitHub から取得し、使い方の説明書として Notion に記録する。
対話起動（`/claude-code-release-watcher`）と Routines（クラウド定期実行・常時起動PC不要）の両方で同じ手順を使う。
Routines は本リポジトリをフレッシュにクローンしてこのスキルを実行する。

> **実行方式の根拠**: Routines を無人実行に使う判断は [ADR-0005](../../../docs/adr/0005-directory-governance-daily-keeper.md) と同じ（API キー不要・既存サブスク枠のみ・常時起動PC不要）。

**このスキルはリポジトリを変更しない。** ファイル変更・コミット・PR 作成は行わず、書き込み先は Notion のみ。

---

## 書き込み先（Notion）

| DB | データソース | 単位 | 重複判定 |
|---|---|---|---|
| ClaudeCodeReleases | `collection://39fb20cf-409c-4613-9f47-e05bf984d2a3` | 1 バージョン 1 行 | `Version`（tag） |
| ClaudeCodeFeatureGuides | `collection://31413ed7-c332-4a39-9327-14c3bda7c56f` | 1 機能 1 行（1 リリース最大 5 件） | `Release` + `OriginalText` |
| Information Hub | `2ef5f750-ec05-8074-9f06-000b7ba89fdb` | 1 バージョン 1 行 | タイトル `Claude Code CLI {x.y.z} 変更履歴` |

- 処理対象の下限: `published_at >= 2026-09-11T15:00:00Z`（日本時間 2026-09-12 以降）。これより古いリリースは処理しない。
- Notion の DB 名・列名は英語の UpperCamelCase、絵文字は使わない。

## 実行環境の制約（2026-09-13 のお試し実行で判明）

- クラウド環境では `api.github.com` への curl / WebFetch が 403 で拒否される。**GitHub API と `gh` は使わない。**
- 待機に ScheduleWakeup は使えない。
- Notion は、番号付きリストの間にコードブロックを挟むと番号が 1 に戻る。`CLAUDE.md` や `claude.ai` のような文字列は自動リンクに化ける。

---

## 手順

### ステップ1: リリース一覧と本文を取得する

1. `date -u +%Y-%m-%dT%H:%M:%SZ` で現在時刻を確認する。
2. WebFetch で Atom フィード `https://github.com/anthropics/claude-code/releases.atom` を取得し、各 entry の tag（`v2.1.270` など）・公開日時（ISO8601、`updated`）・リンク（`https://github.com/anthropics/claude-code/releases/tag/{tag}`）を表形式で返させる。下限以降のリリースを公開日時の古い順に並べ、1 件ずつステップ2〜8 を実行する。1 件で失敗しても次のリリースへ進む。
3. ステップ2 でスキップにならなかったリリースだけ、本文を次の順で取得する（成功したらそこで終わり）。
   1. `curl -sf https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md -o changelog.md` を実行し、`## {x.y.z}`（先頭の v なし）の見出しから次の `## ` 見出しまでの `- ` 行を本文とする。
   2. 失敗したら WebFetch でリリースページを取得し、「すべての箇条書き行を要約・省略せず原文のまま返す」よう指示する。
   3. 取得した行数を最終報告に書く。

### ステップ2: 重複チェックと行の確保（ClaudeCodeReleases）

`Version` で検索する。`notion-query-data-sources` は次の形で呼ぶ。

```json
{"data": {"mode": "sql", "data_source_urls": ["collection://39fb20cf-409c-4613-9f47-e05bf984d2a3"], "query": "SELECT url, Version, Status, createdTime FROM \"collection://39fb20cf-409c-4613-9f47-e05bf984d2a3\" WHERE Version = ?", "params": ["v2.1.270"]}}
```

- `Status=Published` の行がある → そのリリースは**スキップ**。
- `Status=Failed` の行、または作成から 6 時間以上経った `Status=Pending` の行がある → その行を再利用して処理する。
- 行がない → 次のプロパティで新規作成する。
  - `Version`: tag
  - `VersionCode`: major×1000000 + minor×1000 + patch（例: v2.1.270 → 2001270）
  - `ReleasedAt`: 公開日時（`date:ReleasedAt:start` に ISO8601、`date:ReleasedAt:is_datetime` に 1）
  - `ReleaseUrl`: リリースページの URL
  - `Status`: `Pending`

### ステップ3: リリースノートを分類する

本文の `- ` で始まる各行を分類し、`番号 / Area / 種類 / 原文` の一覧を作る。

| 行頭の接頭辞 | Area |
|---|---|
| なし、または `Windows:` / `macOS:` / `Linux:` | `Cli` |
| `[Claude Code on the web]` | `Web` |
| `[VSCode]` | `VSCode` |
| `[Claude Tag]` | `ClaudeTag` |
| それ以外（`[Code Review]` など） | `OutOfScope` |

| 接頭辞を除いた先頭の動詞 | 種類 |
|---|---|
| `Added` | NewFeature |
| `Improved` / `Changed` | Improvement |
| `Fixed` | BugFix |
| `Removed` / `Deprecated` | Deprecation |

破壊的変更を明示している行には BreakingChange も付ける。

### ステップ4: Opus サブエージェントに選定と文章作成を依頼する

Agent ツールを `model: "opus"` で 1 リリースにつき 1 回呼び出す。**フォアグラウンドで呼び出し（`run_in_background` は指定しない）、結果が返るまで待つ。待っている間に同じ調査を並行して行わない。** Opus には Notion への書き込みをさせず、返ってきた下書きを**内容を変えずに** Notion に書き込む。

プロンプトには Version、ReleaseUrl、ステップ3 の分類一覧（原文つき）と、以下の「選定ルール」「執筆ルール」「出力フォーマット」をそのまま含める（サブエージェントは前提知識を持たない）。

**選定ルール**

- Area が Cli / Web / VSCode / ClaudeTag の NewFeature・Improvement から、**使い方が変わる重要なものを最大 5 件**選ぶ。
- 優先: 新しいコマンド・スラッシュコマンド・設定・フラグ・環境変数・ワークフロー、Routines / スキル / MCP / サブエージェント / Workflow など日常の使い方に効くもの。Cli と Web を優先する。
- 除外: Bedrock / Vertex / Foundry / LLM gateway / OpenTelemetry / managed settings / 組織管理者向け設定、見た目だけの細かな UI 調整、パフォーマンスの微改善。
- BugFix は選ばない。該当 0 件なら選ばない。
- 読者は個人開発者（Claude Code CLI on WSL、クラウドの Routines、GitHub Issue 駆動の開発、Notion 連携を使う）。

**執筆ルール**

- Notion には書き込まない。
- リリースノートと公式ドキュメント（`https://code.claude.com/docs/` 配下。`https://code.claude.com/docs/llms.txt` で目次を引き、各ページは `.md` 付き URL を読む）で確認できる事実だけを書く。
- **リリースノートにも公式ドキュメントにもない経緯・既定値・数値を推測で書かない。** 経緯（以前の廃止や変更など）や既定値を書くときは根拠となる公式ドキュメントの記載を確認し、そのページを「参照」に載せる。確認できない点は「公式ドキュメント未記載」と書く。
- 絵文字は使わない。
- ファイル名・ドメイン・コマンド・設定名・環境変数は必ずインラインコードで囲む。
- 手順の途中にコードブロックを挟む場合は、番号付きリストを使わず `### 1. 〜` の短い小見出しで手順を分け、説明は次の段落に書く。
- コードブロックの言語は内容に合わせる（シェルは `bash`、JSON は `json`、スラッシュコマンドや出力例などは `text`）。

**出力フォーマット**（この見出し構成で、Notion Markdown として返す）

```text
=== RELEASE ===
Summary: （日本語 1〜2 行）
Importance: High | Medium | Low   （NewFeature を含む/使い方が変わる=High、Improvement のみ=Medium、BugFix のみ=Low）
--- BODY ---
## 概要
（2〜3 文）
## 説明書を作成した機能
{{GUIDE_LINKS}}
## その他の新機能・改善
- [Area] 日本語 1 行（選ばなかった NewFeature / Improvement / Deprecation すべて）
## バグ修正
計 N 件。影響が大きいものを最大 10 件、日本語 1 行ずつ。残りは「ほか N 件」。
## 対象外
- OutOfScope の行の日本語 1 行（なければこのセクションごと省略）

=== GUIDE 1 ===
OriginalText: （原文 1 行そのまま）
Feature: （日本語の機能名、50 文字以内）
ChangeType: NewFeature | Improvement
Area: Cli | Web | VSCode | ClaudeTag
Summary: （日本語 1 行）
DocsUrl: （公式ドキュメント URL。なければ空）
--- BODY ---
<callout color="blue_bg">
	**一言でいうと**：〇〇ができるようになった（{Version} / {Area} / {ChangeType}）
</callout>
## 何が変わったか
- Before：…
- After：…
## どんなときに使うか
- ユースケース 2〜3 個
## 使い方
（手順。コードブロックを挟むなら ### 1. 〜 の短い小見出しで分ける）
## 設定・オプション
（該当するときだけ表で。| 名前 | 既定値 | 説明 |）
## 注意点・制約
- 対応プラン・環境・既知の制限
## life-os での活用アイデア
- 上記の読者の環境でどう使えるか
## 参照
- [GitHub Release]({ReleaseUrl})
- 公式ドキュメント（あれば）

（=== GUIDE 2 === 以降も同じ。最大 5 件）

=== INFOHUB ===
Register: yes | no   （対象 Area に NewFeature / Improvement がある、または GA・public preview・research preview・beta 開始の記載がある場合 yes。BugFix のみなら no）
--- BODY ---
## 概要
## 主な新機能
### 1. 機能名
- 内容
## 主な改善
## GA・プレビュー
（該当があるときだけ）
## まとめ
## 参考リンク
{{INFOHUB_LINKS}}
```

Opus の出力がフォーマットに従っていない場合は、不足部分だけを指摘して 1 回だけ再依頼する。

### ステップ5: 説明書ページを作る（ClaudeCodeFeatureGuides）

GUIDE ごとに、`Release` = ステップ2 の行 かつ `OriginalText` = 原文 の行が既にあるか確認し、なければ作成する。

- プロパティ: GUIDE の `Feature` / `ChangeType` / `Area` / `Summary` / `OriginalText` / `DocsUrl`（空なら未設定）と、`Release` = ステップ2 の行の URL
- 本文: GUIDE の BODY をそのまま使う
- 作成したページの URL を控える

### ステップ6: リリース行を仕上げる（ClaudeCodeReleases）

- プロパティ: `Summary` / `Importance` は RELEASE の値、`ChangeTypes` はステップ3 で出現した種類すべて
- 本文: RELEASE の BODY で置き換える。`{{GUIDE_LINKS}}` は説明書ごとに `- <mention-page url="説明書のURL">Feature</mention-page>` の行に置換する（0 件なら「なし」）

### ステップ7: Information Hub に登録する（1 バージョン 1 行）

INFOHUB の `Register` が `yes` の場合だけ行う。

1. タイトル `Claude Code CLI {x.y.z} 変更履歴`（先頭の v は付けない）で検索し、既にあれば登録しない。
2. なければ claude.ai のスキル `notion-info-register`（クラウドでは `anthropic-skills:notion-info-register`）を Skill ツールで呼び出し、その手順に従って登録する。スキルが見つからない場合は、同じ内容で `notion-create-pages` を直接呼ぶ。
   - parent: `{"data_source_id": "2ef5f750-ec05-8074-9f06-000b7ba89fdb"}`
   - `Title`: `Claude Code CLI {x.y.z} 変更履歴`
   - `Tag`: `Technology`
   - `userDefined:URL`: ReleaseUrl
   - `Visible`: `__YES__`
   - 本文: INFOHUB の BODY。`{{INFOHUB_LINKS}}` は `- [GitHub Release](https://github.com/anthropics/claude-code/releases/tag/{tag})`、`- <mention-page url="ステップ2の行のURL">ClaudeCodeReleases {Version}</mention-page>`、説明書ごとの `- <mention-page url="説明書のURL">Feature</mention-page>` に置換する

### ステップ8: 完了処理

ステップ2〜7 がすべて成功したら、リリース行の `Status` を `Published` にする。途中で失敗したら `Status` を `Failed` にし、失敗理由をリリース行本文の末尾に「## 実行エラー」として追記して、次のリリースへ進む（次回実行で再処理される）。

### 最終報告

次をまとめて出力する: 現在時刻と処理範囲 / 処理したバージョン / スキップしたバージョン / 本文の取得方法（CHANGELOG かリリースページか）と行数 / 作成した説明書の件数とタイトル / Information Hub 登録の有無（スキル使用か直接登録か）/ Opus サブエージェントを使えたか / 失敗とその理由。対象リリースが 0 件なら「新規リリースなし」とだけ報告する。

---

## Routines セットアップ

Routines の設定はリポジトリ外にあるため、ここに記録する。

| 項目 | 値 |
|---|---|
| 名前 | Claude Code Release Watcher（`trig_01MFBuekFXHo71HUanmFXsxW`） |
| 対象リポジトリ | `masaya-ueki/life-os` |
| スケジュール | `0 23 * * *`（毎日 8:00 JST。Routines の仕様で毎回数分遅れて起動する） |
| モデル | `claude-sonnet-5`（選定と文章作成はステップ4 で Opus サブエージェント） |
| コネクタ | Notion |
| 許可ツール | Bash / Read / Glob / Grep / Skill / WebFetch / Agent |

プロンプト:

```text
claude-code-release-watcher スキル（.claude/skills/claude-code-release-watcher/SKILL.md）を読み、その手順どおりに最後まで実行してください。ユーザーは不在なので確認や質問はしないこと。リポジトリのファイル変更・コミット・PR 作成は一切しないこと。
```
