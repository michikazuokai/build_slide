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

chatext="""以下は、アップロードした%%filename%%.tex のスライドのタイトルを抜き出したものです。この中から主要な項目や必要なら項目を追加して10項目を選んで簡潔な項目（下記項目そのままでも構いません）と簡単な説明文を作ってください。出力形式は　項目と説明文をタブで区切った１行で表示してください"""
chartex2 = """上記の %%filename%%.tex を元に4択問題を１０問作成してください"""
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
    # 1. \begin{frame}{タイトル} の形式
    pattern_begin = re.compile(
        r"\\begin\{frame\}(?:\[.*?\])?\{(.*?)\}", re.UNICODE
    )
    # 2. \frametitle{タイトル} の形式
    pattern_title = re.compile(
        r"\\frametitle\{(.*?)\}", re.UNICODE
    )
    
    titles = []
    inside_frame = False
    
    with content_path.open(encoding="utf-8") as f:
        for line in f:
            # \texttt{} を除去
            line1 = re.sub(r"\\texttt\{([^}]*)\}", r"\1", line)
    
            # --- ① begin{frame}{...} 形式 ---
            match1 = pattern_begin.search(line1)
            if match1:
                titles.append(match1.group(1).strip())
                inside_frame = True
                continue
    
            # --- ② frametitle{...} 形式 ---
            match2 = pattern_title.search(line1)
            if match2:
                titles.append(match2.group(1).strip())
                inside_frame = True
                continue
    
    # ========= 結果出力 =========
    stitle = slideinfo.slidetitle(subj_code, tdir_name)
    print("📑 検出されたスライドタイトル一覧:")
    t1=chatext.replace("%%filename%%",stitle)
    print(t1)
    for i, t in enumerate(titles, start=1):
        t2 = re.sub(r"\\emj[a-zA-Z]+", "", t)
        #t2 = re.sub(r"\\emj[0-9a-zA-Z]+ \S+", "", t)
        t1 = t2.replace("\\", "")
        print(f"{i:02d}. {t1}")
    
    print()
    t2=chartex2.replace("%%filename%%",stitle)
    print(t2)

if __name__ == "__main__":
    main()