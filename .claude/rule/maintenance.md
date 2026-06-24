# メンテナンス基準と監査チェックリスト

> **親**: [rule/README.md](./README.md)

「きれいなディレクトリ」の定義と、[directory-keeper](../skills/directory-keeper/SKILL.md) が
日次で回す監査チェックリスト。**このファイルが「ルール」と「エージェント」の契約**。

---

## 「きれい」の定義

次がすべて満たされている状態を「きれい」とする。

- トップレベルが正典構成（[directory-structure.md](./directory-structure.md)）に収まっている
- ルート直下に許可外の単発ファイルが無い
- 各 workspace member に README がある
- ドキュメントに逐語の重複が無い（[R-DOC-1](./documentation.md)）
- 命名規約（[naming.md](./naming.md)）が守られている
- リンク切れ・孤立した生成物・空のまま放置された雛形が無い

---

## 監査チェックリスト

各項目に **検査手段**（`auto` = `scripts/check_structure.py` で決定的に検査 / `judge` = keeper が内容を読んで判断）と
**対応方針**（`fix` = 安全な機械的修正として PR 化 / `report` = 判断が要るのでレポート）を付す。

| ID | 検査内容 | 手段 | 既定対応 |
|---|---|---|---|
| C-ROOT | ルート直下に許可リスト外のファイルが無い（[R-STRUCT-5](./directory-structure.md)） | auto | report |
| C-TOPDIR | トップレベルが正典4種に収まる（未知のトップディレクトリが無い） | auto | report |
| C-MEMBER-README | 各 workspace member に `README.md` がある（[R-DOC-2](./documentation.md)） | auto | fix（雛形を作成）|
| C-DOC-DUP | README/ドキュメント間に逐語の重複段落が無い（[R-DOC-1](./documentation.md)） | auto | report |
| C-NAME-KEBAB | docs/guides/.claude/rule のファイル名・トップディレクトリが kebab-case（[R-NAME-1](./naming.md)） | auto | fix（改名＋参照更新）|
| C-LINK | ドキュメントの相対リンク・ADR リンクが切れていない（[R-DOC-5](./documentation.md)） | auto | fix（リンク修正）|
| C-GENERATED | 生成物がコミットされていない（[R-STRUCT-4](./directory-structure.md)） | auto | report |
| C-ARCHETYPE | 領域内構成が archetype A/B に沿う（[R-STRUCT-1](./directory-structure.md)） | judge | report |
| C-DOC-PLACE | ドキュメントが種類に応じた場所にある（[R-DOC-3](./documentation.md)） | judge | report |
| C-ADR-LINK | ADR と対応設計が相互リンクされている（[R-DOC-4](./documentation.md)） | judge | report |
| C-STALE | 空雛形の放置・未使用物・「念のため」残置が無い（[R-STRUCT-7](./directory-structure.md)） | judge | report |
| C-UTILS | `utils/`/`common/`/`misc/` 等の曖昧な入れ物が無い（[R-NAME-5](./naming.md)） | judge | report |

---

## 対応方針（自律度 = レポート＋PR）

[ADR-0005](../../docs/adr/0005-directory-governance-daily-keeper.md) のとおり、keeper は次の境界を守る。

- **fix（PR 化してよい）**: 機械的で安全・可逆な修正のみ。雛形 README の追加、kebab-case への改名と参照更新、
  明確なリンク切れの修正など。**1 回の実行＝1 PR**。本文に検出内容と根拠ルールを記す。
- **report（人の判断に委ねる）**: 設計判断・破壊的変更・意味の解釈を伴うもの。ファイル削除や移動、
  archetype 逸脱、ドキュメント重複の解消方針など。PR 本文または Issue に列挙し、**自動では変更しない**。
- **クリーンなら何もしない**: 違反ゼロなら PR も Issue も作らず終了（無駄な通知・コストを出さない）。

> 迷ったら report 側に倒す。directory-keeper は「掃除」であって「設計変更」ではない。
