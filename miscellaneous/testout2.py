from pathlib import Path
import slideinfo
import re

buld_slide = Path(__file__).parent
spath=buld_slide.parent / (slideinfo.slide_getdir('2030302'))

for i in range(2,14):
    di=f"{i:02d}"
    with open(spath/ f'{di}/content.tex', 'r', encoding='utf-8') as f:
        data = f.readlines()

    for v in data:
        match = re.search(r"\\title\{(.*)\}", v)
        if match:
            extracted_string = match.group(1) # グループ1（括弧内の内容）を取得
            print(f"抽出された文字列: {extracted_string}")
            break
exit()

lines = []
with open("session_slide.tex", "r", encoding="utf-8") as f:
    for line in f:
        stripped = line.rstrip()
        lines.append(stripped)

# '\begin{frame}' で始まる行のインデックスを取得
#frame_indices = [i for i, line in enumerate(lines) if line.startswith(r"\begin{frame}")]

def find_frame_blocks(lines):
    frame_indices = []
    start = None

    for idx, line in enumerate(lines):
        if r"\begin{frame}" in line:
            start = idx
        elif r"\end{frame}" in line and start is not None:
            frame_indices.append((start, idx))
            start = None  # 次の begin を探すためにリセット

    return frame_indices

frames = find_frame_blocks(lines)
print(frames)

# for i in range(frames[1][0],frames[1][1]+1):
#     print(lines[i])
exit()
# 再出力
with open("modified_slide.tex", "w", encoding="utf-8") as out:
    for line in lines:
        out.write(line + "\n")