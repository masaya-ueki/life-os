#!/usr/bin/env python3
"""ドキュメント依存グラフ自動生成スクリプト（プロトタイプ）。

リポジトリ内の `.md` ファイルから相対リンクを抽出し、Mermaid 図として
出力する。`--check` モードではレイヤー違反と循環参照を検出する。

関連: Issue #339
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from datetime import datetime
from pathlib import Path

# レイヤー定義（プロトタイプはスクリプト内直書き / 先勝ち）
LAYERS: list[tuple[str, list[str]]] = [
    ("L0_common_rules",  ["AGENTS.md"]),
    ("L1_tool_specific", ["CLAUDE.md", ".github/copilot-instructions.md"]),
    ("L2_domain_rules",  [".claude/rules/*.md"]),
    ("L3_adr",           ["docs/adr/*.md"]),
    ("L4_design_docs",   ["docs/**/*.md"]),
]

OTHER_LAYER = "L_other"

EXCLUDE_DIRS: set[str] = {
    ".git",
    "node_modules",
    "dbt_packages",
    ".terraform",
    "target",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

# Markdown 相対リンク: [text](path.md) または [text](path.md#anchor)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+?\.md)(#[^)]*)?\)")

LAYER_COLORS: dict[str, str] = {
    "L0_common_rules":  "#fff3b0",
    "L1_tool_specific": "#a5d8ff",
    "L2_domain_rules":  "#b2f2bb",
    "L3_adr":           "#ffd6a5",
    "L4_design_docs":   "#e9ecef",
    OTHER_LAYER:        "#dee2e6",
}


def find_markdown_files(root: Path) -> list[Path]:
    """root 配下の `.md` ファイルを EXCLUDE_DIRS を除外して列挙する。"""
    files: list[Path] = []
    for p in root.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        files.append(p)
    return sorted(files)


def extract_links(md_file: Path, root: Path, known_files: set[Path]) -> list[Path]:
    """md_file から参照される `.md` ファイルを抽出する（known_files 内のみ）。"""
    try:
        text = md_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    self_resolved = md_file.resolve()
    links: list[Path] = []
    seen: set[Path] = set()
    for match in LINK_RE.finditer(text):
        target = match.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:", "//")):
            continue
        if target.startswith("/"):
            resolved = (root / target.lstrip("/")).resolve()
        else:
            resolved = (md_file.parent / target).resolve()
        if resolved not in known_files:
            continue
        if resolved == self_resolved:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        links.append(resolved)
    return links


def _glob_match(rel_path: str, pattern: str) -> bool:
    """gitignore 風セマンティクスの簡易 glob マッチ。

    - `/**/` は 0 個以上のディレクトリ（`docs/**/*.md` が `docs/foo.md` にもマッチ）
    - `**` は任意文字列（パス区切り含む）
    - `*` はパス区切りを含まない任意文字列
    """
    if "**" not in pattern:
        return fnmatch.fnmatchcase(rel_path, pattern)
    regex = re.escape(pattern)
    regex = regex.replace(r"/\*\*/", "/(?:.*/)?")
    regex = regex.replace(r"\*\*", ".*")
    regex = regex.replace(r"\*", "[^/]*")
    regex = regex.replace(r"\?", ".")
    return re.fullmatch(regex, rel_path) is not None


def classify_layer(path: Path, root: Path) -> str:
    """path をレイヤー名に分類する（LAYERS の先勝ち）。"""
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return OTHER_LAYER
    for layer_name, patterns in LAYERS:
        for pattern in patterns:
            if _glob_match(rel, pattern):
                return layer_name
    return OTHER_LAYER


def build_graph(root: Path) -> tuple[dict[Path, list[Path]], dict[Path, str]]:
    """グラフ（隣接リスト）と各ノードのレイヤー分類を構築する。"""
    root = root.resolve()
    files = find_markdown_files(root)
    known: set[Path] = {f.resolve() for f in files}
    graph: dict[Path, list[Path]] = {}
    layers: dict[Path, str] = {}
    for f in files:
        f_resolved = f.resolve()
        graph[f_resolved] = extract_links(f, root, known)
        layers[f_resolved] = classify_layer(f_resolved, root)
    return graph, layers


def detect_layer_violations(
    graph: dict[Path, list[Path]],
    layers: dict[Path, str],
) -> list[tuple[Path, Path, str, str]]:
    """上位レイヤー → 下位レイヤー の参照を違反として返す。

    L0 が最上位（汎用）、L4 が最下位（具体設計）。下位 → 上位は許容。
    L_other を含むエッジは判定対象外。
    """
    layer_order = {name: idx for idx, (name, _) in enumerate(LAYERS)}
    violations: list[tuple[Path, Path, str, str]] = []
    for src, targets in graph.items():
        src_layer = layers.get(src, OTHER_LAYER)
        if src_layer not in layer_order:
            continue
        src_idx = layer_order[src_layer]
        for tgt in targets:
            tgt_layer = layers.get(tgt, OTHER_LAYER)
            if tgt_layer not in layer_order:
                continue
            if src_idx < layer_order[tgt_layer]:
                violations.append((src, tgt, src_layer, tgt_layer))
    return violations


def detect_cycles(graph: dict[Path, list[Path]]) -> list[list[Path]]:
    """DFS で閉路を検出する。各閉路は循環ノード列（末尾 = 先頭）。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[Path, int] = {n: WHITE for n in graph}
    cycles: list[list[Path]] = []
    seen_cycles: set[tuple[Path, ...]] = set()

    def visit(node: Path, stack: list[Path]) -> None:
        color[node] = GRAY
        stack.append(node)
        for nbr in graph.get(node, []):
            if nbr not in color:
                continue
            if color[nbr] == GRAY:
                start = stack.index(nbr)
                cycle = stack[start:] + [nbr]
                norm = _normalize_cycle(cycle)
                if norm not in seen_cycles:
                    seen_cycles.add(norm)
                    cycles.append(cycle)
            elif color[nbr] == WHITE:
                visit(nbr, stack)
        stack.pop()
        color[node] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            visit(node, [])
    return cycles


def _normalize_cycle(cycle: list[Path]) -> tuple[Path, ...]:
    """循環を最小ノード起点に回転した正規形に変換（重複排除用）。"""
    core = cycle[:-1] if len(cycle) > 1 and cycle[0] == cycle[-1] else cycle
    if not core:
        return tuple(cycle)
    min_idx = min(range(len(core)), key=lambda i: str(core[i]))
    rotated = core[min_idx:] + core[:min_idx]
    return tuple(rotated)


def make_node_id(path: Path, root: Path) -> str:
    """Mermaid のノード ID（英数字 + アンダースコア）に変換する。"""
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = str(path)
    nid = re.sub(r"[^a-zA-Z0-9]", "_", rel)
    if nid and nid[0].isdigit():
        nid = "n_" + nid
    return nid


def _rel_or_str(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def render_mermaid(
    graph: dict[Path, list[Path]],
    layers: dict[Path, str],
    root: Path,
) -> str:
    """Mermaid（graph LR）文字列を返す。"""
    root = root.resolve()
    lines: list[str] = ["```mermaid", "graph LR"]

    by_layer: dict[str, list[Path]] = {}
    for path, layer in layers.items():
        by_layer.setdefault(layer, []).append(path)

    layer_order_keys = [name for name, _ in LAYERS] + [OTHER_LAYER]
    for layer in layer_order_keys:
        nodes = by_layer.get(layer)
        if not nodes:
            continue
        lines.append(f"    subgraph {layer}")
        for node in sorted(nodes, key=lambda p: str(p)):
            nid = make_node_id(node, root)
            label = _rel_or_str(node, root)
            lines.append(f'        {nid}["{label}"]')
        lines.append("    end")

    edge_lines: list[str] = []
    for src in sorted(graph.keys(), key=lambda p: str(p)):
        src_id = make_node_id(src, root)
        for tgt in sorted(graph[src], key=lambda p: str(p)):
            tgt_id = make_node_id(tgt, root)
            edge_lines.append(f"    {src_id} --> {tgt_id}")
    if edge_lines:
        lines.append("")
        lines.extend(edge_lines)

    lines.append("")
    for layer, color in LAYER_COLORS.items():
        lines.append(f"    classDef {layer} fill:{color},stroke:#333;")
    for layer in layer_order_keys:
        nodes = by_layer.get(layer)
        if not nodes:
            continue
        ids = ",".join(make_node_id(n, root) for n in sorted(nodes, key=lambda p: str(p)))
        lines.append(f"    class {ids} {layer};")

    lines.append("```")
    return "\n".join(lines)


def render_markdown_document(mermaid: str) -> str:
    """`docs/common/doc-graph.md` の本体テキストを返す。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    layer_rows = "\n".join(
        f"| `{name}` | {', '.join(f'`{p}`' for p in patterns)} |"
        for name, patterns in LAYERS
    )
    return f"""<!--
このファイルは scripts/generate_doc_graph.py が自動生成します。
手動編集禁止。再生成は次のコマンドで実施してください:

    python3 scripts/generate_doc_graph.py --output docs/common/doc-graph.md
-->

# ドキュメント依存グラフ

リポジトリ内 `.md` ファイル間の相対リンクを Mermaid 図として可視化したものです。

- 生成日時: {timestamp}
- 生成スクリプト: `scripts/generate_doc_graph.py`
- 関連 Issue: #339

## レイヤー定義

下位レイヤー → 上位レイヤー（例: `CLAUDE.md` → `AGENTS.md`）の参照は許容、
上位レイヤー → 下位レイヤー（例: `AGENTS.md` → `CLAUDE.md`）は禁止。

| レイヤー | 対象パターン |
|---|---|
{layer_rows}

> プロトタイプ段階のため、レイヤー定義の妥当性は動作確認後に調整します。

## 依存グラフ

{mermaid}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Markdown 間の依存関係を Mermaid 図として生成する（Issue #339）",
    )
    parser.add_argument("--root", default=".", help="走査ルート（既定: .）")
    parser.add_argument("--output", default=None, help="Markdown 出力先（未指定なら標準出力）")
    parser.add_argument(
        "--check",
        action="store_true",
        help="レイヤー違反 / 循環参照を検出し、違反があれば非ゼロ終了",
    )
    parser.add_argument("--quiet", action="store_true", help="サマリ出力を抑止（CI 想定）")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    graph, layers = build_graph(root)

    if args.check:
        violations = detect_layer_violations(graph, layers)
        cycles = detect_cycles(graph)

        if violations:
            print("レイヤー違反（上位 → 下位 の参照）:", file=sys.stderr)
            for src, tgt, src_layer, tgt_layer in violations:
                print(
                    f"  [{src_layer}] {_rel_or_str(src, root)}"
                    f" -> [{tgt_layer}] {_rel_or_str(tgt, root)}",
                    file=sys.stderr,
                )

        if cycles:
            print("循環参照:", file=sys.stderr)
            for cycle in cycles:
                path_str = " -> ".join(_rel_or_str(p, root) for p in cycle)
                print(f"  {path_str}", file=sys.stderr)

        if not args.quiet:
            print(
                f"\n検出結果: 違反 {len(violations)} 件 / 循環 {len(cycles)} 件",
                file=sys.stderr,
            )
        return 1 if (violations or cycles) else 0

    mermaid = render_mermaid(graph, layers, root)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_markdown_document(mermaid), encoding="utf-8")
        if not args.quiet:
            print(f"出力: {out_path}", file=sys.stderr)
    else:
        print(mermaid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
