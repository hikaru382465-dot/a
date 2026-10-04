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
IDLE_LATER = (13.0, 13.0, 9.0, 9.0)   # 段階1〜4が終わったあとの静かな時間（最後の段階はそのまま）
LAST_STAGE = 5               # 段階5になったら失敗（段階2で作る）。今は表示だけ
FLASH_KEY = "F"
# 幽霊が出る場所（ボックス中心からの位置 cm。正面＝+Y）。段階1〜4で、だんだん近づく
GHOST_SPOTS = [(0.0, 1300.0), (-240.0, 750.0), (270.0, 360.0), (115.0, 25.0)]
GHOST_SUBS = ["（外に、誰か立っている……）", "（さっきより、近い）", "（ガラスに、何か貼られている）", "（すぐそこにいる）"]
POSTER_FRAC = [0.35, 0.7, 1.0, 1.0]       # 段階1〜4で、張り紙が何割見えるか
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
        self.setup()

    # ---- Play のはじめに1回だけ：参照を集める ----
    def setup(self):
        found = {}
        for a in unreal.GameplayStatics.get_all_actors_of_class(self.world, unreal.Actor):
            found[label_of(a)] = a
        self.hinge = found.get("DoorHinge")
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
        for nm, cls in (("SpotLight", unreal.SpotLightComponent), ("Moon", unreal.DirectionalLightComponent), ("SkyLight", unreal.SkyLightComponent)):
            a = found.get(nm)
            if a is None:
                continue
            c = a.get_component_by_class(cls)
            if c is not None:
                self.extra.append((nm, c, c.get_editor_property("intensity")))
        # 蛍光灯の光る部分（材質 M_Tube の Flicker）とガラス（M_Glass の Dirt）を、動かせる材質にする
        self.tube_mats = []
        for nm, a in found.items():
            if not nm.startswith("Booth_"):
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
        if self.frame is not None:
            o, _e = self.frame.get_actor_bounds(False)
            self.cx, self.cy = o.x, o.y
        if self.hinge is not None:
            self.hinge.set_actor_rotation(unreal.Rotator(0, 0, self.door_yaw), False)
        if self.pawn is not None:
            try:
                mv = self.pawn.get_component_by_class(unreal.FloatingPawnMovement)
                mv.set_editor_property("max_speed", WALK_SPEED)
                mv.set_editor_property("acceleration", WALK_SPEED * 8)
                mv.set_editor_property("deceleration", WALK_SPEED * 8)
            except Exception as e:  # noqa
                log("  (歩く速さを設定できません) %s" % e)
        if self.flash is not None:
            self.set_flash(False)
        self.key = unreal.Key()
        self.key.set_editor_property("key_name", FLASH_KEY)
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
        if abs(loc.z - EYE_HEIGHT) > 0.5:
            self.pawn.set_actor_location(unreal.Vector(loc.x, loc.y, EYE_HEIGHT), False, False)
        self.update_flashlight()
        if self.state == "WALK":
            inside = abs(loc.x - self.cx) < ENTER_HALF and abs(loc.y - self.cy) < ENTER_HALF
            self.inside_t = self.inside_t + dt if inside else 0.0
            if self.inside_t > CLOSE_DELAY:
                self.begin_close()
        elif self.state == "CLOSING":
            k = min(1.0, self.state_t / CLOSE_TIME)
            k = 1 - (1 - k) * (1 - k)                      # 最初に勢いよく、最後にゆっくり
            self.door_yaw = DOOR_OPEN_YAW * (1 - k)
            if self.hinge is not None:
                self.hinge.set_actor_rotation(unreal.Rotator(0, 0, self.door_yaw), False)
            if self.state_t >= CLOSE_TIME:
                self.state, self.state_t = "TRAPPED", 0.0
                self.sub, self.sub_t, self.sub_len = "IDLE", 0.0, IDLE_FIRST
                screen(self.world, "バタン！（とじこめられた）", (255, 120, 120), 4.0)
                self.fade(False, 0.8)
        elif self.state == "TRAPPED":
            self.tick_trapped(dt)
        elif self.state == "DEAD":
            if self.state_t > RESTART_AFTER:
                self.state = "RESTART"
                log("最初に戻ります（RestartLevel）")
                unreal.SystemLibrary.execute_console_command(self.world, "RestartLevel")

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

    def tick_trapped(self, dt):
        self.sub_t += dt
        if self.sub == "IDLE":
            self.set_lights(1.0 if self.t % 7.0 > 0.3 else 0.35)     # ときどきすこし弱まる
            if self.stage >= LAST_STAGE:
                return
            if self.sub_t >= self.sub_len:
                self.sub, self.sub_t, self.sub_len = "FLICKER", 0.0, FLICKER_TIME
                self.flicker_next = 0.0
        elif self.sub == "FLICKER":
            if self.sub_t >= self.flicker_next:
                self.flicker_lit = not self.flicker_lit
                self.flicker_next = self.sub_t + random.uniform(0.03, 0.22)
                self.set_lights(0.9 if self.flicker_lit else 0.0)
                self.blackout(0.0 if self.flicker_lit else FLICKER_BLACK)
            if self.sub_t >= self.sub_len:
                self.sub, self.sub_t, self.sub_len = "DARK", 0.0, DARK_TIME
                self.set_lights(0.0)
                self.blackout(0.0)
                self.stage += 1
                self.ghost_hide()
                if self.stage <= len(POSTER_FRAC):
                    self.reveal(self.stage)
                log("段階 %d" % self.stage)
        elif self.sub == "DARK":
            if self.sub_t >= self.sub_len:
                if self.stage >= LAST_STAGE:
                    self.begin_dead()
                    return
                gx, gy = GHOST_SPOTS[min(self.stage, len(GHOST_SPOTS)) - 1]
                self.ghost_show(self.cx + gx, self.cy + gy)
                screen(self.world, GHOST_SUBS[min(self.stage, len(GHOST_SUBS)) - 1], (200, 220, 255), 4.0)
                idx = min(self.stage - 1, len(IDLE_LATER) - 1)
                self.sub, self.sub_t, self.sub_len = "IDLE", 0.0, IDLE_LATER[idx]
                self.set_lights(1.0)


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
