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
import math
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
IDLE_BETWEEN = 4.0                         # 2回目以降、演出と演出のあいだの静かな時間（秒）
DEAD_DIST = 70.0                           # 失敗のとき、幽霊が目の前に出る距離（cm）
RESTART_AFTER = 6.0                        # 失敗してから、最初に戻るまでの時間（秒）
GLASS_DIRT = 0.35            # ガラスのくもり具合（0=ほぼ透明 〜 1=いまのまま）。外が見えないときは小さくする
FLICKER_BLACK = 0.6          # 点滅で「消えた」瞬間に、画面をこの割合だけ黒くする（0=しない 〜 1=真っ黒）。点滅がグレーに見えるときは大きくする
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
        for a in unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.Actor):
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
            self.tubes.append((c, base))
        # 電話機にあててある SpotLight、月、空も、いっしょに暗くする
        self.extra = []
        for nm, cls in (("SpotLight", unreal.SpotLightComponent), ("Moon", unreal.DirectionalLightComponent), ("DirectionalLight", unreal.DirectionalLightComponent), ("KD_Moon", unreal.DirectionalLightComponent), ("SkyLight", unreal.SkyLightComponent)):
            a = found.get(nm)
            if a is None:
                continue
            c = a.get_component_by_class(cls)
            if c is not None:
                self.extra.append((nm, c, c.get_editor_property("intensity")))
        # 蛍光灯の光る部分（材質 M_Tube の Flicker）とガラス（M_Glass の Dirt）を、動かせる材質にする
        self.tube_mats = []
        for nm, a in found.items():
            if not (nm.startswith("Booth_") or nm.startswith("KD_Tube")):
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
                    elif "Glass" in mn:
                        mid = comp.create_dynamic_material_instance(i, mat)
                        mid.set_scalar_parameter_value("Dirt", GLASS_DIRT)
                except Exception as e:  # noqa
                    log("  (材質を動かせません) %s[%d]: %s" % (nm, i, e))
        self.posters = sorted([(k, v) for k, v in found.items() if k.startswith("Poster_") and k not in ("Poster_Hint", "Poster_Eye")], key=lambda kv: kv[0])
        self.hint = found.get("Poster_Hint")
        self.eye = found.get("Poster_Eye")
        for _k, a in self.posters + [("h", self.hint), ("e", self.eye)]:
            if a is not None:
                a.set_actor_hidden_in_game(True)
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
        if self.flash is not None:
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
        self.key = unreal.Key()
        self.key.set_editor_property("key_name", FLASH_KEY)
        log("Play 開始: 入口方式=%s 効果音=%s" % ("Eキー" if self.hinge is None else "ドアが閉まる", [k for k, v in self.snd.items() if v is not None]))
        log("Play 開始: ドアの軸=%s 懐中電灯=%s 蛍光灯の光=%d 光る材質=%d 他の光=%s プレイヤー=%s ボックス中心=(%.0f,%.0f)" % (
            self.hinge is not None, self.flash is not None, len(self.tubes), len(self.tube_mats), [e[0] for e in self.extra], self.pawn is not None, self.cx, self.cy))
        screen(self.world, "WASD：歩く / マウス：見る / F：懐中電灯", (200, 255, 200), 6.0)

    # ---- 部品 ----
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
            mid.set_scalar_parameter_value("Flicker", mult)          # 蛍光灯の見た目も、光といっしょにちらつく
        part = 1.0 if mult >= 0.5 else DARK_WORLD + (1.0 - DARK_WORLD) * (mult / 0.5)
        for nm, c, base in self.extra:
            c.set_editor_property("intensity", base * (part if nm != "SpotLight" else mult))

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
        # 歩く高さを目の高さに固定（飛ばない）
        if not self.is_char and abs(loc.z - EYE_HEIGHT) > 0.5:
            self.pawn.set_actor_location(unreal.Vector(loc.x, loc.y, EYE_HEIGHT), False, False)
        self.update_flashlight()
        if self.state == "WALK" and self.hinge is None:
            self.tick_walk_e(loc)
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
            self.tick_trapped(dt)
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

    # ---- 閉じ込められてから：「幽霊が近づく」と「張り紙が貼られる」を、別々の場面にして、交互にくりかえす ----
    def start_trapped(self):
        self.steps = []
        for r in range(len(GHOST_SPOTS)):
            self.steps += self.round_steps(r)
        self.steps += [("idle", IDLE_BETWEEN, None, None), ("flicker", FLICKER_TIME, None, None),
                       ("dark", DARK_TIME, self.ghost_hide, self.begin_dead)]
        self.step_i = -1
        self.stage = 0
        self.next_step()

    def round_steps(self, r):
        first = IDLE_FIRST if r == 0 else IDLE_BETWEEN
        n_hold = min(r, len(GHOST_HOLD) - 1)
        return [
            ("idle", first, None, None),
            ("flicker", FLICKER_TIME, None, None),
            ("dark", DARK_TIME, self.hide_all, lambda r=r: self.ghost_scene(r)),            # 暗転のあいだに幽霊を動かす → 外に見える
            ("idle", GHOST_HOLD[n_hold], None, None),
            ("flicker", FLICKER_TIME, None, None),
            ("dark", DARK_TIME, self.ghost_hide, lambda r=r: self.poster_scene_begin(r)),    # 幽霊は消す → 張り紙が貼られはじめる
            ("posters", POSTER_HOLD[n_hold], None, None),
            ("flicker", FLICKER_TIME, None, None),
            ("dark", DARK_TIME, self.posters_hide, None),                                    # 張り紙は、ぜんぶはがす（貼りっぱなしにしない）
        ]

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
        log("張り紙の場面 %d（%d枚）" % (r + 1, self.poster_target))

    def posters_hide(self):
        for _k, a in self.posters:
            a.set_actor_hidden_in_game(True)
        for a in (self.hint, self.eye):
            if a is not None:
                a.set_actor_hidden_in_game(True)
        self.poster_shown = 0
        self.poster_target = 0

    def poster_progress(self, step_t):
        want = min(self.poster_target, int(step_t / POSTER_STEP) + 1)
        while self.poster_shown < want:
            self.posters[self.poster_shown][1].set_actor_hidden_in_game(False)
            self.poster_shown += 1
            if self.poster_shown == 1 and self.hint is not None and self.poster_round == 0:
                self.hint.set_actor_hidden_in_game(False)
        if self.eye is not None and self.poster_round >= 2 and self.poster_shown >= self.poster_target:
            self.eye.set_actor_hidden_in_game(False)

    def next_step(self):
        if self.step_i >= 0:
            exit_fn = self.steps[self.step_i][3]
            if exit_fn is not None:
                exit_fn()
        self.step_i += 1
        if self.step_i >= len(self.steps):
            return
        typ, ln, enter_fn, _ex = self.steps[self.step_i]
        self.step_t = 0.0
        self.flicker_next = 0.0
        if typ == "dark":
            self.set_lights(0.0)
            self.blackout(0.0)
        if enter_fn is not None:
            enter_fn()

    def tick_trapped(self, dt):
        if self.step_i >= len(self.steps):
            return
        self.step_t += dt
        typ, ln, _en, _ex = self.steps[self.step_i]
        if typ in ("idle", "posters"):
            self.set_lights(1.0 if self.t % 7.0 > 0.3 else 0.35)     # ときどきすこし弱まる
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


def main():
    old = getattr(unreal, "_kd_tick_handle", None)
    if old is not None:
        try:
            unreal.unregister_slate_post_tick_callback(old)
        except Exception:  # noqa
            pass
    unreal._kd_tick_handle = unreal.register_slate_post_tick_callback(on_tick)
    log("kd_game を登録しました。▶（Play）を押してください。エラーは Output Log を「KD」で絞って見ます")


main()
