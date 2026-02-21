import sys
from datetime import datetime
from pathlib import Path
from ruamel.yaml import YAML

# YAML オブジェクトの設定
yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

# ルートパスの設定
BUILD_SLIDE_ROOT = Path(__file__).parent.parent
DIRINFO_PATH = BUILD_SLIDE_ROOT / "dirinfo" / "dirinfo.yaml"

def _exit_with_error(message: str):
    """エラーメッセージを表示して終了するヘルパー"""
    print(f"❌ エラー: {message}", file=sys.stderr)
    sys.exit(1)

def _load_yaml(path: Path) -> dict:
    """ファイルをチェックしてYAMLを読み込むヘルパー"""
    if not path.exists():
        _exit_with_error(f"ファイルが見つかりません: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)
            if data is None:
                _exit_with_error(f"ファイルが空です: {path}")
            return data
    except Exception as e:
        _exit_with_error(f"YAMLの読み込みに失敗しました ({path}): {e}")

def _get_required_key(data: dict, key: str, context: str = "設定"):
    """辞書から必須キーを取得するヘルパー。ない場合は終了"""
    if key not in data:
        _exit_with_error(f"{context} 内に必須キー '{key}' が見つかりません。")
    return data[key]

def readslideyaml():
    """メインの設定ファイル dirinfo.yaml を読み込む"""
    return _load_yaml(DIRINFO_PATH)

def getsourcedir():
    """ソースディレクトリのルートを取得する"""
    sdic = readslideyaml()
    fsyear = _get_required_key(sdic, "fsyear", "dirinfo.yaml")
    year_conf = _get_required_key(sdic, fsyear, f"年度設定({fsyear})")
    
    return _get_required_key(year_conf, "dir", f"{fsyear}のディレクトリ設定")

def outputslideyaml(sdic, filename="slideinfo.yaml"):
    """YAMLファイルに書き出す"""
    path = BUILD_SLIDE_ROOT / filename
    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(sdic, f)
    except Exception as e:
        _exit_with_error(f"ファイルの書き出しに失敗しました ({path}): {e}")

def slidedir(subject, course):
    """スライドのディレクトリパスを生成する"""
    sdic = readslideyaml()
    fsyear = _get_required_key(sdic, "fsyear", "dirinfo.yaml")
    year_conf = _get_required_key(sdic, fsyear, f"年度設定({fsyear})")
    
    subject_dir = _get_required_key(year_conf, subject, f"科目設定({subject})")
    return f"{subject_dir}/{course}"

def slidetitle(subject, course):
    """科目別の slideinfo.yaml からタイトルを取得する"""
    sdic = readslideyaml()
    fsyear = _get_required_key(sdic, "fsyear", "dirinfo.yaml")
    year_conf = _get_required_key(sdic, fsyear, f"年度設定({fsyear})")
    
    # 科目のベースディレクトリを取得
    base_pt = Path(_get_required_key(year_conf, "dir", "共通ディレクトリ設定"))

    subject_dir = _get_required_key(year_conf, subject, f"科目設定({subject})")
    
    # 科目別設定ファイルのパス
    info_path = base_pt / subject_dir / "slideinfo" / "slideinfo.yaml"
    
    # 科目別設定の読み込み
    conf = _load_yaml(info_path)
    course_data = _get_required_key(conf, course, f"コース設定({course})")
    
    return _get_required_key(course_data, "title", f"{course} のタイトル設定")

def slideinfoupdate(subject, course):
    """科目別の slideinfo.yaml を探し、更新日時とカウントを更新する"""
    # 1. まず「地図(dirinfo.yaml)」を読み、科目別ファイルの場所を特定する
    sdic = readslideyaml()
    fsyear = _get_required_key(sdic, "fsyear", "dirinfo.yaml")
    year_conf = _get_required_key(sdic, fsyear, f"年度設定({fsyear})")
    
    base_pt = Path(_get_required_key(year_conf, "dir", "共通ディレクトリ設定"))
    
    # 科目別設定ファイルのフルパスを構築
    subject_dir = _get_required_key(year_conf, subject, f"科目設定({subject})")
    # (あなたのフォルダ構成に合わせて /slideinfo/slideinfo.yaml を指定)
    info_path = base_pt / subject_dir / "slideinfo" / "slideinfo.yaml"
    
    # 2. 「台帳(科目別のslideinfo.yaml)」を読み込む
    conf = _load_yaml(info_path)
    course_data = _get_required_key(conf, course, f"コース設定({course})")
    
    # 3. データの更新
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = course_data.get('count', 0)
    
    # get()で値を取得し、それが「空（None, '', 0等）」かどうかを判定
    if not course_data.get('created_at'):
        # キーがない、または中身が空文字 '' の場合はこちら
        course_data['created_at'] = dt
    else:
        # すでに何らかの文字列が入っている場合はこちら
        course_data['update_at'] = dt
    
    course_data['count'] = count + 1
    
    # 4. 「台帳」ファイルに上書き保存
    try:
        with open(info_path, 'w', encoding='utf-8') as f:
            yaml.dump(conf, f)
        print(f"✅ 台帳更新完了: {subject}/{course} (Count: {course_data['count']})")
    except Exception as e:
        _exit_with_error(f"台帳の保存に失敗しました ({info_path}): {e}")

if __name__ == '__main__':
    # テスト用
    try:
        print("--- Source Dir ---")
        print(getsourcedir())
        print(slidetitle("1020701", "02"))
        print("\n--- Slide Dir ---")
        # 実際の値に合わせてテストしてください
        # print(slidedir('1020701', '02'))
    except Exception as e:
        print(f"予期せぬエラー: {e}")