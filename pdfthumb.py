import matplotlib.pyplot as plt
import argparse
from pdf2image import convert_from_path
import math
from pathlib import Path
import slideinfo

def show_pdf_thumbnails(pdf_path, cols=5):
    # 1. PDFを画像のリストに変換 (DPIを下げると高速になります)
    print(pdf_path)
    pages = convert_from_path((pdf_path), dpi=72)
    
    total_pages = len(pages)
    rows = math.ceil(total_pages / cols)
    
    # 2. グラフのレイアウト設定
    fig, axes = plt.subplots(rows, cols, figsize=(15, 3 * rows))
    axes = axes.flatten() # 1次元配列にして扱いやすくする
    
    for i in range(len(axes)):
        if (i < total_pages) :
            # ページを表示
            axes[i].imshow(pages[i])
            if i > 0:
                axes[i].set_title(f"Page {i}", fontsize=8)
        
        # 軸を消してスッキリさせる
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()

def argget():
    ap = argparse.ArgumentParser(description="Beamer スライド部分抽出 & latexmk ビルド")
    ap.add_argument("items", nargs=2, help="科目コード と ディレクトリ名")
    args = ap.parse_args()
    subj_code, tdir_name = args.items
    tagdir = slideinfo.slidedir(subj_code, tdir_name)
    sourcedir_text = slideinfo.getsourcedir()
    title=slideinfo.slidetitle(subj_code, tdir_name)
    return Path(sourcedir_text) / tagdir,subj_code, tdir_name,title

# 実行
# \assetpath 内のファイルなどを指定してください
a=argget()
b=f"{a[2]}_{a[3]}_pr.pdf"
pdfpath=Path(a[0]) /  b
show_pdf_thumbnails(pdfpath)