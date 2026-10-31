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
BOX_CODE = [2, 15, 4, 9]       # 金庫の中の箱（ボタン1〜16）を押す順番。新聞の2つ目の数列「2-15-4-9」
BOX_CAM_FOV = 60.0             # 箱のボタンを押す間の、専用カメラの視野（大きいほど広く見える）
BOX_DIST = 25.0                # カメラから、ボタンの面までの距離（cm）
BOX_BTN = 3.2                  # ボタン1個の大きさ（cm）。4×4 を画面の真ん中に並べる
BOX_DEBUG = False              # True: ボタンの枠と数字を、線と文字で全部出す（本物の箱があるので、ふだんは False）
BOX_HOVER = True               # True: 本物の箱で、マウスが指しているボタンに細い枠を出す
BOX_FLIP = False               # True: 左右を反転する（ゲームの中で、ボタンの数字の並びが左右逆だったら True）
BOX_TOP_H = 6.2                # 箱の原点から、ボタンの面までの高さ（cm・箱の倍率をかける前）
ENVELOPE_CODE = [3, 6, 1, 8]   # 赤い封筒の4けたの鍵（仮の例。本物は、ひかるが決める）。答えはここ1か所だけ：i番目に貼られる張り紙に、i番目の数字が暗い間だけ光る（謎7）
ENVELOPE_DECOYS = {"1997": "「えげつない」の張り紙の年だ……鍵は動かない", "0728": "カメラの広告の728円……これも違う"}   # ひっかけの数字と、出す文（はずれとして数える）
CODE_FLICKER = 1.0             # 謎7（暗い間だけ光る数字）：1枚ごとの最初の点滅（秒）
CODE_DARK = 2.5                # 暗い間（秒）。暗くなった瞬間に、新しい張り紙が貼られ、貼られた分の数字が光る
CODE_LIT = 3.0                 # 明るい間（秒）。数字は消えて、ガラスの文字の言葉だけ見える
CODE_FINAL_DARK = 6.0          # 4枚目のあとの、最後の暗い間（秒）。4つ全部の数字が光る
CODE_HOLD = 8.0                # そのあと、明るいまま4枚が貼られている時間（秒）
CODE_DARK_BLACK = 0.0          # 謎7の暗い間の、画面の黒さ（0〜1）。0 なら光だけ消して画面は見える（数字が見えるように）。1.0 にすると数字も見えなくなる
CODE_HINT_INTERVAL = 90.0      # 封筒を持っているのに開けていないとき、電話機の上のヒントの文字が変わる間隔（秒）
CODE_PERM_SAFE = True          # True: 封筒の鍵が答えの「並べかえ」のとき、「順番がちがう？」と出すだけで、幽霊は近づかない
ENVELOPE_WRONG_GHOST = True    # True: 封筒の鍵をまちがえると、幽霊が1歩近づく（謎が進まないときの「圧力」と同じ）
DOOR_RANGE = 200.0             # 鍵を持ったとき、扉をこの距離（cm）まで見ると「Eで開ける」が出る
DIAL_STEP_TIME = 0.07          # ダイヤルが1目盛り回るのに、キーを押しつづける時間（秒）
TRAP_MARGIN = 3.0              # 閉じ込められている間、ガラスの内がわから、体（PAWN_RADIUS）のほかに、さらにこの距離（cm）あけて止まる（壁ぎわのガタガタ・すり抜け止め）
PAWN_RADIUS = 22.0             # 体の太さ（カプセルの半径・cm）。ふつうの 34 より細くして、せまい電話ボックスの中を動きやすくする。0 で変えない
PHONE_CAM_DIST = 55.0          # 電話機を押す間の専用カメラを、電話機から何cm 離すか（小さいほどアップ）
PHONE_CAM_FOV = 45.0           # そのカメラの視野の角度
PHONE_KEY_U0 = -6.6            # ボタン（3列×4行）の左はし：電話機の「触る点」から右へ何cm（－が左）
PHONE_KEY_Z0 = 8.0             # ボタンの上はし：触る点から上へ何cm
PHONE_KEY_W = 4.4              # ボタン1つの幅（cm）
PHONE_KEY_H = 3.8              # ボタン1つの高さ（cm）
PHONE_KEY_DEBUG = True         # True: ボタンの枠と、いま指しているボタンを、画面に線で出す（位置合わせ用。ぴったり合ったら False）
DIAL_FOV = 30.0                # 金庫のダイヤルを回す間の、視野の角度（小さいほどアップ。ふだんは約90）
DIAL_ZOOM_TIME = 0.45          # アップになるまでの時間（秒）
SAFE_LID_ANGLE = 105.0           # 金庫が開いたとき、ふたが何度まで開くか
SAFE_LID_TIME = 0.9            # ふたが開くのにかかる時間（秒）
SAFE_LID_SIGN = -1.0           # ふたが下へ回ってしまうときは 1.0 にする
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
ITEM_RANGE = 110.0             # 10円・本に、この距離（cm）まで近づいて見ると「Eで…」が出る
READ_RANGE = 150.0             # 掲示板の新聞に、この距離（cm）まで近づいて見ると「Eで読む」が出る
READ_SIZE = 47.0               # 新聞を手に取ったときの、目の前の大きさ（cm。画面の高さに収まるくらい）
READ_DIST = 45.0               # 新聞を、目からこの距離（cm）に出す
LOOK_CONE = 0.96               # 見ている向きが、物のほうへ、どれだけ正確に向いているか（1に近いほど、ちゃんと見ないと反応しない。0.93=約21度 0.96=約16度）
ENTER_RANGE = 170.0            # 入口の前のこの距離（cm）まで近づくと「Eで入る」が出る
ENTER_FADE_OUT = 0.9           # 暗くなるまでの時間（秒）
ENTER_BLACK = 2.6              # 真っ暗のまま待つ時間（秒）。この間に「ドアが開く音 → 中に入る音 → 扉が閉まる音」が鳴る
ENTER_FADE_IN = 1.4            # 明るくなるまでの時間（秒）
SOUND_DIR = "/Game/KoushuDenwa/Sounds"
MATERIAL_DIR = "/Game/KoushuDenwa/Materials"          # setup_game_fp.py が材質（M_CodeGlowTree0〜9・M_GlassGlow0〜9・M_GlassHintC1〜3）を置く場所
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
GHOST_YAW = -90.0                         # 幽霊の向きの補正（度）。今のモデルは回転0度で +Y 向きなので -90。背中を向けるなら 90、横を向くなら 0 か 180
GHOST_Z = 0.0                             # 幽霊の足の高さの補正（cm）。浮くなら－、地面にめり込むなら＋
DEAD_DIST = 70.0                           # 失敗のとき、幽霊が目の前に出る距離（cm）
GHOST_TILT_DEG = 14.0                      # 幽霊の首かしげの角度（度）。かしげる向きが逆なら － にする。0 で首かしげなし
GHOST_TILT_SPEED = 0.6                     # 首かしげのゆらぎの速さ（大きいほど速い。0.6 で1往復が約10秒）
GHOST_JERK = True                          # True: 最後に近づくとき（4回目の場面の終わり・失敗の瞬間）、首をカクッ、カクッと2回動かす
GHOST_MORPH = True                         # True: 表情（口が開く・笑う）をモーフで動かす。False: 表情は動かさない
GHOST_JAW_MAX = 0.6                        # 口が開く最大（0〜1）。場面の終わりに向けて、ゆっくり開く
GHOST_SMILE_BY_LEVEL = [0.0, 0.2, 0.5, 0.8]    # 笑い顔の強さ（演出の強さ1〜4ごと）。失敗の瞬間は歯を見せて笑う（Grin 1.0）
GHOST_TILT_MODE = "auto"                   # 首かしげのやり方。"auto"=骨が動かせれば骨、だめなら全体／"bone"=骨だけ／"body"=体ぜんたいを傾ける
GHOST_ANIM_DIR = "/Game/KoushuDenwa/Ghost"     # 幽霊のアニメ（Ghost_HeadTilt_Natural）の置き場所（setup_game_fp.py が取り込む）
GLASSGHOST_ENABLE = True                   # True: 幽霊の場面（GLASSGHOST_CARDS）で、幽霊がガラスの外にぴったり張りつく。False: 前と同じ（GHOST_SPOTS の場所に立つだけ）
GLASSGHOST_CARDS = [4]                     # ガラスに張りつく幽霊の札（1〜4）。[4]=4回目だけ／[3, 4]=3回目と4回目
GLASSGHOST_GAP = 3.0                       # 幽霊の顔とガラス（外の面）のすきま（cm）。めり込むなら大きく、離れて見えるなら小さく
GLASSGHOST_FACES = [("L", -0.45), ("R", -0.45), ("F", 0.0)]    # 張りつく面（面, 位置）。面: R=右 L=左 F=入口（ドア）B=奥。位置: -1〜1（R・L は入口側が＋、F は右が＋）。初期値=左の奥寄り・右の奥寄り・ドア
GLASSGHOST_LEAN_DEG = 10.0                 # ガラスへ体をかたむける角度（度）。向きが逆（のけぞる）なら － にする
GLASSGHOST_SLIDE = True                    # True: 暗い間に、別の面へ外がわをすべって移る（その場面の後半は、別のガラスにいる）
GLASSGHOST_HEIGHT = 160.0                  # 幽霊の身長（cm。setup_game_fp.py の GHOST_HEIGHT と同じ）
GLASSGHOST_HEAD = 0.93                     # 頭の高さ（身長にかける割合）。顔をこの高さに合わせる
GLASSGHOST_FACE_DEPTH = 9.0                # 頭の中心から顔の表面までの前後の長さ（cm）。顔がガラスにめり込む・離れるときは直す
GLASSGHOST_GRIN = 0.85                     # ガラスに張りついているときの、笑い（Grin 0〜1）。口は GHOST_JAW_MAX まで開く
GLASSGHOST_SOUND = "safe_clunk"            # 張りついたときの「ドン」という音（SOUND_DIR の音の名前）。""で鳴らさない
GLASSGHOST_HANDS = (2, 3)                  # 1回の場面で、あらたに見えるようになる手形の数（最小, 最大）。残りの手形は見えないまま
HAND_PER_SCARE = 1                         # 強さ2以上の「張り紙の演出」のたびに、あらたに見える手形の数
HAND_DELAY = 0.6                           # 手形が1つずつ見えるまでの間隔（秒）
GHOST_ANIM_FULL_DEG = 40.0                # そのアニメの首の最大の傾き（度）。blender/ghost_face.py の「Natural」= 約40度
RESTART_AFTER = 6.0                        # 失敗してから、最初に戻るまでの時間（秒）
END2_HOLD = 7.0                            # エンディング②（行方不明）：新聞の絵を出しておく時間（秒）
END2_SCARE = 3.0                           # エンディング②：幽霊が目の前に出てから、新聞に切りかわるまでの時間（秒）
END2_FADE = 1.0                            # エンディング②：新聞の前に、真っ暗にする時間（秒）
END2_SIZE = 47.0                           # エンディング②：新聞の絵の大きさ（cm・目の前 READ_DIST に出す）
BREAK_CODE = "2929"                        # エンディング③（ドアぶっ壊し）：電話にかける番号（ニクニク）。ジム会員証の「俺最強2929」がヒント
BREAK_FLY_TIME = 1.2                       # ドアが吹っ飛んでいる時間（秒）
BREAK_FLY_DIST = 450.0                     # ドアが飛んでいく距離（cm・入口の外向き）
BREAK_SHAKE = 1.5                          # ドアが飛ぶときの画面のゆれ（度）。0 でゆれない
BREAK_CARD_TIME = 1.5                      # 「ムキッ！」のカットインを出す時間（秒）
INV_KEY = "I"                              # 持ち物の一覧を開く／とじるキー。開いている間：[E] プロテインを飲む／[Y] 財布を見る
INV_DRINK_KEY = "E"                        # 持ち物を開いている間の、プロテインを飲むキー
INV_WALLET_KEY = "Y"                       # 持ち物を開いている間の、財布（ジムの会員証）を見るキー
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


def screen(world, msg, color=(255, 255, 255), t=3.0, key=None):
    try:
        lc = unreal.LinearColor(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, 1.0)
        if key:
            unreal.SystemLibrary.print_string(world, str(msg), True, False, lc, t, key)          # 同じ key の文字は置きかわる（カットインの拡大用）
        else:
            unreal.SystemLibrary.print_string(world, str(msg), True, False, lc, t)
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
    "BOX_CODE": "金庫の中の箱のボタンを押す順番。[2,15,4,9] のように、1〜16 の数字",
    "BOX_CAM_FOV": "箱のボタンを押す間の、カメラの視野（大きいほど広く見える）",
    "BOX_DIST": "カメラから、箱のボタンの面までの距離（cm）",
    "BOX_BTN": "箱のボタン1個の大きさ（cm）",
    "BOX_DEBUG": "true: 箱のボタンの枠と数字を線と文字で全部出す",
    "BOX_HOVER": "true: 箱のボタンのうち、マウスが指している1個に細い枠を出す",
    "BOX_FLIP": "true: 箱のボタンの左右を反転する（数字の並びが逆のとき）",
    "BOX_TOP_H": "箱の原点から、ボタンの面までの高さ（cm）",
    "ENVELOPE_CODE": "赤い封筒の4けたの鍵。[3,6,1,8] のように、0〜9 の数字を4つ（仮の例）",
    "ENVELOPE_DECOYS": "ひっかけの4けたと、出す文。{\"1997\": \"文\", \"0728\": \"文\"} のように（はずれとして数える）",
    "ENVELOPE_WRONG_GHOST": "true: 封筒の鍵をまちがえると、幽霊が1歩近づく",
    "CODE_FLICKER": "謎7：1枚ごとの最初の点滅の長さ（秒）",
    "CODE_DARK": "謎7：暗い間の長さ（秒）。新しい張り紙が貼られ、光る数字が出る",
    "CODE_LIT": "謎7：明るい間の長さ（秒）。数字は消える",
    "CODE_FINAL_DARK": "謎7：4枚目のあとの、最後の暗い間（秒）。4つ全部光る",
    "CODE_HOLD": "謎7：最後に、明るいまま4枚が貼られている時間（秒）",
    "CODE_DARK_BLACK": "謎7：暗い間の画面の黒さ（0〜1）。0 で数字が見える。1 だと数字も見えない",
    "CODE_HINT_INTERVAL": "謎7：封筒が開かないとき、電話機の上のヒントが変わる間隔（秒）",
    "CODE_PERM_SAFE": "true: 封筒の鍵が答えの並べかえのとき、幽霊は近づかない（順番がちがう、と出すだけ）",
    "DOOR_RANGE": "鍵を持ったとき、扉を「Eで開ける」ために見る距離（cm）",
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
    "LOOK_CONE": "見ている向きの正確さ（1に近いほど、物をちゃんと見ないと「Eで…」が出ない。0.93=ゆるい 0.96=ふつう 0.98=きびしい）",
    "SAFE_LID_ANGLE": "金庫が開いたとき、ふたが開く角度（度）",
    "SAFE_LID_TIME": "ふたが開くのにかかる時間（秒）",
    "SAFE_LID_SIGN": "ふたの開く向き（下へ回るなら 1.0 に）",
    "TRAP_MARGIN": "閉じ込められている間、ガラスの内がわから、体の太さのほかに、あける距離（cm）",
    "PAWN_RADIUS": "体の太さ（半径・cm）。0で変えない",
    "PHONE_CAM_DIST": "電話機を押す間のカメラの距離（cm）。小さいほどアップ",
    "PHONE_CAM_FOV": "電話機カメラの視野の角度",
    "PHONE_KEY_U0": "電話のボタン（3列×4行）の左はし。触る点から右へ何cm（－が左）",
    "PHONE_KEY_Z0": "電話のボタンの上はし。触る点から上へ何cm",
    "PHONE_KEY_W": "ボタン1つの幅（cm）",
    "PHONE_KEY_H": "ボタン1つの高さ（cm）",
    "PHONE_KEY_DEBUG": "true: ボタンの枠を線で出す（位置合わせ用）",
    "DIAL_FOV": "ダイヤル専用カメラが無いときの、視野の角度（小さいほどアップ）",
    "DIAL_ZOOM_TIME": "ダイヤルの画面に切りかわるまでの時間（秒）",
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
    "GHOST_YAW": "幽霊の向きの補正（度）。背中を向けるなら 180",
    "GHOST_Z": "幽霊の足の高さの補正（cm）。浮くなら－",
    "DEAD_DIST": "失敗のとき、幽霊が目の前に出る距離（cm）",
    "GHOST_TILT_DEG": "幽霊の首かしげの角度（度）。向きが逆なら － に。0 でなし",
    "GHOST_TILT_SPEED": "首かしげのゆらぎの速さ（大きいほど速い）",
    "GHOST_JERK": "true: 最後に近づくとき、首をカクッと2回動かす",
    "GHOST_MORPH": "true: 幽霊の表情（口が開く・笑う）を動かす。false でなし",
    "GHOST_JAW_MAX": "幽霊の口が開く最大（0〜1）",
    "GHOST_SMILE_BY_LEVEL": "幽霊の笑い顔の強さ（演出の強さ1〜4ごと）",
    "GHOST_TILT_MODE": "首かしげのやり方。auto / bone（骨だけ）/ body（体ぜんたい）",
    "RESTART_AFTER": "失敗してから最初に戻るまでの秒数",
    "END2_HOLD": "エンディング②（行方不明）：新聞の絵を出しておく秒数",
    "END2_SCARE": "エンディング②：幽霊が目の前に出てから、新聞に切りかわるまでの秒数",
    "END2_FADE": "エンディング②：新聞の前の、真っ暗の秒数",
    "END2_SIZE": "エンディング②：新聞の絵の大きさ（cm）",
    "BREAK_CODE": "エンディング③（ドアぶっ壊し）の電話番号。プロテインを飲んでからかける",
    "BREAK_FLY_TIME": "エンディング③：ドアが吹っ飛んでいる秒数",
    "BREAK_FLY_DIST": "エンディング③：ドアが飛んでいく距離（cm）",
    "BREAK_SHAKE": "エンディング③：ドアが飛ぶときの画面のゆれ（度）。0 でゆれない",
    "BREAK_CARD_TIME": "エンディング③：「ムキッ！」のカットインの秒数",
    "INV_KEY": "持ち物の一覧を開く／とじるキー",
    "INV_DRINK_KEY": "持ち物を開いている間の、プロテインを飲むキー",
    "INV_WALLET_KEY": "持ち物を開いている間の、財布（ジムの会員証）を見るキー",
    "GLASSGHOST_ENABLE": "true: 幽霊がガラスの外に張りつく場面を使う。false: 前と同じ",
    "GLASSGHOST_CARDS": "ガラスに張りつく幽霊の札（1〜4。[4]=4回目だけ、[3,4]=3回目と4回目）",
    "GLASSGHOST_GAP": "幽霊の顔とガラスの外の面のすきま（cm）",
    "GLASSGHOST_FACES": "張りつく面の一覧 [面, 位置]。面は R/L/F/B、位置は -1〜1（初期値は 左・右・ドア）",
    "GLASSGHOST_LEAN_DEG": "ガラスへ体をかたむける角度（度）。逆向きなら －",
    "GLASSGHOST_SLIDE": "true: 暗い間に、別の面へすべって移る",
    "GLASSGHOST_HEIGHT": "幽霊の身長（cm）",
    "GLASSGHOST_HEAD": "頭の高さ（身長にかける割合）",
    "GLASSGHOST_FACE_DEPTH": "頭の中心から顔の表面までの長さ（cm）",
    "GLASSGHOST_GRIN": "ガラスに張りついているときの笑い（0〜1）",
    "GLASSGHOST_SOUND": "張りついたときの音の名前（空で鳴らさない）",
    "GLASSGHOST_HANDS": "1回の場面であらたに見える手形の数 [最小, 最大]",
    "HAND_PER_SCARE": "強さ2以上の張り紙の演出のたびに、あらたに見える手形の数",
    "HAND_DELAY": "手形が1つずつ見えるまでの間隔（秒）",
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


KD_SETTING_NAMES = ["FLASH_OUTSIDE", "FLASH_INSIDE", "TUBE_SCALE", "TUBE_GLOW", "IDLE_DIP", "FLICKER_BLACK", "DARK_BLACK", "DARK_WORLD", "GLASS_DIRT", "WALK_SPEED", "ENTER_RANGE", "SWAY_DEG", "SWAY_SPEED", "BOOK_LABEL", "SAFE_LABEL", "SAFE_CODE", "BOX_CODE", "BOX_CAM_FOV", "BOX_DIST", "BOX_BTN", "BOX_DEBUG", "BOX_HOVER", "BOX_FLIP", "BOX_TOP_H", "ENVELOPE_CODE", "ENVELOPE_DECOYS", "ENVELOPE_WRONG_GHOST", "CODE_FLICKER", "CODE_DARK", "CODE_LIT", "CODE_FINAL_DARK", "CODE_HOLD", "CODE_DARK_BLACK", "CODE_HINT_INTERVAL", "CODE_PERM_SAFE", "DOOR_RANGE", "DIAL_STEP_TIME", "DIAL_SIGN", "TRAP_MARGIN", "PAWN_RADIUS", "PHONE_CAM_DIST", "PHONE_CAM_FOV", "PHONE_KEY_U0", "PHONE_KEY_Z0", "PHONE_KEY_W", "PHONE_KEY_H", "PHONE_KEY_DEBUG", "SAFE_LID_ANGLE", "SAFE_LID_TIME", "SAFE_LID_SIGN", "DIAL_FOV", "DIAL_ZOOM_TIME", "PHONE_BACK", "PHONE_Z", "HATCH_Z", "PHONE_COIN_COST", "START_DIST", "START_POS", "MANUAL_WALK", "ARROW_MOVE", "WALKABLE_ANGLE", "ITEM_RANGE", "READ_RANGE", "LOOK_CONE", "READ_SIZE", "READ_DIST", "ENTER_FADE_OUT", "ENTER_BLACK", "ENTER_FADE_IN", "FLICKER_TIME", "DARK_TIME", "GHOST_HOLD", "POSTER_HOLD", "POSTER_STEP", "POSTER_FRAC", "PUZZLE_COUNT", "PRESSURE_INTERVAL", "DEAD_DIST", "GHOST_YAW", "GHOST_Z", "GHOST_TILT_DEG", "GHOST_TILT_SPEED", "GHOST_JERK", "GHOST_MORPH", "GHOST_JAW_MAX", "GHOST_SMILE_BY_LEVEL", "GHOST_TILT_MODE", "GLASSGHOST_ENABLE", "GLASSGHOST_CARDS", "GLASSGHOST_GAP", "GLASSGHOST_FACES", "GLASSGHOST_LEAN_DEG", "GLASSGHOST_SLIDE", "GLASSGHOST_HEIGHT", "GLASSGHOST_HEAD", "GLASSGHOST_FACE_DEPTH", "GLASSGHOST_GRIN", "GLASSGHOST_SOUND", "GLASSGHOST_HANDS", "HAND_PER_SCARE", "HAND_DELAY", "RESTART_AFTER", "GHOST_SPOTS", "END2_HOLD", "END2_SCARE", "END2_FADE", "END2_SIZE", "BREAK_CODE", "BREAK_FLY_TIME", "BREAK_FLY_DIST", "BREAK_SHAKE", "BREAK_CARD_TIME", "INV_KEY", "INV_DRINK_KEY", "INV_WALLET_KEY"]


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


class GhostFx:
    """幽霊の首かしげと表情。アニメBP（ABP）なしで動かす。Game が setup で1つ作り、毎フレーム update(dt) するだけ（tick の中で検索しない）。
    首かしげ：①骨（FBXに焼いてある Ghost_HeadTilt_Natural を「1コマの再生位置」で止めて、傾きの量だけ位置を動かす）→ だめなら ②体ぜんたいを傾ける
    表情：SkeletalMeshComponent.set_morph_target で JawOpen / Smile / Grin（blender/ghost_face.py の形状キー名）"""

    JERK_WINDOWS = ((0.0, 0.12), (0.26, 0.38))        # カクッと動く2回の時間帯（秒）
    MORPHS = ("JawOpen", "Smile", "Grin")

    def __init__(self, actor, logf):
        self.log = logf
        self.actor = actor
        self.comp = None
        self.method = "none"                           # "bone" / "body"
        self.morph_ok = False
        self.names = {}
        self._warned = set()
        self.active = False
        self.dead = False
        self.level = 0
        self.hold = 10.0
        self.t = 0.0
        self.phase = 0.0
        self.base_yaw = 0.0
        self.cur_tilt = 0.0
        self.jerk_t = -1.0
        self.jerk_fired = False
        self.last_jv = 0
        self.glass = False                             # True: ガラスに張りついている（口を開けて笑う・体をガラスへかたむける）
        self.lean = 0.0
        self.cur = {}                                  # いまの表情の値（なめらかに近づける）
        self.sent = {}                                 # 最後にモデルへ送った値
        self.length = 0.0
        try:
            self.comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        except Exception:  # noqa
            self.comp = None
        self._setup_morph()
        self._setup_tilt()

    def _warn(self, key, msg):
        if key not in self._warned:
            self._warned.add(key)
            self.log(msg)

    # ---- 準備 ----
    def _setup_morph(self):
        if not GHOST_MORPH:
            self.log("幽霊の表情: 設定でオフ（GHOST_MORPH=False）")
            return
        if self.comp is None or not callable(getattr(self.comp, "set_morph_target", None)):
            self.log("幽霊の表情: 動かせません（本物のモデルではない／set_morph_target がない）")
            return
        have = None
        try:
            mesh = self.comp.get_editor_property("skeletal_mesh_asset")
            have = [str(m.get_name()) for m in mesh.get_editor_property("morph_targets")]
        except Exception:  # noqa
            have = None
        for n in self.MORPHS:
            real = n
            if have is not None:
                real = next((h for h in have if h == n), None) or next((h for h in have if h.endswith("." + n) or h.endswith("_" + n)), None)
                if real is None:
                    self._warn("m_" + n, "幽霊の表情: モーフ「%s」がモデルにありません（あるのは %s）。この表情は動かしません" % (n, ", ".join(have) or "なし"))
                    continue
            self.names[n] = real
        if have is None:
            self.log("  (モーフ名の一覧を読めないので、JawOpen/Smile/Grin があるものとして送ります)")
        self.morph_ok = bool(self.names)
        if self.morph_ok:
            self.log("幽霊の表情: モーフ %s を動かします" % ", ".join(self.names))

    def _find_anim(self):
        comp = self.comp
        cands = []
        try:
            cands.append(comp.get_editor_property("animation_data").get_editor_property("anim_to_play"))
        except Exception:  # noqa
            pass
        try:
            cands.append(comp.get_editor_property("animation_to_play"))
        except Exception:  # noqa
            pass
        for a in cands:
            if a is not None and "Face" not in str(a.get_name()):
                return a
        try:                                                                  # 見つからないとき：置き場所から「Natural」を探す（setup の外なので1回だけ）
            for p in unreal.EditorAssetLibrary.list_assets(GHOST_ANIM_DIR, recursive=True, include_folder=False):
                a = unreal.EditorAssetLibrary.load_asset(p)
                nm = str(a.get_name())
                if "Natural" in nm and "Face" not in nm:
                    return a
        except Exception:  # noqa
            pass
        return None

    def _init_bone(self):
        comp = self.comp
        for n in ("set_position", "set_play_rate", "set_animation", "play", "set_animation_mode"):
            if not callable(getattr(comp, n, None)):
                return "%s がない" % n
        seq = self._find_anim()
        if seq is None:
            return "首かしげのアニメ（Ghost_HeadTilt_Natural）が見つからない"
        try:
            length = float(seq.get_play_length())
        except Exception:  # noqa
            length = float(seq.get_editor_property("sequence_length"))
        if length <= 0.0:
            return "アニメの長さが読めない"
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.set_animation(seq)
        comp.play(False)
        comp.set_play_rate(0.0)                                               # 勝手に進めず、set_position で傾きを決める
        comp.set_position(0.0, False)
        self.length = length
        return None

    def _setup_tilt(self):
        mode = str(GHOST_TILT_MODE).lower()
        if GHOST_TILT_DEG == 0.0:
            self.log("幽霊の首かしげ: 設定でオフ（GHOST_TILT_DEG=0）")
            return
        self.method = "body"
        why = None
        if self.comp is None:
            why = "仮の姿（筒）なので"
        elif mode == "body":
            why = "GHOST_TILT_MODE=body なので"
        elif GHOST_TILT_DEG < 0.0:
            why = "骨のアニメは一方向にしか傾かないので（GHOST_TILT_DEG が－）"
        else:
            try:
                why = self._init_bone()
            except Exception as e:  # noqa
                why = "骨を動かす準備でエラー %s" % e
            if why is None:
                self.method = "bone"
        self.log("幽霊の首かしげ: %s%s" % ("骨" if self.method == "bone" else "全体", "" if why is None else "（%s）" % why))

    # ---- 場面の出入り ----
    def begin(self, level, dead, hold, yaw, glass=False, lean=0.0):
        self.active = True
        self.glass = bool(glass) and not dead
        self.lean = float(lean) if self.glass else 0.0
        self.dead = bool(dead)
        self.level = max(0, int(level))
        self.hold = max(1.0, float(hold))
        self.t = 0.0
        self.phase = 0.0
        self.base_yaw = float(yaw)
        self.cur_tilt = 0.0
        self.jerk_t = -1.0
        self.jerk_fired = False
        self.last_jv = 0
        if self.dead:
            self.jerk()

    def jerk(self):
        if GHOST_JERK and GHOST_TILT_DEG != 0.0:
            self.jerk_t = 0.0

    def end(self):
        """幽霊が消える：首も表情も、ふつうの状態に戻す"""
        was = self.active
        self.active = False
        self.dead = False
        self.glass = False
        self.lean = 0.0
        self.cur_tilt = 0.0
        self.jerk_t = -1.0
        for n in list(self.sent):
            if self.sent[n] != 0.0:
                self._send(n, 0.0)
        self.cur = {}
        if was:
            self._apply_tilt(0.0, 0.0)

    # ---- 毎フレーム ----
    def update(self, dt):
        if not self.active:
            return
        self.t += dt
        p = 1.0 if self.dead else min(1.0, self.t / self.hold)
        n_lv = max(1, len(GHOST_SMILE_BY_LEVEL))
        if GHOST_JERK and not self.dead and not self.jerk_fired and self.level >= n_lv - 1 and p >= 0.8:
            self.jerk_fired = True                                            # 最後の段階：近づききるころ、首をカクッとさせる
            self.jerk()
        jv = 0
        if self.jerk_t >= 0.0:
            self.jerk_t += dt
            if any(a <= self.jerk_t < b for a, b in self.JERK_WINDOWS):
                jv = 1
            elif self.jerk_t >= self.JERK_WINDOWS[-1][1]:
                self.jerk_t = -1.0
        edge = jv != self.last_jv
        self.last_jv = jv
        # 首かしげ：ゆっくり揺れる傾き（0.1〜1.0倍）＋ カクッのときの一瞬の上乗せ
        self.phase += GHOST_TILT_SPEED * dt
        sway = 0.55 + 0.45 * math.sin(self.phase)
        tgt = GHOST_TILT_DEG * sway + GHOST_TILT_DEG * 0.9 * jv
        k = 1.0 if edge else 1.0 - math.exp(-dt * 3.0)                       # カクッは一瞬で、ふだんはなめらかに
        self.cur_tilt += (tgt - self.cur_tilt) * k
        nod = 0.3 * GHOST_TILT_DEG * (0.5 + 0.5 * math.sin(self.phase * 0.7 + 1.0))
        self._apply_tilt(self.cur_tilt, nod)
        # 表情
        if self.morph_ok:
            if self.dead:
                tg = {"JawOpen": min(1.0, GHOST_JAW_MAX + 0.4 * jv), "Smile": 0.0, "Grin": 1.0}
            elif self.glass:                                                  # ガラスに張りつく：口を大きく開け、にたあっと笑う
                tg = {"JawOpen": min(1.0, GHOST_JAW_MAX * min(1.0, 0.5 + 0.5 * p) + 0.4 * jv), "Smile": 0.0, "Grin": float(GLASSGHOST_GRIN)}
            else:
                lv = min(self.level, n_lv - 1)
                tg = {"JawOpen": GHOST_JAW_MAX * p * (lv + 1.0) / n_lv, "Smile": float(GHOST_SMILE_BY_LEVEL[lv]), "Grin": 0.0}
            kk = 1.0 if edge else 1.0 - math.exp(-dt * 5.0)
            for n, v in tg.items():
                if n not in self.names:
                    continue
                c = self.cur.get(n, 0.0)
                c += (v - c) * kk
                self.cur[n] = c
                if abs(c - self.sent.get(n, 0.0)) > 0.003:
                    self._send(n, c)

    def _send(self, n, v):
        real = self.names.get(n)
        if real is None or not self.morph_ok:
            return
        try:
            self.comp.set_morph_target(real, float(v))
            self.sent[n] = float(v)
        except Exception as e:  # noqa
            self.morph_ok = False
            self._warn("m_err", "幽霊の表情: set_morph_target でエラーなので、表情は止めます: %s" % e)

    def _apply_tilt(self, deg, nod):
        if self.method == "bone":
            try:
                f = max(0.0, min(1.0, deg / GHOST_ANIM_FULL_DEG))
                u = 0.5 - math.sin(math.asin(1.0 - 2.0 * f) / 3.0)            # アニメのなめらかな加速（smoothstep）を逆に引く
                self.comp.set_position((29.0 + 60.0 * u) / 179.0 * self.length, False)    # コマ1〜30は直立、30〜90で傾く
            except Exception as e:  # noqa
                self.method = "body"
                self._warn("t_err", "幽霊の首かしげ: 骨が動かせないので、全体に切りかえます: %s" % e)
        elif self.method == "body":
            try:                                                              # 幽霊は +Y 向き。体の前後の軸まわり＝ピッチ（横にかしげる）、左右の軸まわり＝ロール（少しうなずく）
                self.actor.set_actor_rotation(unreal.Rotator(nod + self.lean, deg, self.base_yaw), False)
            except Exception as e:  # noqa
                self.method = "none"
                self._warn("t_err", "幽霊の首かしげ: 体を傾けられません: %s" % e)


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
        self.safe_base = found.get("DialSafe_Base")                  # 開いた状態の金庫（下の箱とふた）
        self.safe_lid = found.get("DialSafe_Lid")
        self.safe_key = found.get("DialSafe_Key")                    # 開いた金庫の中の、鍵と10円（見せて、すぐ消す）
        self.safe_coin = found.get("DialSafe_Coin")
        self.safe_box = found.get("DialSafe_Box")                    # 金庫の中の、16個ボタンの箱
        self.box_cam = found.get("KD_BoxCam")                        # 箱のボタンを押すときの専用カメラ
        self.lid_pending, self.loot_t = -1.0, -1.0
        self.lid_rot0 = self.safe_lid.get_actor_rotation() if self.safe_lid is not None else None
        self.lid_t = -1.0
        self.phone_cam = found.get("KD_PhoneCam")                    # 電話機専用のカメラ（置き場所は begin_phone で、電話機に合わせる）
        self.phone_cam_on = False
        self.dial_cam = found.get("KD_DialCam")                      # ダイヤル専用のカメラ（setup_game_fp.py が置く）
        self.safe_cam_on = False
        self.dial_value, self.dial_dir, self.dial_entries, self.safe_open, self.has_key = 0, None, [], False, False
        self.box_done, self.has_envelope, self.box_entries = False, False, []
        self.envelope_open, self.has_door_key, self.env_digits, self.exit_stage = False, False, "", 0       # 封筒の鍵・扉の鍵・脱出（やり直しで最初に戻る）
        self.has_memo, self.called_0115, self.dialed_0714, self.lcd_seen, self.digits = False, False, False, False, ""
        self.hatch_open = False
        self.has_protein, self.protein_drunk, self.inv_open = True, False, False       # エンディング③：プロテインは最初から持っている（やり直しで最初に戻る）
        self.ending, self.break_stage, self.door_broken = None, 0, False               # どのエンディングに着いたか："escape" / "missing" / "break"
        self.dead_stage = 0
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
        self.setup_code(found)
        self.setup_hands(found)
        self.ghost = found.get("Ghost")
        if self.ghost is not None:
            self.ghost.set_actor_hidden_in_game(True)
            self.ghost_head = found.get("Ghost_Head")
            if self.ghost_head is not None:
                self.ghost_head.set_actor_hidden_in_game(True)
            try:
                self.gfx = GhostFx(self.ghost, log)                       # 首かしげと表情の準備（部品を最初に1回だけ探す）
            except Exception as e:  # noqa
                self.gfx = None
                log("  (幽霊の首かしげ・表情を準備できません) %s" % e)
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
        self.in_t, self.in_n = max(20.0, self.half_t - 20.0), max(20.0, self.half_n - 20.0)       # 中の歩ける広さ（ガラスの内がわ）。印が無いときは、外形から20cm内側
        inner = found.get("KD_BoothInner")
        if inner is not None:
            isc = inner.get_actor_scale3d()
            if isc.x > 5.0 and isc.y > 5.0:
                self.in_t, self.in_n = isc.x, isc.y
        self.glass_n, self.glass_t = (self.in_n + 1.5, self.in_t + 1.5) if inner is not None else (max(20.0, self.half_n - 3.0), max(20.0, self.half_t - 3.0))      # ガラスの外の面（setup_game_fp.py は、歩ける広さを ガラスの外の面 − 1.5cm にしている）
        log("中の歩ける広さ: 横 ±%.0fcm・奥行き ±%.0fcm（体の太さ %.0fcm）" % (self.in_t, self.in_n, PAWN_RADIUS))
        self.shrink_capsule()
        self.snd = {}
        for nm in ("door_open", "door_close", "latch", "safe_click", "safe_clunk", "safe_creak"):
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

    # ---- 謎7：暗い間だけ光る数字（答えは ENVELOPE_CODE だけで決まる） ----
    def setup_code(self, found):
        self.code_posters = [found.get("KD_CodePoster_%d" % (i + 1)) for i in range(4)]
        self.code_glow = [found.get("KD_CodeGlow_%d" % (i + 1)) for i in range(4)]
        self.code_active = self.code_queued = self.code_seen = self.code_req = False
        self.code_pasted = 0
        self.hint_t, self.hint_stage = 0.0, 0
        self._glow_key = None
        for a in self.code_posters + self.code_glow:
            if a is not None:
                a.set_actor_hidden_in_game(True)
        code = list(ENVELOPE_CODE)
        ans = "".join(str(d) for d in code)
        if len(code) != 4 or not all(isinstance(d, int) and 0 <= d <= 9 for d in code):
            log("[エラー] ENVELOPE_CODE は 0〜9 の数字を4つにしてください（いま %s）" % (code,))
        else:
            if len(set(code)) < 4:
                log("[注意] ENVELOPE_CODE に同じ数字があります（%s）。順番の謎になりにくいので、4つとも別の数字にするのがおすすめ" % ans)
            if ans in ENVELOPE_DECOYS:
                log("[注意] ENVELOPE_CODE（%s）が ENVELOPE_DECOYS の中にあります。ひっかけと答えが同じです" % ans)
        missing = []
        for i in range(4):
            a = self.code_glow[i]
            if a is None or i >= len(code) or not isinstance(code[i], int) or not 0 <= code[i] <= 9:
                continue
            mat = None
            for pre in ("M_CodeGlowTree", "M_GlassGlow"):                    # 外の木用の強い光の材質。なければガラスの文字用で代用
                try:
                    mat = unreal.EditorAssetLibrary.load_asset("%s/%s%d" % (MATERIAL_DIR, pre, code[i]))
                except Exception as e:  # noqa
                    log("  (光る数字の材質を読めません) %s%d: %s" % (pre, code[i], e))
                    mat = None
                if mat is not None:
                    if pre != "M_CodeGlowTree":
                        log("[注意] M_CodeGlowTree%d がないので M_GlassGlow%d で代用します（外の木では暗いかも）。setup_game_fp.py を実行し直してください" % (code[i], code[i]))
                    break
            if mat is not None:
                try:
                    a.get_component_by_class(unreal.StaticMeshComponent).set_material(0, mat)
                except Exception as e:  # noqa
                    log("  (光る数字の材質を入れられません) KD_CodeGlow_%d: %s" % (i + 1, e))
            else:
                missing.append("M_CodeGlowTree%d" % code[i])
        if missing:
            log("[エラー] 外の木の光る数字の材質がありません: %s。setup_game_fp.py を実行し直してください" % ", ".join(missing))
        self.hint_comp, self.hint_mat0, self.hint_mats = None, None, []
        if self.hint is not None:
            try:
                self.hint_comp = self.hint.get_component_by_class(unreal.StaticMeshComponent)
                self.hint_mat0 = self.hint_comp.get_material(0)
            except Exception as e:  # noqa
                log("  (ヒントの材質を読めません) %s" % e)
            try:
                self.hint_mats = [unreal.EditorAssetLibrary.load_asset("%s/M_GlassHintC%d" % (MATERIAL_DIR, i)) for i in (1, 2, 3)]
            except Exception:  # noqa
                self.hint_mats = [None, None, None]
            if any(m is None for m in self.hint_mats):
                log("[注意] ヒントの材質（M_GlassHintC1〜3）がありません。setup_game_fp.py を実行し直してください")
        log("暗号の張り紙: 紙%d枚・数字%d枚・答え %s" % (sum(1 for a in self.code_posters if a is not None), sum(1 for a in self.code_glow if a is not None), ans))

    def update_code_glow(self, mult):
        """外の木の光る数字と、内側のガラスの言葉（貼られた紙）を、切りかえる。
        暗い間（mult<0.05・蛍光灯の棒を隠す条件と同じ）：ガラスの言葉は1枚も出さず（外の木が見えるように）、貼られた分の数字だけが木で光る。
        明るい間：数字は消えて、貼られた分の言葉だけがガラスに出る。変わったときだけ切りかえる"""
        dark = self.code_active and mult < 0.05
        n_glow = self.code_pasted if dark else 0
        n_word = 0 if dark else (self.code_pasted if self.code_active else 0)
        key = (n_glow, n_word)
        if key == self._glow_key:
            return
        self._glow_key = key
        for i, a in enumerate(self.code_glow):
            if a is not None:
                a.set_actor_hidden_in_game(i >= n_glow)
        for i, a in enumerate(self.code_posters):
            if a is not None:
                a.set_actor_hidden_in_game(i >= n_word)
        if dark:                                                   # ふつうの張り紙も、1枚も出さない（念のため）
            self.posters_hide()

    def code_clear(self):
        for a in self.code_posters + self.code_glow:
            if a is not None:
                a.set_actor_hidden_in_game(True)
        self.code_pasted = 0
        self._glow_key = (0, 0)

    def code_begin(self):
        self.code_active = True
        self.code_queued = False
        self.hide_all()
        self.code_pasted = 0
        log("謎7の場面を始めます（答え %s）" % "".join(str(d) for d in ENVELOPE_CODE))

    def code_paste(self, k):
        self.code_pasted = k + 1                                   # 紙は、この暗い間が終わって明るくなったときにガラスに出る（暗い間は外の木の数字だけ）
        self.update_code_glow(self.mult)
        log("謎7：%d枚目の張り紙が貼られました（数字 %s）" % (k + 1, ENVELOPE_CODE[k] if k < len(ENVELOPE_CODE) else "?"))

    def code_end(self):
        self.code_clear()
        self.code_active = False
        self.code_seen = True
        self.hint_t = 0.0
        log("謎7の場面が終わりました")

    def code_steps(self):
        st = []
        for k in range(4):
            st.append(("flicker", CODE_FLICKER, self.code_begin if k == 0 else None, None))
            st.append(("cdark", CODE_DARK, lambda k=k: self.code_paste(k), None))
            st.append(("clit", CODE_LIT, None, None))
        st.append(("flicker", CODE_FLICKER, None, None))
        st.append(("cdark", CODE_FINAL_DARK, None, None))
        st.append(("clit", CODE_HOLD, None, None))
        st.append(("flicker", FLICKER_TIME, None, None))
        st.append(("dark", DARK_TIME, self.code_clear, self.code_end))
        return st

    def start_code_seq(self, restart=False):
        if self.code_queued and not self.code_active:            # 待っている場面が、まだ始まっていない：そのまま待たせる
            return
        if restart and self.code_active:                          # 場面の途中：止めて、最初から
            self.steps = []
            self.step_i = 0
            self.code_clear()
            self.code_active = False
            self.set_lights(1.0)
            self.blackout(0.0)
        self.code_queued = True
        self.run_steps(self.code_steps())

    def set_hint_stage(self, st):
        self.hint_stage = st
        if self.hint_comp is None:
            return
        mat = self.hint_mat0 if st == 0 else self.hint_mats[st - 1]
        if mat is None:
            return
        try:
            self.hint_comp.set_material(0, mat)
            log("電話機の上のヒントを変えました（段階 %d）" % st)
        except Exception as e:  # noqa
            log("  (ヒントを変えられません) %s" % e)

    def tick_code_hint(self, dt):
        """封筒を持っていて、まだ開けていない間だけ、CODE_HINT_INTERVAL 秒ごとに、ヒントの文字が変わる。開いたら元に戻る"""
        if self.hint is None:
            return
        if not (self.code_seen and self.has_envelope and not self.envelope_open):
            if self.hint_stage != 0:
                self.set_hint_stage(0)
            return
        self.hint_t += dt
        st = min(3, int(self.hint_t // CODE_HINT_INTERVAL))
        if st != self.hint_stage:
            self.set_hint_stage(st)

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
        self.update_code_glow(mult)
        self.update_hands()

    def reveal(self, stage):
        frac = POSTER_FRAC[min(stage, len(POSTER_FRAC)) - 1]
        n = int(math.ceil(len(self.posters) * frac))
        for _k, a in self.posters[:n]:
            a.set_actor_hidden_in_game(False)
        if self.hint is not None and stage >= 1:
            self.hint.set_actor_hidden_in_game(False)
        if self.eye is not None and stage >= 3:
            self.eye.set_actor_hidden_in_game(False)

    def ghost_show(self, x, y, face_x=None, face_y=None, level=0, dead=False, hold=10.0, glass=False, lean=0.0):
        if self.ghost is None:
            return
        self.gslide = None                                                    # ガラスをすべっている最中なら、止める
        fx = self.cx if face_x is None else face_x
        fy = self.cy if face_y is None else face_y
        yaw = math.degrees(math.atan2(fy - y, fx - x)) + GHOST_YAW
        gz = 0.0
        try:                                                                  # 足の高さ＝いま立っている地面（体の中心の高さ − カプセルの半分の高さ）
            cap = self.pawn.get_component_by_class(unreal.CapsuleComponent)
            gz = self.pawn.get_actor_location().z - float(cap.get_scaled_capsule_half_height())
        except Exception:  # noqa
            gz = 0.0
        try:
            real = self.ghost.get_component_by_class(unreal.SkeletalMeshComponent) is not None          # 本物のモデル（足元が原点）か、仮の筒（中心が原点）か
        except Exception:  # noqa
            real = False
        if not real:
            gz += 80.0
        self.ghost_z = gz + GHOST_Z
        self.ghost.set_actor_location_and_rotation(unreal.Vector(x, y, gz + GHOST_Z), unreal.Rotator(lean, 0, yaw), False, False)
        self.ghost.set_actor_hidden_in_game(False)
        if self.ghost_head is not None:
            self.ghost_head.set_actor_hidden_in_game(False)
        gfx = getattr(self, "gfx", None)
        if gfx is not None:
            gfx.begin(level, dead, hold, yaw, glass, lean)

    def ghost_hide(self):
        self.gslide = None
        gfx = getattr(self, "gfx", None)
        if gfx is not None:
            gfx.end()
        if self.ghost is not None:
            self.ghost.set_actor_hidden_in_game(True)
            if self.ghost_head is not None:
                self.ghost_head.set_actor_hidden_in_game(True)

    def begin_dead(self):
        """失敗：幽霊が目の前に出る → 赤く暗転 → しばらくして最初に戻る"""
        self.state, self.state_t = "DEAD", 0.0
        self.ending, self.dead_stage = "missing", 0                   # エンディング②：このあと、黒い画面 → 行方不明の新聞（tick_dead）
        self.inv_open = False
        self.set_lights(0.6)
        self.blackout(0.0)
        rot = self.pc.get_control_rotation()
        fwd = unreal.MathLibrary.get_forward_vector(rot)
        loc = self.pawn.get_actor_location()
        x, y = loc.x + fwd.x * DEAD_DIST, loc.y + fwd.y * DEAD_DIST
        self.ghost_show(x, y, loc.x, loc.y, level=len(GHOST_SPOTS) - 1, dead=True, hold=END2_SCARE)
        screen(self.world, "……みつけた", (255, 40, 40), END2_SCARE)
        try:
            self.pc.player_camera_manager.start_camera_fade(0.0, 1.0, 2.5, unreal.LinearColor(0.5, 0, 0, 1), False, True)
        except Exception as e:  # noqa
            log("  (赤い暗転ができません) %s" % e)
        log("失敗エンド（段階%d）→ エンディング②（行方不明）" % self.stage)

    def tick_dead(self, dt):
        """エンディング②：幽霊のジャンプスケア → 暗転 → 行方不明の新聞を全画面で出す → 一定時間後に最初に戻る"""
        t = self.state_t
        if self.dead_stage == 0 and t >= END2_SCARE:
            self.dead_stage = 1
            self.fade(True, END2_FADE)
        elif self.dead_stage == 1 and t >= END2_SCARE + END2_FADE + 0.2:
            self.dead_stage = 2
            self.ghost_hide()
            self.set_lights(0.0)                                        # 新聞のほかは、暗いまま（新聞は光らない材質なので、読める）
            self.set_flash(False)
            self.lock_input(True)
            self.show_picture("M_KDReadMissing", END2_SIZE, 1.14)
            self.blackout(0.0)
            self.fade(False, 0.8)
            screen(self.world, "エンディング②：行方不明", (255, 220, 220), END2_HOLD)
            screen(self.world, "◯◯大学の学生が、公衆電話ボックスの近くで行方不明になった", (230, 230, 230), END2_HOLD, "KD_END2_SUB")
            log("エンディング②（行方不明）：新聞を出しました（%.1f秒）" % END2_HOLD)
        end_t = max(RESTART_AFTER, END2_SCARE + END2_FADE + 0.2 + END2_HOLD)
        if t > end_t:
            self.state = "RESTART"
            log("最初に戻ります（RestartLevel）")
            unreal.SystemLibrary.execute_console_command(self.world, "RestartLevel")

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
        self.clamp_in_booth(loc, dt)
        self.tick_dial_anim(dt)
        self.tick_lid(dt)
        self.tick_fov(dt)
        self.tick_unstuck(loc, dt)
        self.update_flashlight()
        self.tick_sway()
        self.tick_glass_slide(dt)
        self.tick_hands(dt)
        if getattr(self, "gfx", None) is not None:
            self.gfx.update(dt)                                   # 幽霊の首かしげと表情（見えていないときは何もしない）
        self.tick_hud()
        if self.state == "READING":
            self.tick_reading()
        elif self.state == "SAFE":
            self.tick_safe(dt)
        elif self.state == "PHONE":
            self.tick_phone(dt)
        elif self.state == "BOX":
            self.tick_box(dt)
        elif self.state == "ENV":
            self.tick_env(dt)
        elif self.state == "EXIT":
            self.tick_exit(dt)
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
            if self.code_req:
                self.code_req = False
                self.start_code_seq(restart=True)
            self.tick_trapped(dt)
            self.tick_inventory()
            if not self.inv_open:                                   # 持ち物を開いている間は、E で電話・ふた・扉などが反応しない
                self.tick_items(loc)
        elif self.state == "DEAD":
            self.tick_dead(dt)
        elif self.state == "BREAK":
            self.tick_break_door(dt)

    # ---- 買った電話ボックス用：Eキーで入る ----
    def door_point(self):
        """入口の前（ボックスの外）の点。入口の向き front_yaw の +Y 側に half_n だけ出た所"""
        th = math.radians(self.front_yaw)
        # 入口の向き n = (+Y を front_yaw だけ回した向き)
        nx, ny = -math.sin(th), math.cos(th)
        return self.cx + nx * (self.half_n + 40.0), self.cy + ny * (self.half_n + 40.0), (nx, ny)

    def play(self, name):
        snd = getattr(self, "snd", {}).get(name)
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

    PHONE_GRID = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["del", "0", "call"]]

    def phone_frame(self):
        """電話機の面：(触る点 P, 入口の向き n, 電話に向かって右 T)"""
        th = math.radians(self.front_yaw)
        n = (-math.sin(th), math.cos(th))
        return self.phone_point(), n, (n[1], -n[0])

    def show_mouse(self, on):
        try:
            self.pc.set_editor_property("show_mouse_cursor", bool(on))
        except Exception as e:  # noqa
            log("  (マウスの矢印を切りかえられません) %s" % e)
        try:
            wbl = unreal.WidgetBlueprintLibrary
            if on:
                wbl.set_input_mode_game_and_ui(self.pc, None, unreal.MouseLockMode.DO_NOT_LOCK, False)
            else:
                wbl.set_input_mode_game_only(self.pc)
        except Exception as e:  # noqa
            log("  (入力のしかたを切りかえられません) %s" % e)

    def mouse_ray(self):
        """マウスの矢印が指している先への線：(始点, 向き)。取れなければ None"""
        try:
            r = self.pc.deproject_mouse_position_to_world()
        except Exception as e:  # noqa
            if not getattr(self, "_ray_err", False):
                self._ray_err = True
                log("  (マウスの位置を取れません) %s" % e)
            return None
        vals = list(r) if isinstance(r, (tuple, list)) else [r]
        vecs = [v for v in vals if hasattr(v, "x") and hasattr(v, "z")]
        if len(vecs) >= 2:
            return vecs[-2], vecs[-1]
        return None

    def phone_cell(self, ray):
        """マウスが指している電話のボタン (列, 行)。ボタンの外なら None"""
        P, n, T = self.phone_frame()
        O, D = ray
        den = D.x * n[0] + D.y * n[1]
        if abs(den) < 1e-4:
            return None
        t = ((P.x - O.x) * n[0] + (P.y - O.y) * n[1]) / den
        if t < 0:
            return None
        hx, hy, hz = O.x + D.x * t, O.y + D.y * t, O.z + D.z * t
        u = (hx - P.x) * T[0] + (hy - P.y) * T[1]
        v = hz - P.z
        col = int(math.floor((u - PHONE_KEY_U0) / PHONE_KEY_W))
        row = int(math.floor((PHONE_KEY_Z0 - v) / PHONE_KEY_H))
        if 0 <= col < 3 and 0 <= row < 4:
            return col, row
        return None

    def draw_phone_keys(self, hover):
        """ボタンの枠を線で出す（位置合わせ用）。いま指しているボタンは黄色"""
        if not PHONE_KEY_DEBUG:
            return
        try:
            P, n, T = self.phone_frame()
            yaw = math.degrees(math.atan2(n[1], n[0]))
            for r in range(4):
                for c in range(3):
                    u = PHONE_KEY_U0 + (c + 0.5) * PHONE_KEY_W
                    z = PHONE_KEY_Z0 - (r + 0.5) * PHONE_KEY_H
                    ctr = unreal.Vector(P.x + T[0] * u + n[0] * 0.3, P.y + T[1] * u + n[1] * 0.3, P.z + z)
                    col = unreal.LinearColor(1.0, 0.9, 0.2, 1.0) if hover == (c, r) else unreal.LinearColor(0.2, 0.8, 1.0, 1.0)
                    unreal.SystemLibrary.draw_debug_box(self.world, ctr, unreal.Vector(0.3, PHONE_KEY_W / 2.0, PHONE_KEY_H / 2.0), col, unreal.Rotator(0, 0, yaw), 0.06, 0.25)
        except Exception as e:  # noqa
            if not getattr(self, "_dbg_err", False):
                self._dbg_err = True
                log("  (ボタンの枠を描けません) %s" % e)

    def begin_phone(self):
        eye, _r = self.eye_info()
        self.phone_cam_on = False
        cam = getattr(self, "phone_cam", None)
        if cam is not None:                                     # 電話機専用のカメラ：電話機の正面（入口がわ）から見る固定の画面
            try:
                P, n, _T = self.phone_frame()
                pos = unreal.Vector(P.x + n[0] * PHONE_CAM_DIST, P.y + n[1] * PHONE_CAM_DIST, P.z)
                cam.set_actor_location_and_rotation(pos, unreal.Rotator(0, 0, math.degrees(math.atan2(-n[1], -n[0]))), False, False)
                try:
                    cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", float(PHONE_CAM_FOV))
                except Exception as e:  # noqa
                    log("  (電話カメラの視野を設定できません) %s" % e)
                self.phone_cam_on = self.set_view(cam, DIAL_ZOOM_TIME)
            except Exception as e:  # noqa
                log("  (電話カメラを置けません) %s" % e)
        if self.phone_cam_on:
            log("電話専用カメラに切りかえました")
        else:
            if cam is None:
                log("電話専用カメラ（KD_PhoneCam）が無いので、電話のほうを向くだけです。setup_game_fp.py をもう一度実行してください")
            try:
                self.pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, self.phone_point()))
            except Exception as e:  # noqa
                log("  (電話のほうを向けません) %s" % e)
        self.lock_input(True)
        self.show_mouse(True)
        if getattr(self, "key_lmb", None) is None:
            self.key_lmb = unreal.Key()
            self.key_lmb.set_editor_property("key_name", "LeftMouseButton")
        self.state, self.state_t = "PHONE", 0.0
        self.digits = ""
        log("電話を使い始めました（ボタンはマウスでクリックできます）")

    def end_phone(self):
        if getattr(self, "phone_cam_on", False):
            self.set_view(self.pawn, 0.45)
            self.phone_cam_on = False
        self.show_mouse(False)
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
                if self.state != "PHONE":                                 # 電話を閉じた（0714 など）
                    return
        except Exception as e:  # noqa
            log("  (電話のキーを読めません) %s" % e)
        hover = None
        try:                                                              # マウスでボタンをクリック
            ray = self.mouse_ray()
            hover = self.phone_cell(ray) if ray else None
            self.draw_phone_keys(hover)
            if hover is not None and self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self.key_lmb):
                lab = self.PHONE_GRID[hover[1]][hover[0]]
                if lab.isdigit():
                    if len(self.digits) < 8:
                        self.digits += lab
                        self.play("safe_click")
                elif lab == "del":
                    self.digits = self.digits[:-1]
                    self.play("safe_click")
                elif lab == "call" and self.digits:
                    num, self.digits = self.digits, ""
                    self.phone_call(num)
                    if self.state != "PHONE":
                        return
        except Exception as e:  # noqa
            if not getattr(self, "_ph_mouse_err", False):
                self._ph_mouse_err = True
                log("  (電話のマウス操作でエラー) %s" % e)
        if int(self.t * 8) != getattr(self, "_ph_k", -1):
            self._ph_k = int(self.t * 8)
            hv = ("  いま指しているボタン: %s" % {"del": "消す", "call": "かける"}.get(self.PHONE_GRID[hover[1]][hover[0]], self.PHONE_GRID[hover[1]][hover[0]])) if hover is not None else ""
            txt = "電話  番号: %s_   10円: %d枚   [クリック]か[0〜9] 入れる  「かける」か[Enter] 呼ぶ  「消す」か[BackSpace]  [Q] やめる%s" % (self.digits, self.coins, hv)
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
        if num == BREAK_CODE:                                             # エンディング③：いつでも・お金はいらない。プロテインを飲んでいれば、ドアぶっ壊し
            if self.protein_drunk:
                self.end_phone()
                self.begin_break_door()
            else:
                screen(self.world, "……つながらない（力が足りない気がする）", (180, 180, 180), 4.0)
                log("%s：プロテインをまだ飲んでいないので、つながらない" % BREAK_CODE)
            return
        msgs = {"117": ("ポーン…「7月14日 午前0時を お知らせします」", (200, 230, 255)),
                "177": ("「神狩村は…赤い雨です」", (255, 160, 160)),
                "104": ("「お調べします…外の木に 光った順に」", (200, 230, 255))}
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
                    self.on_flag("0714")                                  # 電話中なので、あとで処理される（deferred）
                else:
                    self.code_req = True                                  # お金はいらない：押すたびに、謎7を最初から
                self.end_phone()                                          # 電話カメラのままだとガラスが見えないので、閉じる
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
        self.safe_cam_on = False
        if self.dial_cam is not None:                          # 専用カメラの画面に切りかえる（つまみのおもて側から、アップ）
            self.safe_cam_on = self.set_view(self.dial_cam, DIAL_ZOOM_TIME)
            if self.safe_cam_on:
                log("ダイヤル専用カメラに切りかえました")
        if not self.safe_cam_on:
            if self.dial_cam is None:
                log("ダイヤル専用カメラ（KD_DialCam）が無いので、金庫のほうを向いて視野をせばめます。setup_game_fp.py をもう一度実行すると、専用カメラができます")
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

    def open_safe_visual(self):
        """金庫が開いた：閉じた本体とつまみを隠し、開いた箱を出して、ふたを回して開く"""
        if getattr(self, "safe_base", None) is None or getattr(self, "safe_lid", None) is None:
            log("開いた金庫（DialSafe_Base / DialSafe_Lid）が無いので、見た目は閉じたままです。setup_game_fp.py をもう一度実行してください")
            return
        try:
            for a in (self.dial_body, self.dial_knob):
                if a is not None:
                    a.set_actor_hidden_in_game(True)
            self.safe_base.set_actor_hidden_in_game(False)
            self.safe_lid.set_actor_hidden_in_game(False)
            for a in (self.safe_key, self.safe_coin, getattr(self, "safe_box", None)):
                if a is not None:
                    a.set_actor_hidden_in_game(False)
            self.play("safe_clunk")
            self.lid_pending, self.loot_t = 0.35, 0.0                 # 少しあとに、ふたがきしんで開く。鍵と10円は、見せたあと消える
            log("金庫のふたを開けます")
        except Exception as e:  # noqa
            log("  (開いた金庫を出せません) %s" % e)

    def tick_lid(self, dt):
        if getattr(self, "loot_t", -1.0) >= 0.0:                 # 鍵と10円は、手に入れたので、数秒見せたあと消す
            self.loot_t += dt
            if self.loot_t > 4.5:
                for a in (getattr(self, "safe_key", None), getattr(self, "safe_coin", None)):
                    if a is not None:
                        a.set_actor_hidden_in_game(True)
                self.loot_t = -1.0
        if getattr(self, "lid_pending", -1.0) >= 0.0:
            self.lid_pending -= dt
            if self.lid_pending <= 0.0:
                self.lid_pending = -1.0
                self.lid_t = 0.0
                self.play("safe_creak")
            return
        if getattr(self, "lid_t", -1.0) < 0.0 or getattr(self, "safe_lid", None) is None or getattr(self, "lid_rot0", None) is None:
            return
        self.lid_t += dt
        k = min(1.0, self.lid_t / max(0.1, SAFE_LID_TIME))
        e = 1.0 - (1.0 - k) ** 3
        if k >= 1.0:
            e = 1.0
        r = self.lid_rot0
        try:
            self.safe_lid.set_actor_rotation(unreal.Rotator(r.roll + SAFE_LID_SIGN * SAFE_LID_ANGLE * e, r.pitch, r.yaw), False)
        except Exception as ex:  # noqa
            log("  (ふたを回せません) %s" % ex)
            self.lid_t = -1.0
            return
        if k >= 1.0:
            self.lid_t = -1.0

    def set_view(self, target, t):
        """画面（カメラ）を、target の見ている画面に、t 秒かけて切りかえる。成功なら True"""
        try:
            try:
                self.pc.set_view_target_with_blend(target, float(t), unreal.ViewTargetBlendFunction.VTBLEND_CUBIC, 2.0, False)
            except Exception:  # noqa
                self.pc.set_view_target_with_blend(target, float(t))
            return True
        except Exception as e:  # noqa
            log("  (画面を切りかえられません) %s" % e)
            return False

    def end_safe(self):
        if getattr(self, "safe_cam_on", False):
            self.set_view(self.pawn, 0.45)
            self.safe_cam_on = False
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
            tgt = DIAL_FOV if (self.state == "SAFE" and not getattr(self, "safe_cam_on", False)) else self.fov_base
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

    def shrink_capsule(self):
        """体（カプセル）を細くする：せまい電話ボックスの中で、壁にぶつかってガタガタしないように"""
        if PAWN_RADIUS <= 0 or self.pawn is None:
            return
        try:
            cap = self.pawn.get_component_by_class(unreal.CapsuleComponent)
            r0 = float(cap.get_unscaled_capsule_radius())
            hh = float(cap.get_unscaled_capsule_half_height())
            if r0 > PAWN_RADIUS:
                cap.set_capsule_size(PAWN_RADIUS, hh, True)
                log("体の太さを %.0f → %.0fcm にしました（壁ぎわのガタガタ止め）" % (r0, PAWN_RADIUS))
        except Exception as e:  # noqa
            log("  (体の太さを変えられません) %s" % e)

    def booth_limits(self):
        """ボックスの中で、体の中心が動ける範囲：(入口方向n, 横方向t, 奥行きの限界ln, 横の限界lt)"""
        th = math.radians(self.front_yaw)
        n = (-math.sin(th), math.cos(th))
        t = (math.cos(th), math.sin(th))
        ln = max(8.0, getattr(self, "in_n", self.half_n - 20.0) - PAWN_RADIUS - TRAP_MARGIN)
        lt = max(8.0, getattr(self, "in_t", self.half_t - 20.0) - PAWN_RADIUS - TRAP_MARGIN)
        return n, t, ln, lt

    def clamp_in_booth(self, loc, dt=0.016):
        """閉じ込められている間は、壁の外へ出られない。範囲を出たら、なめらかに押しもどす（ぱっと瞬間移動しない）"""
        if self.state not in ("CLOSING", "TRAPPED", "SAFE", "PHONE", "READING", "ENV") or self.pawn is None:
            return
        (nx, ny), (tx, ty), ln, lt = self.booth_limits()
        rx, ry = loc.x - self.cx, loc.y - self.cy
        tn, tt = rx * nx + ry * ny, rx * tx + ry * ty
        cn, ct = max(-ln, min(ln, tn)), max(-lt, min(lt, tt))
        if abs(cn - tn) > 0.5 or abs(ct - tt) > 0.5:
            k = min(1.0, dt * 12.0)
            mn, mt = tn + (cn - tn) * k, tt + (ct - tt) * k
            self.pawn.set_actor_location(unreal.Vector(self.cx + nx * mn + tx * mt, self.cy + ny * mn + ty * mt, loc.z), False, False)

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
                    self.play("safe_click")
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

    # ---- 金庫の中の箱（16個のボタンを、2→15→4→9 の順に押す） ----
    def box_setup(self):
        """箱のボタンの面を一度だけ計算して保存する（tick では計算だけ）。frame = (中心, 面の法線, 右, 上, ボタン1個の大きさ)"""
        box, bcam = getattr(self, "safe_box", None), getattr(self, "box_cam", None)
        if box is not None and bcam is not None:
            self.box_view = bcam
            sc = box.get_actor_scale3d().x
            bl, cl = box.get_actor_location(), bcam.get_actor_location()
            fx, fy = cl.x - bl.x, cl.y - bl.y                       # 箱から、おもて側（カメラのある側）へ向かう水平の向き
            ln = math.hypot(fx, fy) or 1.0
            fx, fy = fx / ln, fy / ln
            rx, ry = fy, -fx                                         # おもてを見たときの右（setup の right = (f[1], -f[0]) と同じ）
            if BOX_FLIP:
                rx, ry = -rx, -ry
            c = unreal.Vector(bl.x, bl.y, bl.z + BOX_TOP_H * sc)
            n, r, u = unreal.Vector(0.0, 0.0, 1.0), unreal.Vector(rx, ry, 0.0), unreal.Vector(-fx, -fy, 0.0)      # 上（図の上）＝うしろ側＝ボタン1の列
            pitch = BOX_BTN * sc
            self.box_rot = box.get_actor_rotation()
            self.box_ext = unreal.Vector(pitch * 0.45, pitch * 0.45, 0.3)
            lift, real = 0.25, True
        else:
            self.box_view = self.dial_cam
            o = self.dial_cam.get_actor_location()
            n, r, u = self.dial_cam.get_actor_forward_vector(), self.dial_cam.get_actor_right_vector(), self.dial_cam.get_actor_up_vector()
            if BOX_FLIP:
                r = unreal.Vector(-r.x, -r.y, -r.z)
            c = unreal.Vector(o.x + n.x * BOX_DIST, o.y + n.y * BOX_DIST, o.z + n.z * BOX_DIST)
            pitch = BOX_BTN
            self.box_rot = self.dial_cam.get_actor_rotation()
            self.box_ext = unreal.Vector(0.1, pitch * 0.45, pitch * 0.45)
            lift, real = 0.0, False
        self.box_real = real
        self.box_fr = (c, n, r, u, pitch)
        pts = []
        for k in range(16):
            x, y = (k % 4 - 1.5) * pitch, (1.5 - k // 4) * pitch
            pts.append(unreal.Vector(c.x + r.x * x + u.x * y + n.x * lift, c.y + r.y * x + u.y * y + n.y * lift, c.z + r.z * x + u.z * y + n.z * lift))
        self.box_pts = pts
        log("箱のボタンの面: %s・中心=(%.0f,%.0f,%.0f)・ボタン1個=%.1fcm" % ("本物の箱（KD_BoxCam）" if real else "デバッグ（ダイヤルのカメラの前）", c.x, c.y, c.z, pitch))

    def box_cell(self, ray):
        """マウスが指している箱のボタンの番号（1〜16）。ボタンの外なら None"""
        c, f, r, u, pitch = self.box_fr
        O, D = ray
        den = D.x * f.x + D.y * f.y + D.z * f.z
        if abs(den) < 1e-4:
            return None
        t = ((c.x - O.x) * f.x + (c.y - O.y) * f.y + (c.z - O.z) * f.z) / den
        if t < 0:
            return None
        h = (O.x + D.x * t - c.x, O.y + D.y * t - c.y, O.z + D.z * t - c.z)
        x = h[0] * r.x + h[1] * r.y + h[2] * r.z
        y = h[0] * u.x + h[1] * u.y + h[2] * u.z
        col = int(math.floor(x / pitch + 2.0))
        row = int(math.floor(2.0 - y / pitch))
        if 0 <= col < 4 and 0 <= row < 4:
            return row * 4 + col + 1
        return None

    def draw_box_buttons(self, hover):
        if not (BOX_DEBUG or (BOX_HOVER and self.box_real and hover is not None)):
            return
        try:
            for n in (range(1, 17) if BOX_DEBUG else (hover,)):
                p = self.box_pts[n - 1]
                done = n in self.box_entries
                col_ = unreal.LinearColor(1.0, 0.9, 0.2, 1.0) if hover == n else (unreal.LinearColor(0.4, 1.0, 0.4, 1.0) if done else unreal.LinearColor(0.2, 0.8, 1.0, 1.0))
                unreal.SystemLibrary.draw_debug_box(self.world, p, self.box_ext, col_, self.box_rot, 0.06, 0.2)
                if BOX_DEBUG:
                    unreal.SystemLibrary.draw_debug_string(self.world, p, str(n), None, col_, 0.06)
        except Exception as e:  # noqa
            if not getattr(self, "_box_dbg_err", False):
                self._box_dbg_err = True
                log("  (箱のボタンを描けません) %s" % e)

    def begin_box(self):
        """金庫の中の箱を調べる：箱の専用カメラ（なければダイヤルのカメラ）の正面に、16個のボタンを出して、マウスで押す"""
        try:
            self.box_setup()
        except Exception as e:  # noqa
            log("  (箱のボタンの面を計算できません) %s" % e)
            return
        try:
            cc = self.box_view.get_component_by_class(unreal.CameraComponent)
            self.box_fov0 = float(cc.get_editor_property("field_of_view"))
            cc.set_editor_property("field_of_view", float(BOX_CAM_FOV))
        except Exception as e:  # noqa
            self.box_fov0 = None
            log("  (箱のカメラの視野を設定できません) %s" % e)
        self.box_cam_on = self.set_view(self.box_view, DIAL_ZOOM_TIME)
        self.lock_input(True)
        self.show_mouse(True)
        if getattr(self, "key_lmb", None) is None:
            self.key_lmb = unreal.Key()
            self.key_lmb.set_editor_property("key_name", "LeftMouseButton")
        self.key_quit = unreal.Key()
        self.key_quit.set_editor_property("key_name", "Q")
        self.state, self.state_t = "BOX", 0.0
        self.box_entries = []
        log("金庫の中の箱を調べ始めました（ボタンはマウスでクリック）")

    def end_box(self):
        if getattr(self, "box_cam_on", False):
            self.set_view(self.pawn, 0.45)
            self.box_cam_on = False
        if getattr(self, "box_fov0", None) is not None:
            try:
                self.box_view.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", float(self.box_fov0))
            except Exception:  # noqa
                pass
        self.show_mouse(False)
        self.lock_input(False)
        self.state, self.state_t = "TRAPPED", 0.0

    def tick_box(self, dt):
        hover = None
        try:
            if self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self.key_quit):
                self.end_box()
                return
            ray = self.mouse_ray()
            hover = self.box_cell(ray) if ray else None
            self.draw_box_buttons(hover)
            if hover is not None and self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self.key_lmb):
                self.box_press(hover)
        except Exception as e:  # noqa
            if not getattr(self, "_box_err", False):
                self._box_err = True
                log("  (箱のマウス操作でエラー) %s" % e)
        if int(self.t * 8) != getattr(self, "_box_k", -1):
            self._box_k = int(self.t * 8)
            done = " → ".join(str(n) for n in self.box_entries) or "なし"
            txt = "金庫の中の箱  [クリック] ボタンを押す  [Q] やめる   押した順: %s%s" % (done, ("   いま指しているボタン: %d" % hover) if hover else "")
            try:
                unreal.SystemLibrary.print_string(self.world, txt, True, False, unreal.LinearColor(1.0, 0.85, 0.85, 1), 0.3, "KD_BOX_UI")
            except Exception:  # noqa
                pass

    def box_press(self, n):
        self.box_entries.append(n)
        k = len(self.box_entries)
        want = list(BOX_CODE)
        if self.box_entries[-1] != want[k - 1]:
            screen(self.world, "ブッ…（はずれ。最初から）", (255, 120, 120), 2.5)
            log("金庫の箱：はずれ %s" % (self.box_entries,))
            self.box_entries = []
            return
        self.play("safe_click")
        if k < len(want):
            screen(self.world, "カチッ（%d/%d）" % (k, len(want)), (200, 255, 200), 1.5)
            return
        self.box_done = True
        self.has_envelope = True
        self.play("latch")
        self.end_box()
        screen(self.world, "箱が開いた。赤い封筒が入っていた（4けたの鍵がついている）", (255, 170, 170), 6.0)
        log("金庫の中の箱が開きました（赤い封筒）。次：封筒の4けたの鍵（開いた金庫を見て E）")
        self.on_flag("金庫の箱")

    # ---- 赤い封筒の4けたの鍵（数字キーで入れる。電話の番号入れと同じキー） ----
    def begin_env(self):
        self.lock_input(True)
        self.state, self.state_t = "ENV", 0.0
        self.env_digits = ""
        log("赤い封筒の鍵を使い始めました")

    def end_env(self):
        self.lock_input(False)
        self.state, self.state_t = "TRAPPED", 0.0

    def tick_env(self, dt):
        try:
            for name, ch in self.PHONE_KEYS:
                if self.pc.was_input_key_just_pressed(self._key(name)) and len(self.env_digits) < 4:
                    self.env_digits += ch
                    self.play("safe_click")
            if self.pc.was_input_key_just_pressed(self._key("BackSpace")):
                self.env_digits = self.env_digits[:-1]
            if self.state_t > 0.3 and self.pc.was_input_key_just_pressed(self._key("Q")):
                self.end_env()
                return
            if self.state_t > 0.3 and (self.pc.was_input_key_just_pressed(self._key("Enter")) or self.pc.was_input_key_just_pressed(self.key_e)):
                if len(self.env_digits) == 4:
                    self.env_try()
                    return
                screen(self.world, "4けた入れてください", (255, 200, 150), 1.5)
        except Exception as e:  # noqa
            log("  (封筒の鍵のキーを読めません) %s" % e)
        if int(self.t * 8) != getattr(self, "_env_k", -1):
            self._env_k = int(self.t * 8)
            slots = " ".join(list(self.env_digits) + ["＿"] * (4 - len(self.env_digits)))
            txt = "赤い封筒の鍵  [ %s ]   [0〜9] 入れる  [Enter]か[%s] 決める  [BackSpace] 消す  [Q] やめる" % (slots, ENTER_KEY)
            try:
                unreal.SystemLibrary.print_string(self.world, txt, True, False, unreal.LinearColor(1.0, 0.8, 0.8, 1), 0.3, "KD_ENV_UI")
            except Exception:  # noqa
                pass

    def env_try(self):
        code, self.env_digits = self.env_digits, ""
        if code == "".join(str(d) for d in ENVELOPE_CODE):
            self.envelope_open = True
            self.has_door_key = True
            self.play("latch")
            self.end_env()
            screen(self.world, "封筒の中に、鍵が入っていた（扉の鍵）", (255, 240, 160), 6.0)
            log("赤い封筒が開きました（扉の鍵）。次：扉を見て E で外へ")
            self.on_flag("封筒")
            return
        self.play("safe_clunk")
        decoy = ENVELOPE_DECOYS.get(code)
        ans = "".join(str(d) for d in ENVELOPE_CODE)
        if decoy is None and sorted(code) == sorted(ans):               # 数字は合っているが、順番がちがう
            screen(self.world, "数字は合っている気がする……順番がちがう？", (255, 200, 150), 4.0)
            log("封筒の鍵：数字は合っているが順番がちがう %s" % code)
            if CODE_PERM_SAFE:
                return
        else:
            screen(self.world, decoy if decoy else "ブッ…（はずれ）", (255, 120, 120), 3.0)
        if decoy is not None or sorted(code) != sorted(ans):
            log("封筒の鍵：はずれ %s%s" % (code, "（ひっかけ）" if decoy else ""))
        if ENVELOPE_WRONG_GHOST and getattr(self, "trapped_started", False):
            self.pressure()                    # 謎が進まないときの圧力と同じ：幽霊が1歩近づく（近づききったら失敗）

    # ---- 扉の鍵で外へ出る（エンディング①） ----
    def door_inner_point(self):
        """扉を見ているか調べる点：入口の内がわ（ボックスの入口の壁）、目の高さ"""
        th = math.radians(self.front_yaw)
        nx, ny = -math.sin(th), math.cos(th)
        eye_z = getattr(self, "eye_z", None)
        return unreal.Vector(self.cx + nx * (self.half_n - 8.0), self.cy + ny * (self.half_n - 8.0), eye_z if eye_z is not None else getattr(self, "cz", 200.0))

    def relocate_outside(self, reset_door=True):
        """外へ出す共通処理（エンディング①③）：演出を止め、光を戻し、プレイヤーを入口の外へ移して外向きにする"""
        self.steps, self.step_i, self.pending = [], 0, []            # 演出はぜんぶ止める
        self.hide_all()
        self.set_lights(1.0)
        self.set_flash_scale(FLASH_OUTSIDE)
        if reset_door and self.hinge is not None:
            self.door_yaw = DOOR_OPEN_YAW
            self.hinge.set_actor_rotation(unreal.Rotator(0, 0, self.door_base + self.door_yaw), False)
        th = math.radians(self.front_yaw)
        nx, ny = -math.sin(th), math.cos(th)
        loc = self.pawn.get_actor_location()
        self.pawn.set_actor_location(unreal.Vector(self.cx + nx * (self.half_n + 110.0), self.cy + ny * (self.half_n + 110.0), loc.z), False, False)
        try:
            self.pc.set_control_rotation(unreal.Rotator(0, 0, math.degrees(math.atan2(ny, nx))))       # 外むき（ボックスに背を向ける）
        except Exception as e:  # noqa
            log("  (向きを変えられません) %s" % e)

    def begin_exit(self):
        self.state, self.state_t = "EXIT", 0.0
        self.exit_stage = 0
        self.ending = "escape"
        self.inv_open = False
        self.lock_input(True)
        self.play("latch")
        self.play("door_open")
        self.fade(True, ENTER_FADE_OUT)
        log("扉の鍵で外へ出ます（暗転＋ドアの音）")

    def tick_exit(self, dt):
        t = self.state_t
        if self.exit_stage == 0 and t >= ENTER_FADE_OUT + 0.3:            # 真っ暗になってから、外へ移す
            self.exit_stage = 1
            self.relocate_outside()
        elif self.exit_stage == 1 and t >= ENTER_FADE_OUT + 1.2:
            self.exit_stage = 2
            self.blackout(0.0)
            self.fade(False, ENTER_FADE_IN)
            self.lock_input(False)
            screen(self.world, "外に出られた……（エンディング①：脱出）", (200, 255, 200), 10.0)
            log("脱出エンド①（ending=%s）" % self.ending)
        elif self.exit_stage == 2 and t >= ENTER_FADE_OUT + 1.2 + ENTER_FADE_IN:
            self.state, self.state_t = "ESCAPED", 0.0

    # ---- エンディング③：プロテイン＋2929 でドアをぶっ壊す ----
    def flash_color(self, color, alpha, dur):
        """画面を一瞬、色でおおって（alpha）、dur 秒でもとに戻す"""
        try:
            self.pc.player_camera_manager.start_camera_fade(alpha, 0.0, dur, unreal.LinearColor(color[0], color[1], color[2], 1.0), False, False)
        except Exception as e:  # noqa
            log("  (画面をピカッとできません) %s" % e)

    def begin_break_door(self):
        self.state, self.state_t = "BREAK", 0.0
        self.break_stage = 0
        self.ending = "break"
        self.inv_open = False
        self.steps, self.step_i, self.pending = [], 0, []            # 演出はぜんぶ止める（点滅の途中でも、明るく戻す）
        self.set_lights(1.0)
        self.blackout(0.0)
        self.lock_input(True)
        self.fade(True, 0.25)
        self.door_p0 = self.hinge.get_actor_location() if self.hinge is not None else None
        self.door_r0 = self.hinge.get_actor_rotation() if self.hinge is not None else None
        log("エンディング③：ドアぶっ壊し（プロテイン＋%s）" % BREAK_CODE)

    def tick_break_door(self, dt):
        t = self.state_t
        t_card, t_blast = 0.3, 0.3 + BREAK_CARD_TIME
        th = math.radians(self.front_yaw)
        nx, ny = -math.sin(th), math.cos(th)
        if self.break_stage == 0:
            if t >= t_card and int(t * 10) != getattr(self, "_brk_k", -1):          # ムキッ！のカットイン：文字を段階的に大きく（print_string は大きさを変えられないので、飾りと文字数でズーム）
                self._brk_k = int(t * 10)
                k = min(1.0, (t - t_card) / BREAK_CARD_TIME)
                txt = ("ム" if k < 0.25 else "ムキ" if k < 0.5 else "ムキッ！") if k < 0.7 else "＼＼　ムキッ！！　／／"
                pad = "\n" * 3
                screen(self.world, pad + "★ " + txt + " ★" + pad, (255, 215, 60), 0.3, "KD_MUSCLE")
            if t >= t_blast:
                self.break_stage = 1
                self.t_fly0 = t
                self.blackout(0.0)
                self.flash_color((1.0, 1.0, 1.0), 1.0, 0.6)             # 白くピカッ → ドアが吹っ飛ぶ
                self.play("safe_clunk")
                self.play("door_open")
                try:
                    self.pc.set_control_rotation(unreal.Rotator(0, 0, math.degrees(math.atan2(ny, nx))))       # 扉のほうを向く
                except Exception as e:  # noqa
                    log("  (扉のほうを向けません) %s" % e)
                self.shake_base = self.pc.get_control_rotation()
                screen(self.world, "ドガァン！！", (255, 240, 160), 2.0)
                log("ドアが吹っ飛びます（ドアの部品=%s）" % ("あり" if self.hinge is not None else "なし：白い光だけ"))
        elif self.break_stage == 1:
            k = min(1.0, (t - self.t_fly0) / max(0.1, BREAK_FLY_TIME))
            if self.hinge is not None and self.door_p0 is not None:        # 物理を使わず、位置と回転を補間：外向きに飛びながらくるくる回る
                d = BREAK_FLY_DIST * k
                lift = 120.0 * math.sin(math.pi * k)
                self.hinge.set_actor_location(unreal.Vector(self.door_p0.x + nx * d, self.door_p0.y + ny * d, self.door_p0.z + lift), False, False)
                self.hinge.set_actor_rotation(unreal.Rotator(self.door_r0.roll + 540.0 * k, self.door_r0.pitch + 360.0 * k, self.door_r0.yaw + 720.0 * k), False)
                self.door_broken = True
            if BREAK_SHAKE > 0 and k < 0.7:                               # 画面のゆれ（見る向きに小さなランダムを足す）
                try:
                    b = self.shake_base
                    a = BREAK_SHAKE * (1.0 - k)
                    self.pc.set_control_rotation(unreal.Rotator(0, b.pitch + random.uniform(-a, a), b.yaw + random.uniform(-a, a)))
                except Exception:  # noqa
                    pass
            if k >= 1.0:
                self.break_stage = 2
                self.t_fly1 = t
                try:
                    b = self.shake_base
                    self.pc.set_control_rotation(unreal.Rotator(0, b.pitch, b.yaw))
                except Exception:  # noqa
                    pass
        elif self.break_stage == 2 and t >= self.t_fly1 + 0.5:
            self.break_stage = 3
            self.fade(True, 0.5)
        elif self.break_stage == 3 and t >= self.t_fly1 + 1.1:
            self.break_stage = 4
            self.relocate_outside(reset_door=False)                       # ①と同じ：外へ移す（ドアは飛んでいったまま）
            self.blackout(0.0)
            self.fade(False, ENTER_FADE_IN)
            self.lock_input(False)
            screen(self.world, "エンディング③：ドアぶっ壊し", (255, 230, 120), 10.0)
            screen(self.world, "幽霊より筋肉が強かった", (255, 255, 255), 10.0, "KD_END3_SUB")
            log("ドアぶっ壊しエンド③（ending=%s）" % self.ending)
        elif self.break_stage == 4 and t >= self.t_fly1 + 1.1 + ENTER_FADE_IN:
            self.state, self.state_t = "ESCAPED", 0.0

    # ---- 持ち物（I キー）：一覧／プロテインを飲む／財布（ジムの会員証）を見る ----
    def inv_lines(self):
        pr = "なし" if not self.has_protein else ("飲んだ（空）" if self.protein_drunk else "あり")
        return ["持ち物", "　10円: %d枚" % self.coins,
                "　鍵: %s" % ("、".join([n for n, ok in (("小さな鍵", self.has_key and not self.hatch_open), ("扉の鍵", self.has_door_key)) if ok]) or "なし"),
                "　赤い封筒: %s" % ("開けた" if self.envelope_open else "あり" if self.has_envelope else "なし"),
                "　プロテイン: %s" % pr, "　財布（ジムの会員カード入り）"]

    def tick_inventory(self):
        """TRAPPED の間だけ呼ぶ。開いている間は、他の E の操作（tick_items）は止める"""
        try:
            if self.pc.was_input_key_just_pressed(self._key(INV_KEY)):
                self.inv_open = not self.inv_open
                self.play("safe_click")
                if not self.inv_open:
                    screen(self.world, "", (255, 255, 255), 0.01, "KD_INV")
            if not self.inv_open:
                return
            if self.pc.was_input_key_just_pressed(self._key(INV_DRINK_KEY)):
                self.drink_protein()
            elif self.pc.was_input_key_just_pressed(self._key(INV_WALLET_KEY)):
                self.inv_open = False
                screen(self.world, "", (255, 255, 255), 0.01, "KD_INV")
                self.begin_read("M_KDReadGym", 1.585)                     # 会員証を目の前に出す。[E] で閉じる
                log("財布を見ました（ジムの会員証）")
                return
        except Exception as e:  # noqa
            if not getattr(self, "_inv_err", False):
                self._inv_err = True
                log("  (持ち物のキーを読めません) %s" % e)
            return
        if int(self.t * 4) != getattr(self, "_inv_k", -1):
            self._inv_k = int(self.t * 4)
            can = self.has_protein and not self.protein_drunk
            txt = "\n".join(self.inv_lines()) + "\n[%s] プロテインを飲む%s   [%s] 財布を見る   [%s] とじる" % (
                INV_DRINK_KEY, "" if can else "（もう飲めない）", INV_WALLET_KEY, INV_KEY)
            screen(self.world, txt, (255, 240, 200), 0.4, "KD_INV")

    def drink_protein(self):
        if not self.has_protein or self.protein_drunk:
            screen(self.world, "もうプロテインはない", (200, 200, 200), 2.0)
            return
        self.protein_drunk = True
        self.play("latch")
        self.flash_color((1.0, 0.95, 0.4), 0.85, 0.3)
        screen(self.world, "プロテインを飲んだ。力がみなぎる……（ギラッ）", (255, 230, 90), 5.0)
        log("プロテインを飲んだ（%s で電話すると…）" % BREAK_CODE)

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
        self.play("latch")
        if k == len(want):
            self.safe_open = True
            self.has_key = True
            self.coins += 1
            self.open_safe_visual()
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
        if not ARROW_MOVE or self.state not in ("WALK", "TRAPPED", "ESCAPED") or not self.is_char or getattr(self, "manual_on", False) or MANUAL_WALK == "on":
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
        if MANUAL_WALK == "off" or self.state not in ("WALK", "TRAPPED", "ESCAPED"):
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
            if self.state == "TRAPPED":                                   # 閉じ込められている間：壁ぎわでは、壁へ向かう動きを消す（押しつけてガタガタしない）
                (bnx, bny), (btx, bty), bln, blt = self.booth_limits()
                q = self.pawn.get_actor_location()
                qn, qt = (q.x - self.cx) * bnx + (q.y - self.cy) * bny, (q.x - self.cx) * btx + (q.y - self.cy) * bty
                dn, dtt = dx * bnx + dy * bny, dx * btx + dy * bty
                if (qn >= bln - 1.0 and dn > 0) or (qn <= -bln + 1.0 and dn < 0):
                    dn = 0.0
                if (qt >= blt - 1.0 and dtt > 0) or (qt <= -blt + 1.0 and dtt < 0):
                    dtt = 0.0
                dx, dy = bnx * dn + btx * dtt, bny * dn + bty * dtt
                if abs(dx) + abs(dy) < 1e-3:
                    if mvc is not None:
                        v0 = mvc.get_editor_property("velocity")
                        mvc.set_editor_property("velocity", unreal.Vector(0.0, 0.0, v0.z))
                    self._manual_moving = False
                    return
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
        return (f.x * d.x + f.y * d.y + f.z * d.z) / dist > LOOK_CONE

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
            if not self.hatch_open and self.looking_at_pt(hp, ITEM_RANGE + 30.0, 0.96):
                self.prompt_item("[%s] 電話の下のふたを開ける" % ENTER_KEY, "HATCH")
                if pressed:
                    self.open_hatch()
                    return
            elif self.looking_at_pt(pp, ITEM_RANGE + 30.0, 0.95):
                self.prompt_item("[%s] 電話をかける" % ENTER_KEY, "PHONE")
                if pressed:
                    self.begin_phone()
                    return
        if self.dial_body is not None and not self.safe_open and self.state == "TRAPPED" and self.looking_at(self.dial_knob or self.dial_body, ITEM_RANGE):
            self.prompt_item("[%s] 金庫のダイヤルを回す" % ENTER_KEY, "SAFE")
            if pressed:
                self.begin_safe()
                return
        if self.safe_open and not self.box_done and self.state == "TRAPPED" and getattr(self, "safe_base", None) is not None and getattr(self, "dial_cam", None) is not None and self.looking_at(self.safe_base, ITEM_RANGE):
            self.prompt_item("[%s] 金庫の中の箱を調べる" % ENTER_KEY, "BOX")
            if pressed:
                self.begin_box()
                return
        if self.box_done and self.has_envelope and not self.envelope_open and self.state == "TRAPPED" and getattr(self, "safe_base", None) is not None and self.looking_at(self.safe_base, ITEM_RANGE):
            self.prompt_item("[%s] 赤い封筒を開ける" % ENTER_KEY, "ENV")
            if pressed:
                self.begin_env()
                return
        if self.state == "TRAPPED" and self.looking_at_pt(self.door_inner_point(), DOOR_RANGE, 0.9):
            if self.has_door_key:
                self.prompt_item("[%s] 鍵で扉を開ける" % ENTER_KEY, "DOOR")
                if pressed:
                    self.begin_exit()
                    return
            elif pressed:
                screen(self.world, "鍵がかかっている", (255, 200, 150), 2.0)
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

    def show_picture(self, mat_name, size, aspect):
        """絵（材質）を、目の前（READ_DIST）に出す。新聞・本・メモ・会員証・行方不明の新聞で共通。状態は変えない"""
        if self.read_plane is None:
            log("  (KD_ReadPlane が無いので絵を出せません) %s" % mat_name)
            return
        try:
            m = unreal.EditorAssetLibrary.load_asset("/Game/KoushuDenwa/Materials/" + mat_name)
            if m is not None:
                self.read_plane.get_component_by_class(unreal.StaticMeshComponent).set_material(0, m)
            else:
                log("  (材質 %s がありません。setup_game_fp.py を実行し直してください)" % mat_name)
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
        self.read_plane.set_actor_scale3d(unreal.Vector(size * aspect / 50.0, 1.0, size / 70.0))
        self.read_plane.set_actor_hidden_in_game(False)

    def begin_read(self, mat_name="M_KDRead", aspect=1.0):
        """新聞・本を目の前に出す。歩く・見回すを止めて、Eでとじる"""
        self.read_return = self.state
        self.after_read = getattr(self, "after_read", None) if mat_name != "M_KDRead" else None
        self.show_picture(mat_name, READ_SIZE, aspect)
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
            if self.glass_enabled(sp):
                return self.glass_steps(sp, GHOST_HOLD[n_hold])
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
        if self.state not in ("TRAPPED", "PHONE", "SAFE", "BOX", "READING", "ENV") or not getattr(self, "trapped_started", False):
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
        if name == "0714":                                 # 謎7：ふつうの抽選はしない。そのときの強さの「張り紙」の札を使ったことにして、謎7の場面を流す
            self.used.add(("poster", level))
            self.last_type = "poster"
            log("謎 %d/%d（%s）→ 謎7の場面（張り紙の札 強さ%d を使ったことにする）" % (self.solved, PUZZLE_COUNT, name, level))
            screen(self.world, "謎 %d/%d" % (self.solved, PUZZLE_COUNT), (200, 255, 200), 3.0)
            self.start_code_seq()
            return
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
        self.code_clear()

    def ghost_scene(self, r):
        self.stage = r + 1
        gx, gy = GHOST_SPOTS[min(r, len(GHOST_SPOTS) - 1)]
        th = math.radians(self.front_yaw)               # 入口の向きに合わせて回す（入口が +Y のとき 0 度）
        hold = GHOST_HOLD[min(self.level_now, len(GHOST_HOLD) - 1)]
        self.ghost_show(self.cx + gx * math.cos(th) - gy * math.sin(th), self.cy + gx * math.sin(th) + gy * math.cos(th), None, None, level=r, hold=hold)
        screen(self.world, GHOST_SUBS[min(r, len(GHOST_SUBS) - 1)], (200, 220, 255), 4.0)
        log("幽霊の場面 %d" % (r + 1))

    # ---- ガラスに張りつく幽霊（GLASSGHOST_*）と、ガラスの外の手形（KD_Hand_*） ----
    def glass_enabled(self, sp):
        return bool(GLASSGHOST_ENABLE) and self.ghost is not None and (sp + 1) in [int(c) for c in GLASSGHOST_CARDS] and len(self.glass_faces()) > 0

    def glass_faces(self):
        return [(str(f[0]).upper(), max(-1.0, min(1.0, float(f[1])))) for f in GLASSGHOST_FACES if str(f[0]).upper() in ("R", "L", "F", "B")]

    def glass_off(self):
        """ガラスの外の面から、幽霊の足もとまでの距離（cm）。体をかたむけた分（頭が前に出る）と顔の厚みを足して、顔とガラスのすきまが GLASSGHOST_GAP になるようにする"""
        rad = math.radians(abs(GLASSGHOST_LEAN_DEG))
        return GLASSGHOST_GAP + GLASSGHOST_FACE_DEPTH * math.cos(rad) + GLASSGHOST_HEIGHT * GLASSGHOST_HEAD * math.sin(rad)

    def glass_rect(self):
        off = self.glass_off()
        gn = getattr(self, "glass_n", None) or max(20.0, self.half_n - 3.0)
        gt = getattr(self, "glass_t", None) or max(20.0, self.half_t - 3.0)
        return gn, gt, gn + off, gt + off                                    # ガラスの半分(n, t)・幽霊の足もとが並ぶ長方形の半分(n, t)

    def glass_s(self, face):
        """面（壁, 位置）を、長方形のまわりの道のりの上の位置 s にする（入口 F の左端から、R→B→L の順に一周）"""
        gn, gt, hn, ht = self.glass_rect()
        wall, f = face
        if wall == "F":
            return ht + f * gt
        if wall == "R":
            return 2 * ht + (hn - f * gn)
        if wall == "B":
            return 2 * ht + 2 * hn + (ht - f * gt)
        return 4 * ht + 2 * hn + (f * gn + hn)

    def glass_pt(self, s):
        """道のりの位置 s → (入口方向の位置 n, 横の位置 t, 壁の名前)"""
        gn, gt, hn, ht = self.glass_rect()
        s %= 4 * (hn + ht)
        if s < 2 * ht:
            return hn, s - ht, "F"
        s -= 2 * ht
        if s < 2 * hn:
            return hn - s, ht, "R"
        s -= 2 * hn
        if s < 2 * ht:
            return -hn, ht - s, "B"
        s -= 2 * ht
        return -hn + s, -ht, "L"

    def glass_world(self, n, t):
        th = math.radians(self.front_yaw)
        return self.cx + n * (-math.sin(th)) + t * math.cos(th), self.cy + n * math.cos(th) + t * math.sin(th)

    def glass_inward(self, wall):
        """壁の名前 → 内向きの単位ベクトル（世界）"""
        th = math.radians(self.front_yaw)
        nx, ny, tx, ty = -math.sin(th), math.cos(th), math.cos(th), math.sin(th)
        return {"F": (-nx, -ny), "B": (nx, ny), "R": (-tx, -ty), "L": (tx, ty)}[wall]

    def glass_pick(self, avoid=None):
        fs = [f for f in self.glass_faces() if f != avoid]
        c = [f for f in fs if f != getattr(self, "glass_last", None)] or fs          # 前の場面と同じ面は、なるべく避ける
        return random.choice(c) if c else None

    def glass_steps(self, sp, hold):
        """ガラスに張りつく幽霊の場面：明るくなるとガラスの外にぴったり張りついている → 暗い間に別の面へすべる → 明るくなると別のガラスにいる"""
        fa = self.glass_pick()
        fb = self.glass_pick(fa) if GLASSGHOST_SLIDE else None
        n = random.randint(int(min(GLASSGHOST_HANDS)), int(max(GLASSGHOST_HANDS)))
        fl = ("flicker", FLICKER_TIME, None, None)
        if fb is None:
            return [fl, ("dark", DARK_TIME, self.hide_all, lambda: self.glass_ghost_scene(sp, fa, hold, n, True)),
                    ("idle", hold, None, None), fl, ("dark", DARK_TIME, self.ghost_hide, None)]
        h = hold * 0.5
        n1 = n - n // 2
        return [fl, ("dark", DARK_TIME, self.hide_all, lambda: self.glass_ghost_scene(sp, fa, h, n1, True)),
                ("idle", h, None, None), fl,
                ("dark", DARK_TIME, lambda: self.glass_slide_begin(fa, fb), lambda: self.glass_ghost_scene(sp, fb, h, n - n1, False)),
                ("idle", h, None, None), fl, ("dark", DARK_TIME, self.ghost_hide, None)]

    def glass_ghost_scene(self, r, face, hold, n_hands, first):
        if self.code_active or self.ghost is None:                           # 謎7の場面の間は、幽霊を出さない
            return
        self.stage = r + 1
        wall, f = face
        n, t, _w = self.glass_pt(self.glass_s(face))
        x, y = self.glass_world(n, t)
        ix, iy = self.glass_inward(wall)
        self.ghost_show(x, y, x + ix * 100.0, y + iy * 100.0, level=r, hold=hold, glass=True, lean=GLASSGHOST_LEAN_DEG)
        self.glass_last = face
        if GLASSGHOST_SOUND:
            self.play(GLASSGHOST_SOUND)
        self.hand_reveal_near(x, y, n_hands)
        if first:
            screen(self.world, GHOST_SUBS[min(r, len(GHOST_SUBS) - 1)], (200, 220, 255), 4.0)
        log("幽霊の場面 %d（ガラスに張りつく：%s %.2f・顔とガラスのすきま %.1fcm）" % (r + 1, wall, f, GLASSGHOST_GAP))

    def glass_slide_begin(self, fa, fb):
        """暗い間：幽霊が、ガラスの外がわを、別の面へすべる（角は曲がる）"""
        if self.ghost is None:
            return
        sa, sb = self.glass_s(fa), self.glass_s(fb)
        r = self.glass_rect()
        P = 4 * (r[2] + r[3])
        d = (sb - sa + P / 2.0) % P - P / 2.0                                # 近いほうの回り方
        self.gslide = {"sa": sa, "d": d, "t": 0.0, "dur": max(0.3, DARK_TIME * 0.9)}

    def tick_glass_slide(self, dt):
        sl = getattr(self, "gslide", None)
        if sl is None or self.ghost is None:
            return
        sl["t"] += dt
        u = min(1.0, sl["t"] / sl["dur"])
        e = u * u * (3.0 - 2.0 * u)
        n, t, wall = self.glass_pt(sl["sa"] + sl["d"] * e)
        x, y = self.glass_world(n, t)
        ix, iy = self.glass_inward(wall)
        yaw = math.degrees(math.atan2(iy, ix)) + GHOST_YAW
        try:
            self.ghost.set_actor_location_and_rotation(unreal.Vector(x, y, getattr(self, "ghost_z", 0.0)), unreal.Rotator(GLASSGHOST_LEAN_DEG, 0, yaw), False, False)
            gfx = getattr(self, "gfx", None)
            if gfx is not None:
                gfx.base_yaw = yaw
        except Exception as ex:  # noqa
            self.gslide = None
            log("  (ガラスをすべる動きを止めます) %s" % ex)
        if u >= 1.0:
            self.gslide = None

    def setup_hands(self, found):
        self.hands = sorted([(k, v) for k, v in found.items() if k.startswith("KD_Hand_")], key=lambda kv: kv[0])
        self.hand_shown = set()
        self.hand_queue = []
        self._hand_key = None
        self.gslide = None
        self.glass_last = None
        for _k, a in self.hands:
            a.set_actor_hidden_in_game(True)
        log("ガラスの手形: %d 枚（最初は見えません）" % len(self.hands))

    def hand_pick(self, n, near=None):
        taken = set(self.hand_shown) | set(i for _d, i in self.hand_queue)
        cand = [i for i in range(len(self.hands)) if i not in taken]
        if near is not None:
            def dist(i):
                try:
                    p = self.hands[i][1].get_actor_location()
                    return math.hypot(p.x - near[0], p.y - near[1]) + 0.3 * abs(p.z - near[2])
                except Exception:  # noqa
                    return 1e9
            cand.sort(key=dist)
            return cand[:n]
        random.shuffle(cand)
        return cand[:n]

    def hand_reveal_near(self, x, y, n):
        if not getattr(self, "hands", None) or n <= 0:
            return
        z = getattr(self, "ghost_z", 0.0) + GLASSGHOST_HEIGHT * GLASSGHOST_HEAD
        for k, i in enumerate(self.hand_pick(n, (x, y, z))):
            self.hand_queue.append([HAND_DELAY * (k + 1), i])

    def hand_reveal_random(self, n):
        if not getattr(self, "hands", None) or n <= 0:
            return
        for k, i in enumerate(self.hand_pick(n)):
            self.hand_queue.append([HAND_DELAY * (k + 1), i])

    def tick_hands(self, dt):
        q = getattr(self, "hand_queue", None)
        if not q:
            return
        for e in q:
            e[0] -= dt
        due = [e for e in q if e[0] <= 0.0]
        if due:
            self.hand_queue = [e for e in q if e[0] > 0.0]
            for _d, i in due:
                self.hand_shown.add(i)
            self.update_hands()

    def update_hands(self):
        """見えるようになった手形だけ見せる。謎7の暗い間（外の木の数字が見えるように、ガラスの言葉を消す間）は、ぜんぶ隠す"""
        hands = getattr(self, "hands", None)
        if not hands:
            return
        hide = bool(getattr(self, "code_active", False)) and self.mult < 0.05
        key = (tuple(sorted(self.hand_shown)), hide)
        if key == self._hand_key:
            return
        self._hand_key = key
        for i, (_k, a) in enumerate(hands):
            a.set_actor_hidden_in_game(hide or i not in self.hand_shown)

    def poster_scene_begin(self, r):
        self.stage = r + 1
        frac = POSTER_FRAC[min(r, len(POSTER_FRAC) - 1)]
        self.poster_target = int(math.ceil(len(self.posters) * frac))
        self.poster_shown = 0
        self.poster_round = r
        if r >= 1 and HAND_PER_SCARE > 0:                          # 強さ2以上の張り紙の演出：手形もひとつ、ガラスの外に見えてくる
            self.hand_reveal_random(HAND_PER_SCARE)
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
        elif typ == "cdark":                               # 謎7の暗い間：光だけ消す。画面は真っ黒にしない（数字が見えるように）
            self.set_lights(0.0)
            self.blackout(CODE_DARK_BLACK)
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
            self.tick_code_hint(dt)
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
        elif typ == "clit":
            self.set_lights(1.0)                                         # 謎7の明るい間：ちらつかせない
        elif typ == "flicker":
            if self.step_t >= self.flicker_next:
                self.flicker_lit = not self.flicker_lit
                self.flicker_next = self.step_t + random.uniform(0.03, 0.22)
                self.set_lights(0.9 if self.flicker_lit else 0.0)
                self.blackout(0.0 if self.flicker_lit else FLICKER_BLACK)
        if self.step_t >= ln:
            if typ == "flicker":
                self.blackout(0.0)
            if typ in ("dark", "cdark"):
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
