"""
ゲームのしくみ 段階1（エディタで Play したときだけ動く「遊べる試作」）

できること：
  ① 森の入口から歩いて、電話ボックスに入れる（WASD＋マウス。Q/Eで上下はできない：目の高さに固定）
  ② ボックスの奥まで入ると、画面が一瞬くらくなって、ドアが バタン と閉まる（もう出られない）
  ③ 5秒後から、蛍光灯が 点滅 → 暗転 をくりかえす（段階 1〜5 が画面の左上に出る）
  ④ F キーで懐中電灯のオン／オフ

使い方（1回だけ）：
  1) 先に setup_game.py を実行しておく（プレイヤーの開始位置・懐中電灯・当たり判定を置く）
  2) 出力ログの下の Cmd に  py "…/unreal/kd_game.py"  と打つ（エディタを閉じるまで有効）
  3) 上の ▶（Play）を押す。止めるときは Esc。もう一度 Play しても動く

注意：これは「エディタの中で遊ぶ」ためのもの。ゲームとして書き出す（パッケージ）には、
      あとで Blueprint に作り替える。決まりごとはここの Game クラスにまとめてあるので、そのまま移せる。
      毎フレーム検索はしない（参照は Play の最初に1回だけ集める）。
"""
import json
import math
import os
import random
import traceback

import unreal

# ---------------- 書き換えてよい設定 ----------------
DOOR_OPEN_YAW = 100.0        # ドアが開いているときの回転。ドアが内側に開いてしまうなら -100 にする
EYE_HEIGHT = 165.0           # 目の高さ（cm）
WALK_SPEED = 170.0           # 歩く速さ（cm/秒）
ENTER_HALF = 38.0            # ボックスの中心から この範囲（cm）に入ったら閉じ込める
CLOSE_DELAY = 0.5            # 入ってから扉が閉まるまで（秒）
CLOSE_TIME = 0.22            # 扉が閉まる速さ（秒）
IDLE_FIRST = 5.0             # 閉じ込められてから最初の点滅までの時間（秒）
FLICKER_TIME = 2.1           # 点滅の長さ
DARK_TIME = 1.4              # 暗転の長さ
LAST_STAGE = 5               # 段階5になったら失敗（段階2で作る）。今は表示だけ
FLASH_KEY = "F"
ENTER_KEY = "E"                # 電話ボックスに入るキー（買った電話ボックス用：入口のドアは動かさず、暗転と音で入る）
SWAY_DEG = 3.0                 # 掲示板の紙が風でゆれる角度（度）。0 でゆれない。上の画びょうを軸に、下がゆれる
SWAY_SPEED = 0.35              # ゆれる速さ（1秒に何回）
BOOK_LABEL = "book"            # 本の名前（アウトライナーの名前に入っている言葉）。違うときは kd_settings.json で直す
SAFE_LABEL = "safe"            # 金庫の名前に入っている言葉
SAFE_CODE = [("L", 19), ("R", 3), ("L", 8)]   # 金庫の外の扉の番号（L=左へ回して止める／R=右）。新聞の「19-3-8」と、液晶の「ヒダリ ミギ ヒダリ」
DIAL_STEP_TIME = 0.07          # ダイヤルが1目盛り回るのに、キーを押しつづける時間（秒）
TRAP_MARGIN = 28.0             # 閉じ込められている間、壁から この距離（cm）より外へは出られない（すり抜け止め）
DIAL_FOV = 30.0                # 金庫のダイヤルを回す間の、視野の角度（小さいほどアップ。ふだんは約90）
DIAL_ZOOM_TIME = 0.45          # アップになるまでの時間（秒）
DIAL_SIGN = 1.0                # ダイヤルの見た目の回る向きが逆なら -1.0 にする
START_DIST = 1800.0            # 開始位置が遠すぎるとき（空中・地面の下）に、入口の正面から何cm 離して立たせるか
ARROW_MOVE = True              # 矢印キー（↑↓←→）でも歩けるようにする（テンプレのキャラは W A S D だけ）。↑前 ↓後ろ ←左へ →右へ
START_POS = []                 # 開始位置を決め打ちにする：[x, y, z]（cm）。[] なら使わない。PlayerStart を動かしても変わらないときに使う（アウトライナーで、置きたい場所の位置の数字をコピー）
MANUAL_WALK = "auto"           # 歩けないときの、歩く仕組み。"auto"＝動かないときだけ自分で動かす／"on"＝いつも自分で動かす／"off"＝使わない
WALKABLE_ANGLE = 70.0          # 歩ける坂の角度（度）。テンプレは約45度。急な坂で歩けず、すべって落ちるときに大きくする。0 なら変えない
PHONE_BACK = 25.0              # 電話機の「触る点」：奥の壁から手前へ何cm
PHONE_Z = -30.0                # 電話機の「触る点」の高さ（ボックスの中心から。－が下）。電話機が見えている高さに合わせる
HATCH_Z = -105.0               # 電話の下のふたの高さ（ボックスの中心から）。足元近くを見て E
PHONE_COIN_COST = 1            # 電話をかけるときの10円の枚数
ITEM_RANGE = 200.0             # 10円・本に、この距離（cm）まで近づいて見ると「Eで…」が出る
READ_RANGE = 240.0             # 掲示板の新聞に、この距離（cm）まで近づいて見ると「Eで読む」が出る
READ_SIZE = 47.0               # 新聞を手に取ったときの、目の前の大きさ（cm。画面の高さに収まるくらい）
READ_DIST = 45.0               # 新聞を、目からこの距離（cm）に出す
ENTER_RANGE = 260.0            # 入口の前のこの距離（cm）まで近づくと「Eで入る」が出る
ENTER_FADE_OUT = 0.9           # 暗くなるまでの時間（秒）
ENTER_BLACK = 2.6              # 真っ暗のまま待つ時間（秒）。この間に「ドアが開く音 → 中に入る音 → 扉が閉まる音」が鳴る
ENTER_FADE_IN = 1.4            # 明るくなるまでの時間（秒）
SOUND_DIR = "/Game/KoushuDenwa/Sounds"
# 幽霊が出る場所（ボックス中心からの位置 cm。正面＝+Y）。段階1〜4で、だんだん近づく
GHOST_SPOTS = [(0.0, 1300.0), (-240.0, 750.0), (270.0, 360.0), (115.0, 25.0)]
GHOST_SUBS = ["（外に、誰か立っている……）", "（さっきより、近い）", "（ガラスに、何か貼られている）", "（すぐそこにいる）"]
POSTER_FRAC = [0.3, 0.55, 0.8, 1.0]        # 1〜4回目の「張り紙の演出」で、張り紙が何割まで貼られるか
GHOST_HOLD = (11.0, 11.0, 10.0, 9.0)       # 幽霊が外に見えている時間（秒）。この間は張り紙は出ない
POSTER_HOLD = (6.0, 7.0, 8.0, 9.0)         # 張り紙が貼られている時間（秒）。この間は幽霊は出ない。終わると全部はがれる
POSTER_STEP = 0.35                         # 張り紙が1枚ずつ貼られていく間隔（秒）
PUZZLE_COUNT = 8                           # 謎の数（この数だけ解くと、演出の強さが最後の段階まで進む）
PRESSURE_INTERVAL = 150.0                  # 謎が進まないまま、この時間（秒）たつと、幽霊が1段階ずつ近づく（演出の予備は使わない）
FLAG_KEY = "P"                             # テスト用：「謎を1つ解いた」ことにするキー（本物の謎ができたら、solve() を呼ぶ）
DEAD_DIST = 70.0                           # 失敗のとき、幽霊が目の前に出る距離（cm）
RESTART_AFTER = 6.0                        # 失敗してから、最初に戻るまでの時間（秒）
FLASH_OUTSIDE = 1.0            # 外にいるときの、懐中電灯の明るさの倍率（まぶしいときは小さく。0.5 で半分）
FLASH_INSIDE = 0.12          # 閉じ込められたあと、懐中電灯の明るさを、外にいたときの何倍にするか（中は狭くてまぶしいので小さく）
TUBE_SCALE = 1.0             # 蛍光灯の光の強さの倍率（明るすぎるときは小さくする）
IDLE_DIP = 1.0              # 静かな間に、ときどき光がゆれるときの弱さ（1.0 でゆれない）
TUBE_GLOW = 0.5              # 蛍光灯の「光る見た目」の強さの倍率
GLASS_DIRT = 0.25            # ガラスのくもり具合（0=ほぼ透明 〜 1=いまのまま）。外が見えないときは小さくする
FLICKER_BLACK = 0.88         # 点滅で「消えた」瞬間に、画面をこの割合だけ黒くする（0=しない 〜 1=真っ黒）。点滅がグレーに見えるときは大きくする
DARK_BLACK = 1.0             # 暗転のあいだ、画面をこの割合だけ黒くする（どの光が残っていても、ちゃんと暗くなる）。1.0=真っ黒
DARK_WORLD = 0.12            # 暗転のとき、月と空の光をこの倍率まで下げる（1=そのまま）
# ----------------------------------------------------

LOG_PREFIX = "[KD] "


def log(msg):
    unreal.log(LOG_PREFIX + str(msg))


def screen(world, msg, color=(255, 255, 255), t=3.0):
    try:
        unreal.SystemLibrary.print_string(world, str(msg), True, False, unreal.LinearColor(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, 1.0), t)
    except Exception:  # noqa
        pass



# ---------------- 調整つまみ（設定ファイル） ----------------
# 数字は Saved/kd_settings.json に書いてある。メモ帳で開いて数字を変えて保存するだけで効く。
# （ZIP を取り直しても消えない場所にある。無い項目は、最初の実行で自動で足される）
SETTINGS_DESCR = {
    "FLASH_OUTSIDE": "外にいるときの懐中電灯の明るさの倍率。まぶしいときは小さく（0.5 で半分）",
    "FLASH_INSIDE": "閉じ込められたあとの懐中電灯の明るさ（外にいたときの何倍か）。明るすぎたら小さく",
    "TUBE_SCALE": "蛍光灯の光の強さの倍率。明るすぎたら小さく",
    "IDLE_DIP": "静かな間（7秒に一度）光がゆれる弱さ。1.0 にするとゆれない",
    "TUBE_GLOW": "蛍光灯の「光る見た目」の倍率",
    "FLICKER_BLACK": "点滅の「消えた」瞬間に画面を黒くする割合（0〜1）。点滅が暗くならないなら大きく",
    "DARK_BLACK": "暗転のあいだに画面を黒くする割合（0〜1）",
    "DARK_WORLD": "暗転のとき、月と空の光を何倍まで下げるか",
    "GLASS_DIRT": "ガラスのくもりの強さ（M_KDGlass を使うとき）",
    "WALK_SPEED": "歩く速さ（cm/秒）。テンプレのキャラには効かない",
    "ENTER_RANGE": "入口の前の、E で入れる距離（cm）",
    "ENTER_FADE_OUT": "E を押してから暗くなるまでの秒数",
    "ENTER_BLACK": "暗いまま待つ秒数（この間にドアの音が鳴る）",
    "SWAY_DEG": "掲示板の紙が風でゆれる角度（度）。0 でゆれない",
    "SWAY_SPEED": "紙がゆれる速さ（1秒に何回）",
    "BOOK_LABEL": "本の名前に入っている言葉（アウトライナーで確認）",
    "SAFE_LABEL": "金庫の名前に入っている言葉（アウトライナーで確認）",
    "SAFE_CODE": "金庫の番号。[[\"L\",19],[\"R\",3],[\"L\",8]] のように、向き（L左・R右）と数字",
    "DIAL_STEP_TIME": "ダイヤルが1目盛り回る秒数（小さいほど速い）",
    "DIAL_SIGN": "ダイヤルの見た目の向きが逆なら -1 にする",
    "START_DIST": "開始位置が変な所のとき、入口の正面から何cm 離して立たせるか",
    "ARROW_MOVE": "true で、矢印キーでも歩けるようにする（↑前 ↓後ろ ←左 →右）",
    "START_POS": "開始位置を決め打ち：[x, y, z]。空 [] なら使わない。PlayerStart を動かしても変わらないとき用",
    "MANUAL_WALK": "歩く仕組み。auto＝キャラが動かないときだけ自分で動かす／on／off",
    "WALKABLE_ANGLE": "歩ける坂の角度（度）。急な坂で歩けないとき大きく。0なら変えない",
    "PHONE_BACK": "電話機の触る点を、奥の壁から手前へ何cm にするか",
    "PHONE_Z": "電話機の触る点の高さ（ボックスの中心から。マイナスが下）",
    "HATCH_Z": "電話の下のふたの高さ（ボックスの中心から）",
    "PHONE_COIN_COST": "電話1回に必要な10円の枚数",
    "ITEM_RANGE": "10円・本を拾う・開ける距離（cm）",
    "READ_RANGE": "掲示板の新聞を読めるようになる距離（cm）",
    "READ_SIZE": "手に取った新聞の大きさ（cm）。文字が切れるときは小さく",
    "READ_DIST": "手に取った新聞を、目からどれだけ離すか（cm）",
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
    "REPLACE_GLASS_MATERIAL": "true で、買ったガラスの材質を M_KDGlass に替える。false で買ったまま",
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


KD_SETTING_NAMES = ["FLASH_OUTSIDE", "FLASH_INSIDE", "TUBE_SCALE", "TUBE_GLOW", "IDLE_DIP", "FLICKER_BLACK", "DARK_BLACK", "DARK_WORLD", "GLASS_DIRT", "WALK_SPEED", "ENTER_RANGE", "SWAY_DEG", "SWAY_SPEED", "BOOK_LABEL", "SAFE_LABEL", "SAFE_CODE", "DIAL_STEP_TIME", "DIAL_SIGN", "TRAP_MARGIN", "DIAL_FOV", "DIAL_ZOOM_TIME", "PHONE_BACK", "PHONE_Z", "HATCH_Z", "PHONE_COIN_COST", "START_DIST", "START_POS", "MANUAL_WALK", "ARROW_MOVE", "WALKABLE_ANGLE", "ITEM_RANGE", "READ_RANGE", "READ_SIZE", "READ_DIST", "ENTER_FADE_OUT", "ENTER_BLACK", "ENTER_FADE_IN", "FLICKER_TIME", "DARK_TIME", "GHOST_HOLD", "POSTER_HOLD", "POSTER_STEP", "POSTER_FRAC", "PUZZLE_COUNT", "PRESSURE_INTERVAL", "DEAD_DIST", "RESTART_AFTER", "GHOST_SPOTS"]


def game_world():
    for getter in (
        lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(),
        lambda: unreal.EditorLevelLibrary.get_game_world(),
    ):
        try:
            w = getter()
            if w is not None:
                return w
        except Exception:  # noqa
            continue
    return None


def label_of(a):
    try:
        return a.get_actor_label()
    except Exception:  # noqa
        return a.get_name()


class Game:
    """状態：WALK(歩く) → CLOSING(扉が閉まる) → TRAPPED(閉じ込め：IDLE/FLICKER/DARK をくりかえす)"""

    def __init__(self, world):
        apply_settings(KD_SETTING_NAMES, log)        # Play のたびに、設定ファイルの数字を読み直す（ファイルを保存して Play するだけで反映）
        self.world = world
        self.t = 0.0
        self.state = "WALK"
        self.state_t = 0.0
        self.stage = 0
        self.sub = "IDLE"
        self.poster_target = 0
        self.poster_shown = 0
        self.poster_round = 0
        self.steps = []
        self.step_i = 0
        self.step_t = 0.0
        self.sub_t = 0.0
        self.sub_len = IDLE_FIRST
        self.flash_on = False
        self.flicker_next = 0.0
        self.flicker_lit = True
        self.inside_t = 0.0
        self.fade_t = -1.0
        self.errors = 0
        self.mult = 1.0           # 蛍光灯の明るさの倍率
        self.door_yaw = DOOR_OPEN_YAW
        self.door_base = 0.0
        self.front_yaw = 0.0
        self.setup()

    # ---- Play のはじめに1回だけ：参照を集める ----
    def setup(self):
        found = {}
        all_actors = list(unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.Actor))
        for a in all_actors:
            found[label_of(a)] = a
        self.hinge = found.get("DoorHinge")
        if self.hinge is not None:
            self.door_base = self.hinge.get_actor_rotation().yaw      # 閉じているときの向き（買った電話ボックスでは 0 ではない）
        self.flash = found.get("Flashlight")
        self.frame = found.get("PhoneBooth_Booth_Frame") or next((v for k, v in found.items() if k.endswith("Booth_Frame")), None)
        self.tubes = []
        for nm in ("TubeLight_L", "TubeLight_R"):
            a = found.get(nm)
            if a is None:
                continue
            c = a.get_component_by_class(unreal.RectLightComponent)
            base = c.get_editor_property("intensity")
            self.tubes.append((c, base * TUBE_SCALE))
        # レベルの中の光は、ぜんぶ、いっしょに点滅・暗転させる（電話ボックスの中の光だけでなく、街灯・月・空など）。懐中電灯と蛍光灯は別あつかい
        self.extra = []
        for a in all_actors:
            lab = label_of(a)
            if lab == "Flashlight" or lab.startswith("TubeLight"):
                continue
            try:
                comps = a.get_components_by_class(unreal.LightComponent)
            except Exception:  # noqa
                continue
            for c in comps:
                try:
                    kind = "world" if isinstance(c, (unreal.DirectionalLightComponent, unreal.SkyLightComponent)) else "local"
                    self.extra.append((kind, c, c.get_editor_property("intensity")))
                except Exception:  # noqa
                    pass
        # 蛍光灯の光る部分（材質 M_Tube の Flicker）とガラス（M_Glass の Dirt）を、動かせる材質にする
        self.tube_mats = []
        self.tube_bars = [found.get(n) for n in ("KD_Tube_L", "KD_Tube_R") if found.get(n) is not None]
        for nm, a in found.items():
            if not (nm.startswith("Booth_") or nm.startswith("KD_Tube") or "phone_box" in nm.lower()):
                continue
            comp = a.get_component_by_class(unreal.StaticMeshComponent)
            if comp is None:
                continue
            for i in range(comp.get_num_materials()):
                mat = comp.get_material(i)
                mn = mat.get_name() if mat is not None else ""
                try:
                    if "Tube" in mn:
                        self.tube_mats.append(comp.create_dynamic_material_instance(i, mat))
                    elif "KDGlass" in mn:
                        mid = comp.create_dynamic_material_instance(i, mat)
                        mid.set_scalar_parameter_value("Dirt", GLASS_DIRT)
                except Exception as e:  # noqa
                    log("  (材質を動かせません) %s[%d]: %s" % (nm, i, e))
        self.posters = sorted([(k, v) for k, v in found.items() if k.startswith("Poster_") and k not in ("Poster_Hint", "Poster_Eye")], key=lambda kv: kv[0])
        self.hint = found.get("Poster_Hint")
        self.news = found.get("Paper_News")                  # 掲示板の新聞（手に取って読める）
        self.read_plane = found.get("KD_ReadPlane")
        self.coin = found.get("Coin_10yen")
        self.coin_light = found.get("Coin_Light")
        self.coins = 0                                       # 持っている10円
        self.read_mat = None
        low = [(k.lower(), v) for k, v in found.items()]
        self.book = next((v for k, v in low if BOOK_LABEL.lower() in k and "KD" not in label_of(v)), None)
        self.safe = next((v for k, v in low if SAFE_LABEL.lower() in k and "KD" not in label_of(v) and not k.startswith("dialsafe")), None)
        self.dial_body = found.get("DialSafe_Body")                  # ダイヤル式の金庫（本体と、回るつまみ）
        self.dial_knob = found.get("DialSafe_Knob")
        self.dial_value, self.dial_dir, self.dial_entries, self.safe_open, self.has_key = 0, None, [], False, False
        self.has_memo, self.called_0115, self.dialed_0714, self.lcd_seen, self.digits = False, False, False, False, ""
        self.hatch_open = False
        self.dial_knob_rot = self.dial_knob.get_actor_rotation() if self.dial_knob is not None else None
        log("触れる物: 10円=%s 本=%s 金庫=%s" % (label_of(self.coin) if self.coin else "なし", label_of(self.book) if self.book else "なし（BOOK_LABEL を直す）", label_of(self.safe) if self.safe else "なし（SAFE_LABEL を直す）"))
        self.sway = []                                       # 掲示板の紙：上の画びょうを軸に、風でゆれる
        for i, nm in enumerate(("Board_Egetsunai", "Paper_News", "Board_Camera")):
            a = found.get(nm)
            if a is None:
                continue
            try:
                loc, rot = a.get_actor_location(), a.get_actor_rotation()
                top0 = unreal.MathLibrary.transform_location(unreal.Transform(loc, rot, a.get_actor_scale3d()), unreal.Vector(0, 0, 35.0))
                sc = a.get_actor_scale3d()
                b0 = unreal.MathLibrary.transform_location(unreal.Transform(loc, rot, sc), unreal.Vector(0, 0, -35.0))
                b1 = unreal.MathLibrary.transform_location(unreal.Transform(loc, unreal.Rotator(rot.roll + 5.0, rot.pitch, rot.yaw), sc), unreal.Vector(0, 0, -35.0))
                nrm = unreal.MathLibrary.transform_direction(unreal.Transform(loc, rot, sc), unreal.Vector(0, 1, 0))
                sgn = 1.0 if ((b1.x - b0.x) * nrm.x + (b1.y - b0.y) * nrm.y + (b1.z - b0.z) * nrm.z) > 0 else -1.0       # 下が板から離れる向きのほうへだけゆらす（板にめり込まない）
                self.sway.append((a, loc, rot, top0, i * 2.1, sgn))
            except Exception as e:  # noqa
                log("  (紙のゆれを準備できません) %s: %s" % (nm, e))
        self.reading = False
        self.eye = found.get("Poster_Eye")
        for _k, a in self.posters + [("e", self.eye)]:
            if a is not None:
                a.set_actor_hidden_in_game(True)
        if self.hint is not None:
            self.hint.set_actor_hidden_in_game(False)             # 手がかりの張り紙は、はじめから貼ってある（入った瞬間に現れない）
        self.ghost = found.get("Ghost")
        if self.ghost is not None:
            self.ghost.set_actor_hidden_in_game(True)
            self.ghost_head = found.get("Ghost_Head")
            if self.ghost_head is not None:
                self.ghost_head.set_actor_hidden_in_game(True)
        self.dead_t = -1.0
        self.pc = unreal.GameplayStatics.get_player_controller(self.world, 0)
        self.pawn = unreal.GameplayStatics.get_player_pawn(self.world, 0)
        self.cx, self.cy = 0.0, 0.0
        marker = found.get("KD_BoothCenter")
        if marker is not None:                      # 買った電話ボックス用：中心と入口の向きは、印から読む
            ml = marker.get_actor_location()
            self.cz = ml.z
            self.cx, self.cy = ml.x, ml.y
            self.front_yaw = marker.get_actor_rotation().yaw
        elif self.frame is not None:
            o, _e = self.frame.get_actor_bounds(False)
            self.cx, self.cy = o.x, o.y
        if self.hinge is not None:
            self.hinge.set_actor_rotation(unreal.Rotator(0, 0, self.door_base + self.door_yaw), False)
        self.is_char = False
        if self.pawn is not None:
            self.is_char = self.pawn.get_component_by_class(unreal.CharacterMovementComponent) is not None
        if self.pawn is not None and not self.is_char:
            try:
                mv = self.pawn.get_component_by_class(unreal.FloatingPawnMovement)
                mv.set_editor_property("max_speed", WALK_SPEED)
                mv.set_editor_property("acceleration", WALK_SPEED * 8)
                mv.set_editor_property("deceleration", WALK_SPEED * 8)
            except Exception as e:  # noqa
                log("  (歩く速さを設定できません) %s" % e)
        self.flash_base = None
        if self.flash is not None:
            try:
                self.flash_base = self.flash.get_component_by_class(unreal.SpotLightComponent).get_editor_property("intensity")
            except Exception:  # noqa
                pass
            self.set_flash_scale(FLASH_OUTSIDE)
            self.set_flash(False)
        self.half_t, self.half_n = 70.0, 70.0
        if marker is not None:
            msc = marker.get_actor_scale3d()
            if msc.x > 5.0 and msc.y > 5.0:           # setup_game_fp.py が印の大きさに入れた、ボックスの半分の幅・奥行き(cm)
                self.half_t, self.half_n = msc.x, msc.y
        self.snd = {}
        for nm in ("door_open", "door_close", "latch"):
            try:
                self.snd[nm] = unreal.EditorAssetLibrary.load_asset("%s/%s" % (SOUND_DIR, nm))
            except Exception:  # noqa
                self.snd[nm] = None
        self.enter_t = -1.0
        self.key_e = unreal.Key()
        self.key_e.set_editor_property("key_name", ENTER_KEY)
        self.key_flag = unreal.Key()
        self.key_flag.set_editor_property("key_name", FLAG_KEY)
        self.key = unreal.Key()
        self.key.set_editor_property("key_name", FLASH_KEY)
        log("Play 開始: 入口方式=%s 効果音=%s" % ("Eキー" if self.hinge is None else "ドアが閉まる", [k for k, v in self.snd.items() if v is not None]))
        log("Play 開始: ドアの軸=%s 懐中電灯=%s 蛍光灯の光=%d 光る材質=%d 他の光=%d個 プレイヤー=%s ボックス中心=(%.0f,%.0f)" % (
            self.hinge is not None, self.flash is not None, len(self.tubes), len(self.tube_mats), len(self.extra), self.pawn is not None, self.cx, self.cy))
        screen(self.world, "WASD：歩く / マウス：見る / F：懐中電灯", (200, 255, 200), 6.0)

    # ---- 部品 ----
    def set_flash_scale(self, k):
        if self.flash is not None and getattr(self, "flash_base", None) is not None:
            try:
                self.flash.get_component_by_class(unreal.SpotLightComponent).set_editor_property("intensity", self.flash_base * k)
            except Exception as e:  # noqa
                log("  (懐中電灯の明るさを変えられません) %s" % e)

    def set_flash(self, on):
        self.flash_on = on
        try:
            self.flash.get_component_by_class(unreal.SpotLightComponent).set_visibility(on, False)
        except Exception as e:  # noqa
            log("  (懐中電灯の切り替え不可) %s" % e)

    def set_lights(self, mult):
        self.mult = mult
        for c, base in self.tubes:
            c.set_editor_property("intensity", base * mult)
        for mid in self.tube_mats:
            mid.set_scalar_parameter_value("Flicker", mult * TUBE_GLOW)          # 蛍光灯の見た目も、光といっしょにちらつく
        for bar in self.tube_bars:                                              # 消えたときは、光る棒そのものも隠す（材質が残り光るのを防ぐ）
            try:
                bar.set_actor_hidden_in_game(mult < 0.05)
            except Exception:  # noqa
                pass
        part = 1.0 if mult >= 0.5 else DARK_WORLD + (1.0 - DARK_WORLD) * (mult / 0.5)
        for kind, c, base in self.extra:
            c.set_editor_property("intensity", base * (part if kind == "world" else mult))

    def reveal(self, stage):
        frac = POSTER_FRAC[min(stage, len(POSTER_FRAC)) - 1]
        n = int(math.ceil(len(self.posters) * frac))
        for _k, a in self.posters[:n]:
            a.set_actor_hidden_in_game(False)
        if self.hint is not None and stage >= 1:
            self.hint.set_actor_hidden_in_game(False)
        if self.eye is not None and stage >= 3:
            self.eye.set_actor_hidden_in_game(False)

    def ghost_show(self, x, y, face_x=None, face_y=None):
        if self.ghost is None:
            return
        fx = self.cx if face_x is None else face_x
        fy = self.cy if face_y is None else face_y
        yaw = math.degrees(math.atan2(fy - y, fx - x))
        self.ghost.set_actor_location_and_rotation(unreal.Vector(x, y, 0.0), unreal.Rotator(0, 0, yaw), False, False)
        self.ghost.set_actor_hidden_in_game(False)
        if self.ghost_head is not None:
            self.ghost_head.set_actor_hidden_in_game(False)

    def ghost_hide(self):
        if self.ghost is not None:
            self.ghost.set_actor_hidden_in_game(True)
            if self.ghost_head is not None:
                self.ghost_head.set_actor_hidden_in_game(True)

    def begin_dead(self):
        """失敗：幽霊が目の前に出る → 赤く暗転 → しばらくして最初に戻る"""
        self.state, self.state_t = "DEAD", 0.0
        self.set_lights(0.6)
        self.blackout(0.0)
        rot = self.pc.get_control_rotation()
        fwd = unreal.MathLibrary.get_forward_vector(rot)
        loc = self.pawn.get_actor_location()
        x, y = loc.x + fwd.x * DEAD_DIST, loc.y + fwd.y * DEAD_DIST
        self.ghost_show(x, y, loc.x, loc.y)
        screen(self.world, "……みつけた", (255, 40, 40), RESTART_AFTER)
        try:
            self.pc.player_camera_manager.start_camera_fade(0.0, 1.0, 2.5, unreal.LinearColor(0.5, 0, 0, 1), False, True)
        except Exception as e:  # noqa
            log("  (赤い暗転ができません) %s" % e)
        log("失敗エンド（段階%d）" % self.stage)

    def blackout(self, amount):
        """画面の黒さ（0〜1）を、すぐ変える。点滅の「消えた」瞬間を、光の遅れに関係なく暗くする"""
        try:
            self.pc.player_camera_manager.set_manual_camera_fade(amount, unreal.LinearColor(0, 0, 0, 1), False)
        except Exception as e:  # noqa
            if not getattr(self, "_blk_warned", False):
                self._blk_warned = True
                log("  (画面を黒くできません) %s" % e)

    def fade(self, to_black, dur):
        try:
            cm = self.pc.player_camera_manager
            a, b = (0.0, 1.0) if to_black else (1.0, 0.0)
            cm.start_camera_fade(a, b, dur, unreal.LinearColor(0, 0, 0, 1), False, to_black)
        except Exception as e:  # noqa
            log("  (暗転できません) %s" % e)

    # ---- 毎フレーム ----
    def tick(self, dt):
        self.t += dt
        self.state_t += dt
        if self.pawn is None:
            self.pawn = unreal.GameplayStatics.get_player_pawn(self.world, 0)
            return
        loc = self.pawn.get_actor_location()
        if getattr(self, "eye_z", None) is None:                 # 最初に見えたとき：歩く人の種類と、立っている高さを覚える
            try:
                self.is_char = self.pawn.get_component_by_class(unreal.CharacterMovementComponent) is not None
            except Exception:  # noqa
                pass
            self.eye_z = loc.z
            if len(START_POS) == 3:                                    # ひかるが決めた開始位置（PlayerStart より優先）
                try:
                    self.pawn.set_actor_location(unreal.Vector(float(START_POS[0]), float(START_POS[1]), float(START_POS[2])), False, True)
                    loc = self.pawn.get_actor_location()
                    self.eye_z = loc.z
                    log("開始位置を、決め打ちの位置にしました: (%.0f, %.0f, %.0f)" % (loc.x, loc.y, loc.z))
                except Exception as e:  # noqa
                    log("  (START_POS で動かせません) %s" % e)
            # 開始位置が、ボックスから遠い・地面の下のときは、入口の正面に立たせ直す（PlayerStart が別の所にある場合の救済）
            try:
                far = math.hypot(loc.x - self.cx, loc.y - self.cy) > self.half_n + START_DIST + 3000.0
                cz = getattr(self, "cz", None)
                low = cz is not None and loc.z < cz - 400.0
                if (far or low) and getattr(self, "cz", None) is not None:
                    th = math.radians(self.front_yaw)
                    nx, ny = -math.sin(th), math.cos(th)
                    px, py = self.cx + nx * (self.half_n + START_DIST), self.cy + ny * (self.half_n + START_DIST)
                    self.pawn.set_actor_location(unreal.Vector(px, py, self.cz + 250.0), False, False)
                    self.pc.set_control_rotation(unreal.Rotator(0, 0, math.degrees(math.atan2(-ny, -nx))))
                    self.eye_z = self.cz + 250.0
                    loc = self.pawn.get_actor_location()
                    log("開始位置が遠い／低いので、入口の正面へ立たせ直しました: (%.0f, %.0f, %.0f)" % (px, py, self.cz + 250.0))
            except Exception as e:  # noqa
                log("  (開始位置を直せません) %s" % e)
            log("プレイヤー: %s・最初の高さ z=%.0f" % ("歩く人（地面に立つ）" if self.is_char else "ういている人（高さ固定）", loc.z))
        # 歩く高さを固定（飛ばない）。地面に立つ人（Character）は、固定しない。固定する高さは、最初に立った高さ（地面の下に入らない）
        if not self.is_char and abs(loc.z - self.eye_z) > 0.5:
            self.pawn.set_actor_location(unreal.Vector(loc.x, loc.y, self.eye_z), False, False)
        if self.t > 2.0 and not getattr(self, "_diag", False):
            self._diag = True
            try:
                mv = self.pawn.get_component_by_class(unreal.CharacterMovementComponent)
                log("診断: 位置=(%.0f,%.0f,%.0f) 歩く人=%s 動きかた=%s 最高速=%s" % (loc.x, loc.y, loc.z, self.is_char, mv.get_editor_property("movement_mode") if mv else "なし", mv.get_editor_property("max_walk_speed") if mv else "なし"))
            except Exception as e:  # noqa
                log("診断: 位置=(%.0f,%.0f,%.0f) 歩く人=%s (%s)" % (loc.x, loc.y, loc.z, self.is_char, e))
        if self.t > 2.5 and not getattr(self, "_diag2", False):
            self._diag2 = True
            try:                                                   # 体のまわり 4m 以内にある物を、ぜんぶ書き出す（動けない原因さがし）
                near = []
                for a in unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.Actor):
                    if a == self.pawn:
                        continue
                    p = a.get_actor_location()
                    d = math.sqrt((p.x - loc.x) ** 2 + (p.y - loc.y) ** 2 + (p.z - loc.z) ** 2)
                    if d < 400.0:
                        near.append((d, label_of(a), a.get_class().get_name()))
                near.sort()
                log("診断: 体から 4m 以内の物: %s" % ("、".join("%s(%s) %.0fcm" % (n, c, d) for d, n, c in near[:15]) or "なし"))
                try:
                    ov = self.pawn.get_overlapping_actors()
                    log("診断: 体と重なっている物: %s" % ("、".join(label_of(a) for a in ov) or "なし"))
                except Exception as e:  # noqa
                    log("診断: 重なり確認不可 %s" % e)
                try:
                    log("診断: 移動入力が無視されている=%s 視点入力が無視されている=%s" % (self.pc.is_move_input_ignored(), self.pc.is_look_input_ignored()))
                except Exception as e:  # noqa
                    log("診断: 入力無視の確認不可 %s" % e)
            except Exception as e:  # noqa
                log("診断: まわりの確認でエラー %s" % e)
        if self.t > 3.0 and not getattr(self, "_diag3", False):
            self._diag3 = True
            self.diag_floor(loc)
        self.tick_arrows()
        self.tick_manual(dt)
        self.clamp_in_booth(loc)
        self.tick_dial_anim(dt)
        self.tick_fov(dt)
        self.tick_unstuck(loc, dt)
        self.update_flashlight()
        self.tick_sway()
        self.tick_hud()
        if self.state == "READING":
            self.tick_reading()
        elif self.state == "SAFE":
            self.tick_safe(dt)
        elif self.state == "PHONE":
            self.tick_phone(dt)
        elif self.state == "WALK" and self.hinge is None:
            self.tick_walk_e(loc)
            self.tick_news(loc)
            self.tick_items(loc)
        elif self.state == "ENTERING":
            self.tick_entering(dt)
        elif self.state == "WALK":
            inside = abs(loc.x - self.cx) < ENTER_HALF and abs(loc.y - self.cy) < ENTER_HALF
            self.inside_t = self.inside_t + dt if inside else 0.0
            if self.inside_t > CLOSE_DELAY:
                self.begin_close()
        elif self.state == "CLOSING":
            k = min(1.0, self.state_t / CLOSE_TIME)
            k = 1 - (1 - k) * (1 - k)                      # 最初に勢いよく、最後にゆっくり
            self.door_yaw = DOOR_OPEN_YAW * (1 - k)
            if self.hinge is not None:
                self.hinge.set_actor_rotation(unreal.Rotator(0, 0, self.door_base + self.door_yaw), False)
            if self.state_t >= CLOSE_TIME:
                self.state, self.state_t = "TRAPPED", 0.0
                self.start_trapped()
                screen(self.world, "バタン！（とじこめられた）", (255, 120, 120), 4.0)
                self.fade(False, 0.8)
        elif self.state == "TRAPPED":
            if getattr(self, "deferred", None):
                self.on_flag(self.deferred.pop(0))
            self.tick_trapped(dt)
            self.tick_items(loc)
        elif self.state == "DEAD":
            if self.state_t > RESTART_AFTER:
                self.state = "RESTART"
                log("最初に戻ります（RestartLevel）")
                unreal.SystemLibrary.execute_console_command(self.world, "RestartLevel")

    # ---- 買った電話ボックス用：Eキーで入る ----
    def door_point(self):
        """入口の前（ボックスの外）の点。入口の向き front_yaw の +Y 側に half_n だけ出た所"""
        th = math.radians(self.front_yaw)
        # 入口の向き n = (+Y を front_yaw だけ回した向き)
        nx, ny = -math.sin(th), math.cos(th)
        return self.cx + nx * (self.half_n + 40.0), self.cy + ny * (self.half_n + 40.0), (nx, ny)

    def play(self, name):
        snd = self.snd.get(name)
        if snd is not None:
            try:
                unreal.GameplayStatics.play_sound_2d(self.world, snd, 1.0, 1.0, 0.0)
            except Exception as e:  # noqa
                log("  (音を鳴らせません) %s: %s" % (name, e))

    def tick_walk_e(self, loc):
        px, py, _n = self.door_point()
        near = math.hypot(loc.x - px, loc.y - py) < ENTER_RANGE
        if near:
            if int(self.t * 4) != getattr(self, "_prompt_k", -1):            # 0.25秒ごとに案内を出し直す
                self._prompt_k = int(self.t * 4)
                try:
                    unreal.SystemLibrary.print_string(self.world, "[%s] 電話ボックスに入る" % ENTER_KEY, True, False, unreal.LinearColor(1, 1, 0.6, 1), 0.4, "KD_PROMPT")
                except Exception:  # noqa
                    screen(self.world, "[%s] 電話ボックスに入る" % ENTER_KEY, (255, 255, 160), 0.4)
            try:
                if self.pc.was_input_key_just_pressed(self.key_e):
                    self.begin_enter()
            except Exception as e:  # noqa
                log("  (Eキーを読めません) %s" % e)

    def tick_sway(self):
        if SWAY_DEG <= 0.0 or not self.sway:
            return
        for a, loc, rot, top0, ph, sgn in self.sway:
            w = 2.0 * math.pi * SWAY_SPEED * self.t + ph
            th = sgn * SWAY_DEG * (0.55 + 0.45 * (math.sin(w) + 0.4 * math.sin(2.3 * w + 0.7)) / 1.4)       # 0.1〜1.0 倍：外向きだけ
            try:
                nr = unreal.Rotator(rot.roll + th, rot.pitch, rot.yaw)
                top1 = unreal.MathLibrary.transform_location(unreal.Transform(loc, nr, a.get_actor_scale3d()), unreal.Vector(0, 0, 35.0))
                nl = unreal.Vector(loc.x + top0.x - top1.x, loc.y + top0.y - top1.y, loc.z + top0.z - top1.z)     # 上のふちが動かないように、位置を直す
                a.set_actor_location_and_rotation(nl, nr, False, False)
            except Exception as e:  # noqa
                log("  (紙のゆれを止めます) %s" % e)
                self.sway = []
                return

    def phone_point(self):
        th = math.radians(self.front_yaw)
        nx, ny = -math.sin(th), math.cos(th)
        return unreal.Vector(self.cx - nx * (self.half_n - PHONE_BACK), self.cy - ny * (self.half_n - PHONE_BACK), getattr(self, "cz", 200.0) + PHONE_Z)

    def hatch_point(self):
        p = self.phone_point()
        return unreal.Vector(p.x, p.y, getattr(self, "cz", 200.0) + HATCH_Z)

    def looking_at_pt(self, p, rng, thr=0.93):
        try:
            eye, rot = self.eye_info()
            d = unreal.Vector(p.x - eye.x, p.y - eye.y, p.z - eye.z)
            dist = math.sqrt(d.x * d.x + d.y * d.y + d.z * d.z) or 1.0
            if dist > rng:
                return False
            f = unreal.MathLibrary.get_forward_vector(rot)
            return (f.x * d.x + f.y * d.y + f.z * d.z) / dist > thr
        except Exception:  # noqa
            return False

    # ---- 電話の下のふた ----
    def open_hatch(self):
        if not self.has_key:
            screen(self.world, "ふたには鍵がかかっている（小さな鍵がいる）", (255, 200, 150), 3.0)
            return
        self.hatch_open = True
        self.has_memo = True
        self.coins += 1
        screen(self.world, "ふたが開いた。メモと10円を見つけた（10円 %d枚）" % self.coins, (255, 240, 160), 5.0)
        log("電話の下のふたを開けました（メモ・10円③）")
        self.after_read = lambda: self.on_flag("ふた")
        self.begin_read("M_KDReadMemo", 1.33)

    # ---- 電話 ----
    PHONE_KEYS = [("Zero", "0"), ("One", "1"), ("Two", "2"), ("Three", "3"), ("Four", "4"), ("Five", "5"), ("Six", "6"), ("Seven", "7"), ("Eight", "8"), ("Nine", "9"),
                  ("NumPadZero", "0"), ("NumPadOne", "1"), ("NumPadTwo", "2"), ("NumPadThree", "3"), ("NumPadFour", "4"), ("NumPadFive", "5"), ("NumPadSix", "6"), ("NumPadSeven", "7"), ("NumPadEight", "8"), ("NumPadNine", "9")]

    def begin_phone(self):
        eye, _r = self.eye_info()
        try:
            self.pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, self.phone_point()))
        except Exception as e:  # noqa
            log("  (電話のほうを向けません) %s" % e)
        self.lock_input(True)
        self.state, self.state_t = "PHONE", 0.0
        self.digits = ""
        log("電話を使い始めました")

    def end_phone(self):
        self.lock_input(False)
        self.state, self.state_t = "TRAPPED", 0.0

    def tick_phone(self, dt):
        try:
            for name, ch in self.PHONE_KEYS:
                if self.pc.was_input_key_just_pressed(self._key(name)) and len(self.digits) < 8:
                    self.digits += ch
            if self.pc.was_input_key_just_pressed(self._key("BackSpace")):
                self.digits = self.digits[:-1]
            if self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self._key("Q")):
                self.end_phone()
                return
            if self.state_t > 0.3 and (self.pc.was_input_key_just_pressed(self._key("Enter")) or self.pc.was_input_key_just_pressed(self._key("E"))) and self.digits:
                num, self.digits = self.digits, ""
                self.phone_call(num)
        except Exception as e:  # noqa
            log("  (電話のキーを読めません) %s" % e)
        if int(self.t * 8) != getattr(self, "_ph_k", -1):
            self._ph_k = int(self.t * 8)
            txt = "電話  番号: %s_   10円: %d枚   [0〜9] 入れる  [Enter]か[E] かける  [BackSpace] 消す  [Q] やめる" % (self.digits, self.coins)
            try:
                unreal.SystemLibrary.print_string(self.world, txt, True, False, unreal.LinearColor(0.8, 1, 1, 1), 0.3, "KD_PHONE_UI")
            except Exception:  # noqa
                pass

    def pay(self, n):
        """10円を払う。足りないとき、0115 だけは、返却口から1枚落ちてくる（詰み防止）"""
        if self.coins >= n:
            self.coins -= n
            return True
        return False

    def phone_call(self, num):
        log("電話をかけました: %s（10円 %d枚）" % (num, self.coins))
        free = {"110", "119"}
        msgs = {"117": ("ポーン…「7月14日 午前0時を お知らせします」", (200, 230, 255)),
                "177": ("「神狩村は…赤い雨です」", (255, 160, 160)),
                "104": ("「お調べします…張り紙は 貼られた順に」", (200, 230, 255))}
        if num in free:
            first = not self.lcd_seen
            screen(self.world, "（声はない。……液晶に文字が出た）  ソト ヒダリ ミギ ヒダリ", (255, 120, 120), 7.0)
            if first:
                self.lcd_seen = True
                self.on_flag("液晶")
            return
        if num == "0115":
            if not self.pay(PHONE_COIN_COST):
                self.coins += 1
                screen(self.world, "チャリン…返却口から10円が落ちてきた（10円 %d枚）。もう一度かけてみる" % self.coins, (255, 220, 150), 5.0)
                return
            screen(self.world, "「……あの日を……おして……」（女の声）", (255, 120, 120), 8.0)
            if not self.called_0115:
                self.called_0115 = True
                self.on_flag("電話")
            return
        if num == "0714":
            if self.called_0115:
                screen(self.world, "カチッ。液晶に「2 15 4 9」の文字が、一瞬だけ出た", (255, 120, 120), 8.0)
                if not self.dialed_0714:
                    self.dialed_0714 = True
                    self.on_flag("0714")
            else:
                screen(self.world, "ツー、ツー……（つながらない）", (180, 180, 180), 3.0)
            return
        if num in msgs:
            if not self.pay(PHONE_COIN_COST):
                screen(self.world, "10円が足りない", (255, 200, 150), 3.0)
                return
            screen(self.world, msgs[num][0] + "（10円 %d枚）" % self.coins, msgs[num][1], 8.0)
            return
        screen(self.world, "ツー、ツー……（つながらない）", (180, 180, 180), 3.0)

    def lock_input(self, on):
        for fn in ("set_ignore_move_input", "set_ignore_look_input"):
            try:
                getattr(self.pc, fn)(on)
            except Exception as e:  # noqa
                log("  (%s できません) %s" % (fn, e))

    def begin_safe(self):
        """金庫のダイヤルを回す場面。歩く・見回すを止めて、ダイヤルのほうを向く"""
        eye, _rot = self.eye_info()
        try:
            tgt = (self.dial_knob or self.dial_body).get_actor_location()
            self.pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, tgt))
        except Exception as e:  # noqa
            log("  (ダイヤルのほうを向けません) %s" % e)
        self.lock_input(True)
        self.state, self.state_t = "SAFE", 0.0
        self.dial_raw = float(self.dial_value)
        self.dial_disp = float(self.dial_value)
        self.dial_dir, self.dial_entries, self.dial_acc = None, [], 0.0
        self.key_left, self.key_right, self.key_quit = unreal.Key(), unreal.Key(), unreal.Key()
        self.key_left.set_editor_property("key_name", "Left")
        self.key_right.set_editor_property("key_name", "Right")
        self.key_quit.set_editor_property("key_name", "Q")
        log("金庫のダイヤルを回し始めました")

    def end_safe(self):
        self.lock_input(False)
        self.state, self.state_t = "TRAPPED", 0.0

    def set_dial(self, v):
        old = self.dial_value
        self.dial_value = v % 100
        d = self.dial_value - old
        if d > 50:
            d -= 100
        elif d < -50:
            d += 100
        self.dial_raw = getattr(self, "dial_raw", float(old)) + d            # 100を越えても、つながって回る数
        if not hasattr(self, "dial_disp"):
            self.dial_disp = float(old)

    def apply_knob(self):
        if self.dial_knob is not None and self.dial_knob_rot is not None:
            r = self.dial_knob_rot
            try:
                self.dial_knob.set_actor_rotation(unreal.Rotator(r.roll, r.pitch + DIAL_SIGN * getattr(self, "dial_disp", 0.0) * 3.6, r.yaw), False)
            except Exception as e:  # noqa
                log("  (ダイヤルを回せません) %s" % e)

    def tick_dial_anim(self, dt):
        """つまみの見た目を、目標の数字へ、なめらかに追いかけさせる（カクカクしない）"""
        raw = getattr(self, "dial_raw", None)
        if raw is None:
            return
        disp = getattr(self, "dial_disp", raw)
        if abs(raw - disp) > 0.01:
            disp += (raw - disp) * min(1.0, dt * 22.0)
            self.dial_disp = disp
            self.apply_knob()

    def tick_fov(self, dt):
        """ダイヤルを回す間は、視野をせまくして、アップにする（終わると元に戻す）"""
        try:
            cam = getattr(self, "_cam", None)
            if cam is None:
                cam = self.pawn.get_component_by_class(unreal.CameraComponent) if self.pawn is not None else None
                self._cam = cam or False
                if cam:
                    self.fov_base = float(cam.get_editor_property("field_of_view"))
                    self.fov_cur = self.fov_base
            if not cam:
                return
            tgt = DIAL_FOV if self.state == "SAFE" else self.fov_base
            if tgt != getattr(self, "_fov_log", None):
                self._fov_log = tgt
                log("視野（アップ）: %.0f → %.0f にします" % (self.fov_cur, tgt))
            if abs(self.fov_cur - tgt) > 0.05:
                self.fov_cur += (tgt - self.fov_cur) * min(1.0, dt / max(0.05, DIAL_ZOOM_TIME) * 3.0)
                cam.set_editor_property("field_of_view", self.fov_cur)
        except Exception as e:  # noqa
            if not getattr(self, "_fov_err", False):
                self._fov_err = True
                log("  (視野を変えられません) %s" % e)

    def clamp_in_booth(self, loc):
        """閉じ込められている間は、壁の外へ出られない（自分で動かす歩きが、当たり判定を無視して、壁をすり抜けるため）"""
        if self.state not in ("CLOSING", "TRAPPED", "SAFE", "PHONE", "READING") or self.pawn is None:
            return
        th = math.radians(self.front_yaw)
        nx, ny = -math.sin(th), math.cos(th)         # 入口の向き（奥行き）
        tx, ty = math.cos(th), math.sin(th)          # 横
        rx, ry = loc.x - self.cx, loc.y - self.cy
        tn, tt = rx * nx + ry * ny, rx * tx + ry * ty
        ln, lt = max(12.0, self.half_n - TRAP_MARGIN), max(12.0, self.half_t - TRAP_MARGIN)
        cn, ct = max(-ln, min(ln, tn)), max(-lt, min(lt, tt))
        if abs(cn - tn) > 0.1 or abs(ct - tt) > 0.1:
            nxp, nyp = self.cx + nx * cn + tx * ct, self.cy + ny * cn + ty * ct
            self.pawn.set_actor_location(unreal.Vector(nxp, nyp, loc.z), False, False)

    def tick_safe(self, dt):
        try:
            down_l = self.pc.is_input_key_down(self.key_left)
            down_r = self.pc.is_input_key_down(self.key_right)
            if down_l != down_r:
                self.dial_acc += dt
                if self.dial_acc >= DIAL_STEP_TIME:
                    self.dial_acc = 0.0
                    self.dial_dir = "L" if down_l else "R"
                    self.set_dial(self.dial_value + (1 if down_l else -1))
            else:
                self.dial_acc = DIAL_STEP_TIME
            if self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self.key_quit):
                self.end_safe()
                return
            if self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self.key_e):
                self.safe_enter()
        except Exception as e:  # noqa
            log("  (金庫の操作を読めません) %s" % e)
        if int(self.t * 8) != getattr(self, "_safe_k", -1):
            self._safe_k = int(self.t * 8)
            done = " → ".join("%s%d" % (("左" if d == "L" else "右"), v) for d, v in self.dial_entries) or "なし"
            txt = "金庫  数字 %02d（%s）   [←→] 回す  [%s] 決める  [Q] やめる   決めた: %s" % (self.dial_value, {"L": "左", "R": "右"}.get(self.dial_dir, "-"), ENTER_KEY, done)
            try:
                unreal.SystemLibrary.print_string(self.world, txt, True, False, unreal.LinearColor(0.8, 1, 0.8, 1), 0.3, "KD_SAFE_UI")
            except Exception:  # noqa
                pass

    def safe_enter(self):
        if self.dial_dir is None:
            screen(self.world, "先にダイヤルを回してから、決めてください", (255, 200, 150), 2.0)
            return
        self.dial_entries.append((self.dial_dir, self.dial_value))
        k = len(self.dial_entries)
        want = [tuple(c) for c in SAFE_CODE]
        if tuple(self.dial_entries[-1]) != want[k - 1]:
            screen(self.world, "カチ…（はずれ。最初から）", (255, 120, 120), 2.5)
            log("金庫：はずれ %s" % (self.dial_entries,))
            self.dial_entries = []
            return
        screen(self.world, "カチッ（%d/%d）" % (k, len(want)), (200, 255, 200), 1.5)
        if k == len(want):
            self.safe_open = True
            self.has_key = True
            self.coins += 1
            self.end_safe()
            screen(self.world, "ガチャン。金庫が開いた！ 小さな鍵と10円を手に入れた（10円 %d枚）" % self.coins, (255, 240, 160), 6.0)
            log("金庫が開きました（鍵・10円②）")
            self.on_flag("金庫")

    def diag_floor(self, loc):
        """足元の地面を調べる：何の上に立っているか、坂の角度は何度か"""
        try:
            res = unreal.SystemLibrary.line_trace_single(self.world, unreal.Vector(loc.x, loc.y, loc.z), unreal.Vector(loc.x, loc.y, loc.z - 400.0),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [self.pawn], unreal.DrawDebugTrace.NONE, True)
            hit = res[1] if isinstance(res, tuple) and len(res) > 1 and not isinstance(res[1], (bool, float, int)) else res
            if hit is None or isinstance(hit, bool):
                log("診断: 足元に何もありません（地面なし？）")
                return
            nrm = pt = act = None
            try:                                  # UE 5.8: to_tuple() の順番 = (…, location, impact_point, normal, impact_normal, phys_mat, hit_actor, …)
                tp = hit.to_tuple()
                pt, nrm, act = tp[5], tp[7], tp[9]
            except Exception:
                for nm_n, nm_p, nm_a in (("impact_normal", "impact_point", "hit_actor"), ("impact_normal", "impact_point", "actor")):
                    try:
                        nrm = getattr(hit, nm_n, None) or hit.get_editor_property(nm_n)
                        pt = getattr(hit, nm_p, None) or hit.get_editor_property(nm_p)
                        act = getattr(hit, nm_a, None)
                        break
                    except Exception:
                        continue
            if nrm is None or pt is None:
                log("診断: 足元に当たりました（細かい情報は読めません）")
                return
            ang = math.degrees(math.acos(max(-1.0, min(1.0, nrm.z))))
            log("診断: 足元の地面: %s 高さ=%.0f 坂の角度=%.0f度（歩けるのは %.0f度まで）" % (label_of(act) if act else "?", pt.z, ang, WALKABLE_ANGLE if WALKABLE_ANGLE > 0 else 44.8))
        except Exception as e:  # noqa
            log("診断: 足元を調べられません: %s" % e)

    def free_from_big_colliders(self, loc):
        """体が、大きすぎる物（取り込みの倍率ミスなど）の中に入っていると、歩けず、外へ押し出される。体を含む大きさの物を探して、ログに出す。このゲームで置いた物（掲示板・金庫・10円・張り紙）なら、当たり判定を切る"""
        mine = ("Board_", "DialSafe_", "Coin_", "Poster_", "Paper_", "KD_", "TubeLight", "Ghost")
        try:
            for a in unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.Actor):
                if a == self.pawn:
                    continue
                o, e = a.get_actor_bounds(False)
                if abs(loc.x - o.x) < e.x and abs(loc.y - o.y) < e.y and abs(loc.z - o.z) < e.z:
                    nm = label_of(a)
                    big = max(e.x, e.y, e.z) * 2.0
                    if nm.startswith(mine) and big > 400.0:
                        a.set_actor_enable_collision(False)
                        log("診断: 体が、大きすぎる物の中にいたので、当たり判定を切りました: %s（大きさ約%.0fcm・倍率を確かめてください）" % (nm, big))
                    elif big > 3000.0:
                        log("診断: 体を含む大きな物: %s（大きさ約%.0fcm）" % (nm, big))
                    else:
                        log("診断: 体を含む物: %s（大きさ約%.0fcm）" % (nm, big))
        except Exception as e:  # noqa
            log("  (大きな物の確認でエラー) %s" % e)

    def tick_arrows(self):
        """矢印キーで歩く（W A S D が使えないテンプレ用）。歩く場面（外・中）だけ"""
        if not ARROW_MOVE or self.state not in ("WALK", "TRAPPED") or not self.is_char or getattr(self, "manual_on", False) or MANUAL_WALK == "on":
            return
        try:
            f = (1.0 if self.pc.is_input_key_down(self._key("Up")) else 0.0) - (1.0 if self.pc.is_input_key_down(self._key("Down")) else 0.0)
            r = (1.0 if self.pc.is_input_key_down(self._key("Right")) else 0.0) - (1.0 if self.pc.is_input_key_down(self._key("Left")) else 0.0)
            if f == 0.0 and r == 0.0:
                return
            rot = unreal.Rotator(0, 0, self.pc.get_control_rotation().yaw)
            fw = unreal.MathLibrary.get_forward_vector(rot)
            rt = unreal.MathLibrary.get_right_vector(rot)
            if f != 0.0:
                self.pawn.add_movement_input(fw, f, False)
            if r != 0.0:
                self.pawn.add_movement_input(rt, r, False)
        except Exception as e:  # noqa
            if not getattr(self, "_arrow_err", False):
                self._arrow_err = True
                log("  (矢印キーで歩けません) %s" % e)

    def tick_manual(self, dt):
        """キャラが動かないときの、自分で動かす歩き：WASD と矢印。向いている方向へ、WALK_SPEED で進める。
        歩く人（Character）には、動きの部品（CharacterMovement）の速度を直接入れる（地面・坂をなめらかに進む）。それでも進まなければ、体を直接動かす"""
        if MANUAL_WALK == "off" or self.state not in ("WALK", "TRAPPED"):
            return
        if MANUAL_WALK == "auto" and not getattr(self, "manual_on", False):
            return
        try:
            kd = lambda n: self.pc.is_input_key_down(self._key(n))
            f = (1.0 if (kd("W") or kd("Up")) else 0.0) - (1.0 if (kd("S") or kd("Down")) else 0.0)
            r = (1.0 if kd("D") or kd("Right") else 0.0) - (1.0 if kd("A") or kd("Left") else 0.0)
            speed = max(WALK_SPEED, 300.0)
            mvc = self.pawn.get_component_by_class(unreal.CharacterMovementComponent) if self.is_char and not getattr(self, "manual_offset", False) else None
            if f == 0.0 and r == 0.0:
                if mvc is not None and getattr(self, "_manual_moving", False):
                    v = mvc.get_editor_property("velocity")
                    mvc.set_editor_property("velocity", unreal.Vector(0.0, 0.0, v.z))                 # キーを離したら、すっと止まる
                self._manual_moving = False
                return
            rot = unreal.Rotator(0, 0, self.pc.get_control_rotation().yaw)
            fw = unreal.MathLibrary.get_forward_vector(rot)
            rt = unreal.MathLibrary.get_right_vector(rot)
            dx, dy = fw.x * f + rt.x * r, fw.y * f + rt.y * r
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
            self._manual_moving = True
            p0 = self.pawn.get_actor_location()
            if mvc is not None:
                v = mvc.get_editor_property("velocity")
                mvc.set_editor_property("velocity", unreal.Vector(dx * speed, dy * speed, v.z))
                self._man_t = getattr(self, "_man_t", 0.0) + dt
                if self._man_t > 1.0:                                                  # 1秒たっても進まないなら、体を直接動かす方式に変える
                    if math.hypot(p0.x - getattr(self, "_man_p", (p0.x, p0.y))[0], p0.y - getattr(self, "_man_p", (p0.x, p0.y))[1]) < 20.0:
                        self.manual_offset = True
                        log("速度を入れても進まないので、体を直接動かす方式に変えました")
                    self._man_t, self._man_p = 0.0, (p0.x, p0.y)
                elif not hasattr(self, "_man_p"):
                    self._man_p = (p0.x, p0.y)
                return
            step = speed * dt
            delta = unreal.Vector(dx * step, dy * step, 0.0)
            self.pawn.add_actor_world_offset(delta, True, False)
            p1 = self.pawn.get_actor_location()
            if math.hypot(p1.x - p0.x, p1.y - p0.y) < step * 0.3:
                self.pawn.add_actor_world_offset(unreal.Vector(delta.x, delta.y, 0.0), False, True)
        except Exception as e:  # noqa
            if not getattr(self, "_man_err", False):
                self._man_err = True
                log("  (自分で動かす歩きが使えません) %s" % e)

    def tick_unstuck(self, loc, dt):
        """歩くキーを押しているのに、ほとんど動かないとき（地面に埋まっている）は、すこし持ち上げる。さいしょの数秒だけ見る"""
        if self.state != "WALK" or getattr(self, "lifts", 0) >= 8 or getattr(self, "manual_on", False):
            return
        try:
            down = any(self.pc.is_input_key_down(self._key(k)) for k in ("W", "A", "S", "D", "Up", "Down", "Left", "Right"))
        except Exception:  # noqa
            return
        if not down:
            self._stuck_t, self._stuck_p = 0.0, (loc.x, loc.y)
            return
        self._stuck_t = getattr(self, "_stuck_t", 0.0) + dt
        if self._stuck_t < 1.2:
            return
        px, py = getattr(self, "_stuck_p", (loc.x, loc.y))
        moved = math.hypot(loc.x - px, loc.y - py)
        self._stuck_t, self._stuck_p = 0.0, (loc.x, loc.y)
        if moved < 8.0 and MANUAL_WALK == "auto" and not getattr(self, "manual_on", False):
            self.manual_on = True
            log("歩くキーを押しても動かないので、自分で動かす歩きに切り替えました（MANUAL_WALK）")
            return
        if moved < 8.0:
            self.lifts = getattr(self, "lifts", 0) + 1
            self.pawn.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z + 120.0), False, True)
            log("歩けない（埋まっている？）ので、持ち上げました %d 回目: z=%.0f → %.0f" % (self.lifts, loc.z, loc.z + 120.0))

    def _key(self, name):
        k = getattr(self, "_keys", None)
        if k is None:
            k = self._keys = {}
        if name not in k:
            kk = unreal.Key()
            kk.set_editor_property("key_name", name)
            k[name] = kk
        return k[name]

    def tick_hud(self):
        """持ち物（10円）を、画面のすみに出す"""
        if int(self.t * 2) == getattr(self, "_hud_k", -1):
            return
        self._hud_k = int(self.t * 2)
        try:
            unreal.SystemLibrary.print_string(self.world, "10円: %d枚" % self.coins, True, False, unreal.LinearColor(1, 0.85, 0.5, 1), 0.6, "KD_HUD")
        except Exception:  # noqa
            pass

    def looking_at(self, actor, rng):
        """目の前（まっすぐ見ている向き）に、この物があるか（3次元）"""
        eye, rot = self.eye_info()
        p = actor.get_actor_location()
        d = unreal.Vector(p.x - eye.x, p.y - eye.y, p.z - eye.z)
        dist = math.sqrt(d.x * d.x + d.y * d.y + d.z * d.z) or 1.0
        if dist > rng:
            return False
        f = unreal.MathLibrary.get_forward_vector(rot)
        return (f.x * d.x + f.y * d.y + f.z * d.z) / dist > 0.93

    def prompt_item(self, text, key):
        if int(self.t * 4) == getattr(self, "_p_" + key, -1):
            return
        setattr(self, "_p_" + key, int(self.t * 4))
        try:
            unreal.SystemLibrary.print_string(self.world, text, True, False, unreal.LinearColor(1, 1, 0.6, 1), 0.4, "KD_" + key)
        except Exception:  # noqa
            pass

    def tick_items(self, loc):
        """10円を拾う（外）／本を開く（中）"""
        try:
            pressed = self.pc.was_input_key_just_pressed(self.key_e)
        except Exception:  # noqa
            pressed = False
        if self.coin is not None and self.state == "WALK" and self.looking_at(self.coin, ITEM_RANGE):
            self.prompt_item("[%s] 10円を拾う" % ENTER_KEY, "COIN")
            if pressed:
                self.coin.set_actor_hidden_in_game(True)
                self.coin.set_actor_location(unreal.Vector(0, 0, -50000), False, False)           # 当たり判定ごと遠くへ
                if self.coin_light is not None:
                    self.coin_light.set_actor_hidden_in_game(True)
                self.coin = None
                self.coins += 1
                screen(self.world, "10円を拾った（%d枚）" % self.coins, (255, 220, 150), 3.0)
                log("10円を拾いました: %d枚" % self.coins)
                return
        if self.state == "TRAPPED":
            hp, pp = self.hatch_point(), self.phone_point()
            if not self.hatch_open and self.looking_at_pt(hp, ITEM_RANGE + 60.0, 0.95):
                self.prompt_item("[%s] 電話の下のふたを開ける" % ENTER_KEY, "HATCH")
                if pressed:
                    self.open_hatch()
                    return
            elif self.looking_at_pt(pp, ITEM_RANGE + 60.0, 0.93):
                self.prompt_item("[%s] 電話をかける" % ENTER_KEY, "PHONE")
                if pressed:
                    self.begin_phone()
                    return
        if self.dial_body is not None and not self.safe_open and self.state == "TRAPPED" and self.looking_at(self.dial_knob or self.dial_body, ITEM_RANGE):
            self.prompt_item("[%s] 金庫のダイヤルを回す" % ENTER_KEY, "SAFE")
            if pressed:
                self.begin_safe()
                return
        if self.book is not None and self.state == "TRAPPED" and self.looking_at(self.book, ITEM_RANGE):
            self.prompt_item("[%s] 本を開く" % ENTER_KEY, "BOOK")
            if pressed:
                self.begin_read("M_KDReadBook", 0.8)
                if not getattr(self, "book_done", False):
                    self.book_done = True
                    self.after_read = lambda: self.on_flag("本")
                log("本を開きました")

    def eye_info(self):
        """目の位置と、いま見ている向き（まっすぐ水平にした向き）"""
        rot = self.pc.get_control_rotation()
        try:
            eye = self.pc.player_camera_manager.get_camera_location()
        except Exception:  # noqa
            eye = self.pawn.get_actor_location()
        return eye, rot

    def tick_news(self, loc):
        if self.news is None or self.read_plane is None:
            return
        np_ = self.news.get_actor_location()
        dx, dy = np_.x - loc.x, np_.y - loc.y
        dist = math.hypot(dx, dy)
        if dist > READ_RANGE:
            return
        fwd = unreal.MathLibrary.get_forward_vector(self.pc.get_control_rotation())
        fl = math.hypot(fwd.x, fwd.y) or 1.0
        if (fwd.x * dx + fwd.y * dy) / (fl * (dist or 1.0)) < 0.8:          # だいたい新聞のほうを向いているときだけ
            return
        if int(self.t * 4) != getattr(self, "_prompt_k2", -1):
            self._prompt_k2 = int(self.t * 4)
            try:
                unreal.SystemLibrary.print_string(self.world, "[%s] 新聞を手に取る" % ENTER_KEY, True, False, unreal.LinearColor(1, 1, 0.6, 1), 0.4, "KD_PROMPT2")
            except Exception:  # noqa
                pass
        try:
            if self.pc.was_input_key_just_pressed(self.key_e):
                self.begin_read()
        except Exception as e:  # noqa
            log("  (Eキーを読めません) %s" % e)

    def begin_read(self, mat_name="M_KDRead", aspect=1.0):
        """新聞・本を目の前に出す。歩く・見回すを止めて、Eでとじる"""
        self.read_return = self.state
        self.after_read = getattr(self, "after_read", None) if mat_name != "M_KDRead" else None
        try:
            m = unreal.EditorAssetLibrary.load_asset("/Game/KoushuDenwa/Materials/" + mat_name)
            if m is not None:
                self.read_plane.get_component_by_class(unreal.StaticMeshComponent).set_material(0, m)
        except Exception as e:  # noqa
            log("  (読む絵を入れ替えられません) %s" % e)
        eye, rot = self.eye_info()
        yaw = rot.yaw
        try:
            self.pc.set_control_rotation(unreal.Rotator(0, 0, yaw))                 # 見る向きを水平にして、紙が正面に見えるように
        except Exception:  # noqa
            pass
        th = math.radians(yaw)
        loc = unreal.Vector(eye.x + math.cos(th) * READ_DIST, eye.y + math.sin(th) * READ_DIST, eye.z)
        self.read_plane.set_actor_location(loc, False, False)
        self.read_plane.set_actor_rotation(unreal.Rotator(0, 0, yaw + 90.0), False)
        self.read_plane.set_actor_scale3d(unreal.Vector(READ_SIZE * aspect / 50.0, 1.0, READ_SIZE / 70.0))
        self.read_plane.set_actor_hidden_in_game(False)
        for fn in ("set_ignore_move_input", "set_ignore_look_input"):
            try:
                getattr(self.pc, fn)(True)
            except Exception as e:  # noqa
                log("  (%s できません) %s" % (fn, e))
        self.state, self.state_t = "READING", 0.0
        screen(self.world, "[%s] とじる" % ENTER_KEY, (255, 255, 200), 3.0)
        log("新聞を手に取りました（目の前 %.0fcm・大きさ %.0fcm）" % (READ_DIST, READ_SIZE))

    def tick_reading(self):
        try:
            if self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self.key_e):
                self.read_plane.set_actor_hidden_in_game(True)
                for fn in ("set_ignore_move_input", "set_ignore_look_input"):
                    try:
                        getattr(self.pc, fn)(False)
                    except Exception:  # noqa
                        pass
                self.state, self.state_t = getattr(self, "read_return", "WALK"), 0.0
                log("閉じました")
                cb, self.after_read = getattr(self, "after_read", None), None
                if cb is not None:
                    cb()
        except Exception as e:  # noqa
            log("  (Eキーを読めません) %s" % e)

    def begin_enter(self):
        self.state, self.state_t = "ENTERING", 0.0
        self.enter_stage = 0
        self.play("door_open")
        self.fade(True, ENTER_FADE_OUT)
        log("入ります（暗転＋ドアの音）")

    def tick_entering(self, dt):
        t = self.state_t
        if self.enter_stage == 0 and t >= ENTER_FADE_OUT + 0.4:             # 真っ暗になってから、中へ移す
            self.enter_stage = 1
            th = math.radians(self.front_yaw)
            nx, ny = -math.sin(th), math.cos(th)
            loc = self.pawn.get_actor_location()
            self.pawn.set_actor_location(unreal.Vector(self.cx - nx * 8.0, self.cy - ny * 8.0, loc.z), False, False)
            # 奥の壁（電話機）の方を向く：入口の反対向き
            yaw = math.degrees(math.atan2(-ny, -nx))
            try:
                self.pc.set_control_rotation(unreal.Rotator(0, 0, yaw))
            except Exception as e:  # noqa
                log("  (向きを変えられません) %s" % e)
        elif self.enter_stage == 1 and t >= ENTER_FADE_OUT + 1.3:
            self.enter_stage = 2
            self.play("door_close")
        elif self.enter_stage == 2 and t >= ENTER_FADE_OUT + ENTER_BLACK:
            self.enter_stage = 3
            self.fade(False, ENTER_FADE_IN)
            screen(self.world, "（とじこめられた）", (255, 120, 120), 4.0)
        elif self.enter_stage == 3 and t >= ENTER_FADE_OUT + ENTER_BLACK + ENTER_FADE_IN:
            self.state, self.state_t = "TRAPPED", 0.0
            self.start_trapped()
            log("閉じ込め開始")

    def begin_close(self):
        self.state, self.state_t = "CLOSING", 0.0
        log("ドアを閉めます")
        self.fade(True, 0.12)

    def update_flashlight(self):
        if self.pc is None or self.flash is None:
            return
        try:
            if self.pc.was_input_key_just_pressed(self.key):
                self.set_flash(not self.flash_on)
            rot = self.pc.get_control_rotation()
            loc = self.pawn.get_actor_location()
            self.flash.set_actor_location_and_rotation(loc, rot, False, False)
        except Exception as e:  # noqa
            self.errors += 1
            if self.errors < 3:
                log("  (懐中電灯の更新に失敗) %s" % e)

    # ---- 閉じ込められてから：謎を1つ解く（フラグがたつ）たびに、演出を1つだけ出す ----
    # 演出の持ち札：強さ 0〜3 のそれぞれに「幽霊が近づく」「張り紙が貼られる」の2種類（合計8つ）。
    # 謎が進むほど強い札を使い、使った札は二度と出さない（あとで出せる演出がなくならないよう、1回の謎で出すのは1つだけ）。
    # 謎が進まないまま時間がたつと、持ち札を使わずに「幽霊がじわじわ近づく」圧力だけが増える。
    def start_trapped(self):
        self.trapped_started = True
        self.set_flash_scale(FLASH_INSIDE * FLASH_OUTSIDE)
        self.steps = []
        self.step_i = 0
        self.pending = []
        self.used = set()
        self.last_type = None
        self.solved = 0
        self.hint_done = False
        self.pressure_t = 0.0
        self.pressure_n = 0
        self.level_now = 0
        self.posters_hide()                                      # 手がかり以外の張り紙は、入った時点では1枚も出さない
        log("張り紙: 手がかり=%s / 隠した枚数=%d" % ("あり" if self.hint is not None else "なし", len(self.posters) + (1 if self.eye is not None else 0)))
        screen(self.world, "謎 0/%d（%s キーで、解いたことにできます）" % (PUZZLE_COUNT, FLAG_KEY), (200, 255, 200), 6.0)

    def event_steps(self, typ, level, spot=None):
        n_hold = min(level, len(GHOST_HOLD) - 1)
        if typ == "ghost":
            sp = level if spot is None else spot
            return [("flicker", FLICKER_TIME, None, None),
                    ("dark", DARK_TIME, self.hide_all, lambda sp=sp: self.ghost_scene(sp)),
                    ("idle", GHOST_HOLD[n_hold], None, None),
                    ("flicker", FLICKER_TIME, None, None),
                    ("dark", DARK_TIME, self.ghost_hide, None)]
        return [("flicker", FLICKER_TIME, None, None),
                ("dark", DARK_TIME, self.hide_all, lambda: self.poster_scene_begin(level)),
                ("posters", POSTER_HOLD[n_hold], None, None),
                ("flicker", FLICKER_TIME, None, None),
                ("dark", DARK_TIME, self.posters_hide, None)]

    def run_steps(self, steps):
        if self.step_i < len(self.steps):                 # 演出の最中なら、終わってから
            self.pending.append(steps)
            return
        self.steps = steps
        self.step_i = -1
        self.next_step()

    def on_flag(self, name="?"):
        """謎を1つ解いた（フラグがたった）。演出を1つ選んで出す"""
        if self.state not in ("TRAPPED", "PHONE", "SAFE", "READING") or not getattr(self, "trapped_started", False):
            log("(閉じ込められていないので、フラグは無視) %s" % name)
            return
        if self.state != "TRAPPED":                              # 電話・金庫・読んでいる最中は、終わってから演出を出す
            self.deferred = getattr(self, "deferred", []) + [name]
            return
        self.solved += 1
        self.pressure_t = 0.0
        n_lv = len(GHOST_SPOTS)
        level = min(n_lv - 1, (self.solved - 1) * n_lv // max(1, PUZZLE_COUNT))
        self.level_now = level
        choice = None
        for lv in range(level, n_lv):                      # 今の強さの札から探す。なければ、1つ強い札へ
            order = ["ghost", "poster"]
            if self.last_type == "ghost":
                order = ["poster", "ghost"]
            elif self.last_type is None:
                random.shuffle(order)
            for t in order:
                if (t, lv) not in self.used:
                    choice = (t, lv)
                    break
            if choice:
                break
        log("謎 %d/%d（%s）→ 演出: %s" % (self.solved, PUZZLE_COUNT, name, choice))
        screen(self.world, "謎 %d/%d" % (self.solved, PUZZLE_COUNT), (200, 255, 200), 3.0)
        if choice is None:
            return
        self.used.add(choice)
        self.last_type = choice[0]
        self.run_steps(self.event_steps(choice[0], choice[1]))

    def pressure(self):
        """謎が進まないまま時間がたった：持ち札は使わず、幽霊が1段階ずつ近づく。近づききったら失敗"""
        self.pressure_n += 1
        spot = min(len(GHOST_SPOTS) - 1, self.level_now + self.pressure_n)
        log("圧力 %d（幽霊の位置 %d）" % (self.pressure_n, spot))
        if self.level_now + self.pressure_n > len(GHOST_SPOTS):
            self.run_steps([("flicker", FLICKER_TIME, None, None), ("dark", DARK_TIME, self.ghost_hide, self.begin_dead)])
            return
        self.run_steps(self.event_steps("ghost", self.level_now, spot))

    def hide_all(self):
        self.ghost_hide()
        self.posters_hide()

    def ghost_scene(self, r):
        self.stage = r + 1
        gx, gy = GHOST_SPOTS[min(r, len(GHOST_SPOTS) - 1)]
        th = math.radians(self.front_yaw)               # 入口の向きに合わせて回す（入口が +Y のとき 0 度）
        self.ghost_show(self.cx + gx * math.cos(th) - gy * math.sin(th), self.cy + gx * math.sin(th) + gy * math.cos(th))
        screen(self.world, GHOST_SUBS[min(r, len(GHOST_SUBS) - 1)], (200, 220, 255), 4.0)
        log("幽霊の場面 %d" % (r + 1))

    def poster_scene_begin(self, r):
        self.stage = r + 1
        frac = POSTER_FRAC[min(r, len(POSTER_FRAC) - 1)]
        self.poster_target = int(math.ceil(len(self.posters) * frac))
        self.poster_shown = 0
        self.poster_round = r
        screen(self.world, "（紙が……貼られていく）", (255, 160, 160), 3.0)
        try:
            a0 = self.posters[0][1]
            o, e = a0.get_actor_bounds(False)
            log("  張り紙の確認: %s 位置=(%.0f,%.0f,%.0f) 大きさ=(%.0f,%.0f,%.0f)cm ボックス中心=(%.0f,%.0f)" % (self.posters[0][0], o.x, o.y, o.z, e.x * 2, e.y * 2, e.z * 2, self.cx, self.cy))
        except Exception as ex:  # noqa
            log("  (張り紙の確認ができません) %s" % ex)
        log("張り紙の場面 %d（%d枚）" % (r + 1, self.poster_target))

    def posters_hide(self):
        for _k, a in self.posters:
            a.set_actor_hidden_in_game(True)
        if self.eye is not None:
            a = self.eye
            a.set_actor_hidden_in_game(True)
        self.poster_shown = 0
        self.poster_target = 0

    def poster_progress(self, step_t):
        want = min(self.poster_target, int(step_t / POSTER_STEP) + 1)
        while self.poster_shown < want:
            self.posters[self.poster_shown][1].set_actor_hidden_in_game(False)
            self.poster_shown += 1
        if self.eye is not None and self.poster_round >= 2 and self.poster_shown >= self.poster_target:
            self.eye.set_actor_hidden_in_game(False)

    def next_step(self):
        if self.step_i >= 0 and self.step_i < len(self.steps):
            exit_fn = self.steps[self.step_i][3]
            if exit_fn is not None:
                exit_fn()
        self.step_i += 1
        if self.step_i >= len(self.steps):
            if self.pending and self.state == "TRAPPED":          # 待っていた演出があれば、つづけて出す
                nxt = self.pending.pop(0)
                self.steps = nxt
                self.step_i = -1
                self.next_step()
            return
        typ, ln, enter_fn, _ex = self.steps[self.step_i]
        self.step_t = 0.0
        self.flicker_next = 0.0
        if typ == "dark":
            self.set_lights(0.0)
            self.blackout(DARK_BLACK)
        if enter_fn is not None:
            enter_fn()

    def tick_trapped(self, dt):
        try:
            if self.pc.was_input_key_just_pressed(self.key_flag):
                self.on_flag("テストキー")
        except Exception:  # noqa
            pass
        if self.step_i >= len(self.steps):                    # 演出がない間：静か（ときどき光がゆれる）
            self.set_lights(1.0 if self.t % 7.0 > 0.3 else IDLE_DIP)
            self.pressure_t += dt
            if self.pressure_t >= PRESSURE_INTERVAL:
                self.pressure_t = 0.0
                self.pressure()
            return
        self.step_t += dt
        typ, ln, _en, _ex = self.steps[self.step_i]
        if typ in ("idle", "posters"):
            self.set_lights(1.0 if self.t % 7.0 > 0.3 else IDLE_DIP)     # ときどきすこし弱まる
            if typ == "posters":
                self.poster_progress(self.step_t)
        elif typ == "flicker":
            if self.step_t >= self.flicker_next:
                self.flicker_lit = not self.flicker_lit
                self.flicker_next = self.step_t + random.uniform(0.03, 0.22)
                self.set_lights(0.9 if self.flicker_lit else 0.0)
                self.blackout(0.0 if self.flicker_lit else FLICKER_BLACK)
        if self.step_t >= ln:
            if typ == "flicker":
                self.blackout(0.0)
            if typ == "dark":
                self.set_lights(1.0)
                self.blackout(0.0)
            self.next_step()


# ---------------- 登録（Tick） ----------------
_STATE = {"game": None, "errors": 0}


def on_tick(dt):
    try:
        world = game_world()
        if world is None:
            _STATE["game"] = None
            return
        g = _STATE["game"]
        if g is None or g.world != world:
            _STATE["game"] = Game(world)
            return
        g.tick(dt)
    except Exception:  # noqa
        _STATE["errors"] += 1
        if _STATE["errors"] <= 3:
            unreal.log_error(LOG_PREFIX + "Tick でエラー:\n" + traceback.format_exc())
        _STATE["game"] = None


def solve(name="謎"):
    """謎を1つ解いたことにする。本物の謎のしくみから呼ぶ（Cmd から:  py import unreal; unreal._kd_solve('本') ）"""
    g = _STATE.get("game")
    if g is None:
        unreal.log_warning(LOG_PREFIX + "ゲームが動いていません（Playを押してから）")
        return
    g.on_flag(name)


def main():
    apply_settings(KD_SETTING_NAMES, log)
    unreal._kd_solve = solve
    old = getattr(unreal, "_kd_tick_handle", None)
    if old is not None:
        try:
            unreal.unregister_slate_post_tick_callback(old)
        except Exception:  # noqa
            pass
    unreal._kd_tick_handle = unreal.register_slate_post_tick_callback(on_tick)
    log("kd_game を登録しました。▶（Play）を押してください。エラーは Output Log を「KD」で絞って見ます")


main()
