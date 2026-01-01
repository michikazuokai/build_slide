from pathlib import Path
import shutil
lesson_dir = Path(__file__).parent

with open(lesson_dir / 'main_htemp.tex', encoding='utf-8') as f_in, \
     open(lesson_dir / 'main_temp.tex', 'w', encoding='utf-8') as f_out:
    f_out.write(f_in.read().replace('@@dir@@', '05'))

fromPath = lesson_dir.parent/'05/content.tex'
shutil.copy(fromPath, lesson_dir)