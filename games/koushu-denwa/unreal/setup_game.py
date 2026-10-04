"""
ゲームのしくみ 段階1 の準備（1回実行する。やり直しても同じ結果になる）

やること：
  1) 森の入口にプレイヤーの開始位置（PlayerStart）を置く（電話ボックスの方を向く）
  2) 懐中電灯（SpotLight「Flashlight」）を置く（最初は消えている。動かすのは kd_game.py）
  3) 電話ボックスに当たり判定をつける（すり抜けないように）
  4) 保存

そのあと：Cmd に  py "…/unreal/kd_game.py"  と打って、▶（Play）を押す。
"""
import traceback

import unreal

# ---------------- 書き換えてよい設定 ----------------
GAME_DIR = "/Game/KoushuDenwa"
TAG = "KD_Game"
START = (0.0, 2200.0, 100.0)         # プレイヤーの開始位置（cm）。ボックスの正面（+Y）の道の上
START_YAW = -90.0                    # -Y 方向（＝電話ボックスの方）を向く
FLASH_INTENSITY = 3000.0             # 懐中電灯の明るさ（カンデラ）。暗すぎ・明るすぎなら変える
FLASH_INNER, FLASH_OUTER = 14.0, 30.0
FLASH_RADIUS = 1800.0                # 光が届く距離（cm）
# --------------------------------------------------

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


def tag_actor(a, label):
    try:
        a.set_editor_property("tags", [unreal.Name(TAG)])
    except Exception as e:  # noqa
        log("  (タグ設定不可) %s" % e)
    a.set_actor_label(label)


def s_env():
    log("エンジン: %s" % unreal.SystemLibrary.get_engine_version())
    for need in ("DoorHinge", "TubeLight_L", "Booth_Frame"):
        a = find_actor(need)
        log("  %s: %s" % (need, "あり" if a else "【ありません】setup_phonebooth.py を先に実行してください"))
        if a is None and need == "DoorHinge":
            raise RuntimeError("DoorHinge がありません")


def s_clear():
    n = 0
    for a in eas().get_all_level_actors():
        try:
            if TAG in [str(t) for t in a.get_editor_property("tags")]:
                eas().destroy_actor(a)
                n += 1
        except Exception:  # noqa
            pass
    log("前回の生成物を削除: %d" % n)


def s_player_start():
    ps = spawn(unreal.PlayerStart, START, (0, 0, START_YAW))
    tag_actor(ps, "KD_PlayerStart")
    log("PlayerStart を置きました: %s 向き=%s" % (START, START_YAW))


def s_flashlight():
    sp = spawn(unreal.SpotLight, (START[0], START[1], START[2] + 60.0), (0, 0, START_YAW))
    tag_actor(sp, "Flashlight")
    c = sp.get_component_by_class(unreal.SpotLightComponent)
    setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
    setp(c, "intensity_units", unreal.LightUnits.CANDELA)
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


def s_collision():
    """電話ボックスの形そのものを当たり判定にする（Use Complex as Simple）"""
    n = 0
    for a in eas().get_all_level_actors():
        lab = label_of(a)
        if not (lab.startswith("Booth_") or lab == "Door" or lab.endswith("PhoneBooth_Door")):
            continue
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh = comp.get_editor_property("static_mesh") if comp else None
        if mesh is None:
            continue
        try:
            bs = mesh.get_editor_property("body_setup")
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            mesh.set_editor_property("body_setup", bs)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            n += 1
        except Exception as e:  # noqa
            log("  (当たり判定を設定できず) %s : %s" % (lab, e))
        setp(comp, "collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    log("当たり判定をつけた数: %d" % n)


def s_save():
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception as e:  # noqa
        log("  (レベル保存不可) %s" % e)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


def main():
    log("=== ゲームのしくみ 段階1 の準備 ===")
    step("環境確認", s_env)
    step("前回の生成物を消す", s_clear, ["環境確認"])
    step("プレイヤーの開始位置", s_player_start, ["前回の生成物を消す"])
    step("懐中電灯", s_flashlight, ["前回の生成物を消す"])
    step("当たり判定", s_collision, ["環境確認"])
    step("保存", s_save, ["環境確認"])
    log("SUMMARY: " + ", ".join("%s=%s" % (k, v) for k, v in RESULTS.items()))
    if any(v == "FAIL" for v in RESULTS.values()):
        log_err("失敗した手順があります → 出力ログを「KD」で絞って全部コピーして、Claudeに送ってください")
    else:
        log("完了。次に Cmd で  py \"…/unreal/kd_game.py\"  を実行して、▶（Play）を押してください")
    write_log_file()


main()
