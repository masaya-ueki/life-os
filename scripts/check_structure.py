#!/usr/bin/env python3
"""life-os ディレクトリ構成の決定的チェック（fitness function）。

`rule/` で定めた構造ルールのうち、機械的に判定できるものを検査する。
判断を要する項目（archetype 逸脱・ドキュメント配置の妥当性など）はここでは扱わず、
directory-keeper（.claude/skills/directory-keeper/SKILL.md）が内容を読んで判断する。

使い方:
    python scripts/check_structure.py            # 人が読むレポート
    python scripts/check_structure.py --json      # JSON 出力（keeper が解析する）
    python scripts/check_structure.py --strict     # warning でも非ゼロ終了

終了コード: error が 1 件以上なら 1。--strict なら warning でも 1。なければ 0。

設計根拠: rule/maintenance.md（監査チェックリスト）/ docs/adr/0004-...md
依存: 標準ライブラリのみ（Python 3.12+）。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- 正典の許可リスト（rule/directory-structure.md の正本に対応） ---

ROOT_ALLOWED_FILES = {
    "README.md",
    "CLAUDE.md",  # Claude Code のプロジェクト指示書
    "pyproject.toml",
    "uv.lock",
    ".importlinter",
    ".gitignore",
    ".python-version",
    "LICENSE",
    ".pre-commit-config.yaml",
    "compose.yaml",  # ローカル実行用 Docker Compose（docs/adr/0006）
    ".dockerignore",  # Docker ビルドコンテキスト除外（context=ルートのため直下に必要）
}

# content 領域 + 支援ディレクトリ（領域=workspace members は pyproject から動的に取得）
CONTENT_AND_SUPPORT_DIRS = {
    "docs",
    "guides",
    "rule",
    "scripts",
    "docker",  # 支援: テスト実行用 Dockerfile（docs/adr/0006）
    ".claude",
    ".github",
}

# 領域コンテナ: Bounded Context（workspace member）をまとめる親ディレクトリ。
# 直下には member（domains/<領域>）だけを置く。shared は Shared Kernel としてルート直下に残す。
DOMAIN_CONTAINER = "domains"

# 走査から除外（VCS 内部・生成物・ネストした worktree）
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".eggs",
    "build",
    "dist",
}

# 命名 kebab を強制するドキュメント領域（README.md / LICENSE は慣習的に除外）
KEBAB_DOC_DIRS = {"docs", "guides", "rule"}
KEBAB_EXEMPT_STEMS = {"README", "LICENSE"}
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:[-.][a-z0-9]+)*$")

# git にコミットされていてはならない生成物パターン
GENERATED_PATTERNS = [
    re.compile(r"(^|/)__pycache__/"),
    re.compile(r"\.pyc$"),
    re.compile(r"(^|/)\.venv/"),
    re.compile(r"(^|/)build/"),
    re.compile(r"(^|/)dist/"),
    re.compile(r"\.egg-info(/|$)"),
    re.compile(r"(^|/)\.pytest_cache/"),
    re.compile(r"(^|/)\.mypy_cache/"),
    re.compile(r"(^|/)\.ruff_cache/"),
    re.compile(r"(^|/)\.DS_Store$"),
    re.compile(r"(^|/)node_modules/"),
]

MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
DUP_MIN_LEN = 120  # この文字数以上の段落が複数ファイルに逐語で現れたら重複とみなす


@dataclass
class Finding:
    check: str
    severity: str  # "error" | "warning"
    path: str
    message: str


def _iter_files(suffix: str | None = None):
    """除外ディレクトリを飛ばしてリポジトリ内のファイルを走査する。"""
    stack = [REPO_ROOT]
    while stack:
        current = stack.pop()
        for child in current.iterdir():
            if child.is_dir():
                if child.name in SKIP_DIR_NAMES:
                    continue
                # ネストした worktree（.claude/worktrees/*）は別チェックアウトなので除外
                if child.relative_to(REPO_ROOT).as_posix().startswith(".claude/worktrees"):
                    continue
                stack.append(child)
            elif suffix is None or child.suffix == suffix:
                yield child


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _workspace_members() -> list[str]:
    pyproject = REPO_ROOT / "pyproject.toml"
    if not pyproject.exists():
        return []
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return list(data.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", []))


# --- 各チェック ---


def check_root_hygiene(findings: list[Finding]) -> None:
    """C-ROOT: ルート直下に許可外の単発ファイルが無い（R-STRUCT-5）。"""
    for child in REPO_ROOT.iterdir():
        if child.name in SKIP_DIR_NAMES:
            continue  # worktree では .git がファイルなのでここで除外
        if child.is_file() and child.name not in ROOT_ALLOWED_FILES:
            findings.append(
                Finding(
                    "C-ROOT",
                    "error",
                    child.name,
                    f"ルート直下の許可外ファイル。rule/directory-structure.md の許可リストに無い: {child.name}",
                )
            )


def check_top_level_dirs(findings: list[Finding], members: list[str]) -> None:
    """C-TOPDIR: トップレベルが正典4種に収まる。"""
    # member は domains/<領域> のようにネストし得るため、許可するのは先頭セグメント
    # （shared / domains 等の実トップレベル名）。
    member_tops = {m.split("/", 1)[0] for m in members}
    allowed = member_tops | CONTENT_AND_SUPPORT_DIRS
    for child in REPO_ROOT.iterdir():
        if not child.is_dir() or child.name in SKIP_DIR_NAMES:
            continue
        if child.name.startswith(".") and child.name not in allowed:
            continue  # .git 等のツール用隠しディレクトリは対象外
        if child.name not in allowed:
            findings.append(
                Finding(
                    "C-TOPDIR",
                    "warning",
                    child.name,
                    "未知のトップレベルディレクトリ。領域 / content領域 / 支援 のどれか確認し rule/ を更新する",
                )
            )


def check_domains_container(findings: list[Finding], members: list[str]) -> None:
    """C-DOMAIN: domains/ 直下は workspace member の領域だけ（雑多な混入を防ぐ）。"""
    base = REPO_ROOT / DOMAIN_CONTAINER
    if not base.exists():
        return
    member_paths = set(members)
    for child in base.iterdir():
        if child.name in SKIP_DIR_NAMES:
            continue
        rel = child.relative_to(REPO_ROOT).as_posix()
        if child.is_file():
            findings.append(
                Finding(
                    "C-DOMAIN",
                    "warning",
                    rel,
                    f"{DOMAIN_CONTAINER}/ 直下にファイルがある。領域(member)以外を置かない: {child.name}",
                )
            )
        elif rel not in member_paths:
            findings.append(
                Finding(
                    "C-DOMAIN",
                    "warning",
                    rel,
                    f"{DOMAIN_CONTAINER}/ 直下が workspace member でない。pyproject の members に追加するか移動する: {rel}",
                )
            )


def check_member_readme(findings: list[Finding], members: list[str]) -> None:
    """C-MEMBER-README: 各 workspace member に README がある（R-DOC-2）。"""
    for member in members:
        if not (REPO_ROOT / member / "README.md").exists():
            findings.append(
                Finding(
                    "C-MEMBER-README",
                    "error",
                    f"{member}/README.md",
                    f"workspace member '{member}' に README.md が無い",
                )
            )


def check_naming(findings: list[Finding]) -> None:
    """C-NAME-KEBAB: トップディレクトリと docs/guides/rule の md 名が kebab-case（R-NAME-1）。"""
    for child in REPO_ROOT.iterdir():
        if child.is_dir() and not child.name.startswith(".") and child.name not in SKIP_DIR_NAMES:
            if not KEBAB_RE.match(child.name):
                findings.append(
                    Finding("C-NAME-KEBAB", "warning", child.name, f"トップディレクトリ名が kebab-case でない: {child.name}")
                )
    for doc_dir in KEBAB_DOC_DIRS:
        base = REPO_ROOT / doc_dir
        if not base.exists():
            continue
        for md in base.rglob("*.md"):
            if md.stem in KEBAB_EXEMPT_STEMS:
                continue
            if not KEBAB_RE.match(md.stem):
                findings.append(
                    Finding("C-NAME-KEBAB", "warning", _rel(md), f"ドキュメント名が kebab-case でない: {md.name}")
                )


def check_links(findings: list[Finding]) -> None:
    """C-LINK: ドキュメントの相対リンクが解決できる（R-DOC-5）。"""
    for md in _iter_files(".md"):
        try:
            lines = md.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        in_fence = False
        for lineno, line in enumerate(lines, start=1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue  # コード例の中のリンクは検査しない
            for target in MD_LINK_RE.findall(line):
                target = target.strip()
                if not target or target[0] in "#" or "://" in target or target.startswith("mailto:"):
                    continue
                if "*" in target:
                    continue  # XXXX-*.md などのプレースホルダは除外
                path_part = target.split("#", 1)[0].split("?", 1)[0]
                if not path_part:
                    continue
                resolved = (md.parent / path_part).resolve()
                if not resolved.exists():
                    findings.append(
                        Finding(
                            "C-LINK",
                            "warning",
                            f"{_rel(md)}:{lineno}",
                            f"リンク切れ: {target}",
                        )
                    )


def _paragraphs(text: str) -> list[str]:
    """空行区切りの段落を正規化して返す（コードフェンス内は除外）。"""
    out: list[str] = []
    in_fence = False
    buf: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            buf = []
            continue
        if in_fence:
            continue
        if line.strip() == "":
            if buf:
                out.append(" ".join(buf))
                buf = []
        else:
            buf.append(line.strip())
    if buf:
        out.append(" ".join(buf))
    norm = []
    for para in out:
        collapsed = re.sub(r"\s+", " ", para).strip()
        if collapsed.startswith(("|", "#", ">")):
            continue  # 表・見出し・引用（ADR 等の共有引用）は重複対象外
        # リンク記法を表示テキストに畳んだ実プローズ量で判定（共有リンクの誤検知を防ぐ）
        prose = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", collapsed)
        if len(prose) >= DUP_MIN_LEN:
            norm.append(collapsed)
    return norm


def check_doc_duplication(findings: list[Finding]) -> None:
    """C-DOC-DUP: 複数の Markdown に逐語で重複する段落が無い（R-DOC-1）。"""
    seen: dict[str, set[str]] = {}
    for md in _iter_files(".md"):
        try:
            text = md.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for para in set(_paragraphs(text)):
            seen.setdefault(para, set()).add(_rel(md))
    for para, files in seen.items():
        if len(files) >= 2:
            findings.append(
                Finding(
                    "C-DOC-DUP",
                    "warning",
                    " / ".join(sorted(files)),
                    f"複数ファイルに重複する段落（Single Source of Truth 違反）: 「{para[:60]}…」",
                )
            )


def check_generated(findings: list[Finding]) -> None:
    """C-GENERATED: 生成物が git にコミットされていない（R-STRUCT-4）。"""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return  # git が無い環境ではスキップ
    for tracked in result.stdout.splitlines():
        for pattern in GENERATED_PATTERNS:
            if pattern.search(tracked):
                findings.append(
                    Finding("C-GENERATED", "warning", tracked, f"生成物がコミットされている: {tracked}")
                )
                break


def run_checks() -> list[Finding]:
    findings: list[Finding] = []
    members = _workspace_members()
    check_root_hygiene(findings)
    check_top_level_dirs(findings, members)
    check_domains_container(findings, members)
    check_member_readme(findings, members)
    check_naming(findings)
    check_links(findings)
    check_doc_duplication(findings)
    check_generated(findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="life-os ディレクトリ構成の決定的チェック")
    parser.add_argument("--json", action="store_true", help="JSON で出力する")
    parser.add_argument("--strict", action="store_true", help="warning でも非ゼロ終了する")
    args = parser.parse_args()

    findings = run_checks()
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    if args.json:
        print(json.dumps({"findings": [asdict(f) for f in findings],
                          "summary": {"error": len(errors), "warning": len(warnings)}},
                         ensure_ascii=False, indent=2))
    else:
        if not findings:
            print("✓ 構成チェック: 指摘なし（クリーン）")
        else:
            for f in findings:
                mark = "✗" if f.severity == "error" else "⚠"
                print(f"{mark} [{f.check}] {f.path}\n    {f.message}")
            print(f"\n— error: {len(errors)} / warning: {len(warnings)}")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
