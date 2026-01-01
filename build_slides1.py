# build_slides.py — Beamer スライド部分抽出 & latexmk ビルド（metropolis/SimpleDarkBlue対応）
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

# tech 以外：\noteT を無視してコンパイルを通す（本文に \noteT があってもOK）
NOTES_CMD_OFF = r"""
\providecommand{\noteT}[2]{} % noteT を無視
"""

# tech：\noteT を有効化して、ノートページの見た目も差し替える
NOTES_CMD_TECH = r"""
% --- tech のときだけ noteT を有効化（テンプレートの \providecommand を上書き） ---
\makeatletter
\renewcommand{\noteT}[2]{%
 \gdef\notetitletext{#1}%
 \note{#2}%
}
% タイトル未指定のときのために初期化
\renewcommand{\notetitletext}{}%

\setbeamertemplate{note page}{%
 \begin{minipage}{\linewidth}
 \vspace{1.2ex} % タイトルを少し下げる（必要に応じて調整）
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

%教師用のPDFは奇数ページからスライドを出力
\oddslideenforcetrue
"""

# =========================
#  Utility
# =========================

def parse_page_range(range_str: str) -> tuple[int, int]:
    """
    ""  -> (-1, -1)  (指定なし)
    "5" -> (5, 5)
    "3-7" -> (3, 7)
    "0" -> (1, 1)  (互換のため)
    """
    if not range_str:
        return -1, -1

    s = range_str.strip()
    if "-" in s:
        try:
            a, b = map(int, s.split("-", 1))
        except ValueError:
            raise argparse.ArgumentTypeError("ページ範囲は整数で '開始-終了' 形式で指定")
        a = max(1, a)
        if b < a:
            b = a
        return a, b

    try:
        n = int(s)
    except ValueError:
        raise argparse.ArgumentTypeError("ページ範囲は整数で指定してください")
    return (1, 1) if n == 0 else (n, n)


def theme_from_first_line(first_line: str) -> str:
    """
    1行目に "@@@--(metropolis|SimpleDarkBlue)--@@@" があれば採用
    ない場合は SimpleDarkBlue にフォールバック
    """
    m = re.search(r"@@@--\((.*?)\)--@@@", first_line or "")
    if not m:
        return "SimpleDarkBlue"

    val = m.group(1).strip()
    if val in {"metropolis", "SimpleDarkBlue"}:
        return val

    print(f"テーマの値が不正です: {val}", file=sys.stderr)
    sys.exit(1)


def safe_tex_path(p: str | Path) -> str:
    return str(p).replace("\\", "/")


def run_latexmk(build_dir: Path, main_tex: Path, timeout_s: int = 360) -> None:
    cmd = [
        "latexmk", "-lualatex", "-shell-escape",
        "-interaction=nonstopmode", "-file-line-error",
        "-halt-on-error",
        f"-outdir={safe_tex_path(build_dir)}",
        safe_tex_path(main_tex),
    ]
    print("RUN:", " ".join(cmd))

    start = time.perf_counter()
    try:
        res = subprocess.run(
            cmd,
            cwd=build_dir,
            capture_output=True,
            text=True,
            timeout=timeout_s
        )
    except subprocess.TimeoutExpired:
        print(f"❌ タイムアウトしました（{timeout_s}秒）", file=sys.stderr)
        sys.exit(1)

    end = time.perf_counter()
    print(f"latexコンパイル時間: {end - start:.3f}秒")

    if res.returncode != 0:
        # なるべくエラー行を抽出
        lines = []
        for ln in (res.stdout.splitlines() + res.stderr.splitlines()):
            if ln.startswith("! ") or "LaTeX Error" in ln or "Undefined control sequence" in ln:
                lines.append(ln)
        tail = "\n".join(lines[-120:]) or (res.stdout + "\n" + res.stderr)[-4000:]
        print("リターンコード:", res.returncode)
        print("❌ LaTeX コンパイル失敗\n--- LOG ---\n" + tail, file=sys.stderr)
        sys.exit(1)

    print("✅ LaTeX コンパイル成功")


def find_frame_positions(tex: str) -> list[tuple[int, int]]:
    """
    \begin{frame} ... \end{frame} を素朴に抽出（入れ子なし想定）
    タイトル形式いろいろ対応するため、begin{frame}〜end{frame}全体を取る
    """
    pattern = re.compile(
        r"(\\begin\{frame\}(?:\[[^\]]*\])?(?:\{.*?\})?.*?\\end\{frame\})",
        flags=re.DOTALL
    )
    return [(m.start(1), m.end(1)) for m in pattern.finditer(tex)]


def extract_frames(tex: str, fp: int, tp: int) -> str:
    pos = find_frame_positions(tex)
    if not pos:
        return ""
    total = len(pos)

    fp = max(1, fp)
    tp = min(tp, total)
    if fp > tp:
        return ""

    parts = []
    for i, (s, e) in enumerate(pos, start=1):
        if fp <= i <= tp:
            parts.append(tex[s:e])
    return "\n\n".join(parts)


def apply_modes_to_template(tex_head: str, *, ho: bool, tech: bool) -> str:
    """
    テンプレの置換：
      - pause mode
      - teacher mode
      - notes documentclass / notes option / notes macro injection
    """

    # pause / teacher
    tex_head = tex_head.replace("%@@pausemode@@",
                                r"\mypausemodefalse" if ho else r"\mypausemodetrue")
    tex_head = tex_head.replace("%@@teachermode@@",
                                r"\teachermodetrue" if tech else r"\teachermodefalse")

    # notes
    if tech:
        # tech：handout + show notes + noteT有効
        tex_head = tex_head.replace("%@@notesdocumentmode@@",
                                    r"\documentclass[handout,aspectratio=169]{beamer}")
        tex_head = tex_head.replace("%@@notesmode@@", r"\setbeameroption{show notes}")
        tex_head = tex_head.replace("%@@notesmode_tech@@", NOTES_CMD_TECH)
    else:
        # ho/pr：notesは出さない、noteTは無視
        tex_head = tex_head.replace("%@@notesdocumentmode@@",
                                    r"\documentclass[aspectratio=169]{beamer}")
        tex_head = tex_head.replace("%@@notesmode@@", "")
        tex_head = tex_head.replace("%@@notesmode_tech@@", NOTES_CMD_OFF)

    return tex_head


# =========================
#  Main
# =========================

def main() -> None:
    ap = argparse.ArgumentParser(description="Beamer スライド部分抽出 & latexmk ビルド")
    ap.add_argument("items", nargs=2, help="科目コード と ディレクトリ名")
    ap.add_argument("--page", "-p", default="", help="フレーム番号範囲（例: 5 / 3-7）")
    ap.add_argument("--ho", action="store_true", help="ハンドアウト（pause無効）")
    ap.add_argument("--tech", action="store_true", help="教師モードON（note出力）")
    args = ap.parse_args()

    subj_code, tdir_name = args.items

    tagdir = slideinfo.slidedir(subj_code, tdir_name)
    if not tagdir:
        print(subj_code, tdir_name)
        print("❌ 対象ディレクトリが解決できません", file=sys.stderr)
        sys.exit(1)

    root = Path(__file__).parent  # build_slide/
    sourcedir_text = slideinfo.getsourcedir()
    app_dir = Path(sourcedir_text) / tagdir
    content_path = app_dir / "content.tex"
    if not content_path.exists():
        print(f"❌ content.tex が見つかりません: {content_path}", file=sys.stderr)
        sys.exit(1)

    # page range
    try:
        fp, tp = parse_page_range(args.page)
    except argparse.ArgumentTypeError as e:
        print("❌", e, file=sys.stderr)
        sys.exit(1)

    # read content
    text2 = content_path.read_text(encoding="utf-8")

    # theme decision
    first_line = text2.splitlines()[0] if text2 else ""
    ctheme = theme_from_first_line(first_line)

    print(f"対象ディレクトリ: {tagdir}")
    print(f"ページ範囲: {f'{fp}～{tp}' if fp != -1 else '指定なし'} / ho: {args.ho} / tech: {args.tech}")
    print(f"beamerテーマ: {ctheme}")

    # template selection
    templ_map = {
        "SimpleDarkBlue": "main_template_org1.txt",
        "metropolis": "metro_template_org1.txt"
    }
    templ_file = root / "templates" / templ_map[ctheme]
    if not templ_file.exists():
        print(f"❌ テンプレートが見つかりません: {templ_file}", file=sys.stderr)
        sys.exit(1)

    templ = templ_file.read_text(encoding="utf-8")

    # placeholders
    sdir_tex = safe_tex_path(tagdir)
    stitle = f"{tdir_name} {slideinfo.slidetitle(subj_code, tdir_name)}"

    tex_head = (
        templ
        .replace("@@sdir@@", sdir_tex)
        .replace("@@stitle@@", stitle)
        .replace("@@sourcedir@@", sourcedir_text)
    )

    # 背景色（tech だけ白など）テンプレが %@@setbeamcolor@@ を持つ前提
    if args.tech:
        tex_head = tex_head.replace("%@@setbeamcolor@@",
                                    r"\setbeamercolor{background canvas}{bg=white}")
    else:
        tex_head = tex_head.replace("%@@setbeamcolor@@", "")

    # mode injection (pause/teacher/notes)
    tex_head = apply_modes_to_template(tex_head, ho=args.ho, tech=args.tech)

    print("✅ プリアンブル作成")

    # frame extraction
    if fp != -1:
        part = extract_frames(text2, fp, tp)
        if not part.strip():
            print("⚠ 指定範囲に一致する frame がありません。全体をビルドします。")
            part = text2
        body = part.rstrip()
        suffix_tag = "_test"
    else:
        body = text2.rstrip()
        suffix_tag = None

    # build dir
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)
    main_tex = build_dir / "main.tex"

    out_lines = [tex_head, "", body]
    if not body.endswith(r"\end{document}"):
        out_lines.append(r"\end{document}")

    main_tex.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("✅ build/main.tex 生成:", main_tex)

    # copy main.tex to source dir (任意：あなたの運用に合わせて維持)
    try:
        shutil.copy2(main_tex, app_dir / "main.tex")
        print("✅ main.tex をコピーしました:", app_dir / "main.tex")
    except Exception as e:
        print(f"⚠ main.tex のコピーに失敗: {e}")

    # latexmk
    run_latexmk(build_dir, main_tex, timeout_s=360)

    pdf_path = build_dir / "main.pdf"
    if not pdf_path.exists():
        print("❌ main.pdf が見つかりません", file=sys.stderr)
        sys.exit(1)

    # output name
    title = slideinfo.slidetitle(subj_code, tdir_name)
    stem = f"{tdir_name}_{title}"
    if suffix_tag:
        stem += suffix_tag
    else:
        if args.tech:
            stem += "_tech"
        elif not args.ho:
            stem += "_pr"
        # ho は suffix なし（あなたの元仕様）

    final_pdf = app_dir / f"{stem}.pdf"

    try:
        shutil.copy2(pdf_path, final_pdf)
#    except Exception as e:
#        print(f"❌ PDFコピー失敗: {e}", file=sys.stderr)
#        sys.exit(1)
    except OSError as e:
        # 本体はコピー済みで、メタデータだけ失敗のケースがある
        if os.path.exists(final_pdf) and os.path.getsize(final_pdf) > 0:
            print(f"⚠️ PDFコピーは完了（メタデータコピーのみ失敗）: {e}", file=sys.stderr)
        else:
            print(f"❌ PDFコピー失敗: {e}", file=sys.stderr)
            sys.exit(1)


    print("✅ 出力:", final_pdf)

    # 更新（あなたの slideinfo 連携）
    slideinfo.slideinfoupdate(subj_code, tdir_name)


if __name__ == "__main__":
    main()