import re
import json
from pathlib import Path

def getmacro():
    currpath=Path(__file__).parent
    empath=(currpath.parent.parent)/'build/emoji_macros.tex'
    latex_commands=""
    with empath.open(encoding="utf-8") as f:
        for line in f:
            latex_commands+=line


    # 正規表現で抽出
    # pattern = r"\\newcommand{\\emj([a-zA-Z0-9_]+)}{.*?{\\includegraphics\[.*?]{([a-zA-Z0-9_]+)\.png}}}"
    pattern = r"\\newcommand{\\emj([\wぁ-んァ-ヶ一-龯ーＡ-Ｚａ-ｚ０-９]+)}{.*?\\includegraphics\[.*?]{([\wぁ-んァ-ヶ一-龯ーＡ-Ｚａ-ｚ０-９]+)\.png}}"

    matches = re.findall(pattern, latex_commands)

    # JSONデータ作成
    data = []
    for caption, filename in matches:
        data.append({
            "src": f"{filename}.png",
            "alt": filename,
            "caption": caption
        })

    # srcキーを基準にソート
    sorted_data = sorted(data, key=lambda x: x["src"])
    return sorted_data
    # # 結果を出力
    # print(json.dumps(sorted_data, indent=2, ensure_ascii=False))