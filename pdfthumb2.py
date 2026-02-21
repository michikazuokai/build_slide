import argparse
import math
from pathlib import Path
import os
import sys
import subprocess

from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

import slideinfo


def make_thumbnail_sheet_pdf(
    src_pdf: Path,
    out_pdf: Path,
    cols: int = 4,
    rows: int = 6,
    dpi: int = 110,
    margin_mm: float = 8.0,
    gutter_mm: float = 2.0,
    draw_pageno: bool = True,
):
    src_pdf = Path(src_pdf)
    out_pdf = Path(out_pdf)

    if not src_pdf.exists():
        raise FileNotFoundError(f"PDF not found: {src_pdf}")

    pages = convert_from_path(str(src_pdf), dpi=dpi)
    total = len(pages)

    per_sheet = cols * rows
    sheets = math.ceil(total / per_sheet)

    page_w, page_h = A4
    margin = margin_mm * mm
    gutter = gutter_mm * mm

    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin

    cell_w = (usable_w - (cols - 1) * gutter) / cols
    cell_h = (usable_h - (rows - 1) * gutter) / rows

    # --- ページ番号(ラベル)領域をセルの下に確保 ---
    pageno_font = "Helvetica"
    pageno_size = 8
    label_pad_y = 0.8 * mm
    label_area_h = (pageno_size * 0.9) + (2 * label_pad_y)  # だいたいの高さ

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    c.setTitle(out_pdf.name)

    for s in range(sheets):
        start = s * per_sheet
        end = min(start + per_sheet, total)

        for idx in range(start, end):
            slot = idx - start
            col = slot % cols
            row = slot // cols  # 0が上段

            x0 = margin + col * (cell_w + gutter)

            # ReportLabは原点が左下。row=0を上段にする
            y_top = page_h - margin - row * (cell_h + gutter)
            y0 = y_top - cell_h  # このセルの下端

            # 画像は「ラベル領域」を除いた上側に描画
            img_area_y0 = y0 + label_area_h
            img_area_h = cell_h - label_area_h

            img = pages[idx]
            iw, ih = img.size

            # セル内（画像領域）に収める（縦横比維持）
            scale = min(cell_w / iw, img_area_h / ih)
            dw = iw * scale
            dh = ih * scale

            x = x0 + (cell_w - dw) / 2
            y = img_area_y0 + (img_area_h - dh) / 2

            c.drawImage(
                ImageReader(img),
                x, y,
                width=dw, height=dh,
                preserveAspectRatio=True,
                mask='auto'
            )

            # --- ページ番号：表紙(0)はなし。2枚目(1)を「1」 ---
            if draw_pageno and idx != 0:
                label = str(idx)  # idx=1 -> "1"
                c.setFont(pageno_font, pageno_size)
                tw = c.stringWidth(label, pageno_font, pageno_size)

                # セル下側ラベル領域の中央に配置
                tx = x0 + (cell_w - tw) / 2
                ty = y0 + label_pad_y
                c.drawString(tx, ty, label)

        c.showPage()

    c.save()
    print(f"[OK] wrote: {out_pdf}  (source pages={total}, sheets={sheets}, grid={cols}x{rows})")


def argget():
    ap = argparse.ArgumentParser(description="スライドPDFをA4サムネイルPDFに変換（4x6）")
    ap.add_argument("items", nargs=2, help="科目コード と ディレクトリ名")
    ap.add_argument("--dpi", type=int, default=110, help="サムネイル生成のDPI（高いほど綺麗・遅い）")
    ap.add_argument("--no-pageno", action="store_true", help="サムネイルにページ番号を付けない")
    ap.add_argument("--tech", action="store_true", help="教師用メモ（Teacher note）を出力に含める")
    args = ap.parse_args()

    subj_code, tdir_name = args.items
    tagdir = slideinfo.slidedir(subj_code, tdir_name)
    sourcedir_text = slideinfo.getsourcedir()
    title = slideinfo.slidetitle(subj_code, tdir_name)
    base_dir = Path(sourcedir_text) / tagdir
    return base_dir, subj_code, tdir_name, title, args.dpi, (not args.no_pageno), args.tech


if __name__ == "__main__":
    base_dir, subj_code, tdir_name, title, dpi, draw_pageno, is_tech = argget()
    
    if is_tech:
        src_name = f"{tdir_name}_{title}_tech.pdf"
    else:
        src_name = f"{tdir_name}_{title}.pdf"
    src_pdf = base_dir / src_name

    out_pdf = base_dir / f"{tdir_name}_{title}_thumbsheet_A4_{4}x{6}.pdf"

    make_thumbnail_sheet_pdf(
        src_pdf=src_pdf,
        out_pdf=out_pdf,
        cols=4,
        rows=6,
        dpi=dpi,
        margin_mm=8.0,
        gutter_mm=2.0,
        draw_pageno=draw_pageno,
    )

    if not out_pdf.exists():
        raise FileNotFoundError(out_pdf)

    subprocess.run(["open", str(out_pdf)], check=False)