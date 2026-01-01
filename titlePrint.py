# build_slides.py — 両テーマ latexmk 統一・範囲抽出ビルド 完全版
from __future__ import annotations
from pathlib import Path
import subprocess
import argparse
import re
import shutil
import sys
import time

import slideinfo  # slidedir(), slidetitle(), slideinfoupdate()


# ----------------- メイン -----------------
def main():
    ap = argparse.ArgumentParser(description="Beamer スライド部分抽出 & latexmk ビルド")
    ap.add_argument("items", nargs=2, help="科目コード と ディレクトリ名")
    ap.add_argument("--page", "-p", default="", help="フレーム番号範囲（例: 5 / 3-7）")
    ap.add_argument("--ho", action="store_true", help="ハンドアウト（pause無効）")
    ap.add_argument("--tech", action="store_true", help="教師モードON")
    args = ap.parse_args()

    subj_code, tdir_name = args.items
    tagdir = slideinfo.slidedir(subj_code, tdir_name)
    
    if not tagdir:
        print("❌ 対象ディレクトリが解決できません", file=sys.stderr)
        sys.exit(1)

    root = Path(__file__).parent                  # build_slide/
    app_dir = Path(slideinfo.getsourcedir()) / tagdir                # 例: project_root/2030302.../07
    content_path = app_dir / "content.tex"
    if not content_path.exists():
        print(f"❌ content.tex が見つかりません: {content_path}", file=sys.stderr)
        sys.exit(1)

    # ========= 処理 =========
    pattern = re.compile(
        r"\\begin\{frame\}(?:\[.*?\])?\{(.*?)\}", re.UNICODE
    )
    # 説明：
    #   \\begin{frame}         ← \begin{frame} を検出
    #   (?:\[.*?\])?           ← [fragile], [allowframebreaks] などを非捕捉で許可
    #   \{(.*?)\}              ← {} 内のタイトル部分をキャプチャ



    # text2 = content_path.read_text(encoding="utf-8")
    titles = []
    
    with content_path.open(encoding="utf-8") as f:
        for line in f:
            line1=re.sub(r"\\texttt\{([^}]*)\}", r"\1", line)
            match = pattern.search(line1)
            if match:
                titles.append(match.group(1).strip())
        
    # ========= 結果出力 =========
    stitle = slideinfo.slidetitle(subj_code, tdir_name)
    print("📑 検出されたスライドタイトル一覧:")
    print(f"タイトル：{stitle}")
    for i, t in enumerate(titles, start=1):
        t1=t.replace("\\","")
        print(f"{i:02d}. {t1}")
    
    print(f"\n合計: {len(titles)} 件")

if __name__ == "__main__":
    main()