import re

def themechk(fs):
    # 正規表現で抽出
    # 行の中からパターンを探す
    match = re.search(r"@@@--\((.*?)\)--@@@", fs)
    if match:
        extracted = match.group(1)  # ( ... ) 内の文字列
        if extracted in ["metropolis","SimpleDarkBlue"]:
            return extracted
        else:
            print(f'テーマの値が不正です {extracted}')
            exit(1)
    else:
        #マッチしない時は"SimpleDarkBlue"を返す
        return "SimpleDarkBlue"

print(themechk("% @@@--(metropolis)--@@@"))
print(themechk("% @@@--(SimpleDarkBlue)--@@@"))
print(themechk("%------------------------"))
print(themechk("% @@@--(newthememe)--@@@"))
