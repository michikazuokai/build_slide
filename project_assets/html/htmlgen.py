from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import convert

# ベースパス（注意：file:/// はPathには不要）
base_path = Path('/Volumes/NBPlan/TTC/build_slide/project_assets/emoji/emoji_pngs/')
template_dir = base_path.parent.parent / 'html'
template_file = 'template.html'  # ファイル名だけ

output_file = template_dir / 'output.html'

# データ読み込み
image_data = convert.getmacro()

# テンプレート環境設定（テンプレートのあるディレクトリを指定）
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template(template_file)  # ← ここはstr型！

# HTMLレンダリング
html_output = template.render(images=image_data, base_path=(str(base_path)+"/"))

# 保存
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_output)

print("✅ HTMLファイルを生成しました →", output_file)