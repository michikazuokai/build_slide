from datetime import datetime
from pathlib import Path
# import json
#import yaml
from ruamel.yaml import YAML

# YAML オブジェクト作成（RoundTrip 用）
yaml = YAML()
yaml.preserve_quotes = True   # 引用符を保持したい場合
yaml.indent(mapping=2, sequence=4, offset=2)

build_slide = Path(__file__).parent.parent

def readslideyaml():
    filename = build_slide / "dirinfo/dirinfo.yaml"
    # YAMLを辞書として読み込む
    with open(filename, 'r', encoding='utf-8') as f:
#        sdic = yaml.safe_load(f)
        sdic = yaml.load(f)

    return sdic

def getsourcedir():
    sdic = readslideyaml()
    # fsyear取得
    fsyear = sdic["fsyear"]
    # fsyearの年配下のマッピング取得
    year_conf = sdic[fsyear]

    return year_conf['dir']

#     # subjectが年配下に存在するかチェック
#     if subject not in year_conf:
#         print(f"エラー: '{subject}' は {fsyear}年度に存在しません", file=sys.stderr)
#         sys.exit(1)

# #    sdic = readslidejson()
#     try:
#         _ = sdic["sourceinfo"]["dir"]
#         return sdic["sourceinfo"]["dir"]
#     except KeyError:
#         print("slideinfに [sourceinfo][dir]が存在しません")
#         return None

# def outputslidejson(sdic):
#     # ファイルを開いて辞書をJSON形式で書き出す
#     # 'w' モードでファイルを開く（ファイルが存在しない場合は新規作成、存在する場合は上書き）
#     filename = build_slide / "slideinfo.json"
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(sdic, f, ensure_ascii=False, indent=4)

def outputslideyaml(sdic):
    # YAMLファイルに書き出し
    # 'w' モードでファイルを開く（ファイルが存在しない場合は新規作成、存在する場合は上書き）
    filename = build_slide / "slideinfo.yaml"
    with open(filename, 'w', encoding='utf-8') as f:
#        yaml.dump(sdic, f, allow_unicode=True, sort_keys=False)
        yaml.dump(sdic, f)

def slidedir(subject,course):
    sdic = readslideyaml()
    fsyear=sdic['fsyear']

    return f"{sdic[fsyear][subject]}/{course}"

    # 1. subject の存在チェック
    try:
        _ = sdic[subject] # 値は必要ないが、アクセスを試みる
        return f"{sdic[subject]['dir']}/{course}"
    except KeyError:
        print(f'** ({subject}) は存在しません **')
        return None

def slidetitle(subject,course):
    sdic = readslideyaml()

    fsyear = sdic["fsyear"]
    year_conf = sdic[fsyear]

    # 1. subject の存在チェック
    pt = Path(year_conf["dir"])
    try:
        _ = year_conf.get(subject) # 値は必要ないが、アクセスを試みる
        pt1=(pt / year_conf[subject] / "slideinfo/slideinfo.yaml")
    except KeyError:
        print(f'** ({subject}) が存在しません 終了します **')
        raise 
    
    if not Path(pt1).exists():
        print(f"エラー: ファイルが存在しません: {pt1}")
        raise

    try:
        with open(pt1, "r", encoding="utf-8") as f:
            conf = yaml.load(f)
        if conf is None:
            print(f"警告: ファイルが空または無効なYAML: {pt}")
            return None
    except Exception as e:
        print(f"その他のエラー: {e}")
        return None
    
    with open(pt1, "r", encoding="utf-8") as f:
        conf1 = yaml.load(f)

    try:
        _ = conf1.get(course) # 値は必要ないが、アクセスを試みる
        return conf1[course]["title"]
    except KeyError:
        print(f'** ({subject}) にtitleが存在しません **')
        return 'unknownTitle'


def slideinfoupdate(subject,course):
#    sdic = readslidejson()
    sdic = readslideyaml()
    dt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if subject not in sdic:
        raise KeyError(f"Key '{subject}' not found in slideinfo.yaml")   
    if course not in sdic[subject]:
        raise KeyError(f"course Key '{course}' not found in slideinfo.yaml")
    
    if sdic[subject][course]['count']>0:
        sdic[subject][course]['update_at']=dt
    else:
        sdic[subject][course]['created_at']=dt
    sdic[subject][course]['count']+=1
    # ファイルを開いて辞書をJSON形式で書き出す
#    outputslidejson(sdic)
    outputslideyaml(sdic)

# def slide_getdir(subject):
# #    sdic = readslidejson()
#     sdic = readslideyaml()
#     return sdic[subject]['dir']


if __name__ == '__main__':
    print(readslideyaml())
    print(Path(getsourcedir())/ slidedir('1020701','02'))
    print(slidetitle('1020701','99'))


    # wdir=slidedir('1010401','02')
    # if not wdir:
    #     print('error')
    # else:
    #     print(wdir)

    # print(slidetitle('1010401','02'))