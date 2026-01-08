from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# 1 絵文字とファイル名の対応リスト
emoji_list = [
    ("📌", "pinx"),
    ("🎯", "target"),
    ("📝", "memo"),
    ("🧪", "lab"),
    ("📘", "booka"),
    ("📚", "bookb"),
    ("🔧", "tool"),
    ("🛠️", "toolx2"),
    ("🕒", "time"),
    ("✅", "checkx"),
    ("👉","r_yubi"),
    ("📦","box"),
    ("🔁","loopx"),
    ("📅","calenderx"),
    ("📄","docx1"),
    ("🧾","docx2"),
    ("🎓","gcap"),
    ("💡","bublex1"),
    ("🧪","testtubex1"),
    ("🎨","palettex1"),
    ("🖥","monitor"),
    ("⚙️","gear"),
    ("🖊️","pen"),
    ("🗑️","garbage"),
    ("🌐","globe"),
    ("🔗","link"),
    ("🗂️","foldera"),
    ("📋","clipboard"),
    ("🧩","piece"),
    ("🔧","wrench"),
    ("📎","clip"),
    ("📍","piny"),
    ("🌟","glowingstar"),
    ("🔍","MG"),
    ("🚀","rocket"),
    ("⭕️","ok"),
    ("❌","ng"),
    ("💻","pc"),
    ("🧠","brain"),
    ("👆","uyubi"),
    ("🔹","bluediamond"),
    ("⚠️","caution"),
    ("🤔","facea"),
    ("⏱️","stopwatch"),
    ("▶︎","blacktrianglea"),
    ("◀︎","blacktriangleb"),
    ("👥", "groupa"),
    ("🔭", "telescorpe"),
    ("🔑", "key"),
    ("❗️", "bang"),
    ("💬", "speechB"),
    ("💥", "explosion"),
    ("🙌", "banzai"),
    ("⚫️", "dotblack"),
    ("●", "dotblackS"),
    ]

# スクリプト自身の親ディレクトリを取得
p_dir = Path(__file__).parent.parent
# 2 出力先ディレクトリ
output_dir = p_dir / "emoji/emoji_pngs"
output_dir.mkdir(exist_ok=True)

# 3 MacのApple Color Emojiフォントのパス
font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
font_size = 160


# 4 各絵文字画像の生成
for emoji_char, name in emoji_list:
    img = Image.new("RGBA", (200, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)
    draw.text((20, 10), emoji_char, font=font, embedded_color=True)
    img.save(os.path.join(output_dir, f"{name}.png"))

print("✅ 絵文字画像を保存しました →", output_dir)