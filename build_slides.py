# build_slides.py — 両テーマ latexmk 統一・範囲抽出ビルド 完全版
from __future__ import annotations
from pathlib import Path
import subprocess
import argparse
import re
import shutil
import sys,os
import time

import slideinfo  # slidedir(), slidetitle(), slideinfoupdate()

notecmd1=r'''
\setbeamertemplate{note page}{%
  \usebeamerfont{frametitle} \vspace{1.5ex}
  % ← タイトルの切り替え部分
  \ifx\notetitletext\empty
    \insertframetitle
  \else
    \notetitletext
  \fi
  \\[-1.5ex]
  {\hfill \textcolor{gray}{\scriptsize Note}} \\[-1ex]
  \rule{\linewidth}{0.4pt} \par
  {\scriptsize \insertnote}
}
'''

notecmd=r'''
% ノートタイトル付きマクロ
\newcommand{\noteT}[2]{%
  \gdef\notetitletext{#1}%
  \note{#2}%
}

\makeatletter
\renewcommand{\notetitletext}{} % 初期化（すでに定義されているため）
\setbeamertemplate{note page}{%
  \begin{minipage}{\linewidth}
    \vspace{1ex} % ← タイトルを少し下げる（ここを調整）
    {\Large \bfseries
      \ifx\notetitletext\@empty
        \insertframetitle
      \else
        \notetitletext
      \fi
    }

    \vspace{-1.5ex}
    \rule{\linewidth}{0.8pt}

%    \vspace{0.5ex}
%    \hfill {\textcolor{gray}{\LARGE \textbf{Note}}}
%    \par\nointerlineskip
%    \rule{\linewidth}{0.4pt}

    {\scriptsize
    \vspace{1ex}
    \insertnote
    }
  \end{minipage}
}
\makeatother

'''

notecmd2=r'''
\setbeamertemplate{note page}{%
  \begin{minipage}{\linewidth}
    \usebeamerfont{frametitle}
    \vspace{1.5ex}

    % safe title switching
    \ifx\notetitletext\empty
      \insertframetitle
    \else
      \notetitletext
    \fi

    \vspace{0.5ex}

    \hfill {\textcolor{gray}{\scriptsize Note}}
    \par\nointerlineskip
    \rule{\linewidth}{0.4pt}

    {\scriptsize
    \vspace{0.8ex}
    \insertnote
    }
  \end{minipage}
}
'''
# ----------------- ユーティリティ -----------------
def parse_page_range(range_str: str) -> tuple[int, int]:
    if not range_str:
        return -1, -1
    if "-" in range_str:
        try:
            s, e = map(int, range_str.split("-"))
        except ValueError:
            raise argparse.ArgumentTypeError("ページ範囲は整数で '開始-終了' 形式で指定")
        s = max(1, s)
        if e < s:
            e = s
        return s, e
    else:
        try:
            n = int(range_str)
        except ValueError:
            raise argparse.ArgumentTypeError("ページ範囲は整数で指定してください")
        return (1, 1) if n == 0 else (n, n)

def find_frame_positions(tex: str) -> list[tuple[int, int]]:
    # \begin{frame}[...]{...} ... \end{frame} を素朴に抽出（入れ子想定なし）
    pattern = r'(\\begin{frame}(\[[^\]]*\])?[^}]*?}.*?\\end{frame})(\s*|\n|$)'
    return [(m.start(1), m.end(1)) for m in re.finditer(pattern, tex, flags=re.DOTALL)]

def extract_frames(tex: str, fp: int, tp: int) -> str:
    pos = find_frame_positions(tex)
    if not pos:
        return ""
    total = len(pos)
    fp = max(1, fp); tp = min(tp, total)
    if fp > tp:
        return ""
    return "\n\n".join(tex[s:e] for i, (s, e) in enumerate(pos, 1) if fp <= i <= tp)

def theme_from_first_line(first_line: str) -> str:
    # 1行目に "@@@--(metropolis|SimpleDarkBlue)--@@@" があれば採用
    m = re.search(r"@@@--\((.*?)\)--@@@", first_line or "")
    if not m:
        return "SimpleDarkBlue"
    val = m.group(1)
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
            cmd, cwd=build_dir, capture_output=True, text=True, timeout=timeout_s
        )
    except subprocess.TimeoutExpired:
        print(f"❌ タイムアウトしました（{timeout_s}秒）", file=sys.stderr)
        sys.exit(1)
    end = time.perf_counter()
    print(f"latexコンパイル時間: {end - start:.4f}秒")

    if res.returncode != 0:
        lines = []
        for ln in (res.stdout.splitlines() + res.stderr.splitlines()):
            if ln.startswith("! ") or "error" in ln.lower():
                lines.append(ln)
        tail = "\n".join(lines[-80:]) or res.stdout[-3000:]
        print("リターンコード:",res.returncode)
        print("❌ LaTeX コンパイル失敗\n--- LOG ---\n" + tail, file=sys.stderr)
        sys.exit(1)
    print("✅ LaTeX コンパイル成功")

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
        print(subj_code, tdir_name)
        print("❌ 対象ディレクトリが解決できません", file=sys.stderr)
        sys.exit(1)

    root = Path(__file__).parent                  # build_slide/
    sourcedir_text=slideinfo.getsourcedir()
    app_dir = Path(sourcedir_text) / tagdir                # 例: project_root/2030302.../07
    content_path = app_dir / "content.tex"
    if not content_path.exists():
        print(f"❌ content.tex が見つかりません: {content_path}", file=sys.stderr)
        sys.exit(1)

    try:
        fp, tp = parse_page_range(args.page)
    except argparse.ArgumentTypeError as e:
        print("❌", e, file=sys.stderr)
        sys.exit(1)

    text2 = content_path.read_text(encoding="utf-8")
    ctheme = theme_from_first_line(text2.splitlines()[0] if text2 else "")
    print(f"対象ディレクトリ: {tagdir}")
    print(f"ページ範囲: {f'{fp}～{tp}' if fp!=-1 else '指定なし'} / ハンドアウト: {args.ho} / 教師モード: {args.tech}")
    print(f"beamerテーマ: {ctheme}")

    templ_map = {"SimpleDarkBlue": "main_template_org1.txt",
                 "metropolis":   "metro_template_org1.txt"}
    templ_file = root / "templates" / templ_map[ctheme]
    if not templ_file.exists():
        print(f"❌ テンプレートが見つかりません: {templ_file}", file=sys.stderr)
        sys.exit(1)

    templ = templ_file.read_text(encoding="utf-8")
    sdir_tex = safe_tex_path(tagdir)
#    sdir_tex = safe_tex_path(str(app_dir))
    stitle = f"{tdir_name} {slideinfo.slidetitle(subj_code, tdir_name)}"

    tex_head = (templ
                .replace("@@sdir@@", sdir_tex)
                .replace("@@stitle@@", stitle)
                .replace("@@sourcedir@@", sourcedir_text))
    #print(tex_head)
    tex_head = tex_head.replace("%@@pausemode@@",
                                r"\mypausemodefalse" if args.ho else r"\mypausemodetrue")
    tex_head = tex_head.replace("%@@teachermode@@",
                                r"\teachermodetrue" if args.tech else r"\teachermodefalse")
    # techの時は背景色は白にする
    if args.tech:
        tex_head = tex_head.replace("%@@setbeamcolor@@",r"\setbeamercolor{background canvas}{bg=white}")

    # notesの対応
    if args.ho:  # 
        tex_head = tex_head.replace("%@@notesdocumentmode@@",
                                    r"\documentclass[aspectratio=169]{beamer}")
        # %@@notesmode@@"は変更しない
    elif args.tech:  #_tech
        tex_head = tex_head.replace("%@@notesdocumentmode@@",
                                    r"\documentclass[handout,aspectratio=169]{beamer}")
        tex_head = tex_head.replace("%@@notesmode@@", r"\setbeameroption{show notes}")
        tex_head = tex_head.replace("%@@notesmode_tech@@", notecmd)
#        tex_head = tex_head.replace("%@@notesmode_tech@@", r"\setbeamertemplate{note page}{\usebeamerfont{frametitle} \vspace{1.5ex} \insertframetitle \\[-1.5ex] {\hfill \textcolor{gray}{\scriptsize Note}} \\[-1ex] \rule{\linewidth}{0.4pt} \par {\scriptsize \insertnote}}")
    else:  #_pr
        tex_head = tex_head.replace("%@@notesdocumentmode@@",
                                    r"\documentclass[aspectratio=169]{beamer}")
#                                    r"\documentclass[notes,aspectratio=169]{beamer}")
#        tex_head = tex_head.replace("%@@notesmode@@", r"\setbeameroption{show notes on second screen=right}")
#        tex_head = tex_head.replace("%@@notesmode@@", r"\setbeameroption{show notes}")

    print("プリアンブル作成")
    # --- フレーム部分抽出 ---
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

    # --- build/main.tex 生成 ---
    build_dir = root / "build"
    build_dir.mkdir(exist_ok=True)
    main_tex = build_dir / "main.tex"

    out_lines = [tex_head, "", body]
    if not body.endswith(r"\end{document}"):
        out_lines.append(r"\end{document}")
    main_tex.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("build/main.tex 生成")
    #--main.texのコピー---------------------------------------
    shutil.copy(build_dir / "main.tex", app_dir/"main.tex")
    print("main.texをコピーしました")
    
    # --- latexmk 実行（両テーマ共通） ---
    run_latexmk(build_dir, main_tex, timeout_s=360)
    print("latexmk 実行（両テーマ共通）")
    
    pdf_path = build_dir / "main.pdf"
    if not pdf_path.exists():
        print("❌ main.pdf が見つかりません", file=sys.stderr)
        sys.exit(1)

    # --- 出力名決定 & 配置 ---
    title = slideinfo.slidetitle(subj_code, tdir_name)
    stem = f"{tdir_name}_{title}"
    if suffix_tag:
        stem += suffix_tag
    else:
        if args.tech:
            stem += "_tech"
        elif not args.ho:
            stem += "_pr"
    final_pdf = app_dir / f"{stem}.pdf"

    # tmp_copy = "/tmp/tmp_build.pdf"
    
    # def wait_until_stable(path, timeout=10.0, interval=0.2):
    #     """ファイルのサイズが安定するまで待つ（SMB対応）"""
    #     start = time.time()
    #     last = -1
    #     while time.time() - start < timeout:
    #         try:
    #             size = os.path.getsize(path)
    #             if size > 0 and size == last:
    #                 return True
    #             last = size
    #         except:
    #             pass
    #         time.sleep(interval)
    #     return False
    
    # # ====== 1. SMB 上の PDF が安定するまで待つ ======
    # if not wait_until_stable(pdf_path, timeout=10):
    #     print("PDF が安定しません（SMB 同期中？）")
    #     sys.exit(1)
    
    # # ====== 2. まず SMB → /tmp にコピーする ======
    # for i in range(10):
    #     try:
    #         shutil.copyfile(pdf_path, tmp_copy)
    #         print("SMB → TMP: OK")
    #         break
    #     except Exception as e:
    #         print("retry SMB→TMP...", e)
    #         time.sleep(0.2)
    # else:
    #     print("SMB→TMP コピー失敗")
    #     sys.exit(1)
    
    # # ====== 3. /tmp → SMB final にコピー（これは 100% 成功）======
    # for i in range(10):
    #     try:
    #         shutil.copyfile(tmp_copy, final_pdf)
    #         print("TMP → FINAL: OK")
    #         break
    #     except Exception as e:
    #         print("retry TMP→FINAL...", e)
    #         time.sleep(0.2)
    # else:
    #     print("TMP→FINAL コピー失敗")
    #     sys.exit(1)
   # for i in range(10):
   #     if os.path.exists(pdf_path):
   #         try:
   #             shutil.copy2(pdf_path, final_pdf)
   #             break
   #         except Exception as e:
   #             print("retry...", e)
   #             time.sleep(0.2)
   # else:
   #     print("コピー失敗（最終）")
   #     sys.exit(1)
   #     raise

    try:
        shutil.copy2(pdf_path, final_pdf)
    except Exception as e:
        print(f"コピー失敗: {e}")
        sys.exit(1)
        raise

    print("✅ 出力:", final_pdf)
    
    # 必要なら掃除（buildを残すならコメントアウト）
    # for ext in ["aux","log","nav","out","snm","toc","vrb","fls","fdb_latexmk"]:
    #     for p in build_dir.glob(f"*.{ext}"):
    #         p.unlink(missing_ok=True)

    slideinfo.slideinfoupdate(subj_code, tdir_name)

if __name__ == "__main__":
    main()