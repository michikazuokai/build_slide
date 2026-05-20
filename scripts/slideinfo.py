# /Volumes/NBPlan/TTC/build_slide/scripts/slideinfo.py
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime
from typing import Any


# ============================================================
# Path settings
# ============================================================

# このファイル:
# /Volumes/NBPlan/TTC/build_slide/scripts/slideinfo.py
#
# parent        = /Volumes/NBPlan/TTC/build_slide/scripts
# parent.parent = /Volumes/NBPlan/TTC/build_slide
# parent.parent.parent = /Volumes/NBPlan/TTC

BUILD_SLIDE_ROOT = Path(__file__).resolve().parent.parent
TTC_ROOT = BUILD_SLIDE_ROOT.parent

COMMON_UTIL_DIR = TTC_ROOT / "@TTC" / "util"

if str(COMMON_UTIL_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_UTIL_DIR))


try:
    from utils import (
        get_current_fsyear,
        get_source_root,
        get_lesson_relative_dir,
        get_lesson_title,
        load_slideinfo_by_subno,
        save_slideinfo,
        get_required_key,
    )
except ImportError as e:
    print("❌ @TTC/util/utils.py の読み込みに失敗しました。", file=sys.stderr)
    print(f"   COMMON_UTIL_DIR: {COMMON_UTIL_DIR}", file=sys.stderr)
    print(f"   error: {e}", file=sys.stderr)
    sys.exit(1)


# ============================================================
# Error helper
# ============================================================

def _exit_with_error(message: str) -> None:
    """
    build_slide 用のエラー終了。
    旧 slideinfo.py と同じように、エラーを表示して終了する。
    """
    print(f"❌ エラー: {message}", file=sys.stderr)
    sys.exit(1)


def _safe_call(func, *args, **kwargs):
    """
    utils.py 側で発生した例外を、build_slide 用のメッセージにして終了する。
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        _exit_with_error(str(e))


# ============================================================
# Public functions for build_slides1.py
# ============================================================

def getsourcedir() -> str:
    """
    現在年度の授業資料ルートを返す。

    旧 slideinfo.py の getsourcedir() 相当。

    例:
        /Volumes/NBPlan/TTC/授業資料/2026年度/
    """
    source_root = _safe_call(get_source_root)
    return str(source_root)


def slidedir(subject: str, course: str) -> str:
    """
    授業資料ルートから見た、指定授業回フォルダの相対パスを返す。

    旧 slideinfo.py の slidedir() 相当。

    例:
        subject = "1020701"
        course  = "02"

    戻り値:
        1020701.GITバージョン管理/02
    """
    return _safe_call(get_lesson_relative_dir, subject, course)


def slidetitle(subject: str, course: str) -> str:
    """
    科目別 slideinfo.yaml から、指定授業回の title を返す。

    旧 slideinfo.py の slidetitle() 相当。
    """
    return _safe_call(get_lesson_title, subject, course)


def slideinfoupdate(subject: str, course: str) -> None:
    """
    科目別 slideinfo.yaml の created_at / update_at / count を更新する。

    旧 slideinfo.py の slideinfoupdate() 相当。

    slideinfo.yaml の構造は次のような想定。

    '02':
      title: コンピュータと2進数の基本
      schedule_type: 授業
      count: 51
      created_at: '2026-03-17 12:45:28'
      update_at: '2026-05-06 07:36:16'
    """
    try:
        fsyear = get_current_fsyear()
        slideinfo_data, subject_dir = load_slideinfo_by_subno(subject, fsyear)

        course = str(course).zfill(2)

        course_data = get_required_key(
            slideinfo_data,
            course,
            f"slideinfo.yaml の授業回設定({course})",
        )

        if not isinstance(course_data, dict):
            raise TypeError(f"授業回設定({course}) がdict形式ではありません。")

        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        count = course_data.get("count", 0)

        try:
            count = int(count)
        except Exception:
            count = 0

        if not course_data.get("created_at"):
            course_data["created_at"] = dt
        else:
            course_data["update_at"] = dt

        course_data["count"] = count + 1

        save_slideinfo(subject_dir, slideinfo_data)

        print(f"✅ 台帳更新完了: {subject}/{course} (Count: {course_data['count']})")

    except Exception as e:
        _exit_with_error(str(e))


# ============================================================
# Compatibility / debug functions
# ============================================================

def readslideyaml() -> dict[str, Any]:
    """
    旧 slideinfo.py 互換用。

    以前は build_slide/dirinfo/dirinfo.yaml を読んでいたが、
    新構成では @TTC/dirinfo/dirinfo.yaml を読む。

    ただし build_slides1.py からは通常使わない。
    """
    try:
        from utils import load_dirinfo
        return load_dirinfo()
    except Exception as e:
        _exit_with_error(str(e))


# ============================================================
# Simple test
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("build_slide/scripts/slideinfo.py 動作確認")
    print("=" * 70)

    try:
        print("\n[1] パス確認")
        print("BUILD_SLIDE_ROOT:", BUILD_SLIDE_ROOT)
        print("TTC_ROOT        :", TTC_ROOT)
        print("COMMON_UTIL_DIR :", COMMON_UTIL_DIR)
        print("COMMON_UTIL exists:", COMMON_UTIL_DIR.exists())

        print("\n[2] 授業資料ルート確認")
        print("getsourcedir():", getsourcedir())

        # 必要に応じて変更してください
        subject = "1020701"
        course = "02"

        print("\n[3] テスト対象")
        print("subject:", subject)
        print("course :", course)

        print("\n[4] slidedir() 確認")
        print("slidedir:", slidedir(subject, course))

        print("\n[5] slidetitle() 確認")
        print("slidetitle:", slidetitle(subject, course))

        print("\n[6] slideinfoupdate() 確認")
        print("注意: 実行すると slideinfo.yaml の count / created_at / update_at が更新されます。")
        print("テストでは自動実行しません。必要なら次の行のコメントを外してください。")
        # slideinfoupdate(subject, course)

        print("\n✅ slideinfo.py の確認が完了しました。")

    except Exception as e:
        print("\n❌ 動作確認中にエラーが発生しました。")
        print(type(e).__name__, ":", e)
        raise