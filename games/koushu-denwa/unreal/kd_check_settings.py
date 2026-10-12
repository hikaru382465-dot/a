"""kd_settings.json の確認：書き方（カンマ・かっこ・引用符）のまちがいと、数字の種類のまちがいを探す。
使い方（Unreal の Cmd 欄）：  py "…/unreal/kd_check_settings.py"      結果は出力ログ（KD で絞る）に出る。"""
import ast
import json
import os
import re

try:
    import unreal
    LOG = lambda m: unreal.log("[KD] " + m)
    WARN = lambda m: unreal.log_warning("[KD] " + m)
    SAVED = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
except Exception:  # noqa  （Unreal の外でも試せるように）
    LOG = WARN = print
    SAVED = os.environ.get("KD_SAVED", ".")

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(SAVED, "kd_settings.json")


def defaults(fname, list_name):
    src = open(os.path.join(HERE, fname), encoding="utf-8").read()
    names = ast.literal_eval(re.search(r"^%s = (\[.*?\])\s*$" % list_name, src, re.M | re.S).group(1))
    out = {}
    for n in names:
        m = re.search(r"^%s\s*=\s*(.+?)(?:\s+#.*)?$" % re.escape(n), src, re.M)
        if m:
            try:
                out[n] = ast.literal_eval(m.group(1).strip())
            except Exception:  # noqa
                out[n] = None
    return out


def main():
    problems = 0
    LOG("確認するファイル: %s" % PATH)
    if not os.path.exists(PATH):
        WARN("ファイルがありません。先に kd_game.py か setup_game_fp.py を一度動かしてください")
        return
    text = open(PATH, encoding="utf-8").read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        line = text.splitlines()[e.lineno - 1] if e.lineno <= len(text.splitlines()) else ""
        WARN("書き方がまちがっています：%d 行目・%d 文字目: %s" % (e.lineno, e.colno, e.msg))
        WARN("  その行: %s" % line.strip())
        WARN("  よくあるまちがい：行の終わりのカンマ（,）の付け忘れ／最後の行に余分なカンマ／\" の閉じ忘れ／全角の記号")
        return
    vals = data.get("設定")
    if not isinstance(vals, dict):
        WARN("\"設定\" の項目がありません（{ \"設定\": { ... } } の形にしてください）")
        return
    known = {}
    known.update(defaults("kd_game.py", "KD_SETTING_NAMES"))
    known.update(defaults("setup_game_fp.py", "SETUP_SETTING_NAMES"))
    for k, v in vals.items():
        if k not in known:
            WARN("知らない項目: %s（名前のまちがい？ 使われません）" % k)
            problems += 1
            continue
        d = known[k]
        if d is None:
            continue
        ok = True
        if isinstance(d, bool):
            ok = isinstance(v, bool)
        elif isinstance(d, (int, float)):
            ok = isinstance(v, (int, float)) and not isinstance(v, bool)
        elif isinstance(d, str):
            ok = isinstance(v, str)
        elif isinstance(d, (list, tuple)):
            ok = isinstance(v, list)
        if not ok:
            WARN("種類がちがう: %s = %r（初期値は %r）" % (k, v, d))
            problems += 1
    for k in ("START_POS",):
        v = vals.get(k)
        if isinstance(v, list) and v and len(v) != 3:
            WARN("START_POS は、数字が3つ（x, y, z）必要です: %r" % (v,))
            problems += 1
    for k in ("REPLACE_GLASS_MATERIAL",):
        if vals.get(k) is False:
            WARN("REPLACE_GLASS_MATERIAL が false です。買ったガラスの材質が、元に戻されます（ひかるが直したままにしたいときは null）")
            problems += 1
    if vals.get("TUBE_SCALE") not in (None,) and isinstance(vals.get("TUBE_SCALE"), (int, float)) and vals["TUBE_SCALE"] < 0.9:
        LOG("メモ: TUBE_SCALE=%s（蛍光灯の光を、さらに %s 倍にしています。ひかるが直した明るさをそのまま使うなら 1.0）" % (vals["TUBE_SCALE"], vals["TUBE_SCALE"]))
    if problems == 0:
        LOG("問題は見つかりませんでした（%d 項目を確認）" % len(vals))
    else:
        WARN("気になる所が %d 件ありました" % problems)


main()
