"""
ゲームのしくみ 段階1〜2 の準備（買った公衆電話があるレベル用。FirstPersonMap など）
何度実行しても同じ結果になる（KD_Game タグの物は、毎回消して置き直す）。

やること：
  1) 買った公衆電話を探して、大きさ・中心・入口の向きを求める
  2) 当たり判定を「形そのもの」にして、中に入れるようにする
  3) 天井に蛍光灯2本（光＋光る見た目）を付ける ／ 効果音（ドア）を取り込む。入口は E キーで「暗転→ドアの音→中に入る」にする（ドアは動かさない）
  4) プレイヤーの開始位置を、入口の正面の遠くに動かす（既存の PlayerStart を使う）
  5) 懐中電灯、張り紙（14枚）、幽霊（仮）を置く
入口の向きは、下の FRONT で決める（+X / -X / +Y / -Y のどちらが「開いている側」か）。
そのあと Cmd で  py "…/unreal/kd_game.py"  を実行して ▶（Play）。
"""
import json
import os
import math
import random
import traceback

import unreal

# ---------------- 書き換えてよい設定 ----------------
GAME_DIR = "/Game/KoushuDenwa"
TAG = "KD_Game"
BOOTH_KEY = "phone_box"              # 電話ボックスの名前に入っている言葉（glass を含む名前は除く）
FRONT = "-Y"                         # 入口（開いている側）の向き。+X / -X / +Y / -Y のどれか（下見で確認済み：-Y）
NIGHT_MODE = True                    # True: 夕方の空を夜にする（本編レベルだけ。スタート画面は変えない）
SUN_INTENSITY = 0.0                  # 太陽の明るさ（夜は 0）
MOON_INTENSITY = 0.35                # 月の光
SKY_INTENSITY = 0.25                 # 空の光
PROTECT_LEVELS = ("FirstPersonMap",)  # このレベル（スタート画面用）では実行しない。本編用にコピーしたレベルで実行する
START_HEIGHT = 400.0                 # 開始位置の高さ（ボックスの足元から何cm 上）。高めに置いて、落ちて地面に立たせる（地面に埋まって歩けなくなるのを防ぐ）
START_DIST = 1800.0                  # プレイヤーを、入口の正面から何cm 離して立たせるか
FLASH_INTENSITY = 3000.0             # 懐中電灯の明るさ（カンデラ）
FLASH_INNER, FLASH_OUTER = 14.0, 30.0
FLASH_RADIUS = 1800.0
POSTER_GLOW = 0.15                   # 張り紙の、うすい自己発光の強さ
GHOST_SCALE = 1.2                    # 本物の幽霊の大きさ（1.0=約160cm）。プレイヤー（約190cm）より少し高くして、見上げる怖さを出す
GHOST_MODEL = True                  # True: 本物の幽霊のモデル（assets/unreal/ghost/Ghost_rigged.fbx）を置く。取り込みに失敗したら、仮の姿（黒い筒＋白い頭）を置く。False: いつも仮の姿
GHOST_HEIGHT = 160.0                 # 幽霊の身長（cm）。取り込み後に測って、この高さに合わせる
RESET_POSTERS = True                 # True: ガラスの文字・目の写真の位置は、実行のたびに、ガラスの面から計算し直す（手で動かした位置は覚えない）。手で動かした位置を残したいなら False
GLASS_GAP = 2.0                      # ガラスの文字を、ガラスの面から内側へ何cm 離して貼るか（浮いて見えるなら小さく。ガラスにめり込むなら大きく）
WALL_INSET = 20.0                    # 張り紙を、ボックスの外形（屋根のはみ出しを含む）から内側へ何cm 入れた所に貼るか。外にはみ出すときは大きくする
GLASS_GLOW = 6.0                     # ガラスの文字の光り方（大きいほど、暗い中で白く光る）
GLASS_SCALE = 1.3                    # ガラスの文字の大きさ（1.0 = 横50×縦70cm の板。1.3 で 65×91cm。大きいほどガラスいっぱいに出る）
CODE_SCALE = 0.8                     # 謎7：貼られる4枚の紙（ガラスの文字）の大きさ（GLASS_SCALE にかける倍率）
CODE_TREE_SIZE = 110.0               # 謎7：外の木に光る数字の板の高さ（cm）。数字そのものは板の高さの約6割。小さくて読めないなら大きく
CODE_TREE_Z = 170.0                  # 謎7：光る数字の中心の高さ（木の根もと＝地面から cm）。目の高さくらい
CODE_TREE_MIN = 450.0                # 謎7：数字を光らせる木を、ボックスの中心から何cm 以上はなれた所から選ぶか
CODE_TREE_MAX = 800.0                # 同じく、何cm 以内か（遠いと小さくて読めない）
CODE_TREE_ANGLE = 40.0               # 同じく、入口の向きから左右に何度までの木を選ぶか（ガラスごしに4本いっぺんに見える範囲）
CODE_TREE_PICK = "auto"              # "auto": 森の木から自動で4本選ぶ（足りなければ、黒い枯れ木の柱を足す）／"spawn": いつも専用の柱を4本立てる
CODE_TREE_ORDER = [1, 3, 0, 2]       # 左→右に並べた4本のうち、光る順番（0=いちばん左）。[1,3,0,2] = 左から2番目→右はし→左はし→右から2番目。左から右にならない順番
CODE_TREE_TRUNK_R = 25.0             # 木の幹の半径の見つもり（cm）。数字を、幹の表面からさらに3cm 手前に貼る。幹にめり込む／浮くなら変える
CODE_TREE_GLOW = 3.0                 # 謎7：外の木の数字の光り方（GLASS_GLOW にかける倍率）。まぶしすぎ・暗すぎなら変える
GLASS_SPREAD = True                  # True: ガラスの文字を、ガラスぜんたい（4面・上から下まで）に散りばめる。False: 昔の12か所だけ
GLASS_COUNT = 24                     # ガラスの文字の枚数（GLASS_SPREAD=True のとき。12より多く・36以下。4面に同じ数ずつ）
GLASS_SIZE_MIN = 0.8                 # 散りばめる文字の大きさのばらつき（GLASS_SCALE にかける倍率の下限と上限）
GLASS_SIZE_MAX = 1.5
GLASS_TILT = 7.0                     # 散りばめる文字の傾き（度。±）
POSTER_SCALE = 0.5                   # 張り紙の大きさ（1.0 = 横50cm×縦70cm）。大きすぎて外が見えないときは小さくする
KEEP_HAND_PLACEMENT = True           # True: 掲示板・張り紙を手で動かしてあれば、この準備を実行し直しても、その位置のまま。false にすると、BOARD_* などの数字の位置に作り直す
BOARD_SCALE = 0.75                   # 掲示板の大きさ（1.0 = 横264×高さ245cm。公衆電話が高さ約314cm なので、0.75 で横198×高さ184cm）
SAFE_BACK = -28.0                    # ダイヤル式の金庫を、ボックスの中心から奥（入口の反対）へ何cm（－が奥）
SAFE_SIDE = 22.0                     # 金庫を、中心から横へ何cm（＋は入口に向かって左）
SAFE_SCALE = 1.6                     # 金庫の大きさ（1.0 = 本物の手提げ金庫 幅36cm。見やすいよう 1.6 で幅58cm）
DIAL_CAM_DIST = 30.0                 # 金庫のダイヤルを回すとき、専用カメラを、つまみの前（おもて側）から何cm 離すか（小さいほどアップ）
DIAL_CAM_FOV = 42.0                  # そのカメラの視野の角度（小さいほどアップ）
BOX_CAM_BACK = 9.0                   # 金庫の中の箱を押すカメラ（KD_BoxCam）を、箱の上面の真ん中から、おもて側へ何cm 離すか（金庫の倍率つき）
BOX_CAM_UP = 30.0                    # 同じく、上へ何cm（FOV60で 4×4 のボタンが画面の高さの約6割になる）
BOX_TOP = 6.2                        # 箱のボタンの面の高さ（箱の原点から cm・Blenderの設計どおり）
SAFE_TURN = 0.0                      # 金庫の向き（入口の向きから何度まわすか）
BOARD_DIST = 450.0                   # 掲示板を、ボックスの入口の前（外）から何cm 離して立てるか
BOARD_SIDE = 260.0                   # 掲示板を、入口の正面から横へ何cm ずらすか（＋は入口に向かって左）
BOARD_TURN = 25.0                    # 掲示板を、入口の向きから何度まわして、道のほうへ向けるか
PAPER_WIND_AMP = 1.6                 # 紙が風でゆれる大きさ（cm）。0 でゆれない。下のふちほど大きくゆれる
PAPER_WIND_MATERIAL = False          # True: 紙の材質に、頂点をゆらす仕組みを付ける（まだ実験中。材質が壊れて市松もようになったら False に）
PAPER_WIND_SPEED = 0.35              # ゆれる速さ（1秒に何回ゆれるか）
TUBE_Z_FROM_TOP = 40.0               # 蛍光灯を、天井の上端から何cm 下に付けるか
# --------------------------------------------------

mel = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
STATE = {}

# ---------------- 調整つまみ（設定ファイル） ----------------
# 数字は Saved/kd_settings.json に書いてある。メモ帳で開いて数字を変えて保存するだけで効く。
# （ZIP を取り直しても消えない場所にある。無い項目は、最初の実行で自動で足される）
SETTINGS_DESCR = {
    "FLASH_INSIDE": "閉じ込められたあとの懐中電灯の明るさ（外にいたときの何倍か）。明るすぎたら小さく",
    "TUBE_SCALE": "蛍光灯の光の強さの倍率。明るすぎたら小さく",
    "TUBE_GLOW": "蛍光灯の「光る見た目」の倍率",
    "FLICKER_BLACK": "点滅の「消えた」瞬間に画面を黒くする割合（0〜1）。点滅が暗くならないなら大きく",
    "CODE_SCALE": "謎7：貼られる4枚の紙（ガラスの文字）の大きさ（ガラスの文字の大きさにかける倍率）",
    "CODE_TREE_SIZE": "謎7：外の木に光る数字の板の高さ（cm）。数字は板の約6割",
    "CODE_TREE_Z": "謎7：光る数字の中心の高さ（地面から cm）",
    "CODE_TREE_MIN": "謎7：数字を光らせる木の、ボックス中心からの最小の距離（cm）",
    "CODE_TREE_MAX": "謎7：同じく最大の距離（cm）",
    "CODE_TREE_ANGLE": "謎7：木を選ぶ範囲。入口の向きから左右に何度まで",
    "CODE_TREE_PICK": "謎7：auto=森の木から自動で4本選ぶ（足りなければ柱を足す）／spawn=いつも専用の柱を4本立てる",
    "CODE_TREE_ORDER": "謎7：左→右に並べた4本の光る順番（0=いちばん左）。[1,3,0,2] は左右の順にならない",
    "CODE_TREE_TRUNK_R": "謎7：木の幹の半径の見つもり（cm）。数字は、幹の表面からさらに3cm 手前に貼る",
    "CODE_TREE_GLOW": "謎7：外の木の数字の光り方（ガラスの文字の光り方にかける倍率）",
    "GLASS_SPREAD": "true: ガラスの文字を、ガラスぜんたいに散りばめる。false: 昔の12か所だけ",
    "GLASS_COUNT": "ガラスの文字の枚数（散りばめるとき。12〜36）",
    "GLASS_SIZE_MIN": "散りばめる文字の大きさの倍率の下限（ガラスの文字の大きさにかける）",
    "GLASS_SIZE_MAX": "散りばめる文字の大きさの倍率の上限",
    "GLASS_TILT": "散りばめる文字の傾き（度。±）",
    "DARK_BLACK": "暗転のあいだに画面を黒くする割合（0〜1）",
    "DARK_WORLD": "暗転のとき、月と空の光を何倍まで下げるか",
    "GLASS_DIRT": "ガラスのくもりの強さ（M_KDGlass を使うとき）",
    "WALK_SPEED": "歩く速さ（cm/秒）。テンプレのキャラには効かない",
    "ENTER_RANGE": "入口の前の、E で入れる距離（cm）",
    "ENTER_FADE_OUT": "E を押してから暗くなるまでの秒数",
    "ENTER_BLACK": "暗いまま待つ秒数（この間にドアの音が鳴る）",
    "ENTER_FADE_IN": "明るくなるまでの秒数",
    "FLICKER_TIME": "点滅の長さ（秒）",
    "DARK_TIME": "暗転の長さ（秒）",
    "GHOST_HOLD": "幽霊が外に見えている秒数（演出の強さ1〜4ごと）",
    "POSTER_HOLD": "張り紙が貼られている秒数（演出の強さ1〜4ごと）",
    "POSTER_STEP": "張り紙が1枚ずつ貼られる間隔（秒）",
    "POSTER_FRAC": "張り紙が何割まで貼られるか（演出の強さ1〜4ごと）",
    "PUZZLE_COUNT": "謎の数（演出の強さが最後まで進む謎の数）",
    "PRESSURE_INTERVAL": "謎が進まないとき、幽霊が1段階近づくまでの秒数",
    "DEAD_DIST": "失敗のとき、幽霊が目の前に出る距離（cm）",
    "RESTART_AFTER": "失敗してから最初に戻るまでの秒数",
    "GHOST_SPOTS": "幽霊の出る場所（[横, 入口の方向] の cm。ボックスの中心から。4か所）",
    "FRONT": "電話ボックスの入口の向き（+X / -X / +Y / -Y）",
    "START_HEIGHT": "開始位置を、ボックスの足元から何cm 上に置くか（高いと、落ちて地面に立つ）",
    "START_DIST": "プレイヤーを入口の前から何cm離して立たせるか",
    "NIGHT_MODE": "true で、本編レベルを夜にする",
    "SUN_INTENSITY": "太陽の明るさ（夜は 0）",
    "MOON_INTENSITY": "月の光の強さ",
    "SKY_INTENSITY": "空の光の強さ",
    "POSTER_SCALE": "張り紙の大きさ（1.0 = 横50cm×縦70cm）",
    "WALL_INSET": "張り紙を、ボックスの外形から内側へ何cm入れて貼るか",
    "POSTER_GLOW": "張り紙のうすい自己発光の強さ",
    "FLASH_INTENSITY": "懐中電灯の明るさ（カンデラ。外にいるときの強さ）",
    "FLASH_INNER": "懐中電灯の、中心の角度",
    "FLASH_OUTER": "懐中電灯の、外側の角度",
    "FLASH_RADIUS": "懐中電灯の光が届く距離（cm）",
    "TUBE_Z_FROM_TOP": "蛍光灯を、天井の上端から何cm下に付けるか",
    "KEEP_HAND_PLACEMENT": "true: 掲示板・張り紙を手で動かした位置を、準備をやり直しても残す。false: 数字の位置に作り直す",
    "BOARD_SCALE": "掲示板の大きさの倍率（1.0 で横264×高さ245cm）。大きいと感じたら小さく",
    "SAFE_BACK": "ダイヤル式の金庫を、ボックスの中心から奥へ何cm（マイナスが奥）",
    "SAFE_SIDE": "金庫を、中心から横へ何cm（プラスは入口に向かって左）",
    "SAFE_SCALE": "金庫の大きさの倍率（1.0 で幅36cm）",
    "SAFE_TURN": "金庫の向き（度）",
    "COIN_DIST": "10円①を、入口の前から何cm の所に置くか",
    "COIN_SIDE": "10円①を、入口の正面から横へ何cm（プラスは入口に向かって左）",
    "BOARD_DIST": "掲示板を、入口の前から何cm 離して立てるか",
    "BOARD_SIDE": "掲示板を、入口の正面から横に何cm ずらすか（＋は入口に向かって左）",
    "BOARD_TURN": "掲示板を、道の方へ何度まわして向けるか",
    "PAPER_WIND_MATERIAL": "実験中。true で紙の材質の頂点をゆらす（壊れることがある）。ふだんは false（紙のゆれは kd_game.py が付ける）",
    "PAPER_WIND_AMP": "掲示板の紙が風でゆれる大きさ（cm）。0 でゆれない",
    "PAPER_WIND_SPEED": "紙がゆれる速さ（1秒に何回）",
    "REPLACE_GLASS_MATERIAL": "null=さわらない（初期値）。true で、買ったガラスの材質を M_KDGlass に替える。false で買ったまま",
}


def _kd_settings_path():
    try:
        d = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
    except Exception:  # noqa
        d = unreal.Paths.project_saved_dir()
    return os.path.join(d, "kd_settings.json")


def _kd_tojson(v):
    if isinstance(v, (list, tuple)):
        return [_kd_tojson(x) for x in v]
    return v


def _kd_coerce(default, v):
    if isinstance(default, bool):
        return bool(v)
    if isinstance(default, int):
        return int(v)
    if isinstance(default, float):
        return float(v)
    if isinstance(default, (list, tuple)):
        if len(default) == 0:                       # 空の初期値（例：START_POS）。入れた数字を、そのまま使う
            return type(default)(tuple(x) if isinstance(x, (list, tuple)) else x for x in v)
        return type(default)(_kd_coerce(default[i] if i < len(default) else default[-1], x) if not isinstance(x, (list, tuple)) else tuple(x) for i, x in enumerate(v))
    return v


def apply_settings(names, logf):
    """設定ファイルの数字を、このスクリプトの設定に反映する。ファイルに無い項目は、いまの値を書き足す"""
    path = _kd_settings_path()
    data = {}
    ok = True
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # noqa
            ok = False
            logf("  (設定ファイルを読めません。いまの値を使います) %s : %s" % (path, e))
    vals = data.setdefault("設定", {})
    added = False
    applied = []
    g = globals()
    for n in names:
        if n not in g:
            continue
        if n in vals:
            try:
                new = _kd_coerce(g[n], vals[n])
                if new != g[n]:
                    applied.append(n)
                g[n] = new
            except Exception as e:  # noqa
                logf("  (設定 %s の値が変です。いまの値を使います) %s" % (n, e))
        else:
            vals[n] = _kd_tojson(g[n])
            added = True
    descr = data.setdefault("説明", {})
    for n in names:
        if n in SETTINGS_DESCR and descr.get(n) != SETTINGS_DESCR[n]:
            descr[n] = SETTINGS_DESCR[n]
            added = True
    if ok and added:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa
            logf("  (設定ファイルを書けません) %s" % e)
    logf("設定ファイル: %s（ファイルの値を使ったもの: %s）" % (path, ", ".join(applied) if applied else "なし"))


SETUP_SETTING_NAMES = ["FRONT", "START_DIST", "START_HEIGHT", "COIN_DIST", "COIN_SIDE", "FLASH_INTENSITY", "FLASH_INNER", "FLASH_OUTER", "FLASH_RADIUS", "POSTER_GLOW", "GLASS_GLOW", "WALL_INSET", "GLASS_GAP", "RESET_POSTERS", "GHOST_MODEL", "GHOST_HEIGHT", "POSTER_SCALE", "GLASS_SCALE", "CODE_SCALE", "CODE_TREE_SIZE", "CODE_TREE_Z", "CODE_TREE_MIN", "CODE_TREE_MAX", "CODE_TREE_ANGLE", "CODE_TREE_PICK", "CODE_TREE_ORDER", "CODE_TREE_TRUNK_R", "CODE_TREE_GLOW", "GLASS_SPREAD", "GLASS_COUNT", "GLASS_SIZE_MIN", "GLASS_SIZE_MAX", "GLASS_TILT", "TUBE_Z_FROM_TOP", "NIGHT_MODE", "SUN_INTENSITY", "MOON_INTENSITY", "SKY_INTENSITY", "REPLACE_GLASS_MATERIAL", "SAFE_BACK", "SAFE_SIDE", "SAFE_SCALE", "SAFE_TURN", "DIAL_CAM_DIST", "DIAL_CAM_FOV", "KEEP_HAND_PLACEMENT", "BOARD_SCALE", "BOARD_DIST", "BOARD_SIDE", "BOARD_TURN", "PAPER_WIND_MATERIAL", "PAPER_WIND_AMP", "PAPER_WIND_SPEED"]

LOG_LINES = []
RESULTS = {}


def log(msg):
    line = "[KD] " + str(msg)
    LOG_LINES.append(line)
    unreal.log(line)


def log_err(msg):
    line = "[KD][FAIL] " + str(msg)
    LOG_LINES.append(line)
    unreal.log_error(line)


def write_log_file():
    try:
        import os
        p = os.path.join(unreal.Paths.project_saved_dir(), "Logs", "KD_game.txt")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(LOG_LINES))
        unreal.log("[KD] ログファイル: " + p)
    except Exception as e:  # noqa
        unreal.log_warning("[KD] ログファイルを書けませんでした: %s" % e)


def step(name, fn, depends=()):
    for d in depends:
        if RESULTS.get(d) != "OK":
            RESULTS[name] = "SKIP"
            log("[SKIP] %s（%s が成功していないため）" % (name, d))
            return False
    try:
        fn()
        RESULTS[name] = "OK"
        log("[OK] " + name)
        return True
    except Exception:
        RESULTS[name] = "FAIL"
        log_err("%s\n%s" % (name, traceback.format_exc()))
        return False


def setp(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception as e:  # noqa
        log("  (設定できず) %s = %r : %s" % (prop, value, str(e).splitlines()[0] if str(e) else e))
        return False


def eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def label_of(a):
    try:
        return a.get_actor_label()
    except Exception:  # noqa
        return ""


def find_actor(label_part):
    for a in eas().get_all_level_actors():
        if label_part in label_of(a):
            return a
    return None


def spawn(cls, loc, rot=(0, 0, 0)):
    return eas().spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))


KEEP_POSE = {}                       # ひかるが手で動かした、掲示板・張り紙の位置と向き（作り直しても、そのまま使う）
KEEP_PREFIX = ("Board_", "Paper_News", "Poster_", "Coin_", "DialSafe_")


def tag_actor(a, label):
    try:
        a.set_editor_property("tags", [unreal.Name(TAG)])
    except Exception as e:  # noqa
        log("  (タグ設定不可) %s" % e)
    a.set_actor_label(label)
    if KEEP_HAND_PLACEMENT and label in KEEP_POSE:
        try:
            loc, rot = KEEP_POSE[label]
            a.set_actor_location_and_rotation(loc, rot, False, False)
        except Exception as e:  # noqa
            log("  (手で動かした位置を戻せません) %s: %s" % (label, e))


KEEP_TUBE = {}


def s_clear():
    n = 0
    for a in eas().get_all_level_actors():
        try:
            lab = a.get_actor_label()
            if lab.startswith(KEEP_PREFIX) and not (RESET_POSTERS and lab.startswith("Poster_")) and lab not in ("Board_Egetsunai", "Paper_News", "Board_Camera", "DialSafe_Knob", "DialSafe_Base", "DialSafe_Lid", "DialSafe_Key", "DialSafe_Coin", "DialSafe_Box") and not lab.startswith("Board_Pin_") \
                    and TAG in [str(t) for t in a.get_editor_property("tags")]:          # 紙と画びょうは、掲示板からの相対位置で作り直す（掲示板について行く）
                KEEP_POSE[lab] = (a.get_actor_location(), a.get_actor_rotation())
        except Exception:  # noqa
            pass
        try:
            if a.get_actor_label() in ("TubeLight_L", "TubeLight_R"):
                KEEP_TUBE[a.get_actor_label()] = a.get_component_by_class(unreal.RectLightComponent).get_editor_property("intensity")
            elif a.get_actor_label() == "Coin_Light":
                KEEP_TUBE["Coin_Light"] = a.get_component_by_class(unreal.PointLightComponent).get_editor_property("intensity")
        except Exception:  # noqa
            pass
        try:
            if TAG in [str(t) for t in a.get_editor_property("tags")]:
                eas().destroy_actor(a)
                n += 1
        except Exception:  # noqa
            pass
    log("前回の生成物を削除: %d" % n)


def s_flashlight():
    c0 = STATE["geo"]["center"]
    sp = spawn(unreal.SpotLight, (c0[0], c0[1], c0[2]), (0, 0, 0))
    tag_actor(sp, "Flashlight")
    c = sp.get_component_by_class(unreal.SpotLightComponent)
    setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
    units = getattr(unreal.LightUnits, "CANDELAS", None) or getattr(unreal.LightUnits, "CANDELA", None)
    if units is not None:
        setp(c, "intensity_units", units)
    else:
        log("  (光の単位 カンデラ が見つかりません。既定の単位のまま)")
    setp(c, "intensity", FLASH_INTENSITY)
    setp(c, "inner_cone_angle", FLASH_INNER)
    setp(c, "outer_cone_angle", FLASH_OUTER)
    setp(c, "attenuation_radius", FLASH_RADIUS)
    setp(c, "source_radius", 2.0)
    setp(c, "use_temperature", True)
    setp(c, "temperature", 4800.0)
    setp(c, "visible", False)
    try:
        c.set_visibility(False, False)
    except Exception:  # noqa
        pass


# ---------------- 段階2：張り紙・幽霊（仮） ----------------
def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", ".."))


def tex_game_dir():
    return os.path.join(repo_root(), "games", "koushu-denwa", "assets", "tex", "game")


def import_tasks(tasks):
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)


def mk_task(filename, dest, scale=None, fbx_ui=None):
    t = unreal.AssetImportTask()
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("replace_existing_settings", True)
    t.set_editor_property("save", True)
    t.set_editor_property("filename", filename)
    t.set_editor_property("destination_path", dest)
    if fbx_ui is not None:
        t.set_editor_property("options", fbx_ui)
    return t


def s_poster_textures():
    d = tex_game_dir()
    names = sorted(f for f in os.listdir(d) if (f.startswith("poster_") or f.startswith("glass_")) and f.lower().endswith((".png", ".jpg")))
    if not names:
        raise RuntimeError("張り紙の画像がありません: %s" % d)
    import_tasks([mk_task(os.path.join(d, f), GAME_DIR + "/Textures/Game") for f in names])
    STATE["poster_files"] = names
    log("張り紙の画像を取り込みました: %d 枚" % len(names))


def import_poster(fbx, scale):
    ui = unreal.FbxImportUI()
    setp(ui, "import_mesh", True)
    setp(ui, "import_as_skeletal", False)
    setp(ui, "import_materials", False)
    setp(ui, "import_textures", False)
    setp(ui, "automated_import_should_detect_type", False)
    setp(ui, "mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property("static_mesh_import_data")
    setp(d, "combine_meshes", True)
    setp(d, "auto_generate_collision", False)
    setp(d, "transform_vertex_to_absolute", True)
    setp(d, "import_uniform_scale", float(scale))
    import_tasks([mk_task(fbx, GAME_DIR + "/Game", fbx_ui=ui)])
    mesh = None
    for p in unreal.EditorAssetLibrary.list_assets(GAME_DIR + "/Game", recursive=True, include_folder=False):
        a = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(a, unreal.StaticMesh) and "oster" in a.get_name():
            mesh = a
    if mesh is None:
        raise RuntimeError("Poster のメッシュが見つかりません")
    e = mesh.get_bounds().box_extent
    return mesh, e


def s_poster_mesh():
    fbx = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", "Poster.fbx")
    if not os.path.exists(fbx):
        raise RuntimeError("Poster.fbx がありません: %s" % fbx)
    scale = 100.0                                    # 電話ボックスと同じ：メートル → cm
    mesh, e = import_poster(fbx, scale)
    big = max(e.x, e.y, e.z) * 2.0
    log("ポスター板の大きさ（取り込み直後）: 長い辺=%.1fcm（70 が正常）" % big)
    if abs(big - 70.0) > 6.0 and big > 0.0:            # 大きさがずれていたら、70cm になるように取り込み直す
        scale = scale * 70.0 / big
        mesh, e = import_poster(fbx, scale)
        big = max(e.x, e.y, e.z) * 2.0
        log("ポスター板を、倍率 %.2f で取り込み直しました: 長い辺=%.1fcm" % (scale, big))
    log("ポスター板の大きさ: %.1f × %.1f × %.1f cm（50×1以下×70 前後が正常）" % (e.x * 2, e.y * 2, e.z * 2))
    STATE["poster_mesh"] = mesh


def new_material(name):
    path = GAME_DIR + "/Materials"
    full = "%s/%s" % (path, name)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        unreal.EditorAssetLibrary.delete_asset(full)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, path, unreal.Material, unreal.MaterialFactoryNew())
    if m is None:
        raise RuntimeError("材質を作れません: " + name)
    return m


def xx(m, cls, x, y):
    return mel.create_material_expression(m, cls, x, y)


def cst(m, v, y=0):
    e = xx(m, unreal.MaterialExpressionConstant, -600, y)
    e.set_editor_property("r", float(v))
    return e


def mulx(m, a, b, y=0):
    e = xx(m, unreal.MaterialExpressionMultiply, -400, y)
    mel.connect_material_expressions(a, "", e, "A")
    mel.connect_material_expressions(b, "", e, "B")
    return e


def glass_glow_material(m, t, glow, fog=True):
    """ガラスの文字の材質：両面・透明な背景・文字だけが光る（明るさ glow）。fog=False は、霧にうすめられないようにする（遠くの光る数字用）"""
    setp(m, "two_sided", True)
    setp(m, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    setp(m, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    if not fog:
        setp(m, "apply_fogging", False)
    mel.connect_material_property(mulx(m, t, cst(m, glow, 100), 0), "", MP.MP_EMISSIVE_COLOR)
    mel.connect_material_property(t, "A", MP.MP_OPACITY)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)


def s_poster_materials():
    mats = {}
    for f in STATE["poster_files"]:
        base = os.path.splitext(f)[0]                      # poster_01
        tex = unreal.EditorAssetLibrary.load_asset("%s/Textures/Game/%s" % (GAME_DIR, base))
        m = new_material("M_" + "".join(w.capitalize() for w in base.split("_")))      # M_Poster01 / M_Glass01
        setp(m, "two_sided", True)
        t = xx(m, unreal.MaterialExpressionTextureSample, -800, 0)
        t.set_editor_property("texture", tex)
        if base.startswith("glass_"):                       # ガラスの文字：紙なし。背景は透明、文字だけがうっすら光る
            glass_glow_material(m, t, GLASS_GLOW)
            mats[base] = m
            if base.startswith("glass_glow_"):               # 外の木に光る数字用：もっと強く光る別の材質（M_CodeGlowTree0〜9）
                dg = base.split("_")[-1]
                mt = new_material("M_CodeGlowTree%s" % dg)
                tt = xx(mt, unreal.MaterialExpressionTextureSample, -800, 0)
                tt.set_editor_property("texture", tex)
                glass_glow_material(mt, tt, GLASS_GLOW * CODE_TREE_GLOW, fog=False)
                mats["tree_glow_%s" % dg] = mt
            continue
        mel.connect_material_property(mulx(m, t, cst(m, 0.8, -100), 0), "", MP.MP_BASE_COLOR)
        mel.connect_material_property(mulx(m, t, cst(m, POSTER_GLOW, 100), 150), "", MP.MP_EMISSIVE_COLOR)
        mel.connect_material_property(cst(m, 0.9, 300), "", MP.MP_ROUGHNESS)
        mel.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        mats[base] = m
    STATE["poster_mats"] = mats
    log("張り紙の材質を作りました: %d" % len(mats))


def ghost_textures():
    d = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", "ghost")
    dest = GAME_DIR + "/Textures/Ghost"
    tasks = [mk_task(os.path.join(d, "Ghost_%s.png" % k), dest) for k in ("albedo", "normal", "roughness", "metallic") if os.path.exists(os.path.join(d, "Ghost_%s.png" % k))]
    import_tasks(tasks)
    tx = {}
    for k in ("albedo", "normal", "roughness", "metallic"):
        a = unreal.EditorAssetLibrary.load_asset("%s/Ghost_%s" % (dest, k))
        if a is None:
            continue
        if k == "normal":
            setp(a, "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            setp(a, "srgb", False)
            setp(a, "flip_green_channel", True)                      # Blender（OpenGL）→ Unreal（DirectX）の向きの違いを直す
        elif k in ("roughness", "metallic"):
            setp(a, "srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        tx[k] = a
    return tx


def ghost_materials(tx):
    """幽霊の材質5つ（Blenderの穴の順：肌・口の中・歯・舌・歯ぐき）"""
    skin = new_material("M_GhostSkin")
    setp(skin, "two_sided", True)                                    # 髪の面が、うらから見ても消えないように
    t = xx(skin, unreal.MaterialExpressionTextureSample, -900, 0)
    setp(t, "texture", tx["albedo"])
    mel.connect_material_property(t, "", MP.MP_BASE_COLOR)
    if "normal" in tx:
        tn = xx(skin, unreal.MaterialExpressionTextureSample, -900, 300)
        setp(tn, "texture", tx["normal"])
        setp(tn, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        mel.connect_material_property(tn, "", MP.MP_NORMAL)
    if "roughness" in tx:
        tr = xx(skin, unreal.MaterialExpressionTextureSample, -900, 600)
        setp(tr, "texture", tx["roughness"])
        setp(tr, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        mel.connect_material_property(tr, "R", MP.MP_ROUGHNESS)
    mel.connect_material_property(cst(skin, 0.0, 900), "", MP.MP_METALLIC)
    mel.recompile_material(skin)
    unreal.EditorAssetLibrary.save_loaded_asset(skin)

    def vcol_material(name, rough, glow):
        m = new_material(name)
        vc = xx(m, unreal.MaterialExpressionVertexColor, -800, 0)             # Blender で付けた頂点カラー「Col」（口の中の赤みと、歯の黄ばみ）
        mel.connect_material_property(vc, "RGB", MP.MP_BASE_COLOR)
        if glow > 0:
            mel.connect_material_property(mulx(m, vc, cst(m, glow, 100), 150), "", MP.MP_EMISSIVE_COLOR)      # 暗い中でも、口の中がうっすら見える
        mel.connect_material_property(cst(m, rough, 300), "", MP.MP_ROUGHNESS)
        mel.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        return m

    def const_material(name, col, rough):
        m = new_material(name)
        c = xx(m, unreal.MaterialExpressionConstant3Vector, -600, 0)
        setp(c, "constant", unreal.LinearColor(col[0], col[1], col[2], 1.0))
        mel.connect_material_property(c, "", MP.MP_BASE_COLOR)
        mel.connect_material_property(cst(m, rough, 240), "", MP.MP_ROUGHNESS)
        mel.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        return m
    return [skin, vcol_material("M_GhostMouth", 0.45, 0.06), vcol_material("M_GhostTeeth", 0.15, 0.0),
            const_material("M_GhostTongue", (0.66, 0.27, 0.29), 0.4), const_material("M_GhostGum", (0.62, 0.22, 0.25), 0.35)]


def import_ghost_fbx(fbx, dest, scale):
    ui = unreal.FbxImportUI()
    setp(ui, "import_mesh", True)
    setp(ui, "import_as_skeletal", True)
    setp(ui, "import_animations", True)
    setp(ui, "import_materials", False)
    setp(ui, "import_textures", False)
    setp(ui, "automated_import_should_detect_type", False)
    setp(ui, "mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    d = ui.get_editor_property("skeletal_mesh_import_data")
    setp(d, "import_morph_targets", True)                                        # 表情（口を開ける・にっこり・歯を見せて笑う）
    setp(d, "import_uniform_scale", float(scale))
    try:
        setp(d, "vertex_color_import_option", unreal.VertexColorImportOption.REPLACE)       # 口の中・歯の色（頂点カラー）を使う
    except Exception as e:  # noqa
        log("  (頂点カラーの取り込み設定できず) %s" % e)
    import_tasks([mk_task(fbx, dest, fbx_ui=ui)])
    sk = None
    anims = []
    for p_ in unreal.EditorAssetLibrary.list_assets(dest, recursive=True, include_folder=False):
        a = unreal.EditorAssetLibrary.load_asset(p_)
        if isinstance(a, unreal.SkeletalMesh):
            sk = a
        elif isinstance(a, unreal.AnimSequence):
            anims.append(a)
    return sk, anims


def s_ghost_model():
    """本物の幽霊（Ghost_rigged.fbx）：骨つき・表情つきのモデルを取り込んで、Ghost として置く"""
    fbx = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", "ghost", "Ghost_rigged.fbx")
    if not os.path.exists(fbx):
        raise RuntimeError("Ghost_rigged.fbx がありません: %s" % fbx)
    dest = GAME_DIR + "/Ghost"
    tx = ghost_textures()
    if "albedo" not in tx:
        raise RuntimeError("幽霊の肌の絵（Ghost_albedo.png）がありません")
    sk, anims = import_ghost_fbx(fbx, dest, 100.0)
    if sk is None:
        raise RuntimeError("幽霊のスケルタルメッシュを取り込めませんでした")
    h = sk.get_bounds().box_extent.z * 2.0
    log("幽霊の高さ（取り込み直後）: %.0fcm（%.0f が正常）" % (h, GHOST_HEIGHT))
    if h > 1.0 and abs(h - GHOST_HEIGHT) > GHOST_HEIGHT * 0.08:
        sk, anims = import_ghost_fbx(fbx, dest, 100.0 * GHOST_HEIGHT / h)
        log("幽霊を、倍率 %.2f で取り込み直しました: 高さ %.0fcm" % (100.0 * GHOST_HEIGHT / h, sk.get_bounds().box_extent.z * 2.0))
    mats = ghost_materials(tx)
    a = spawn(unreal.SkeletalMeshActor, (0, 3000, 0))
    comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
    try:
        comp.set_skeletal_mesh_asset(sk)
    except Exception:  # noqa
        comp.set_editor_property("skeletal_mesh_asset", sk)
    for i, m in enumerate(mats):
        comp.set_material(i, m)
    nat = next((x for x in anims if "Natural" in x.get_name() and "Face" not in x.get_name()), None) or (anims[0] if anims else None)
    if nat is not None:
        try:
            comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
            comp.set_animation(nat)
            comp.play(True)
        except Exception as e:  # noqa
            log("  (幽霊のアニメを設定できません) %s" % e)
    try:
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:  # noqa
        pass
    a.set_actor_scale3d(unreal.Vector(GHOST_SCALE, GHOST_SCALE, GHOST_SCALE))
    tag_actor(a, "Ghost")
    a.set_actor_hidden_in_game(True)
    log("本物の幽霊を置きました（骨 %s・アニメ %d本・材質 %d）。最初は見えません" % ("あり", len(anims), len(mats)))


def s_ghost():
    """幽霊（仮の姿）：黒い体＋白い頭。本物のモデルが取り込めたら、そちらを置く（GHOST_MODEL）"""
    if GHOST_MODEL:
        try:
            s_ghost_model()
            return
        except Exception as e:  # noqa
            log("本物の幽霊を置けなかったので、仮の姿にします: %s" % e)
    cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
    sph = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
    body_m = new_material("M_GhostBody")
    setp(body_m, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mel.connect_material_property(mulx(body_m, cst(body_m, 1.0, 0), cst(body_m, 0.02, 100), 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(body_m)
    head_m = new_material("M_GhostHead")
    setp(head_m, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    col = xx(head_m, unreal.MaterialExpressionConstant3Vector, -600, 0)
    col.set_editor_property("constant", unreal.LinearColor(0.75, 0.82, 0.9, 1.0))
    mel.connect_material_property(mulx(head_m, col, cst(head_m, 2.5, 100), 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(head_m)
    for m in (body_m, head_m):
        unreal.EditorAssetLibrary.save_loaded_asset(m)
    body = spawn(unreal.StaticMeshActor, (0, 3000, 0))
    bc = body.get_component_by_class(unreal.StaticMeshComponent)
    bc.set_static_mesh(cyl)
    bc.set_material(0, body_m)
    setp(bc, "mobility", unreal.ComponentMobility.MOVABLE)
    body.set_actor_scale3d(unreal.Vector(0.5, 0.5, 1.6))     # 太さ50cm・高さ160cm
    tag_actor(body, "Ghost")
    head = spawn(unreal.StaticMeshActor, (0, 3000, 175))
    hc = head.get_component_by_class(unreal.StaticMeshComponent)
    hc.set_static_mesh(sph)
    hc.set_material(0, head_m)
    setp(hc, "mobility", unreal.ComponentMobility.MOVABLE)
    head.set_actor_scale3d(unreal.Vector(0.26, 0.2, 0.3))
    tag_actor(head, "Ghost_Head")
    head.attach_to_actor(body, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    for a in (body, head):
        a.set_actor_hidden_in_game(True)
        try:
            a.get_component_by_class(unreal.StaticMeshComponent).set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        except Exception:  # noqa
            pass
    log("幽霊（仮）を置きました。最初は見えません")


def s_night():
    """夕方 → 夜：太陽を消して、青白い月を足す。空の光も弱める"""
    sun = find_actor("DirectionalLight")
    if sun is not None and "KD" not in label_of(sun):
        c = sun.get_component_by_class(unreal.DirectionalLightComponent)
        setp(c, "intensity", SUN_INTENSITY)
        log("太陽の明るさ = %s" % SUN_INTENSITY)
    moon = spawn(unreal.DirectionalLight, (0, 0, 800), (0, -35.0, 40.0))
    tag_actor(moon, "KD_Moon")
    mc = moon.get_component_by_class(unreal.DirectionalLightComponent)
    setp(mc, "intensity", MOON_INTENSITY)
    setp(mc, "use_temperature", True)
    setp(mc, "temperature", 9000.0)
    setp(mc, "mobility", unreal.ComponentMobility.MOVABLE)
    sky = find_actor("SkyLight")
    if sky is not None:
        setp(sky.get_component_by_class(unreal.SkyLightComponent), "intensity", SKY_INTENSITY)
        try:
            sky.get_component_by_class(unreal.SkyLightComponent).recapture_sky()
        except Exception:  # noqa
            pass
    log("夜にしました（月=%s 空=%s）" % (MOON_INTENSITY, SKY_INTENSITY))


def s_save():
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception as e:  # noqa
        log("  (レベル保存不可) %s" % e)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)



# ---------------- 電話ボックスを調べる ----------------
DIRS = {"+X": (1.0, 0.0), "-X": (-1.0, 0.0), "+Y": (0.0, 1.0), "-Y": (0.0, -1.0)}


def rot90(v, k):
    """(x,y) を、上から見て k×90度（UEのYaw+方向）まわす"""
    x, y = v
    for _ in range(k % 4):
        x, y = -y, x
    return (x, y)


def find_booth():
    for a in eas().get_all_level_actors():
        lab = label_of(a).lower()
        if BOOTH_KEY in lab and "glass" not in lab and "KD" not in label_of(a):
            return a
    return None


def s_env():
    log("エンジン: %s" % unreal.SystemLibrary.get_engine_version())
    try:
        wname = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name()
    except Exception:  # noqa
        wname = ""
    log("いま開いているレベル: %s" % wname)
    if wname in PROTECT_LEVELS:
        raise RuntimeError("このレベル（%s）はスタート画面用なので、何も変えません。「ファイル → 現在のレベルを別名で保存」で本編用（例 L_Main）にコピーして、そのレベルで実行してください" % wname)
    b = find_booth()
    if b is None:
        raise RuntimeError("名前に %s を含む電話ボックスが見つかりません（BOOTH_KEY を直してください）" % BOOTH_KEY)
    if FRONT not in DIRS:
        raise RuntimeError("FRONT は +X / -X / +Y / -Y のどれかにしてください")
    o, e = b.get_actor_bounds(False)
    n = DIRS[FRONT]
    t = rot90(n, -1)                          # 入口の面にそった向き（+90度まわすと n になる）
    STATE["booth"] = b
    STATE["geo"] = {"center": (o.x, o.y, o.z), "ext": (e.x, e.y, e.z), "n": n, "t": t,
                    "zmin": o.z - e.z, "zmax": o.z + e.z}
    log("電話ボックス: %s 中心=(%.0f,%.0f,%.0f) 半径=(%.0f,%.0f,%.0f) 入口の向き=%s" % (label_of(b), o.x, o.y, o.z, e.x, e.y, e.z, FRONT))


def front_half():
    """入口の向き(n)方向の、ボックスの半分の長さ。pf と側面方向(t)の半分の長さ"""
    g = STATE["geo"]
    ex, ey, ez = g["ext"]
    n, t = g["n"], g["t"]
    half_n = abs(n[0]) * ex + abs(n[1]) * ey
    half_t = abs(t[0]) * ex + abs(t[1]) * ey
    return half_n, half_t


def world(d, s, z):
    """ボックス中心から、入口方向に d、側面方向に s、高さ z の世界座標"""
    g = STATE["geo"]
    cx, cy, _ = g["center"]
    n, t = g["n"], g["t"]
    return (cx + n[0] * d + t[0] * s, cy + n[1] * d + t[1] * s, z)


def s_center_marker():
    g = STATE["geo"]
    n = g["n"]
    yaw0 = math.degrees(math.atan2(n[1], n[0])) - 90.0     # kd_game.py が「入口の向き」を知るための印（+Y 向きを yaw0 だけ回した向き）
    half_n, half_t = front_half()
    a = spawn(unreal.StaticMeshActor, g["center"], (0, 0, yaw0))
    a.set_actor_scale3d(unreal.Vector(half_t, half_n, 1.0))          # 印の「大きさ」に、横の半分(x)と奥行きの半分(y)をcmで入れておく（kd_game.py が読む）
    tag_actor(a, "KD_BoothCenter")
    setp(a.get_component_by_class(unreal.StaticMeshComponent), "mobility", unreal.ComponentMobility.MOVABLE)
    a.set_actor_hidden_in_game(True)
    # 中の「歩ける広さ」の印：ガラスの内がわの半分の幅・奥行き(cm)を、大きさに入れておく（kd_game.py が読む。壁ぎわの歩きがガタガタしないように）
    gh = glass_halves()
    in_n, in_t = (gh[0] - 1.5, gh[1] - 1.5) if gh else (half_n - WALL_INSET, half_t - WALL_INSET)
    b = spawn(unreal.StaticMeshActor, g["center"], (0, 0, yaw0))
    b.set_actor_scale3d(unreal.Vector(in_t, in_n, 1.0))
    tag_actor(b, "KD_BoothInner")
    setp(b.get_component_by_class(unreal.StaticMeshComponent), "mobility", unreal.ComponentMobility.MOVABLE)
    b.set_actor_hidden_in_game(True)
    log("中の歩ける広さ（ガラスの内がわ）: 横 ±%.1fcm・奥行き ±%.1fcm" % (in_t, in_n))


def s_collision():
    """電話ボックスの形そのものを当たり判定にする（中に入れるように）"""
    b = STATE["booth"]
    n = 0
    for c in b.get_components_by_class(unreal.StaticMeshComponent):
        mesh = c.get_editor_property("static_mesh")
        if mesh is None:
            continue
        try:
            bs = mesh.get_editor_property("body_setup")
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            mesh.set_editor_property("body_setup", bs)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            n += 1
            log("  %s: 当たり判定 OK" % mesh.get_name())
        except Exception as ex:  # noqa
            log("  %s: 当たり判定を設定できず : %s" % (mesh.get_name(), str(ex).splitlines()[0]))
        try:
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception as ex:  # noqa
            log("  %s: collision_enabled を設定できず : %s" % (mesh.get_name(), str(ex).splitlines()[0]))
        try:
            c.set_visibility(True, False)            # 前の版でガラスを「非表示」にしていたら、表示に戻す
        except Exception as ex:  # noqa
            log("  %s: 表示を戻せず : %s" % (mesh.get_name(), str(ex).splitlines()[0]))
    log("当たり判定をつけた数: %d（ガラスも表示に戻しました）" % n)


def s_player_start():
    """PlayerStart を、入口の正面に置く。レベルに PlayerStart が何個あっても、ぜんぶ入口の正面に並べる（遠い所の1個から始まってしまうのを防ぐ）"""
    starts = [a for a in eas().get_all_level_actors() if isinstance(a, unreal.PlayerStart)]
    g = STATE["geo"]
    half_n, _ = front_half()
    x, y, _z = world(half_n + START_DIST, 0, 0)
    z = g["zmin"] + START_HEIGHT
    n = g["n"]
    yaw = math.degrees(math.atan2(-n[1], -n[0]))           # ボックスの方を向く
    if not starts:
        ps = spawn(unreal.PlayerStart, (x, y, z), (0, 0, yaw))
        tag_actor(ps, "KD_PlayerStart")
        log("PlayerStart を新しく置きました: (%.0f, %.0f, %.0f)" % (x, y, z))
        return
    t = g["t"]
    for i, ps in enumerate(starts):
        off = i * 150.0                                    # 2個目からは、横に 1.5m ずつずらす（重なって出られなくならないように）
        ps.set_actor_location_and_rotation(unreal.Vector(x + t[0] * off, y + t[1] * off, z), unreal.Rotator(0, 0, yaw), False, False)
    log("PlayerStart %d 個を、入口の正面へ動かしました: (%.0f, %.0f, %.0f) 向き=%.0f" % (len(starts), x, y, z, yaw))


def s_sounds():
    d = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "sounds")
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(".wav"))
    if not files:
        raise RuntimeError("効果音がありません: %s" % d)
    import_tasks([mk_task(os.path.join(d, f), GAME_DIR + "/Sounds") for f in files])
    log("効果音を取り込みました: %s" % ", ".join(files))


GLASS_OPACITY_SCALE = 0.3             # ガラスのくもりの強さ（小さいほど外がよく見える）。kd_game.py の GLASS_DIRT でも変えられる
REPLACE_GLASS_MATERIAL = None          # True: 買ったガラスの材質を、くもりを弱めた材質（M_KDGlass）に替える。False: 買ったままの材質（前の版で替えていたら、元に戻す）


def s_glass_material():
    """買ったガラスはくもりが強くて外が見えないので、くもり（汚れ）を弱められるガラスの材質に替える"""
    if REPLACE_GLASS_MATERIAL is None:
        log("ガラスの材質: さわりません（ひかるが直したものを残す）")
        return
    if not REPLACE_GLASS_MATERIAL:
        n = 0
        for c in STATE["booth"].get_components_by_class(unreal.StaticMeshComponent):
            mesh = c.get_editor_property("static_mesh")
            if mesh is not None and "glass" in mesh.get_name().lower():
                try:
                    c.set_material(0, mesh.get_material(0))          # 部品につけていた別の材質を外して、買ったときの材質（アセットの初期の材質）に戻す
                    n += 1
                except Exception as ex:  # noqa
                    log("  (ガラスの材質を戻せません) %s" % ex)
        log("ガラスの材質を、買ったときのものに戻しました: %d 部品" % n)
        return
    d = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "tex")
    names = [f for f in ("glass_color.png", "glass_rough.png") if os.path.exists(os.path.join(d, f))]
    if not names:
        raise RuntimeError("ガラスの画像がありません: %s" % d)
    import_tasks([mk_task(os.path.join(d, f), GAME_DIR + "/Textures/KDGlass") for f in names])
    col = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/KDGlass/glass_color")
    rgh = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/KDGlass/glass_rough")
    m = new_material("M_KDGlass")
    setp(m, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    setp(m, "translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    setp(m, "two_sided", True)
    gc = xx(m, unreal.MaterialExpressionTextureSample, -800, -200)
    gc.set_editor_property("texture", col)
    mel.connect_material_property(mulx(m, gc, cst(m, 0.45, -250), -200), "", MP.MP_BASE_COLOR)
    dirt = xx(m, unreal.MaterialExpressionScalarParameter, -600, 300)
    setp(dirt, "parameter_name", "Dirt")
    setp(dirt, "default_value", GLASS_OPACITY_SCALE)
    op = xx(m, unreal.MaterialExpressionMultiply, -400, 150)
    mel.connect_material_expressions(gc, "A", op, "A")
    mel.connect_material_expressions(dirt, "", op, "B")
    mel.connect_material_property(op, "", MP.MP_OPACITY)
    if rgh is not None:
        rt = xx(m, unreal.MaterialExpressionTextureSample, -800, 0)
        rt.set_editor_property("texture", rgh)
        mel.connect_material_property(rt, "R", MP.MP_ROUGHNESS)
    else:
        mel.connect_material_property(cst(m, 0.1, 0), "", MP.MP_ROUGHNESS)
    mel.connect_material_property(cst(m, 0.6, 100), "", MP.MP_SPECULAR)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    n = 0
    for c in STATE["booth"].get_components_by_class(unreal.StaticMeshComponent):
        mesh = c.get_editor_property("static_mesh")
        if mesh is not None and "glass" in mesh.get_name().lower():
            c.set_material(0, m)
            n += 1
    log("ガラスの材質を M_KDGlass に替えました: %d 部品（くもり=%.2f）" % (n, GLASS_OPACITY_SCALE))


def s_lights():
    """天井に蛍光灯：RectLight 2本（TubeLight_L/R）＋ 光る見た目の棒（KD_Tube_L/R。材質 M_KDTube の Flicker で明るさを変える）"""
    g = STATE["geo"]
    half_n, half_t = front_half()
    zmax = g["zmax"]
    z = zmax - TUBE_Z_FROM_TOP
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    tm = new_material("M_KDTube")
    setp(tm, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    fl = xx(tm, unreal.MaterialExpressionScalarParameter, -800, 100)
    setp(fl, "parameter_name", "Flicker")
    setp(fl, "default_value", 1.0)
    col = xx(tm, unreal.MaterialExpressionConstant3Vector, -600, -100)
    col.set_editor_property("constant", unreal.LinearColor(1.0, 0.9, 0.78, 1.0))
    mel.connect_material_property(mulx(tm, mulx(tm, col, cst(tm, 25.0, 0), -100), fl, 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(tm)
    unreal.EditorAssetLibrary.save_loaded_asset(tm)
    n = g["n"]
    yaw_depth = math.degrees(math.atan2(n[1], n[0]))       # 棒は入口〜奥の向きにのばす
    for side, nm in ((-1, "L"), (1, "R")):
        s = side * 27.0
        loc = world(0.0, s, z)
        r = spawn(unreal.RectLight, loc, (0, -90.0, yaw_depth))
        tag_actor(r, "TubeLight_" + nm)
        lc = r.get_component_by_class(unreal.RectLightComponent)
        setp(lc, "mobility", unreal.ComponentMobility.MOVABLE)
        setp(lc, "intensity_units", unreal.LightUnits.LUMENS)
        setp(lc, "intensity", KEEP_TUBE.get("TubeLight_" + nm, 350.0 if nm == "R" else 1500.0))
        setp(lc, "use_temperature", True)
        setp(lc, "temperature", 5000.0)
        setp(lc, "source_width", 85.0)
        setp(lc, "source_height", 3.0)
        setp(lc, "barn_door_angle", 88.0)
        setp(lc, "attenuation_radius", 600.0)
        tube = spawn(unreal.StaticMeshActor, world(0.0, s, z + 2.0), (0, 0, yaw_depth))
        tc = tube.get_component_by_class(unreal.StaticMeshComponent)
        tc.set_static_mesh(cube)
        tc.set_material(0, tm)
        setp(tc, "mobility", unreal.ComponentMobility.MOVABLE)
        tube.set_actor_scale3d(unreal.Vector(0.85, 0.04, 0.03))
        tag_actor(tube, "KD_Tube_" + nm)
        try:
            tc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        except Exception:  # noqa
            pass
    log("蛍光灯を付けました（高さ %.0f）" % z)


# 壁ごとの貼る位置：(壁, 壁にそった位置, 高さ(床からの高さ), 大きさ)。壁は「入口の向き」から見た相対：
#   B=奥（入口の反対）  R=右  L=左（入口から中を見たとき）  F=入口（ドアの内側）
SLOTS = [("R", -40, 125, 1.0), ("R", 5, 160, 1.0), ("R", 45, 115, 1.0), ("R", -5, 195, 1.0),
         ("L", -45, 150, 1.0), ("L", 42, 160, 1.0), ("L", -5, 195, 1.0),
         ("F", -45, 130, 1.0), ("F", 40, 155, 1.0), ("F", 0, 195, 1.0),
         ("B", -46, 120, 1.0), ("B", 46, 150, 1.0)]
HINT_SLOT = ("B", 0, 185, 1.0)        # 電話機の真上
EYE_SLOT = ("L", 0, 140, 1.5)         # 左の壁の真ん中に、大きく


def glass_halves():
    """ガラスの面の位置：ボックス中心から、入口方向(n)と側面方向(t)へ、それぞれ何cm か（ガラスの外がわの面）。測れなければ None"""
    key = "glass_halves"
    if key in STATE:
        return STATE[key]
    g = STATE["geo"]
    cx, cy, _cz = g["center"]
    n, t = g["n"], g["t"]
    mx_n = mx_t = None
    for c in STATE["booth"].get_components_by_class(unreal.StaticMeshComponent):
        mesh = c.get_editor_property("static_mesh")
        if mesh is None or "glass" not in mesh.get_name().lower():
            continue
        corners = None
        try:                                                                # 部品の「大きさ」と置き場所から、ガラスの8つの角を世界座標で出す（回転・拡大込み）
            mb = mesh.get_bounds()
            xf = c.get_world_transform()
            o, e = mb.origin, mb.box_extent
            corners = [xf.transform_location(unreal.Vector(o.x + sx * e.x, o.y + sy * e.y, o.z + sz * e.z))
                       for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        except Exception as ex:  # noqa
            log("  (ガラスの角を出せません。別の方法で測ります) %s" % ex)
        if corners:
            v_n = max(abs((p.x - cx) * n[0] + (p.y - cy) * n[1]) for p in corners)
            v_t = max(abs((p.x - cx) * t[0] + (p.y - cy) * t[1]) for p in corners)
            mx_n = v_n if mx_n is None else max(mx_n, v_n)
            mx_t = v_t if mx_t is None else max(mx_t, v_t)
            continue
        b = None
        for getter in (lambda: c.get_editor_property("bounds"), lambda: c.bounds):
            try:
                b = getter()
                break
            except Exception:  # noqa
                continue
        if b is None:
            continue
        try:
            o, e = b.origin, b.box_extent
            dn = (o.x - cx) * n[0] + (o.y - cy) * n[1]
            dt = (o.x - cx) * t[0] + (o.y - cy) * t[1]
            hn = abs(n[0]) * e.x + abs(n[1]) * e.y
            ht = abs(t[0]) * e.x + abs(t[1]) * e.y
            v_n, v_t = max(abs(dn - hn), abs(dn + hn)), max(abs(dt - ht), abs(dt + ht))
            mx_n = v_n if mx_n is None else max(mx_n, v_n)
            mx_t = v_t if mx_t is None else max(mx_t, v_t)
        except Exception as ex:  # noqa
            log("  (ガラスの大きさを読めません) %s" % ex)
    STATE[key] = (mx_n, mx_t) if (mx_n and mx_t) else None
    half_n, half_t = front_half()
    if STATE[key]:
        log("ガラスの面の位置: 前後 ±%.1fcm・左右 ±%.1fcm（ボックスぜんたいは 前後 ±%.1f・左右 ±%.1f）→ ガラスの面から内側へ %.1fcm に貼ります" % (mx_n, mx_t, half_n, half_t, GLASS_GAP))
    else:
        log("ガラスの面の位置を測れなかったので、ボックスの外形から %.0fcm 内側（WALL_INSET）に貼ります。浮いて見えるなら、WALL_INSET を小さくしてください" % WALL_INSET)
    return STATE[key]


def wall_half(wall):
    """壁にそった位置 u の、ガラスの内がわの半分の長さ(cm)。B/F は 横(t)方向、R/L は 入口方向(n)"""
    half_n, half_t = front_half()
    gh = glass_halves()
    if gh:
        wn, wt = gh[0] - GLASS_GAP, gh[1] - GLASS_GAP
    else:
        wn, wt = half_n - WALL_INSET, half_t - WALL_INSET
    return wt if wall in ("B", "F") else wn


def wall_pose_rel(wall, u, z, extra=0.0):
    """壁の名前から、世界座標と、張り紙の面が内側を向く yaw を返す。張り紙の板は yaw=0 で +Y 向き。extra: さらに内側へ何cm 寄せるか（重なる板どうしのチラつき防止）"""
    g = STATE["geo"]
    n = g["n"]
    zmin = g["zmin"]
    wn = wall_half("R")                                # 入口方向(n)のガラスの半分
    wt = wall_half("B")                                # 横(t)方向のガラスの半分
    if wall == "B":
        d, s, inward = -wn, u, (n[0], n[1])            # 奥の壁：面は入口側（+n）を向く
    elif wall == "F":
        d, s, inward = wn, -u, (-n[0], -n[1])
    elif wall == "R":
        t = g["t"]
        d, s, inward = u, wt, (-t[0], -t[1])
    else:
        t = g["t"]
        d, s, inward = u, -wt, (t[0], t[1])
    # 面の向き inward を向く yaw（板は yaw=0 で +Y 向き）
    yaw = math.degrees(math.atan2(inward[1], inward[0])) - 90.0
    if wall in ("R", "L"):
        # R/L は「側面方向 t」が s、「入口方向 n」が d にあたる：u は n 方向に動かす
        pos = world(u, s, zmin + z)
    else:
        pos = world(d, s, zmin + z)
    if extra:
        pos = (pos[0] + inward[0] * extra, pos[1] + inward[1] * extra, pos[2])
    return pos, yaw


# 散りばめるとき、よける場所：(壁, 壁の中心から ±何cm 以内, 高さの下, 高さの上)。電話機とヒントの文字（奥）・目の写真（左）を隠さないため
GLASS_KEEPOUT = [("B", 32.0, 80.0, 230.0), ("L", 30.0, 100.0, 185.0)]
GLASS_Z_MIN, GLASS_Z_MAX = 45.0, 245.0      # ガラスの文字の中心の高さ（床から cm）の範囲。下の方から上の方まで
GLASS_WALLS = ["R", "L", "F", "B"]


def glass_slot_plan(count, seed=714):
    """ガラスの文字の場所の一覧 [(壁, u, z, 大きさ, 傾き度)]。4面に同じ数ずつ、格子（1行ごとに半分ずらす）＋ゆらぎ。
    先頭から順に取ると、どの途中までを取っても 4面にまんべんなく散る（面を順ぐりに並べる）。同じ seed なら、いつも同じ"""
    rng = random.Random(seed)
    per = max(1, int(round(count / 4.0)))
    cols = 2 if per <= 6 else 3
    rows = int(math.ceil(per / float(cols)))
    faces = {}
    for wall in GLASS_WALLS:
        half = wall_half(wall)
        cells = [(r, c) for r in range(rows) for c in range(cols)]
        rng.shuffle(cells)                                     # 余る分は、ランダムな区画を外す
        out = []
        for r, c in sorted(cells[:per]):
            shift = (0.25 if r % 2 else -0.25) if cols > 1 else 0.0
            fu = (c + 0.5 + shift) / cols + rng.uniform(-0.12, 0.12) / cols
            fu = min(0.97, max(0.03, fu))
            u = (fu * 2 - 1) * half * 0.92
            fz = (r + 0.5 + rng.uniform(-0.3, 0.3)) / rows
            z = GLASS_Z_MIN + (GLASS_Z_MAX - GLASS_Z_MIN) * min(1.0, max(0.0, fz))
            for kw, ku, zlo, zhi in GLASS_KEEPOUT:
                if kw == wall and abs(u) < ku and zlo <= z <= zhi:
                    u = (1.0 if u >= 0 else -1.0) * max(abs(u), half * 0.72)
            out.append((wall, u, z, rng.uniform(GLASS_SIZE_MIN, GLASS_SIZE_MAX), rng.uniform(-GLASS_TILT, GLASS_TILT)))
        rng.shuffle(out)
        faces[wall] = out
    plan = []
    for i in range(per):                                       # 面を順ぐりに：R, L, F, B, R, L, F, B...
        for wall in GLASS_WALLS:
            if i < len(faces[wall]):
                plan.append(faces[wall][i])
    return plan[:max(1, min(36, count))]


def s_posters():
    mesh = STATE["poster_mesh"]
    mats = STATE["poster_mats"]
    rng = random.Random(714)
    normal = ["glass_%02d" % i for i in range(1, 13)]
    if GLASS_SPREAD:
        cnt = max(1, min(36, int(GLASS_COUNT)))
        order = []                                             # 12種類を順ぐりに使い回す（毎周シャッフル）
        while len(order) < cnt:
            lap = list(normal)
            rng.shuffle(lap)
            order += lap
        slots = [(w, u, z, sc, tilt, (i % 24) * 0.05) for i, (w, u, z, sc, tilt) in enumerate(glass_slot_plan(cnt))]
        plan = [("Poster_%02d" % (i + 1), order[i], slots[i]) for i in range(len(slots))]
    else:
        rng.shuffle(normal)
        plan = [("Poster_%02d" % (i + 1), normal[i], SLOTS[i][:3] + (SLOTS[i][3], 0.0, 0.0)) for i in range(len(SLOTS))]
    plan.append(("Poster_Hint", "glass_hint", HINT_SLOT + (0.0, 0.0)))
    if "poster_eye" in mats:
        plan.append(("Poster_Eye", "poster_eye", EYE_SLOT + (0.0, 0.0)))
    n = 0
    for label, key, (wall, u, z, sc, tilt, extra) in plan:
        if key not in mats:
            log("  (画像なし) %s" % key)
            continue
        loc, yaw = wall_pose_rel(wall, u, z, extra)
        # 板は +Y 向きの縦板：pitch が板の面の中でのかたむき（紙を斜めに貼った感じ）、yaw は壁に合わせて少しゆらす
        a = spawn(unreal.StaticMeshActor, loc, (0, tilt, yaw + rng.uniform(-4, 4)))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        c.set_material(0, mats[key])
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        k = sc * (GLASS_SCALE if key.startswith("glass_") else POSTER_SCALE)
        a.set_actor_scale3d(unreal.Vector(k, k, k))
        tag_actor(a, label)
        a.set_actor_hidden_in_game(True)
        n += 1
    log("張り紙を貼りました: %d 枚（最初は見えません）%s" % (n, "。ガラスぜんたいに散りばめました" if GLASS_SPREAD else ""))


# 謎7：4枚の「貼られる紙」（ガラスの文字）。貼られる順に 右の奥→左の手前→ドア→右の手前（形式は SLOTS と同じ）。奥の壁（電話機とヒント）は避ける
CODE_SLOTS = [("R", -40, 150, 1.0), ("L", 42, 150, 1.0), ("F", 0, 150, 1.0), ("R", 45, 150, 1.0)]
CODE_POSTER_TEX = ["glass_03", "glass_05", "glass_07", "glass_10"]      # でられない／たすけて／まってた／みぃつけた
CODE_POSTER_EXTRA = 2.5                  # 普通の張り紙と重なっても、この4枚のほうが手前（内側へ何cm）になるようにする


def yaw_to(dx, dy):
    """+Y 向きの板が、方向 (dx,dy) を向くための yaw"""
    return math.degrees(math.atan2(dy, dx)) - 90.0


def tree_candidates():
    """入口の前、距離 CODE_TREE_MIN〜MAX、入口の向きから ±CODE_TREE_ANGLE 度の中にある、森の木（setup_forest.py が置いた pine_* / dead_*）。
    [(左右の位置 s, 左右の角度 deg, 距離 dist, x, y, アクター)]"""
    g = STATE["geo"]
    cx, cy, _ = g["center"]
    n, t = g["n"], g["t"]
    res = []
    for a in eas().get_all_level_actors():
        lab = label_of(a)
        if not (lab.startswith("pine_") or lab.startswith("dead_")):
            continue
        try:
            if TAG in [str(x) for x in a.get_editor_property("tags")]:
                continue
            p = a.get_actor_location()
        except Exception:  # noqa
            continue
        dx, dy = p.x - cx, p.y - cy
        d_n = dx * n[0] + dy * n[1]
        d_t = dx * t[0] + dy * t[1]
        dist = math.hypot(dx, dy)
        if d_n <= 0 or not (CODE_TREE_MIN <= dist <= CODE_TREE_MAX):
            continue
        ang = math.degrees(math.atan2(d_t, d_n))
        if abs(ang) > CODE_TREE_ANGLE:
            continue
        res.append((d_t, ang, dist, p.x, p.y, a))
    return res


def pick_code_trees(cands, n=4):
    """候補から、左右にばらけた n 本を選ぶ。角度の範囲を n 等分した中心（目標）に近い木を1本ずつ（距離は中間に近いほうを優先）。
    目標の近く（等分の幅の半分＋3度）に木がなければ None（専用の柱を足す）。戻り値：(左→右の長さ n のリスト, 目標の角度のリスト)"""
    lo = CODE_TREE_ANGLE
    targets = [-lo + (i + 0.5) * (2.0 * lo / n) for i in range(n)]
    tol = lo / n + 3.0
    mid = 0.5 * (CODE_TREE_MIN + CODE_TREE_MAX)
    used = set()
    out = []
    for tg in targets:
        best, bi = None, None
        for i, c in enumerate(cands):
            if i in used or abs(c[1] - tg) > tol:
                continue
            score = abs(c[1] - tg) + abs(c[2] - mid) / 100.0
            if best is None or score < best:
                best, bi = score, i
        if bi is None:
            out.append(None)
        else:
            used.add(bi)
            out.append(cands[bi])
    return out, targets


def code_tree_spots():
    """4本の置き場所を、左→右の順で返す：[(x, y, 木の actor か None, 目標の角度)]。木がなければ、目標の角度・中間あたりの距離に専用の柱"""
    g = STATE["geo"]
    cx, cy, _ = g["center"]
    n, t = g["n"], g["t"]
    cands = tree_candidates() if CODE_TREE_PICK != "spawn" else []
    picked, targets = pick_code_trees(cands)
    rng = random.Random(7140)
    span = CODE_TREE_MAX - CODE_TREE_MIN
    spots = []
    for i, c in enumerate(picked):
        if c is not None:
            spots.append((c[3], c[4], c[5], targets[i]))
        else:
            ang = math.radians(targets[i])
            dist = rng.uniform(CODE_TREE_MIN + 0.15 * span, CODE_TREE_MAX - 0.15 * span)
            dn, dt = math.cos(ang) * dist, math.sin(ang) * dist
            spots.append((cx + n[0] * dn + t[0] * dt, cy + n[1] * dn + t[1] * dt, None, targets[i]))
    log("光る数字の木: 候補%d本（CODE_TREE_PICK=%s）→ 森の木 %d本・専用の柱 %d本" % (len(cands), CODE_TREE_PICK, sum(1 for s_ in spots if s_[2] is not None), sum(1 for s_ in spots if s_[2] is None)))
    return spots


def trunk_material():
    """専用の柱の、暗い樹皮の材質（光らない・ざらざら）"""
    m = new_material("M_CodeTrunk")
    c = xx(m, unreal.MaterialExpressionConstant3Vector, -600, 0)
    setp(c, "constant", unreal.LinearColor(0.03, 0.022, 0.016, 1.0))
    mel.connect_material_property(c, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(cst(m, 0.95, 240), "", MP.MP_ROUGHNESS)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def s_code_posters():
    """謎7：KD_CodePoster_1〜4（内側のガラスの文字・貼られる紙）と、外の4本の木に光る KD_CodeGlow_1〜4（数字。材質は kd_game.py が ENVELOPE_CODE から入れる）。
    i 番目に光る数字の木は、左→右に並べた4本の CODE_TREE_ORDER[i] 番目"""
    mesh = STATE["poster_mesh"]
    mats = STATE["poster_mats"]
    glow0 = mats.get("tree_glow_0") or mats.get("glass_glow_0")
    n = 0
    for i, (wall, u, z, sc) in enumerate(CODE_SLOTS):
        key = CODE_POSTER_TEX[i]
        if key not in mats:
            log("  (画像なし) %s" % key)
            continue
        loc, yaw = wall_pose_rel(wall, u, z, CODE_POSTER_EXTRA)
        k = CODE_SCALE * sc * GLASS_SCALE
        a = spawn(unreal.StaticMeshActor, loc, (0, 0, yaw))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        c.set_material(0, mats[key])
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        a.set_actor_scale3d(unreal.Vector(k, k, k))
        tag_actor(a, "KD_CodePoster_%d" % (i + 1))
        a.set_actor_hidden_in_game(True)
        n += 1
    log("暗号の張り紙（内側の紙）: %d枚" % n)
    if glow0 is None:
        log("  (画像なし) glass_glow_0")
        return
    g = STATE["geo"]
    cx, cy, _ = g["center"]
    zg = g["zmin"]                                              # 地面の高さ（ボックスの足もと）
    spots = code_tree_spots()                                   # 左→右
    order = list(CODE_TREE_ORDER)
    if sorted(order) != [0, 1, 2, 3]:
        log("[注意] CODE_TREE_ORDER は 0〜3 を1回ずつ並べてください（いま %s）。[1,3,0,2] にします" % (order,))
        order = [1, 3, 0, 2]
    cyl = tmat = None
    k = CODE_TREE_SIZE / 70.0                                   # 板（高さ70cm）を、高さ CODE_TREE_SIZE にする倍率
    made = 0
    for i in range(4):
        tx, ty, tree, tg = spots[order[i]]
        if tree is None:                                        # 専用の柱：直径 CODE_TREE_TRUNK_R×2・高さ350 の黒い円柱（根もとは地面）
            if cyl is None:
                cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
                tmat = trunk_material()
            tr = spawn(unreal.StaticMeshActor, (tx, ty, zg + 175.0), (0, 0, 0))
            trc = tr.get_component_by_class(unreal.StaticMeshComponent)
            trc.set_static_mesh(cyl)
            trc.set_material(0, tmat)
            tr.set_actor_scale3d(unreal.Vector(CODE_TREE_TRUNK_R * 2 / 100.0, CODE_TREE_TRUNK_R * 2 / 100.0, 3.5))
            tag_actor(tr, "KD_CodeTrunk_%d" % (i + 1))
        dx, dy = cx - tx, cy - ty
        dl = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dl, dy / dl                               # 木から、ボックスの中心へ向かう向き
        off = CODE_TREE_TRUNK_R + 3.0
        loc = (tx + ux * off, ty + uy * off, zg + CODE_TREE_Z)
        a = spawn(unreal.StaticMeshActor, loc, (0, 0, yaw_to(ux, uy)))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        c.set_material(0, glow0)
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        setp(c, "cast_shadow", False)
        a.set_actor_scale3d(unreal.Vector(k, k, k))
        tag_actor(a, "KD_CodeGlow_%d" % (i + 1))
        a.set_actor_hidden_in_game(True)
        made += 1
        log("  光る数字 %d番目 → 左から%d本目の木（距離 %.0fcm・角度 %.0f度・%s）" % (i + 1, order[i] + 1, dl, tg, "森の木" if tree is not None else "専用の柱"))
    log("暗号の数字（外の木）: %d枚" % made)


# ---------------- 掲示板（外）と、手に取って読める新聞 ----------------
BOARD_FILES = ["board_egetsunai", "board_camera", "paper_kamigari", "book_news", "memo_hatch", "wood_color", "wood_normal", "wood_rough"]


def s_board_textures():
    d = tex_game_dir()
    tasks = []
    for b in BOARD_FILES:
        f = os.path.join(d, b + ".png")
        if not os.path.exists(f):
            raise RuntimeError("画像がありません: %s" % f)
        tasks.append(mk_task(f, GAME_DIR + "/Textures/Game"))
    import_tasks(tasks)
    tn = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/Game/wood_normal")
    setp(tn, "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    setp(tn, "srgb", False)
    unreal.EditorAssetLibrary.save_loaded_asset(tn)
    tr = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/Game/wood_rough")
    setp(tr, "srgb", False)
    unreal.EditorAssetLibrary.save_loaded_asset(tr)
    log("掲示板の画像を取り込みました: %d 枚（凹凸は法線マップ、粗さは線形）" % len(BOARD_FILES))


def tex_param(m, name, asset, x, y, uv=None, normal=False):
    t = xx(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    setp(t, "parameter_name", name)
    setp(t, "texture", asset)
    if normal:
        setp(t, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif name == "Rough":
        try:
            setp(t, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        except Exception:  # noqa
            pass
    if uv is not None:
        mel.connect_material_expressions(uv, "", t, "UVs")
    return t


def scalar_param(m, name, v, x, y):
    e = xx(m, unreal.MaterialExpressionScalarParameter, x, y)
    setp(e, "parameter_name", name)
    setp(e, "default_value", float(v))
    return e


def add_wind(m, amp, speed, x0=-1500, y0=700):
    """紙の下のふちほど、風でひらひらゆれる（頂点を動かす。上のふちは画びょうでとまっている）。つまみ: WindAmp（cm） / WindSpeed"""
    tm = xx(m, unreal.MaterialExpressionTime, x0, y0)
    wp = xx(m, unreal.MaterialExpressionWorldPosition, x0, y0 + 120)
    dirv = xx(m, unreal.MaterialExpressionConstant3Vector, x0, y0 + 240)
    dirv.set_editor_property("constant", unreal.LinearColor(0.021, 0.013, 0.0, 1.0))
    dot = xx(m, unreal.MaterialExpressionDotProduct, x0 + 150, y0 + 180)
    mel.connect_material_expressions(wp, "", dot, "A")
    mel.connect_material_expressions(dirv, "", dot, "B")                # 紙ごとに、ゆれのタイミングをずらす
    tsp = mulx(m, tm, scalar_param(m, "WindSpeed", speed, x0, y0 + 360), y0 + 20)
    ph = xx(m, unreal.MaterialExpressionAdd, x0 + 300, y0)
    mel.connect_material_expressions(tsp, "", ph, "A")
    mel.connect_material_expressions(dot, "", ph, "B")
    s1 = xx(m, unreal.MaterialExpressionSine, x0 + 450, y0)
    setp(s1, "period", 1.0)
    mel.connect_material_expressions(ph, "", s1, "Input")
    ph2 = mulx(m, ph, cst(m, 2.3, y0 + 480), y0 + 200)
    s2 = xx(m, unreal.MaterialExpressionSine, x0 + 450, y0 + 200)
    setp(s2, "period", 1.0)
    mel.connect_material_expressions(ph2, "", s2, "Input")
    wave = xx(m, unreal.MaterialExpressionAdd, x0 + 600, y0)
    mel.connect_material_expressions(s1, "", wave, "A")
    mel.connect_material_expressions(mulx(m, s2, cst(m, 0.4, y0 + 520), y0 + 250), "", wave, "B")     # 速いゆれを少し足して、風のむらにする
    uvv = xx(m, unreal.MaterialExpressionTextureCoordinate, x0 + 450, y0 + 380)
    vmask = xx(m, unreal.MaterialExpressionComponentMask, x0 + 600, y0 + 380)
    setp(vmask, "r", False)
    setp(vmask, "g", True)
    mel.connect_material_expressions(uvv, "", vmask, "Input")
    weight = mulx(m, vmask, vmask, y0 + 400)                               # 上(0)は動かず、下(1)ほど大きく
    amount = mulx(m, mulx(m, wave, weight, y0 + 100), scalar_param(m, "WindAmp", amp, x0 + 600, y0 + 520), y0 + 150)
    vn = xx(m, unreal.MaterialExpressionVertexNormalWS, x0 + 750, y0 + 100)
    off = xx(m, unreal.MaterialExpressionMultiply, x0 + 900, y0 + 100)
    mel.connect_material_expressions(vn, "", off, "A")
    mel.connect_material_expressions(amount, "", off, "B")
    mel.connect_material_property(off, "", MP.MP_WORLD_POSITION_OFFSET)


def safe_wind(m, amp, speed):
    if not PAPER_WIND_MATERIAL:
        return
    try:
        add_wind(m, amp, speed)
    except Exception as ex:  # noqa
        log("  (紙のゆれを付けられません。ゆれなしで続けます) %s" % ex)


def s_board_materials():
    """木：色・法線（凹凸）・粗さを別々の画像から。つまみ（パラメータ）: Brightness / NormalStrength / Tiling / RoughMul"""
    T = GAME_DIR + "/Textures/Game/"
    ld = unreal.EditorAssetLibrary.load_asset
    m = new_material("M_KDWood")
    uv = xx(m, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    mulu = xx(m, unreal.MaterialExpressionMultiply, -950, 0)
    mel.connect_material_expressions(uv, "", mulu, "A")
    mel.connect_material_expressions(scalar_param(m, "Tiling", 1.0, -1150, 120), "", mulu, "B")
    col = tex_param(m, "Color", ld(T + "wood_color"), -800, -200, mulu)
    nrm = tex_param(m, "Normal", ld(T + "wood_normal"), -800, 100, mulu, normal=True)
    rgh = tex_param(m, "Rough", ld(T + "wood_rough"), -800, 400, mulu)
    mel.connect_material_property(mulx(m, col, scalar_param(m, "Brightness", 1.0, -800, -350), -100), "", MP.MP_BASE_COLOR)
    flat = xx(m, unreal.MaterialExpressionConstant3Vector, -600, 250)
    flat.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    lerp = xx(m, unreal.MaterialExpressionLinearInterpolate, -400, 250)
    mel.connect_material_expressions(flat, "", lerp, "A")
    mel.connect_material_expressions(nrm, "", lerp, "B")
    mel.connect_material_expressions(scalar_param(m, "NormalStrength", 1.0, -650, 400), "", lerp, "Alpha")
    mel.connect_material_property(lerp, "", MP.MP_NORMAL)
    mel.connect_material_property(mulx(m, rgh, scalar_param(m, "RoughMul", 1.0, -800, 550), 450), "", MP.MP_ROUGHNESS)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    STATE["wood"] = m
    # 紙：Brightness / Glow（暗い所でも読める弱い自己発光）/ Rough
    for nm, tx in (("M_BoardEgetsunai", "board_egetsunai"), ("M_BoardCamera", "board_camera"), ("M_PaperKamigari", "paper_kamigari")):
        pm = new_material(nm)
        setp(pm, "two_sided", True)
        if nm == "M_PaperKamigari":                              # 新聞は、切り抜いた形（ふちのやぶれ）のとおりに表示する
            setp(pm, "blend_mode", unreal.BlendMode.BLEND_MASKED)
        t = tex_param(pm, "Tex", ld(T + tx), -800, 0)
        mel.connect_material_property(mulx(pm, t, scalar_param(pm, "Brightness", 0.8, -800, -150), 0), "", MP.MP_BASE_COLOR)
        mel.connect_material_property(mulx(pm, t, scalar_param(pm, "Glow", POSTER_GLOW, -800, 200), 150), "", MP.MP_EMISSIVE_COLOR)
        mel.connect_material_property(scalar_param(pm, "Rough", 0.9, -600, 350), "", MP.MP_ROUGHNESS)
        if nm == "M_PaperKamigari":
            mel.connect_material_property(t, "A", MP.MP_OPACITY_MASK)
        safe_wind(pm, PAPER_WIND_AMP, PAPER_WIND_SPEED)
        mel.recompile_material(pm)
        unreal.EditorAssetLibrary.save_loaded_asset(pm)
        try:
            log("  材質 %s: 画像=%s" % (nm, t.get_editor_property("texture").get_name()))
        except Exception as ex:  # noqa
            log("  材質 %s: 画像が入っていません！ %s" % (nm, ex))
        STATE[nm] = pm
    # 読むとき用：光らない設定の、見やすい明るさ
    rm = new_material("M_KDRead")
    setp(rm, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    t = tex_param(rm, "Tex", ld(T + "paper_kamigari"), -800, 0)
    setp(rm, "blend_mode", unreal.BlendMode.BLEND_MASKED)
    setp(rm, "two_sided", True)
    mel.connect_material_property(mulx(rm, t, scalar_param(rm, "Brightness", 0.9, -800, -150), 0), "", MP.MP_EMISSIVE_COLOR)
    mel.connect_material_property(t, "A", MP.MP_OPACITY_MASK)
    safe_wind(rm, PAPER_WIND_AMP * 0.3, PAPER_WIND_SPEED * 0.8)                          # 手に持った新聞は、すこしだけゆれる
    mel.recompile_material(rm)
    unreal.EditorAssetLibrary.save_loaded_asset(rm)
    STATE["M_KDRead"] = rm
    mm = new_material("M_KDMetal")
    mc = xx(mm, unreal.MaterialExpressionConstant3Vector, -600, 0)
    mc.set_editor_property("constant", unreal.LinearColor(0.16, 0.16, 0.18, 1.0))
    mel.connect_material_property(mc, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(cst(mm, 0.85, 120), "", MP.MP_METALLIC)
    mel.connect_material_property(cst(mm, 0.5, 240), "", MP.MP_ROUGHNESS)
    mel.recompile_material(mm)
    unreal.EditorAssetLibrary.save_loaded_asset(mm)
    STATE["M_KDMetal"] = mm
    rb = new_material("M_KDReadBook")                                               # 本の古い新聞を、目の前に出す用
    setp(rb, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    tb = tex_param(rb, "Tex", ld(T + "book_news"), -800, 0)
    mel.connect_material_property(mulx(rb, tb, scalar_param(rb, "Brightness", 0.9, -800, -150), 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(rb)
    unreal.EditorAssetLibrary.save_loaded_asset(rb)
    STATE["M_KDReadBook"] = rb
    rmm = new_material("M_KDReadMemo")                                              # 電話の下のふたの中のメモ
    setp(rmm, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    tm_ = tex_param(rmm, "Tex", ld(T + "memo_hatch"), -800, 0)
    mel.connect_material_property(mulx(rmm, tm_, scalar_param(rmm, "Brightness", 0.9, -800, -150), 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(rmm)
    unreal.EditorAssetLibrary.save_loaded_asset(rmm)
    STATE["M_KDReadMemo"] = rmm
    cm = new_material("M_KDCoin")                                                  # 10円玉：銅色の金属
    cc = xx(cm, unreal.MaterialExpressionConstant3Vector, -600, 0)
    cc.set_editor_property("constant", unreal.LinearColor(0.62, 0.30, 0.14, 1.0))
    mel.connect_material_property(cc, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(mulx(cm, cc, cst(cm, 0.25, 100), 100), "", MP.MP_EMISSIVE_COLOR)       # 暗い夜でも、ほんのり見える
    mel.connect_material_property(cst(cm, 0.9, 150), "", MP.MP_METALLIC)
    mel.connect_material_property(cst(cm, 0.35, 250), "", MP.MP_ROUGHNESS)
    mel.recompile_material(cm)
    unreal.EditorAssetLibrary.save_loaded_asset(cm)
    STATE["M_KDCoin"] = cm
    pin = new_material("M_KDPin")
    pc_ = xx(pin, unreal.MaterialExpressionConstant3Vector, -600, 0)
    pc_.set_editor_property("constant", unreal.LinearColor(0.55, 0.04, 0.03, 1.0))
    mel.connect_material_property(pc_, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(cst(pin, 0.35, 150), "", MP.MP_ROUGHNESS)
    mel.recompile_material(pin)
    unreal.EditorAssetLibrary.save_loaded_asset(pin)
    STATE["M_KDPin"] = pin
    log("掲示板の材質を作りました（木・張り紙3種・読む用・画びょう）")


def import_fbx_once(fbx, scale, dest, collision=True):
    ui = unreal.FbxImportUI()
    setp(ui, "import_mesh", True)
    setp(ui, "import_as_skeletal", False)
    setp(ui, "import_materials", False)
    setp(ui, "import_textures", False)
    setp(ui, "automated_import_should_detect_type", False)
    setp(ui, "mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property("static_mesh_import_data")
    setp(d, "combine_meshes", True)
    setp(d, "auto_generate_collision", collision)
    setp(d, "transform_vertex_to_absolute", True)
    setp(d, "import_uniform_scale", float(scale))
    import_tasks([mk_task(fbx, dest, fbx_ui=ui)])
    mesh = None
    for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True, include_folder=False):
        a = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            mesh = a
    if mesh is None:
        raise RuntimeError("メッシュが見つかりません: " + dest)
    return mesh, mesh.get_bounds().box_extent


def import_fit(fname, sub, longest_cm, collision=True):
    """assets/unreal/<fname> を取り込み、いちばん長い辺が longest_cm になるように、取り込み後の大きさを測って合わせる"""
    fbx = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", fname)
    if not os.path.exists(fbx):
        raise RuntimeError("%s がありません: %s" % (fname, fbx))
    dest = GAME_DIR + "/" + sub
    scale = 100.0
    mesh, e = import_fbx_once(fbx, scale, dest, collision)
    big = max(e.x, e.y, e.z) * 2.0
    log("%s の大きさ（取り込み直後）: %.1f × %.1f × %.1f cm（最長 %.0f が正常）" % (fname, e.x * 2, e.y * 2, e.z * 2, longest_cm))
    if big > 0.0 and abs(big - longest_cm) > longest_cm * 0.08:
        scale = scale * longest_cm / big
        mesh, e = import_fbx_once(fbx, scale, dest, collision)
        log("%s を、倍率 %.3f で取り込み直しました: %.1f × %.1f × %.1f cm" % (fname, scale, e.x * 2, e.y * 2, e.z * 2))
    return mesh


def import_board():
    return import_fit("BulletinBoard.fbx", "Board", 264.0)


def s_board():
    """入口の前の道ばたに、木の掲示板を立てる。張り紙2枚と、手に取れる新聞（Paper_News）を貼る"""
    g = STATE["geo"]
    half_n, _ht = front_half()
    n = g["n"]
    th = math.radians(BOARD_TURN)
    f = (n[0] * math.cos(th) - n[1] * math.sin(th), n[0] * math.sin(th) + n[1] * math.cos(th))       # 掲示板の正面の向き
    tf = (f[1], -f[0])                                       # 正面を向いたとき、左へ向かう向き
    cx, cy, _ = g["center"]
    px = cx + n[0] * (half_n + BOARD_DIST) + g["t"][0] * BOARD_SIDE
    py = cy + n[1] * (half_n + BOARD_DIST) + g["t"][1] * BOARD_SIDE
    gz = g["zmin"]
    yaw = math.degrees(math.atan2(f[1], f[0]))
    sphere = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
    if KEEP_HAND_PLACEMENT and "Board_Model" in KEEP_POSE:         # 手で動かした掲示板の位置を基準に、紙などを置く
        pl, pr = KEEP_POSE["Board_Model"]
        px, py, gz, yaw = pl.x, pl.y, pl.z, pr.yaw + 90.0
        f = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
        tf = (f[1], -f[0])
        log("  手で動かした掲示板の位置を使います: (%.0f,%.0f,%.0f) 向き=%.0f度" % (px, py, gz, yaw))
    elif KEEP_HAND_PLACEMENT and "Board_Panel" in KEEP_POSE:       # 古い版（箱を組んだ掲示板）を手で動かしてあれば、その位置に合わせる
        pl, pr = KEEP_POSE["Board_Panel"]
        px, py, gz, yaw = pl.x, pl.y, pl.z - 130.0, pr.yaw
        f = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
        tf = (f[1], -f[0])
        log("  古い掲示板の位置に合わせました")
    board_mesh = import_board()
    bm = spawn(unreal.StaticMeshActor, (px, py, gz), (0, 0, yaw - 90.0))
    bc = bm.get_component_by_class(unreal.StaticMeshComponent)
    bc.set_static_mesh(board_mesh)
    bm.set_actor_scale3d(unreal.Vector(BOARD_SCALE, BOARD_SCALE, BOARD_SCALE))
    bc.set_material(0, STATE["wood"])
    bc.set_material(1, STATE["M_KDMetal"])
    setp(bc, "mobility", unreal.ComponentMobility.MOVABLE)
    tag_actor(bm, "Board_Model")

    def at(a, b, z):
        return (px + f[0] * a + tf[0] * b, py + f[1] * a + tf[1] * b, gz + z)

    mesh = STATE["poster_mesh"]
    S = BOARD_SCALE
    face = (2.0 + 0.8) * S                                      # 板の表面から少しだけ浮かせる
    pin = STATE["M_KDPin"]
    # 板に向かって「右」が -b、「左」が +b
    items = [("Board_Egetsunai", "M_BoardEgetsunai", 65.0 * S, (0.9 * S, 1.0, 0.9 * S), 2.5),
             ("Paper_News", "M_PaperKamigari", 0.0, (0.9 * S, 1.0, 0.64 * S), -1.5),
             ("Board_Camera", "M_BoardCamera", -65.0 * S, (0.9 * S, 1.0, 0.9 * S), -2.0)]
    for label, mn, b, sc, tilt in items:
        a = spawn(unreal.StaticMeshActor, at(face, b, 130.0 * S), (0, tilt, yaw - 90.0))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        c.set_material(0, STATE[mn])
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        a.set_actor_scale3d(unreal.Vector(sc[0], sc[1], sc[2]))
        tag_actor(a, label)
        top = 130.0 * S + 35.0 * sc[2] - 3.0 * S
        pn = spawn(unreal.StaticMeshActor, at(face + 1.2 * S, b, top), (0, 0, yaw))
        pc2 = pn.get_component_by_class(unreal.StaticMeshComponent)
        pc2.set_static_mesh(sphere)
        pc2.set_material(0, pin)
        setp(pc2, "mobility", unreal.ComponentMobility.MOVABLE)
        pn.set_actor_scale3d(unreal.Vector(0.035 * S, 0.035 * S, 0.035 * S))
        tag_actor(pn, "Board_Pin_" + label)
    # 読むとき用の板（最初は隠しておく。kd_game.py が目の前に出す）
    rp = spawn(unreal.StaticMeshActor, g["center"], (0, 0, 0))
    rc = rp.get_component_by_class(unreal.StaticMeshComponent)
    rc.set_static_mesh(mesh)
    rc.set_material(0, STATE["M_KDRead"])
    setp(rc, "mobility", unreal.ComponentMobility.MOVABLE)
    try:
        rc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:  # noqa
        pass
    tag_actor(rp, "KD_ReadPlane")
    rp.set_actor_hidden_in_game(True)
    log("掲示板を立てました: 位置=(%.0f,%.0f) 向き=%.0f度（入口の前 %.0fcm・横 %.0fcm）" % (px, py, yaw, BOARD_DIST, BOARD_SIDE))


COIN_DIST = 300.0                      # 10円①を、入口の前から何cm の所に落とすか
COIN_SIDE = -220.0                     # 入口の正面から横へ何cm（＋は入口に向かって左）


SAFE_FILES = ["safe_wood_color", "safe_wood_normal", "safe_wood_rough", "safe_plate"]


def wood_material(name, prefix, tiling=1.0):
    """木目の材質：色・法線（凹凸）・粗さの3画像。つまみ: Tiling / Brightness / NormalStrength / RoughMul"""
    T = GAME_DIR + "/Textures/Game/"
    ld = unreal.EditorAssetLibrary.load_asset
    m = new_material(name)
    uv = xx(m, unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    mulu = xx(m, unreal.MaterialExpressionMultiply, -950, 0)
    mel.connect_material_expressions(uv, "", mulu, "A")
    mel.connect_material_expressions(scalar_param(m, "Tiling", tiling, -1150, 120), "", mulu, "B")
    col = tex_param(m, "Color", ld(T + prefix + "_color"), -800, -200, mulu)
    nrm = tex_param(m, "Normal", ld(T + prefix + "_normal"), -800, 100, mulu, normal=True)
    rgh = tex_param(m, "Rough", ld(T + prefix + "_rough"), -800, 400, mulu)
    mel.connect_material_property(mulx(m, col, scalar_param(m, "Brightness", 1.0, -800, -350), -100), "", MP.MP_BASE_COLOR)
    flat = xx(m, unreal.MaterialExpressionConstant3Vector, -600, 250)
    flat.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    lerp = xx(m, unreal.MaterialExpressionLinearInterpolate, -400, 250)
    mel.connect_material_expressions(flat, "", lerp, "A")
    mel.connect_material_expressions(nrm, "", lerp, "B")
    mel.connect_material_expressions(scalar_param(m, "NormalStrength", 1.0, -650, 400), "", lerp, "Alpha")
    mel.connect_material_property(lerp, "", MP.MP_NORMAL)
    mel.connect_material_property(mulx(m, rgh, scalar_param(m, "RoughMul", 1.0, -800, 550), 450), "", MP.MP_ROUGHNESS)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def s_safe_materials():
    d = tex_game_dir()
    tasks = []
    for b in SAFE_FILES:
        f = os.path.join(d, b + ".png")
        if not os.path.exists(f):
            raise RuntimeError("画像がありません: %s（ZIPを取り直してください）" % f)
        tasks.append(mk_task(f, GAME_DIR + "/Textures/Game"))
    import_tasks(tasks)
    tn = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/Game/safe_wood_normal")
    setp(tn, "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    setp(tn, "srgb", False)
    unreal.EditorAssetLibrary.save_loaded_asset(tn)
    tr = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/Game/safe_wood_rough")
    setp(tr, "srgb", False)
    unreal.EditorAssetLibrary.save_loaded_asset(tr)

    def pbr(name, col, metal, rough):
        m = new_material(name)
        c = xx(m, unreal.MaterialExpressionConstant3Vector, -600, 0)
        c.set_editor_property("constant", unreal.LinearColor(col[0], col[1], col[2], 1.0))
        mel.connect_material_property(c, "", MP.MP_BASE_COLOR)
        mel.connect_material_property(cst(m, metal, 120), "", MP.MP_METALLIC)
        mel.connect_material_property(cst(m, rough, 240), "", MP.MP_ROUGHNESS)
        mel.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        return m
    STATE["M_KDSafeWood"] = wood_material("M_KDSafeWood", "safe_wood", 1.0)             # 木目プリントの塗装（傷とはがれつき）
    STATE["M_KDNickel"] = pbr("M_KDNickel", (0.72, 0.72, 0.75), 1.0, 0.3)               # ニッケルめっき（取っ手・ダイヤル）
    STATE["M_KDBlack"] = pbr("M_KDBlack", (0.02, 0.02, 0.02), 0.0, 0.5)
    STATE["M_KDBrass"] = pbr("M_KDBrass", (0.78, 0.58, 0.22), 1.0, 0.35)                     # 小さな鍵：真鍮
    STATE["M_KDBoxLacquer"] = pbr("M_KDBoxLacquer", (0.06, 0.035, 0.025), 0.0, 0.35)    # 箱の漆（黒に近い茶色）
    STATE["M_KDSafeInner"] = pbr("M_KDSafeInner", (0.22, 0.02, 0.03), 0.0, 0.9)           # 開いた金庫の内張り（くすんだ赤）
    pm = new_material("M_KDSafePlate")                                                  # 銘板（黒いエナメルに銀の文字）
    t = tex_param(pm, "Tex", unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/Game/safe_plate"), -800, 0)
    mel.connect_material_property(t, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(mulx(pm, t, cst(pm, 0.08, 100), 100), "", MP.MP_EMISSIVE_COLOR)      # 暗くても、文字がうっすら見える
    mel.connect_material_property(cst(pm, 0.4, 250), "", MP.MP_METALLIC)
    mel.connect_material_property(cst(pm, 0.35, 330), "", MP.MP_ROUGHNESS)
    mel.recompile_material(pm)
    unreal.EditorAssetLibrary.save_loaded_asset(pm)
    STATE["M_KDSafePlate"] = pm
    bf = os.path.join(d, "puzzlebox_buttons.png")                                       # 箱のボタンの数字（象牙色）
    if not os.path.exists(bf):
        raise RuntimeError("画像がありません: %s（ZIPを取り直してください）" % bf)
    import_tasks([mk_task(bf, GAME_DIR + "/Textures/Game")])
    im = new_material("M_KDBoxIvory")
    it = tex_param(im, "Tex", unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Textures/Game/puzzlebox_buttons"), -800, 0)
    mel.connect_material_property(it, "", MP.MP_BASE_COLOR)
    mel.connect_material_property(cst(im, 0.0, 120), "", MP.MP_METALLIC)
    mel.connect_material_property(cst(im, 0.6, 240), "", MP.MP_ROUGHNESS)
    mel.recompile_material(im)
    unreal.EditorAssetLibrary.save_loaded_asset(im)
    STATE["M_KDBoxIvory"] = im
    log("金庫の材質を作りました（木目・ニッケル・銘板・黒・箱の漆と象牙）")


def s_safe():
    """手提げ金庫（本体 DialSafe_Body＋回るつまみ DialSafe_Knob）を、ボックスの中に置く"""
    g = STATE["geo"]
    n = g["n"]
    gz = g["zmin"]
    px, py, _z = world(SAFE_BACK, SAFE_SIDE, gz)
    yaw = math.degrees(math.atan2(n[1], n[0])) + SAFE_TURN                      # 前（おもて面）が向く向き
    if KEEP_HAND_PLACEMENT and "DialSafe_Body" in KEEP_POSE:
        pl, pr = KEEP_POSE["DialSafe_Body"]
        px, py, gz, yaw = pl.x, pl.y, pl.z, pr.yaw + 90.0
        log("  手で動かした金庫の位置を使います: (%.0f,%.0f,%.0f) 向き=%.0f度" % (px, py, gz, yaw))
    f = (math.cos(math.radians(yaw)), math.sin(math.radians(yaw)))
    right = (f[1], -f[0])                                                         # 金庫のおもてを見たときの「右」
    S = SAFE_SCALE
    body_mesh = import_fit("DialSafe.fbx", "Safe", 36.0)                          # 最長＝幅 36cm
    body = spawn(unreal.StaticMeshActor, (px, py, gz), (0, 0, yaw - 90.0))
    bc = body.get_component_by_class(unreal.StaticMeshComponent)
    bc.set_static_mesh(body_mesh)
    bc.set_material(0, STATE["M_KDSafeWood"])
    bc.set_material(1, STATE["M_KDNickel"])
    bc.set_material(2, STATE["M_KDSafePlate"])
    bc.set_material(3, STATE["M_KDBlack"])
    setp(bc, "mobility", unreal.ComponentMobility.MOVABLE)
    body.set_actor_scale3d(unreal.Vector(S, S, S))
    tag_actor(body, "DialSafe_Body")
    kmesh = import_fit("SafeDial.fbx", "SafeKnob", 5.9, collision=False)         # つまみ：別のフォルダに取り込む
    kx = px + right[0] * 4.0 * S + f[0] * 13.4 * S                                # 本体の原点から：右へ4cm・前へ13.4cm・高さ6cm（Blenderの設計どおり）
    ky = py + right[1] * 4.0 * S + f[1] * 13.4 * S
    kz = gz + 6.0 * S
    kn = spawn(unreal.StaticMeshActor, (kx, ky, kz), (0, 0, yaw - 90.0))
    kc = kn.get_component_by_class(unreal.StaticMeshComponent)
    kc.set_static_mesh(kmesh)
    kc.set_material(0, STATE["M_KDNickel"])
    kc.set_material(1, STATE["M_KDBlack"])
    setp(kc, "mobility", unreal.ComponentMobility.MOVABLE)
    kn.set_actor_scale3d(unreal.Vector(S, S, S))
    tag_actor(kn, "DialSafe_Knob")
    # ダイヤル専用のカメラ：つまみのおもて側（f の向き）に置いて、つまみを見る。回している間、この画面になる（プレイヤーの位置と関係なく、アップで見える）
    d = DIAL_CAM_DIST
    camx, camy, camz = kx + f[0] * d, ky + f[1] * d, kz + 0.12 * d
    cyaw = math.degrees(math.atan2(-f[1], -f[0]))
    cpitch = -math.degrees(math.atan2(0.12 * d, d))
    cam = spawn(unreal.CameraActor, (camx, camy, camz), (0, cpitch, cyaw))
    try:
        cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", float(DIAL_CAM_FOV))
    except Exception as e:  # noqa
        log("  (ダイヤルのカメラの視野を設定できません) %s" % e)
    tag_actor(cam, "KD_DialCam")
    pcam = spawn(unreal.CameraActor, g["center"], (0, 0, 0))                       # 電話機を回す（押す）ときの専用カメラ。置き場所と向きは、kd_game.py が電話機の位置に合わせて動かす
    tag_actor(pcam, "KD_PhoneCam")
    # 開いた状態の金庫：下の箱（上が開いている）とふた。はじめは隠しておき、金庫が開いたときに kd_game.py が、本体とつまみを隠して、これを出す（ふたが回って開く）
    base_mesh = import_fit("DialSafeBase.fbx", "SafeBase", 36.0)
    lid_mesh = import_fit("DialSafeLid.fbx", "SafeLid", 36.2, collision=False)
    base = spawn(unreal.StaticMeshActor, (px, py, gz), (0, 0, yaw - 90.0))
    bsc = base.get_component_by_class(unreal.StaticMeshComponent)
    bsc.set_static_mesh(base_mesh)
    for i, key in enumerate(("M_KDSafeWood", "M_KDNickel", "M_KDSafePlate", "M_KDBlack", "M_KDSafeInner")):
        bsc.set_material(i, STATE[key])
    setp(bsc, "mobility", unreal.ComponentMobility.MOVABLE)
    base.set_actor_scale3d(unreal.Vector(S, S, S))
    tag_actor(base, "DialSafe_Base")
    hx, hy, hz = px - f[0] * 12.0 * S, py - f[1] * 12.0 * S, gz + 10.4 * S                    # うしろのちょうつがい（本体の原点から：うしろへ12cm・高さ10.4cm）
    lid = spawn(unreal.StaticMeshActor, (hx, hy, hz), (0, 0, yaw - 90.0))
    lc = lid.get_component_by_class(unreal.StaticMeshComponent)
    lc.set_static_mesh(lid_mesh)
    for i, key in enumerate(("M_KDSafeWood", "M_KDNickel", "M_KDSafePlate", "M_KDBlack", "M_KDSafeInner")):
        lc.set_material(i, STATE[key])
    setp(lc, "mobility", unreal.ComponentMobility.MOVABLE)
    lid.set_actor_scale3d(unreal.Vector(S, S, S))
    tag_actor(lid, "DialSafe_Lid")
    # 箱の中に置く、小さな鍵と10円②（金庫が開いたとき、kd_game.py が一瞬だけ見せて、手に入れたことにして消す）
    key_mesh = import_fit("SafeKey.fbx", "SafeKey", 6.9, collision=False)
    right_ = (f[1], -f[0])
    fz = gz + (2.5 + BOX_TOP) * S + 0.3                                                        # 金庫の底（2.5cm）の上にある、パズルの箱のてっぺんの上（鍵と10円は、箱の上にのる）
    key = spawn(unreal.StaticMeshActor, (px - right_[0] * 6.0 * S - f[0] * 2.0 * S, py - right_[1] * 6.0 * S - f[1] * 2.0 * S, fz), (0, 0, yaw - 90.0 + 25.0))
    kcc = key.get_component_by_class(unreal.StaticMeshComponent)
    kcc.set_static_mesh(key_mesh)
    kcc.set_material(0, STATE["M_KDBrass"])
    setp(kcc, "mobility", unreal.ComponentMobility.MOVABLE)
    key.set_actor_scale3d(unreal.Vector(S, S, S))
    tag_actor(key, "DialSafe_Key")
    cyl_ = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
    coin2 = spawn(unreal.StaticMeshActor, (px + right_[0] * 6.5 * S + f[0] * 1.0 * S, py + right_[1] * 6.5 * S + f[1] * 1.0 * S, fz + 0.4), (0, 0, 0))
    cc2 = coin2.get_component_by_class(unreal.StaticMeshComponent)
    cc2.set_static_mesh(cyl_)
    cc2.set_material(0, STATE["M_KDCoin"])
    setp(cc2, "mobility", unreal.ComponentMobility.MOVABLE)
    try:
        cc2.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:  # noqa
        pass
    coin2.set_actor_scale3d(unreal.Vector(0.05, 0.05, 0.004))
    tag_actor(coin2, "DialSafe_Coin")
    # 金庫の中のパズルの箱（16個のボタン）。底の中心に置く
    box_mesh = import_fit("PuzzleBox.fbx", "PuzzleBox", 19.3, collision=False)
    box = spawn(unreal.StaticMeshActor, (px, py, gz + 2.5 * S), (0, 0, yaw - 90.0))
    xc = box.get_component_by_class(unreal.StaticMeshComponent)
    xc.set_static_mesh(box_mesh)
    for i, key_ in enumerate(("M_KDBoxLacquer", "M_KDBrass", "M_KDBoxIvory", "M_KDBlack")):
        xc.set_material(i, STATE[key_])
    setp(xc, "mobility", unreal.ComponentMobility.MOVABLE)
    box.set_actor_scale3d(unreal.Vector(S, S, S))
    tag_actor(box, "DialSafe_Box")
    # 箱のボタンを押すときの専用カメラ：箱の上面の真ん中から、おもて側（f）に BOX_CAM_BACK・上に BOX_CAM_UP 離して、真ん中を見下ろす
    tx, ty, tz = px, py, gz + (2.5 + BOX_TOP) * S
    bcx, bcy, bcz = tx + f[0] * BOX_CAM_BACK * S, ty + f[1] * BOX_CAM_BACK * S, tz + BOX_CAM_UP * S
    bcyaw = math.degrees(math.atan2(-f[1], -f[0]))
    bcpitch = -math.degrees(math.atan2(BOX_CAM_UP, BOX_CAM_BACK))
    bcam = spawn(unreal.CameraActor, (bcx, bcy, bcz), (0, bcpitch, bcyaw))
    tag_actor(bcam, "KD_BoxCam")
    log("箱のカメラ（KD_BoxCam）を置きました: (%.0f,%.0f,%.0f) 向き=%.0f度・下向き %.0f度（箱の上面の真ん中 (%.0f,%.0f,%.0f) を見る）" % (bcx, bcy, bcz, bcyaw, -bcpitch, tx, ty, tz))
    for a_ in (base, lid, key, coin2, box):
        a_.set_actor_hidden_in_game(True)
        try:
            a_.set_is_temporarily_hidden_in_editor(True)
        except Exception:  # noqa
            pass
    log("手提げ金庫を置きました: (%.0f,%.0f) 向き=%.0f度・倍率 %.1f（奥へ %.0fcm・横へ %.0fcm）" % (px, py, yaw, S, SAFE_BACK, SAFE_SIDE))


def s_coin():
    """道ばたの10円①（Coin_10yen）。ほんのり光る小さな点の明かり（Coin_Light）つき"""
    g = STATE["geo"]
    half_n, _ht = front_half()
    n = g["n"]
    cx, cy, _ = g["center"]
    x = cx + n[0] * (half_n + COIN_DIST) + g["t"][0] * COIN_SIDE
    y = cy + n[1] * (half_n + COIN_DIST) + g["t"][1] * COIN_SIDE
    gz = g["zmin"]
    cyl = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
    a = spawn(unreal.StaticMeshActor, (x, y, gz + 1.0), (0, 0, 0))
    c = a.get_component_by_class(unreal.StaticMeshComponent)
    c.set_static_mesh(cyl)
    c.set_material(0, STATE["M_KDCoin"])
    setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
    try:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    except Exception:  # noqa
        pass
    a.set_actor_scale3d(unreal.Vector(0.07, 0.07, 0.004))             # 直径7cm・厚さ8mm（見つけやすいよう、本物より大きめ）
    tag_actor(a, "Coin_10yen")
    pl = spawn(unreal.PointLight, (x, y, gz + 35.0), (0, 0, 0))
    lc = pl.get_component_by_class(unreal.PointLightComponent)
    setp(lc, "mobility", unreal.ComponentMobility.MOVABLE)
    setp(lc, "intensity", KEEP_TUBE.get("Coin_Light", 1.2))               # ひかるが決めた明るさ（cd）を引き継ぐ。初期値 1.2
    setp(lc, "attenuation_radius", 150.0)
    setp(lc, "light_color", unreal.Color(255, 190, 120, 255))
    tag_actor(pl, "Coin_Light")
    log("10円①を置きました: (%.0f,%.0f)（入口の前 %.0fcm・横 %.0fcm）" % (x, y, COIN_DIST, COIN_SIDE))


def main():
    log("=== ゲームのしくみ 準備（買った電話ボックス用） ===")
    apply_settings(SETUP_SETTING_NAMES, log)
    step("環境確認", s_env)
    step("前回の生成物を消す", s_clear, ["環境確認"])
    step("中心の印", s_center_marker, ["前回の生成物を消す"])
    step("当たり判定", s_collision, ["環境確認"])
    step("効果音", s_sounds, ["環境確認"])
    step("ガラスの材質", s_glass_material, ["環境確認"])
    step("蛍光灯", s_lights, ["前回の生成物を消す"])
    step("プレイヤーの開始位置", s_player_start, ["環境確認"])
    step("懐中電灯", s_flashlight, ["中心の印"])
    step("張り紙の画像", s_poster_textures, ["環境確認"])
    step("張り紙の板", s_poster_mesh, ["環境確認"])
    step("張り紙の材質", s_poster_materials, ["張り紙の画像"])
    step("張り紙を貼る", s_posters, ["張り紙の板", "張り紙の材質", "前回の生成物を消す"])
    step("暗号の張り紙", s_code_posters, ["張り紙の板", "張り紙の材質", "前回の生成物を消す"])
    step("幽霊（仮）", s_ghost, ["前回の生成物を消す"])
    step("掲示板の画像", s_board_textures, ["環境確認"])
    step("掲示板の材質", s_board_materials, ["掲示板の画像"])
    step("掲示板", s_board, ["掲示板の材質", "張り紙の板", "前回の生成物を消す"])
    step("10円", s_coin, ["掲示板の材質", "前回の生成物を消す"])
    step("金庫の材質", s_safe_materials, ["環境確認"])
    step("ダイヤル式の金庫", s_safe, ["金庫の材質", "前回の生成物を消す"])
    if NIGHT_MODE:
        step("夜にする", s_night, ["前回の生成物を消す"])
    step("保存", s_save, ["環境確認"])
    log("SUMMARY: " + ", ".join("%s=%s" % (k, v) for k, v in RESULTS.items()))
    if any(v == "FAIL" for v in RESULTS.values()):
        log_err("失敗した手順があります → 出力ログを「KD」で絞って全部コピーして、Claudeに送ってください")
    else:
        log("完了。次に Cmd で  py \"…/unreal/kd_game.py\"  を実行して、▶（Play）を押してください")
    write_log_file()


main()
