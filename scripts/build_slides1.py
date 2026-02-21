# build_slides.py — Beamer スライド部分抽出 & latexmk ビルド（分割テンプレート対応版）
from __future__ import annotations

from pathlib import Path
import subprocess
import argparse
import re
import shutil
import sys
import time
import os
import slideinfo  # slidedir(), slidetitle(), slideinfoupdate(), getsourcedir()

# =========================
#  Notes 注入コード
# =========================

NOTES_CMD_OFF = r"""\providecommand{\noteT}[2]{} % noteT を無視"""

NOTES_CMD_TECH = r"""
\makeatletter
\renewcommand{\noteT}[2]{%
 \gdef\notetitletext{#1}%
 \note{#2}%
}
\renewcommand{\notetitletext}{}%
\setbeamertemplate{note page}{%
 \begin{minipage}{\linewidth}
 \vspace{1.2ex}
 {\Large\bfseries
 \ifx\notetitletext\@empty
 \insertframetitle
 \else
 \notetitletext
 \fi
 }\par
 \vspace{-1.2ex}
 \rule{\linewidth}{0.8pt}\par
 \vspace{0.8ex}
 {\scriptsize \insertnote}
 \end{minipage}
}
\makeatother
\oddslideenforcetrue
"""

# =========================
#  Utility
# =========================

def parse_page_range(range_str: str) -> tuple[int, int]:
    if not range_str: return -1, -1
    s = range_str.strip()
    if "-" in s:
        try:
            a, b = map(int, s.split("-", 1))
            a = max(1, a)
            if b < a: b = a
            return a, b
        except ValueError:
            raise argparse.ArgumentTypeError("範囲指定エラー")
    try:
        n = int(s)
        return (1, 1) if n == 0 else (n, n)
    except ValueError:
        raise argparse.ArgumentTypeError("数値指定エラー")

def theme_from_first_line(first_line: str) -> str:
    m = re.search(r"@@@--\((.*?)\)--@@@", first_line or "")
    val = m.group(1).strip() if m else "SimpleDarkBlue"
    return val if val in {"metropolis", "SimpleDarkBlue"} else "SimpleDarkBlue"

def safe_tex_path(p: str | Path) -> str:
    return str(p).replace("\\", "/")

def run_latexmk(build_dir: Path, main_tex: Path, timeout_s: int = 360) -> None:
    cmd = ["latexmk", "-lualatex", "-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
           f"-outdir={safe_tex_path(build_dir)}", safe_tex_path(main_tex)]
    print("RUN:", " ".join(cmd))
    start = time.perf_counter()
    try:
        res = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print("❌ タイムアウト", file=sys.stderr); sys.exit(1)
    
    print(f"latexコンパイル時間: {time.perf_counter() - start:.3f}秒")
    if res.returncode != 0:
        print("❌ LaTeX コンパイル失敗", file=sys.stderr); sys.exit(1)
    print("✅ LaTeX コンパイル成功")

def find_frame_positions(tex: str) -> list[tuple[int, int]]:
    pattern = re.compile(r"(\\begin\{frame\}(?:\[[^\]]*\])?(?:\{.*?\})?.*?\\end\{frame\})", flags=re.DOTALL)
    return [(m.start(1), m.end(1)) for m in pattern.finditer(tex)]

def extract_frames(tex: str, fp: int, tp: int) -> str:
    pos = find_frame_positions(tex)
    if not pos: return ""
    fp, tp = max(1, fp), min(tp, len(pos))
    return "\n\n".join([tex[pos[i-1][0]:pos[i-1][1]] for i in range(fp, tp+1)])

def apply_modes_to_template(content: str, *, ho: bool, tech: bool) -> str:
    content = content.replace("%@@pausemode@@", r"\mypausemodefalse" if ho else r"\mypausemodetrue")
    content = content.replace("%@@teachermode@@", r"\teachermodetrue" if tech else r"\teachermodefalse")
    if tech:
        content = content.replace("%@@notesdocumentmode@@", r"\documentclass[handout,aspectratio=169]{beamer}")
        content = content.replace("%@@notesmode@@", r"\setbeameroption{show notes}")
        content = content.replace("%@@notesmode_tech@@", NOTES_CMD_TECH)
    else:
        content = content.replace("%@@notesdocumentmode@@", r"\documentclass[aspectratio=169]{beamer}")
        content = content.replace("%@@notesmode@@", "")
        content = content.replace("%@@notesmode_tech@@", NOTES_CMD_OFF)
    return content

def sync_page_comments_to_source(content_path: Path):
    text = content_path.read_text(encoding="utf-8")
    text2 = re.sub(rf'(?m)^\s*%@@PAGEBAND@@\s*\n(?:^\s*%[^\n]*\n)+', '', text)
    count = 0
    def repl(match):
        nonlocal count; count += 1
        return f"\n%@@PAGEBAND@@\n% {'-'*88}\n%   page {count:02d}\n% {'-'*88}\n{match.group(0)}"
    new_text = re.sub(r'(?m)^\\begin\{frame\}', repl, text2)
    if text != new_text:
        content_path.write_text(new_text, encoding="utf-8")
        print(f"✅ ページ番号刷新 (Total: {count} frames)")

# =========================
#  引数表示
# =========================
def display_build_config(subj_code: str, tdir_name: str, tagdir: str, stitle: str, 
                         args: argparse.Namespace, ctheme: str, content_path: Path):
    """実行前に現在のビルド設定を一覧表示する"""
    
    # タイトルの取得元を判定
    title_source = "(引数指定)" if args.title else "(YAML取得)"
    
    # ページ範囲の表示
    page_info = f"{args.page}" if args.page else "全文（指定なし）"
    
    # --- モード表示の判定ロジック ---
    if args.tech:
        mode_info = "教師用 (Teacher Mode)"
    elif args.ho:
        mode_info = "ハンズアウト (Handout Mode)"
    else:
        mode_info = "プレゼン用 (Presentation Mode)"
    # ------------------------------

    print("\n" + "="*65)
    print("  🚀 ビルド設定の最終確認")
    print("-" * 65)
    print(f"  ■ 科目コード    : {subj_code}")
    print(f"  ■ コマ番号      : {tdir_name}")
    print(f"  ■ 解決パス      : {tagdir}")
    print(f"  ■ スライド題名  : {stitle} {title_source}")
    print(f"  ■ ページ範囲    : {page_info}")
    print(f"  ■ 出力モード    : {mode_info}") # ここに反映されます
    print(f"  ■ Beamerテーマ  : {ctheme}")
    print(f"  ■ 左フッター    : {'[非表示]' if args.hidefooter else '[表示]'}")
    print(f"  ■ ソースファイル: {content_path}")
    print("=" * 65 + "\n")

# =========================
#  Main
# =========================

def main() -> None:
    ap = argparse.ArgumentParser(description="Beamer スライド部分抽出 & ビルド")
    ap.add_argument("items", nargs=2, help="科目コード ディレクトリ名")
    ap.add_argument("--page", "-p", default="")
    ap.add_argument("--ho", action="store_true")
    ap.add_argument("--tech", action="store_true")
    ap.add_argument("--hidefooter", action="store_true")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    subj_code, tdir_name = args.items
    tagdir = slideinfo.slidedir(subj_code, tdir_name)
    if not tagdir: sys.exit(1)

    root = Path(__file__).parent.parent
    sourcedir_text = slideinfo.getsourcedir()
    app_dir = Path(sourcedir_text) / tagdir
    content_path = app_dir / "content.tex"
    if not content_path.exists(): sys.exit(1)

    # 1. 前準備
    sync_page_comments_to_source(content_path)
    fp, tp = parse_page_range(args.page)
    stitle = args.title if args.title else slideinfo.slidetitle(subj_code, tdir_name)
    sdir_tex = safe_tex_path(tagdir)
    l_footer_content = "" if args.hidefooter else r"\scriptsize\color{gray!50} \myfootertext"

    # ビルドディレクトリ作成（サブファイル書き込み前に必要）
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)

    # 2. テンプレート読み込みと置換
    text2 = content_path.read_text(encoding="utf-8")
    ctheme = theme_from_first_line(text2.splitlines()[0] if text2 else "")

    # 引数の表示
    display_build_config(subj_code, tdir_name, tagdir, stitle, args, ctheme, content_path)
    
    templ_map = {"SimpleDarkBlue": "main_template_org1.tex", "metropolis": "main_template_org1.tex"}
    templ_file = root / "templates" / templ_map[ctheme]
    if not templ_file.exists(): sys.exit(1)

    # 親テンプレートの処理
    templ_raw = templ_file.read_text(encoding="utf-8")
    tex_main = apply_modes_to_template(templ_raw, ho=args.ho, tech=args.tech)
    tex_main = tex_main.replace("@@stitle@@", stitle)

    # サブファイルの処理
    sub_files = ["preamble.tex", "macros.tex", "styles.tex", "emoji_macros.tex", "grid_debug.tex","teacherframe.sty"]
    for sub_name in sub_files:
        sub_path = root / "templates" / sub_name
        if not sub_path.exists(): continue
        sub_c = sub_path.read_text(encoding="utf-8")
        sub_c = sub_c.replace("@@sdir@@", sdir_tex).replace("@@sourcedir@@", safe_tex_path(sourcedir_text)).replace("@@leftfooter@@", l_footer_content)
        
        if args.tech:
            sub_c = sub_c.replace("%@@setbeamcolor@@", r"\setbeamercolor{background canvas}{bg=white}")
        else:
            sub_c = sub_c.replace("%@@setbeamcolor@@", "")
        
        sub_c = apply_modes_to_template(sub_c, ho=args.ho, tech=args.tech)
        (build_dir / sub_name).write_text(sub_c, encoding="utf-8")

    print("✅ プリアンブル作成（サブファイルの配備完了）")

    # 3. 本文抽出
    if fp != -1:
        body = extract_frames(text2, fp, tp).rstrip()
        suffix_tag = "_test"
    else:
        body = text2.rstrip()
        suffix_tag = None

    # 4. main.tex 組み立て
    final_tex = tex_main.replace("@@BODY@@", body)
    main_tex = build_dir / "main.tex"
    main_tex.write_text(final_tex, encoding="utf-8")


    # out_lines = [tex_main, "", body]
    # if not body.strip().endswith(r"\end{document}"):
    #     out_lines.append(r"\end{document}")
    
    # main_tex = build_dir / "main.tex"
    # main_tex.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    
    try: shutil.copy2(main_tex, app_dir / "main.tex")
    except: pass

    # 5. 実行とコピー
    run_latexmk(build_dir, main_tex)
    
    stem = f"{tdir_name}_{stitle}{suffix_tag if suffix_tag else ('_tech' if args.tech else ('_pr' if not args.ho else ''))}"
    final_pdf = app_dir / f"{stem}.pdf"
    shutil.copy2(build_dir / "main.pdf", final_pdf)
    
    print("✅ 出力:", final_pdf)
    slideinfo.slideinfoupdate(subj_code, tdir_name)

if __name__ == "__main__":
    main()