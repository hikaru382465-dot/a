"""
下見スクリプト（何も変えない。調べて、ログに出すだけ）

買った公衆電話（名前に phone_box が入るもの）の
  ・大きさと中心   ・部品（コンポーネント）の一覧   ・当たり判定の種類
  ・まわりの4方向（+X -X +Y -Y）に、文字を空中に出す（どちらが入口か見分ける用。10分間）
  ・レベルの主なアクター（名前・種類・位置）
を調べる。結果は 出力ログ（KD で絞る）と Saved/Logs/KD_probe.txt に出る。

使い方：L_Booth ではなく、買った公衆電話があるレベル（FirstPersonMap）を開いて、Cmd に
  py "…/unreal/kd_probe.py"
"""
import os
import traceback

import unreal

KEY = "phone_box"            # 電話ボックスの名前に入っている言葉
LINES = []


def log(msg):
    line = "[KD] " + str(msg)
    LINES.append(line)
    unreal.log(line)


def eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def label_of(a):
    try:
        return a.get_actor_label()
    except Exception:  # noqa
        return a.get_name()


def v(x):
    return "(%.0f, %.0f, %.0f)" % (x.x, x.y, x.z)


def main():
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        log("エンジン: %s / レベル: %s" % (unreal.SystemLibrary.get_engine_version(), world.get_name()))
    except Exception as e:  # noqa
        log("(レベル名を取得できません) %s" % e)
        world = None
    actors = list(eas().get_all_level_actors())
    log("アクター数: %d" % len(actors))
    for a in actors:
        try:
            o, e = a.get_actor_bounds(False)
            log("  %-40s %-26s 位置%s 半径%s" % (label_of(a)[:40], a.get_class().get_name()[:26], v(a.get_actor_location()), v(e)))
        except Exception:  # noqa
            log("  %s %s" % (label_of(a), a.get_class().get_name()))
    booths = [a for a in actors if KEY in label_of(a).lower() and "glass" not in label_of(a).lower()]
    if not booths:
        log("【%s を含む名前のアクターがありません】アウトライナーの名前を教えてください" % KEY)
    for b in booths:
        o, e = b.get_actor_bounds(False)
        log("=== 電話ボックス: %s ===" % label_of(b))
        log("  中心=%s 半径=%s（全体の大きさ=%s cm）" % (v(o), v(e), v(unreal.Vector(e.x * 2, e.y * 2, e.z * 2))))
        log("  位置=%s 回転=%s 拡大=%s" % (v(b.get_actor_location()), b.get_actor_rotation(), v(b.get_actor_scale3d())))
        for c in b.get_components_by_class(unreal.SceneComponent):
            try:
                log("  部品: %s (%s) 位置=%s" % (c.get_name(), c.get_class().get_name(), v(c.get_world_location())))
            except Exception:  # noqa
                pass
        for c in b.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property("static_mesh")
            if m is None:
                continue
            log("  メッシュ: %s / 材質数=%d" % (m.get_name(), c.get_num_materials()))
            try:
                bs = m.get_editor_property("body_setup")
                log("  当たり判定の種類: %s" % bs.get_editor_property("collision_trace_flag"))
            except Exception as ex:  # noqa
                log("  (当たり判定を調べられません) %s" % ex)
        if world is not None:
            for txt, dx, dy in (("+X", 1, 0), ("-X", -1, 0), ("+Y", 0, 1), ("-Y", 0, -1)):
                p = unreal.Vector(o.x + dx * (e.x + 120), o.y + dy * (e.y + 120), o.z + e.z)
                try:
                    unreal.SystemLibrary.draw_debug_string(world, p, txt, None, unreal.LinearColor(1, 1, 0, 1), 600.0)
                except Exception as ex:  # noqa
                    log("  (文字を出せません) %s" % ex)
                    break
            log("  4方向の文字（+X -X +Y -Y）を空中に出しました（10分間）。電話ボックスの【入口（開いている側）】がどの文字の側か見てください")
    try:
        p = os.path.join(unreal.Paths.project_saved_dir(), "Logs", "KD_probe.txt")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write("\n".join(LINES))
        unreal.log("[KD] ログファイル: " + p)
    except Exception as ex:  # noqa
        unreal.log_warning("[KD] ログファイルを書けませんでした: %s" % ex)


try:
    main()
except Exception:  # noqa
    unreal.log_error("[KD][FAIL] 下見\n" + traceback.format_exc())
