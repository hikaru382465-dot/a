"""
ゲームのしくみ 段階1〜2 の準備（買った公衆電話があるレベル用。FirstPersonMap など）
何度実行しても同じ結果になる（KD_Game タグの物は、毎回消して置き直す）。

やること：
  1) 買った公衆電話を探して、大きさ・中心・入口の向きを求める
  2) 当たり判定を「形そのもの」にして、中に入れるようにする
  3) 入口にドア（動く板）を付ける ／ 天井に蛍光灯2本（光＋光る見た目）を付ける
  4) プレイヤーの開始位置を、入口の正面の遠くに動かす（既存の PlayerStart を使う）
  5) 懐中電灯、張り紙（14枚）、幽霊（仮）を置く
入口の向きは、下の FRONT で決める（+X / -X / +Y / -Y のどちらが「開いている側」か）。
そのあと Cmd で  py "…/unreal/kd_game.py"  を実行して ▶（Play）。
"""
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
PROTECT_LEVELS = ("FirstPersonMap",)  # このレベル（スタート画面用）では実行しない。本編用にコピーしたレベルで実行する
START_DIST = 1800.0                  # プレイヤーを、入口の正面から何cm 離して立たせるか
FLASH_INTENSITY = 3000.0             # 懐中電灯の明るさ（カンデラ）
FLASH_INNER, FLASH_OUTER = 14.0, 30.0
FLASH_RADIUS = 1800.0
POSTER_GLOW = 0.15                   # 張り紙の、うすい自己発光の強さ
WALL_INSET = 7.0                     # 張り紙を、ボックスの外形から内側へ何cm 入れた所に貼るか
DOOR_THICK = 4.0                     # ドアの厚さ（cm）
POST = 10.0                          # 柱の太さのめやす（ドアの幅から引く）
TUBE_Z_FROM_TOP = 40.0               # 蛍光灯を、天井の上端から何cm 下に付けるか
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
    a = spawn(unreal.StaticMeshActor, g["center"], (0, 0, yaw0))
    tag_actor(a, "KD_BoothCenter")
    setp(a.get_component_by_class(unreal.StaticMeshComponent), "mobility", unreal.ComponentMobility.MOVABLE)
    a.set_actor_hidden_in_game(True)


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
    log("当たり判定をつけた数: %d" % n)


def s_player_start():
    ps = None
    for a in eas().get_all_level_actors():
        if isinstance(a, unreal.PlayerStart):
            ps = a
            break
    g = STATE["geo"]
    half_n, _ = front_half()
    x, y, _z = world(half_n + START_DIST, 0, 0)
    z = g["zmin"] + 100.0
    n = g["n"]
    yaw = math.degrees(math.atan2(-n[1], -n[0]))           # ボックスの方を向く
    if ps is None:
        ps = spawn(unreal.PlayerStart, (x, y, z), (0, 0, yaw))
        tag_actor(ps, "KD_PlayerStart")
        log("PlayerStart を新しく置きました")
    else:
        ps.set_actor_location_and_rotation(unreal.Vector(x, y, z), unreal.Rotator(0, 0, yaw), False, False)
        log("既存の PlayerStart を動かしました: (%.0f, %.0f, %.0f) 向き=%.0f" % (x, y, z, yaw))


def s_door():
    """入口にドア（板）と蝶番（DoorHinge）を付ける。kd_game.py が DoorHinge の向きを回して開け閉めする"""
    g = STATE["geo"]
    half_n, half_t = front_half()
    zmin, zmax = g["zmin"], g["zmax"]
    height = (zmax - zmin) - 40.0
    width = 2 * half_t - 2 * POST
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    mat = new_material("M_KDDoor")
    setp(mat, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mel.connect_material_property(cst(mat, 0.02, 0), "", MP.MP_BASE_COLOR)
    mel.connect_material_property(cst(mat, 0.45, 100), "", MP.MP_OPACITY)
    mel.connect_material_property(cst(mat, 0.15, 200), "", MP.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    # 蝶番は、入口の面の「t の負の側」の端（そこから +t 方向にドアが伸びる）
    hx, hy, hz = world(half_n - DOOR_THICK / 2, -half_t + POST, zmin + 5.0)
    n = g["n"]
    yaw0 = math.degrees(math.atan2(n[1], n[0])) - 90.0    # 入口が +Y のとき 0 度になる（ドアは +t 方向に伸びる）
    hinge = spawn(unreal.StaticMeshActor, (hx, hy, hz), (0, 0, yaw0))
    tag_actor(hinge, "DoorHinge")
    setp(hinge.get_component_by_class(unreal.StaticMeshComponent), "mobility", unreal.ComponentMobility.MOVABLE)
    hinge.set_actor_hidden_in_game(False)
    # ドア本体：Cube（100cm角）を、幅×厚さ×高さにのばす。t 方向に伸びるので、向きは n が +Y なら 0 度
    cxw, cyw, czw = world(half_n - DOOR_THICK / 2, -half_t + POST + width / 2, zmin + 5.0 + height / 2)
    door = spawn(unreal.StaticMeshActor, (cxw, cyw, czw), (0, 0, yaw0))
    c = door.get_component_by_class(unreal.StaticMeshComponent)
    c.set_static_mesh(cube)
    c.set_material(0, mat)
    setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
    door.set_actor_scale3d(unreal.Vector(width / 100.0, DOOR_THICK / 100.0, height / 100.0))
    tag_actor(door, "KD_Door")
    door.attach_to_actor(hinge, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    STATE["door_yaw0"] = yaw0
    log("ドアを付けました: 幅%.0f 高さ%.0f 厚さ%.0f / 蝶番の基準の向き=%.0f" % (width, height, DOOR_THICK, yaw0))


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
        setp(lc, "intensity", 350.0 if nm == "R" else 1500.0)
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


def wall_pose_rel(wall, u, z):
    """壁の名前から、世界座標と、張り紙の面が内側を向く yaw を返す。張り紙の板は yaw=0 で +Y 向き"""
    g = STATE["geo"]
    half_n, half_t = front_half()
    n = g["n"]
    zmin = g["zmin"]
    if wall == "B":
        d, s, inward = -(half_n - WALL_INSET), u, (n[0], n[1])            # 奥の壁：面は入口側（+n）を向く
    elif wall == "F":
        d, s, inward = (half_n - WALL_INSET - DOOR_THICK), -u, (-n[0], -n[1])
    elif wall == "R":
        t = g["t"]
        d, s, inward = u, half_t - WALL_INSET, (-t[0], -t[1])
    else:
        t = g["t"]
        d, s, inward = u, -(half_t - WALL_INSET), (t[0], t[1])
    # 面の向き inward を向く yaw（板は yaw=0 で +Y 向き）
    yaw = math.degrees(math.atan2(inward[1], inward[0])) - 90.0
    if wall in ("R", "L"):
        # R/L は「側面方向 t」が s、「入口方向 n」が d にあたる：u は n 方向に動かす
        pos = world(u, s, zmin + z)
    else:
        pos = world(d, s, zmin + z)
    return pos, yaw


def s_posters():
    mesh = STATE["poster_mesh"]
    mats = STATE["poster_mats"]
    rng = random.Random(714)
    normal = ["poster_%02d" % i for i in range(1, 13)]
    rng.shuffle(normal)
    plan = [("Poster_%02d" % (i + 1), normal[i], SLOTS[i]) for i in range(len(SLOTS))]
    plan.append(("Poster_Hint", "poster_hint", HINT_SLOT))
    if "poster_eye" in mats:
        plan.append(("Poster_Eye", "poster_eye", EYE_SLOT))
    n = 0
    for label, key, (wall, u, z, sc) in plan:
        if key not in mats:
            log("  (画像なし) %s" % key)
            continue
        loc, yaw = wall_pose_rel(wall, u, z)
        a = spawn(unreal.StaticMeshActor, loc, (0, 0, yaw + rng.uniform(-4, 4)))
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        c.set_static_mesh(mesh)
        c.set_material(0, mats[key])
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        tag_actor(a, label)
        a.set_actor_hidden_in_game(True)
        n += 1
    log("張り紙を貼りました: %d 枚（最初は見えません）" % n)


def main():
    log("=== ゲームのしくみ 準備（買った電話ボックス用） ===")
    step("環境確認", s_env)
    step("前回の生成物を消す", s_clear, ["環境確認"])
    step("中心の印", s_center_marker, ["前回の生成物を消す"])
    step("当たり判定", s_collision, ["環境確認"])
    step("ドア", s_door, ["前回の生成物を消す"])
    step("蛍光灯", s_lights, ["前回の生成物を消す"])
    step("プレイヤーの開始位置", s_player_start, ["環境確認"])
    step("懐中電灯", s_flashlight, ["中心の印"])
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
