"""
ゲームのしくみ 段階1 の準備（1回実行する。やり直しても同じ結果になる）

やること：
  1) 森の入口にプレイヤーの開始位置（PlayerStart）を置く（電話ボックスの方を向く）
  2) 懐中電灯（SpotLight「Flashlight」）を置く（最初は消えている。動かすのは kd_game.py）
  3) 電話ボックスに当たり判定をつける（すり抜けないように）
  4) 保存

そのあと：Cmd に  py "…/unreal/kd_game.py"  と打って、▶（Play）を押す。
"""
import os
import math
import random
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
POSTER_GLOW = 0.15                   # 張り紙が暗闇で少し見えるように、うすく光らせる強さ
WALL = 66.0                          # ボックスの中心から、張り紙を貼る壁（ガラスの内側）までの距離（cm）
# --------------------------------------------------

mel = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
STATE = {}
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
            log("  %s: メッシュなし（スキップ）" % lab)
            continue
        try:
            bs = mesh.get_editor_property("body_setup")
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            mesh.set_editor_property("body_setup", bs)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            n += 1
            log("  %s: 当たり判定 OK" % lab)
        except Exception as e:  # noqa
            log("  %s: 当たり判定を設定できず : %s" % (lab, str(e).splitlines()[0] if str(e) else e))
        try:
            comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception as e:  # noqa
            log("  %s: collision_enabled を設定できず : %s" % (lab, str(e).splitlines()[0] if str(e) else e))
    log("当たり判定をつけた数: %d" % n)


def s_glass():
    """ガラスの「くもり」を、あとから強さを変えられる（Dirt）ようにする。外が見えない問題の対策"""
    mel = unreal.MaterialEditingLibrary
    mp = unreal.MaterialProperty.MP_OPACITY
    m = unreal.EditorAssetLibrary.load_asset(GAME_DIR + "/Materials/M_Glass")
    if m is None:
        raise RuntimeError("M_Glass がありません")
    node = mel.get_material_property_input_node(m, mp)
    out = mel.get_material_property_input_node_output_name(m, mp)
    if node is None:
        raise RuntimeError("M_Glass の Opacity につながっている部品が見つかりません")
    if isinstance(node, unreal.MaterialExpressionMultiply):
        log("  M_Glass はすでに Dirt つきです")
        return
    par = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 300)
    setp(par, "parameter_name", "Dirt")
    setp(par, "default_value", 0.35)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 200)
    mel.connect_material_expressions(node, out, mul, "A")
    mel.connect_material_expressions(par, "", mul, "B")
    mel.connect_material_property(mul, "", mp)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    log("M_Glass に Dirt（くもりの強さ）を足しました")


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
    names = sorted(f for f in os.listdir(d) if f.startswith("poster_") and f.lower().endswith((".png", ".jpg")))
    if not names:
        raise RuntimeError("張り紙の画像がありません: %s" % d)
    import_tasks([mk_task(os.path.join(d, f), GAME_DIR + "/Textures/Game") for f in names])
    STATE["poster_files"] = names
    log("張り紙の画像を取り込みました: %d 枚" % len(names))


def s_poster_mesh():
    fbx = os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", "Poster.fbx")
    if not os.path.exists(fbx):
        raise RuntimeError("Poster.fbx がありません: %s" % fbx)
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
    setp(d, "import_uniform_scale", 100.0)          # 電話ボックスと同じ：メートル → cm
    import_tasks([mk_task(fbx, GAME_DIR + "/Game", fbx_ui=ui)])
    mesh = None
    for p in unreal.EditorAssetLibrary.list_assets(GAME_DIR + "/Game", recursive=True, include_folder=False):
        a = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(a, unreal.StaticMesh) and "oster" in a.get_name():
            mesh = a
    if mesh is None:
        raise RuntimeError("Poster のメッシュが見つかりません")
    e = mesh.get_bounds().box_extent
    log("ポスター板の大きさ（cm の半分）: %.1f × %.1f × %.1f（25×35 前後が正常）" % (e.x, e.y, e.z))
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


def s_poster_materials():
    mats = {}
    for f in STATE["poster_files"]:
        base = os.path.splitext(f)[0]                      # poster_01
        tex = unreal.EditorAssetLibrary.load_asset("%s/Textures/Game/%s" % (GAME_DIR, base))
        m = new_material("M_" + "".join(w.capitalize() for w in base.split("_")))      # M_Poster01
        setp(m, "two_sided", True)
        t = xx(m, unreal.MaterialExpressionTextureSample, -800, 0)
        t.set_editor_property("texture", tex)
        mel.connect_material_property(mulx(m, t, cst(m, 0.8, -100), 0), "", MP.MP_BASE_COLOR)
        mel.connect_material_property(mulx(m, t, cst(m, POSTER_GLOW, 100), 150), "", MP.MP_EMISSIVE_COLOR)
        mel.connect_material_property(cst(m, 0.9, 300), "", MP.MP_ROUGHNESS)
        mel.recompile_material(m)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        mats[base] = m
    STATE["poster_mats"] = mats
    log("張り紙の材質を作りました: %d" % len(mats))


# 壁ごとの貼る位置：(壁, 壁にそった位置, 高さ, 大きさ)。R=右(+X) L=左(-X) B=奥(-Y・電話機の壁) F=手前(+Y・ドアの壁)
SLOTS = [("R", -40, 125, 1.0), ("R", 5, 160, 1.0), ("R", 45, 115, 1.0), ("R", -5, 195, 1.0),
         ("L", -45, 150, 1.0), ("L", 42, 160, 1.0), ("L", -5, 195, 1.0),
         ("F", -45, 130, 1.0), ("F", 40, 155, 1.0), ("F", 0, 195, 1.0),
         ("B", -46, 120, 1.0), ("B", 46, 150, 1.0)]
HINT_SLOT = ("B", 0, 185, 1.0)        # 電話機の真上
EYE_SLOT = ("L", 0, 140, 1.5)         # 左の壁の真ん中に、大きく


def wall_pose(wall, u, z, cx, cy):
    if wall == "R":
        return (cx + WALL, cy + u, z), 90.0          # 面は -X（ボックスの内側）を向く
    if wall == "L":
        return (cx - WALL, cy + u, z), -90.0
    if wall == "B":
        return (cx + u, cy - WALL, z), 0.0
    return (cx + u, cy + WALL, z), 180.0


def s_posters():
    mesh = STATE["poster_mesh"]
    mats = STATE["poster_mats"]
    o, _e = find_actor("Booth_Frame").get_actor_bounds(False)
    cx, cy = o.x, o.y
    rng = random.Random(714)
    normal = ["poster_%02d" % i for i in range(1, 13)]
    rng.shuffle(normal)                                     # どれから出るかをランダムに
    plan = [("Poster_%02d" % (i + 1), normal[i], SLOTS[i]) for i in range(len(SLOTS))]
    plan.append(("Poster_Hint", "poster_hint", HINT_SLOT))
    if "poster_eye" in mats:
        plan.append(("Poster_Eye", "poster_eye", EYE_SLOT))
    n = 0
    for label, key, (wall, u, z, sc) in plan:
        if key not in mats:
            log("  (画像なし) %s" % key)
            continue
        loc, yaw = wall_pose(wall, u, z, cx, cy)
        a = spawn(unreal.StaticMeshActor, loc, (0, 0, yaw + rng.uniform(-4, 4)))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        c.set_material(0, mats[key])
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        tag_actor(a, label)
        a.set_actor_hidden_in_game(True)                     # 最初は見えない（kd_game.py が順に出す）
        n += 1
    log("張り紙を貼りました: %d 枚（最初は見えません）" % n)


def s_ghost():
    """幽霊（仮の姿）：黒い体＋白い頭。あとで Blender / Mixamo のモデルに替える"""
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
    step("ガラスの透け具合", s_glass, ["環境確認"])
    step("張り紙の画像", s_poster_textures, ["環境確認"])
    step("張り紙の板", s_poster_mesh, ["環境確認"])
    step("張り紙の材質", s_poster_materials, ["張り紙の画像"])
    step("張り紙を貼る", s_posters, ["張り紙の板", "張り紙の材質", "前回の生成物を消す"])
    step("幽霊（仮）", s_ghost, ["前回の生成物を消す"])
    step("保存", s_save, ["環境確認"])
    log("SUMMARY: " + ", ".join("%s=%s" % (k, v) for k, v in RESULTS.items()))
    if any(v == "FAIL" for v in RESULTS.values()):
        log_err("失敗した手順があります → 出力ログを「KD」で絞って全部コピーして、Claudeに送ってください")
    else:
        log("完了。次に Cmd で  py \"…/unreal/kd_game.py\"  を実行して、▶（Play）を押してください")
    write_log_file()


main()
