"""サンプルブランドテンプレート（.pptx）を生成するユーティリティ。

使い方:
  uv run --project scripts/deckgen python scripts/deckgen/tools/make_brand_template.py

出力: scripts/deckgen/templates/sample-brand.pptx

生成したファイルを PowerPoint で開き「テンプレートとして保存」すれば
.potx（PowerPoint テンプレート形式）として使える。
python-pptx は .pptx の生成のみサポートしているため、
.potx が必要な場合は PowerPoint での再保存が必要。
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches

# deckgen が参照している 16:9 寸法
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ブランドカラー（domains/presentation/templates/theme-tokens.yml の default テーマと一致）
BRAND_ACCENT = RGBColor(0x25, 0x63, 0xEB)   # #2563eb — 強調・アクセント
BRAND_BG     = RGBColor(0xFF, 0xFF, 0xFF)   # #ffffff — スライド背景
BRAND_FG     = RGBColor(0x1A, 0x1A, 0x2E)   # #1a1a2e — 本文
BRAND_MUTED  = RGBColor(0x6B, 0x72, 0x80)   # #6b7280 — 補足テキスト


def _set_solid_fill(fill, rgb: RGBColor) -> None:
    """pptx の FillFormat にソリッドカラーを設定する。"""
    fill.solid()
    fill.fore_color.rgb = rgb


def _apply_master_background(prs: Presentation, rgb: RGBColor) -> None:
    """スライドマスターの背景色を設定する。

    deckgen は --template 使用時に use_bg=False として自前の背景塗りを省略する。
    マスター側に背景を定義しておくことで、テンプレ継承が正しく機能する。
    """
    master = prs.slide_master
    bg = master.background
    _set_solid_fill(bg.fill, rgb)


def _apply_title_slide_accent(prs: Presentation, rgb: RGBColor) -> None:
    """タイトルスライドレイアウトのプレースホルダに accent 色を適用する。

    deckgen の title expression（表紙）は layout を使用せずシェイプを直接描画するため
    実質的な影響はないが、PowerPoint でテンプレを編集する際の参考としてマークする。
    """
    for layout in prs.slide_master.slide_layouts:
        if layout.name in ("Title Slide", "タイトル スライド"):
            for ph in layout.placeholders:
                try:
                    _set_solid_fill(ph.fill, rgb)
                except Exception:
                    pass
            break


def main() -> None:
    out = Path(__file__).parent.parent / "templates" / "sample-brand.pptx"
    out.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width  = SLIDE_W
    prs.slide_height = SLIDE_H

    _apply_master_background(prs, BRAND_BG)
    _apply_title_slide_accent(prs, BRAND_ACCENT)

    prs.save(str(out))
    print(f"[make_brand_template] 生成: {out}")
    print("  → PowerPoint で開き「テンプレートとして保存(.potx)」すると .potx を作成できます。")
    print("  → deckgen での使い方:")
    print(f"      uv run --project scripts/deckgen -m deckgen <slug> --template {out}")


if __name__ == "__main__":
    main()
