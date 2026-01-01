from pathlib import Path
from itertools import tee, islice


pt=Path("/Volumes/NBPlan/TTC/授業資料/2025年度/")
app_dir = pt / "1010401.産業一般1/05"
content_path = app_dir / "content.tex"


text2 = content_path.read_text(encoding="utf-8")
texlst=text2.split('\n')

def find_end_to_next_start_ranges(lines):
    end_indices = []
    start_indices = []

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith(r"\begin{frame}"):
            start_indices.append(i)
        elif line.startswith(r"\end{frame}"):
            end_indices.append(i)
    
    pairs = [(0, start_indices[0])]
    start_pos = 0
    for end in end_indices:
        # 次の開始行を探す（終了行より大きい最小の開始行）
        while start_pos < len(start_indices) and start_indices[start_pos] <= end:
            start_pos += 1
        if start_pos < len(start_indices):
            pairs.append((end, start_indices[start_pos]))
        else:
            # 次の開始行がなければペアは作らない（またはNoneを入れるなど）
            pairs.append((end, None))
            break
    return pairs

pagepair=find_end_to_next_start_ranges(texlst)
print(pagepair)
print(len(pagepair))

for v in pagepair:
    if v[1]:
        print(texlst[v[1]])
# ilst=[]
# for j,v in enumerate(texlst):
#     if v.startswith(r'\begin{frame}'):
#         ilst.append(j)
#     if v.startswith(r'\end{frame}'):
#         ilst.append(j)
# # xlen=len(ilst)-1
# # for x in range(1,xlen,2):
# #     for i in range(ilst[x]+1,ilst[x+1]): 
# #         print(x,i,texlst[i])
# print(ilst)

# def sliding_window(iterable, n):
#     iters = tee(iterable, n)
#     for i, it in enumerate(iters):
#         # 0番目はそのまま、1番目は1回進める…というようにずらす
#         for _ in range(i):
#             next(it, None)
#     return zip(*iters)

# ret=sliding_window(texlst[19:23],3)
# for v in sliding_window(texlst[20:23],3):
#     print(v)