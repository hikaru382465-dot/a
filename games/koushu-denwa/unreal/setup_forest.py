"""
Unreal Engine 5 用：電話ボックスのまわりを「夜の森」にするスクリプト

先に setup_phonebooth.py を実行して、レベル L_Booth ができていること。
やること：画像の取り込み → 材質（地面・道・樹皮・針葉・岩） → 木と岩の取り込み
          → 地面を森の土に → 道 → 電話ボックスの足もとのコンクリート → 木・岩・切り株を散らす → 霧を濃く
何度実行しても同じ結果になる（前回の自動生成物はタグ KD_Forest で消してから作り直す）。

使い方（UEエディタ）：出力ログの入力欄を「Cmd」にして
    py "C:/…/a/games/koushu-denwa/unreal/setup_forest.py"
終わったら出力ログを「KD」で絞って、全部コピーして Claude に送る。

⚠ Claudeは Unreal を実行できないため、API名の違いでエラーが出る可能性がある。
   失敗した手順は [KD][FAIL] と原因が出る（他の手順は続けて実行される）。

重いとき：下の TREE_COUNT / ROCK_COUNT を減らす（メモリが足りないパソコン向け）。
Fab の本格的な木を使いたいとき：EXTERNAL_TREE_FOLDER に、その木があるフォルダーを書く（例 "/Game/Fab"）。
"""
import os
import math
import random
import traceback
import datetime

import unreal

# ---------------- 書き換えてよい設定 ----------------
REPO_ROOT = ""                      # 空なら、このファイルの場所から自動で求める
GAME_DIR = "/Game/KoushuDenwa"
TAG = "KD_Forest"
TREE_COUNT = 70                     # 松＋枯れ木の数（重いときは 40 に）
ROCK_COUNT = 30
STUMP_COUNT = 6
FOREST_RADIUS = 4500.0              # 森の広がり（cm）。4500 = 半径45m
CLEARING_RADIUS = 650.0             # 電話ボックスのまわりの空き地（cm）
PATH_HALF_WIDTH = 300.0             # 道のまわりに木を置かない幅（cm）
EXTERNAL_TREE_FOLDER = ""           # 例 "/Game/Fab" 。空なら、自作の木を使う
MESH_ROLL = 90.0          # 木・岩を立てる回転（立たないときは -90 にする）
MESH_PITCH = 0.0
GROUND_DARK = 0.35        # 地面の暗さ（小さいほど暗い。1.0でそのまま）
MOON_INTENSITY = 0.2      # 月の光（setup_phonebooth.py では 0.5）
SKY_INTENSITY = 0.12      # 空の光（同 0.3）
FOG_DENSITY = 0.045                 # 森の霧の濃さ
# --------------------------------------------------

LOG_LINES = []
STATE = {}
RESULTS = {}


def _log_path():
    try:
        return os.path.join(unreal.Paths.project_saved_dir(), "Logs", "KD_forest.txt")
    except Exception:
        return os.path.join(os.path.expanduser("~"), "KD_forest.txt")


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
        p = _log_path()
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
    except Exception as e:
        log("  (設定できず) %s = %r : %s" % (prop, value, str(e).splitlines()[0] if str(e) else e))
        return False


def repo_root():
    if REPO_ROOT:
        return REPO_ROOT
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        raise RuntimeError("REPO_ROOT を書き換えてください（このスクリプトの場所を取得できませんでした）")
    return os.path.normpath(os.path.join(here, "..", "..", ".."))


def tex_dir():
    return os.path.join(repo_root(), "games", "koushu-denwa", "assets", "tex")


def trees_fbx():
    return os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", "Trees.fbx")


# ---------------- 1) 環境確認 ----------------
def eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def label_of(a):
    try:
        return a.get_actor_label()
    except Exception:
        return ""


def find_actor(label_part):
    for a in eas().get_all_level_actors():
        if label_part in label_of(a):
            return a
    return None


def s_env():
    log("エンジン: %s" % unreal.SystemLibrary.get_engine_version())
    log("日時: %s" % datetime.datetime.now().isoformat(timespec="seconds"))
    if not os.path.exists(trees_fbx()):
        raise FileNotFoundError("Trees.fbx が見つかりません: " + trees_fbx())
    STATE["tools"] = unreal.AssetToolsHelpers.get_asset_tools()
    frame = find_actor("Booth_Frame")
    door = find_actor("Door")
    if frame is None or door is None:
        raise RuntimeError("電話ボックスが見つかりません。先に setup_phonebooth.py を実行して、レベル L_Booth を開いてください")
    fo, fe = frame.get_actor_bounds(False)
    do, de = door.get_actor_bounds(False)
    STATE["center"] = (fo.x, fo.y)
    dx, dy = do.x - fo.x, do.y - fo.y
    n = math.hypot(dx, dy) or 1.0
    # ドアのある側が「正面」。道はそちらへ伸ばす（浮動小数の誤差で斜めにならないよう、軸にそろえる）
    if abs(dx) >= abs(dy):
        STATE["front"] = (1.0 if dx > 0 else -1.0, 0.0)
    else:
        STATE["front"] = (0.0, 1.0 if dy > 0 else -1.0)
    log("ボックス中心=(%.0f, %.0f)  正面の向き=%s" % (fo.x, fo.y, STATE["front"]))


# ---------------- 2) 画像の取り込み ----------------
TEX_FILES = [
    "forest_ground_color.png", "forest_ground_normal.png", "forest_ground_rough.png",
    "forest_path_color.png", "forest_path_normal.png",
    "bark_color.png", "bark_normal.png", "leaves_color.png", "leaves_normal.png",
    "rock_color.png", "rock_normal.png",
    "floor_color.png", "floor_normal.png", "floor_rough.png",          # 足もとのコンクリート（電話ボックスの床と同じ）
]


def s_import_tex():
    tasks = []
    for f in TEX_FILES:
        p = os.path.join(tex_dir(), f)
        if not os.path.exists(p):
            log("  (画像なし) " + p)
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        t.set_editor_property("filename", p)
        t.set_editor_property("destination_path", GAME_DIR + "/Textures")
        tasks.append(t)
    STATE["tools"].import_asset_tasks(tasks)
    STATE["tex"] = {}
    for f in TEX_FILES:
        name = os.path.splitext(f)[0]
        a = unreal.EditorAssetLibrary.load_asset("%s/Textures/%s" % (GAME_DIR, name))
        if a is None:
            continue
        if "normal" in name:
            setp(a, "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            setp(a, "srgb", False)
            setp(a, "flip_green_channel", True)
        elif "rough" in name:
            setp(a, "compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            setp(a, "srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        STATE["tex"][name] = a
    log("取り込んだ画像: %d 枚" % len(STATE["tex"]))


# ---------------- 3) 材質 ----------------
mel = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty


def new_material(name):
    path = GAME_DIR + "/Materials"
    full = "%s/%s" % (path, name)
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        unreal.EditorAssetLibrary.delete_asset(full)
    m = STATE["tools"].create_asset(name, path, unreal.Material, unreal.MaterialFactoryNew())
    if m is None:
        raise RuntimeError("材質を作れません: " + name)
    return m


def x_(mat, cls, x, y):
    return mel.create_material_expression(mat, cls, x, y)


def c1(mat, v, y=0):
    e = x_(mat, unreal.MaterialExpressionConstant, -600, y)
    e.set_editor_property("r", float(v))
    return e


def tex_node(mat, tex, y=0, normal=False, tiling=None):
    e = x_(mat, unreal.MaterialExpressionTextureSample, -800, y)
    e.set_editor_property("texture", tex)
    if normal:
        e.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    if tiling:
        tc = x_(mat, unreal.MaterialExpressionTextureCoordinate, -1100, y)
        tc.set_editor_property("u_tiling", float(tiling[0]))
        tc.set_editor_property("v_tiling", float(tiling[1]))
        mel.connect_material_expressions(tc, "", e, "UVs")
    return e


def mk_tex_material(name, color, normal=None, rough=None, rough_const=0.9, tiling=None, metallic=0.0, dark=1.0):
    m = new_material(name)
    base = tex_node(m, color, -300, tiling=tiling)
    if dark != 1.0:                               # 色を暗くする（1.0 = そのまま）
        mul = x_(m, unreal.MaterialExpressionMultiply, -500, -300)
        mel.connect_material_expressions(base, "", mul, "A")
        mel.connect_material_expressions(c1(m, dark, -200), "", mul, "B")
        base = mul
    mel.connect_material_property(base, "", MP.MP_BASE_COLOR)
    if normal is not None:
        mel.connect_material_property(tex_node(m, normal, 0, normal=True, tiling=tiling), "", MP.MP_NORMAL)
    if rough is not None:
        mel.connect_material_property(tex_node(m, rough, 300, tiling=tiling), "R", MP.MP_ROUGHNESS)
    else:
        mel.connect_material_property(c1(m, rough_const, 300), "", MP.MP_ROUGHNESS)
    mel.connect_material_property(c1(m, metallic, 400), "", MP.MP_METALLIC)
    mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def s_materials():
    T = STATE["tex"]
    M = {}
    # 地面は 12000cm の板に、200cm ごとに画像を繰り返す＝60回
    M["ground"] = mk_tex_material("M_ForestGround", T["forest_ground_color"], T.get("forest_ground_normal"), T.get("forest_ground_rough"), tiling=(60, 60), dark=GROUND_DARK)
    M["path"] = mk_tex_material("M_ForestPath", T["forest_path_color"], T.get("forest_path_normal"), rough_const=0.92, tiling=(2.5, 1.5), dark=GROUND_DARK + 0.1)
    M["Bark"] = mk_tex_material("M_Bark", T["bark_color"], T.get("bark_normal"), rough_const=0.92)
    M["Leaves"] = mk_tex_material("M_Leaves", T["leaves_color"], T.get("leaves_normal"), rough_const=0.9)
    M["Rock"] = mk_tex_material("M_Rock", T["rock_color"], T.get("rock_normal"), rough_const=0.88)
    if "floor_color" in T:
        M["pad"] = mk_tex_material("M_BoothPad", T["floor_color"], T.get("floor_normal"), T.get("floor_rough"), tiling=(2, 2))
    STATE["mats"] = M
    log("作った材質: %s" % ", ".join(sorted(M)))


# ---------------- 4) 木・岩の取り込み ----------------
def s_import_trees():
    ui = unreal.FbxImportUI()
    setp(ui, "import_mesh", True)
    setp(ui, "import_as_skeletal", False)
    setp(ui, "automated_import_should_detect_type", False)
    setp(ui, "import_materials", False)
    setp(ui, "import_textures", False)
    setp(ui, "mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property("static_mesh_import_data")
    setp(d, "combine_meshes", False)
    setp(d, "build_nanite", True)                 # 細かい形を軽く描ける
    setp(d, "auto_generate_collision", False)
    setp(d, "transform_vertex_to_absolute", True)      # 向き（横倒し）を直す。電話ボックスと同じ設定
    t = unreal.AssetImportTask()
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("replace_existing_settings", True)
    t.set_editor_property("save", True)
    t.set_editor_property("filename", trees_fbx())
    t.set_editor_property("destination_path", GAME_DIR + "/Trees")
    t.set_editor_property("options", ui)
    try:
        unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    except Exception:  # noqa
        pass
    STATE["tools"].import_asset_tasks([t])
    paths = list(t.get_editor_property("imported_object_paths"))
    if not paths:
        paths = list(unreal.EditorAssetLibrary.list_assets(GAME_DIR + "/Trees", recursive=True, include_folder=False))
    meshes = {"pine": [], "dead": [], "stump": [], "rock": []}
    M = STATE["mats"]
    for p in paths:
        a = unreal.EditorAssetLibrary.load_asset(p)
        if not isinstance(a, unreal.StaticMesh):
            continue
        nm = a.get_name()
        for i, sm in enumerate(a.get_editor_property("static_materials")):
            sname = str(sm.get_editor_property("material_slot_name")).split(".")[0]
            if sname in M:
                a.set_material(i, M[sname])
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        key = "pine" if "Pine" in nm else "dead" if "Dead" in nm else "stump" if "Stump" in nm else "rock" if "Rock" in nm else None
        if key:
            meshes[key].append(a)
    # Fab など外部の木を足す
    if EXTERNAL_TREE_FOLDER:
        ext = {"pine": [], "rock": []}
        for p in unreal.EditorAssetLibrary.list_assets(EXTERNAL_TREE_FOLDER, recursive=True, include_folder=False):
            a = unreal.EditorAssetLibrary.load_asset(p)
            if isinstance(a, unreal.StaticMesh):
                low = a.get_name().lower()
                if "pine" in low or "tree" in low or "conifer" in low:
                    ext["pine"].append(a)
                elif "rock" in low or "boulder" in low:
                    ext["rock"].append(a)
        for k in ("pine", "rock"):
            if ext[k]:
                meshes[k] = ext[k]               # 自作のものと入れ替える（枯れ木・切り株は自作のまま）
        log("外部の木と入れ替えました（%s）松=%d 岩=%d" % (EXTERNAL_TREE_FOLDER, len(ext["pine"]), len(ext["rock"])))
    STATE["meshes"] = meshes
    log("木・岩: " + ", ".join("%s=%d" % (k, len(v)) for k, v in meshes.items()))
    if not meshes["pine"]:
        raise RuntimeError("松が見つかりません。取り込み結果: %s" % paths)


# ---------------- 5) レベルの準備（前回の自動生成物を消す） ----------------
def tag_actor(a, label=None):
    try:
        a.set_editor_property("tags", [unreal.Name(TAG)])
    except Exception as e:  # noqa
        log("  (タグ設定不可) %s" % e)
    if label:
        a.set_actor_label(label)


def spawn(cls, loc=(0, 0, 0), rot=(0, 0, 0)):
    """rot は (roll, pitch, yaw)"""
    return eas().spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(*rot))


def s_clear():
    n = 0
    for a in eas().get_all_level_actors():
        try:
            if TAG in [str(t) for t in a.get_editor_property("tags")]:
                eas().destroy_actor(a)
                n += 1
        except Exception:  # noqa
            pass
    log("前回の自動生成物を削除: %d" % n)


# ---------------- 6) 地面・道・足もと ----------------
def spawn_plane(label, loc, scale, yaw, material):
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    a = spawn(unreal.StaticMeshActor, loc, (0, 0, yaw))
    c = a.get_component_by_class(unreal.StaticMeshComponent)
    c.set_static_mesh(plane)
    a.set_actor_scale3d(unreal.Vector(*scale))
    c.set_material(0, material)
    tag_actor(a, label)
    return a


def path_points():
    cx, cy = STATE["center"]
    fx, fy = STATE["front"]
    rx, ry = -fy, fx                              # 右向き
    pts = []
    t = 380.0
    while t <= 4500.0:
        off = 300.0 * math.sin(t / 900.0)         # ゆるくくねる道
        pts.append((cx + fx * t + rx * off, cy + fy * t + ry * off))
        t += 500.0
    return pts


def dist_to_path(x, y, pts):
    best = 1e9
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        best = min(best, math.hypot(x - (ax + dx * t), y - (ay + dy * t)))
    return best


def s_ground():
    M = STATE["mats"]
    g = find_actor("Ground")
    if g is not None:                             # setup_phonebooth.py が置いた地面を、森の土に変える
        c = g.get_component_by_class(unreal.StaticMeshComponent)
        c.set_material(0, M["ground"])
        g.set_actor_scale3d(unreal.Vector(120, 120, 1))
        log("既存の Ground を森の土にして、120×120m に広げました")
    else:
        spawn_plane("Ground", (0, 0, -1), (120, 120, 1), 0, M["ground"])
        log("Ground を新しく作りました")
    cx, cy = STATE["center"]
    if "pad" in M:
        spawn_plane("BoothPad", (cx, cy, 0.5), (3.4, 3.4, 1), 0, M["pad"])    # 電話ボックスの足もとのコンクリート
    pts = path_points()
    STATE["path"] = pts
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        L = math.hypot(bx - ax, by - ay)
        yaw = math.degrees(math.atan2(by - ay, bx - ax))
        spawn_plane("Path_%02d" % i, ((ax + bx) / 2, (ay + by) / 2, 0.8), (L / 100.0 * 1.06, 3.0, 1), yaw, M["path"])
    log("道を %d 区画つくりました" % (len(pts) - 1))


# ---------------- 7) 木・岩・切り株を散らす ----------------
def orient_for(mesh):
    """取り込んだ木・岩は横倒しなので、roll=90 で立てる（ひかるが手作業で確かめた値）"""
    if EXTERNAL_TREE_FOLDER and mesh.get_path_name().startswith(EXTERNAL_TREE_FOLDER):
        return (0.0, 0.0)
    return (MESH_ROLL, MESH_PITCH)


def unit_of(mesh):
    """大きさが m 単位（小さい）なら 100 倍、すでに cm（大きい）なら 1 倍"""
    key = mesh.get_path_name()
    if key not in _UNITS:
        e = mesh.get_bounds().box_extent
        _UNITS[key] = 1.0 if max(e.x, e.y, e.z) * 2.0 > 300 else 100.0
    return _UNITS[key]


_UNITS = {}


def scatter(kind, count, rng, placed, min_gap, scale_range, tilt=0.0, near=None):
    meshes = STATE["meshes"][kind]
    if not meshes:
        return 0
    cx, cy = STATE["center"]
    pts = STATE["path"]
    n = 0
    tries = 0
    while n < count and tries < count * 40:
        tries += 1
        r = math.sqrt(rng.random()) * FOREST_RADIUS
        a = rng.random() * math.tau
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        if r < CLEARING_RADIUS:
            continue
        if dist_to_path(x, y, pts) < PATH_HALF_WIDTH:
            continue
        if any(math.hypot(x - px, y - py) < min_gap for px, py in placed):
            continue
        s = rng.uniform(*scale_range)
        m = rng.choice(meshes)
        base_roll, base_pitch = orient_for(m)
        act = spawn(unreal.StaticMeshActor, (x, y, 0), (base_roll + rng.uniform(-tilt, tilt), base_pitch + rng.uniform(-tilt, tilt), rng.random() * 360.0))
        comp = act.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(m)
        setp(comp, "mobility", unreal.ComponentMobility.STATIC)
        k = unit_of(m) * s
        act.set_actor_scale3d(unreal.Vector(k, k, k))   # Blenderは m、UEは cm。FBX変換で100倍になっていない場合に備える
        tag_actor(act, "%s_%03d" % (kind, n))
        placed.append((x, y))
        n += 1
    return n


def s_scatter():
    rng = random.Random(1998)
    placed = []
    n_trees = scatter("pine", int(TREE_COUNT * 0.75), rng, placed, 260.0, (0.8, 1.35), tilt=1.5)
    n_dead = scatter("dead", TREE_COUNT - int(TREE_COUNT * 0.75), rng, placed, 260.0, (0.8, 1.3), tilt=2.0)
    n_rock = scatter("rock", ROCK_COUNT, rng, placed, 160.0, (0.7, 1.6), tilt=6.0)
    n_stump = scatter("stump", STUMP_COUNT, rng, placed, 200.0, (0.8, 1.3))
    log("置いた数: 松=%d 枯れ木=%d 岩=%d 切り株=%d" % (n_trees, n_dead, n_rock, n_stump))


def s_fix_scale():
    """倍率はメッシュごとに scatter() で決めているので、ここでは何もしない"""
    log("倍率はメッシュごとに設定済み")


# ---------------- 8) 霧を濃く ----------------
def s_fog():
    fog = find_actor("Fog")
    if fog is None:
        log("  (Fog が見つかりません。スキップ)")
        return
    c = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    setp(c, "fog_density", FOG_DENSITY)
    setp(c, "volumetric_fog_distance", 8000.0)
    log("霧の濃さ = %s" % FOG_DENSITY)


def s_night():
    sun = find_actor("Moon")
    if sun is not None:
        setp(sun.get_component_by_class(unreal.DirectionalLightComponent), "intensity", MOON_INTENSITY)
    sky = find_actor("SkyLight")
    if sky is not None:
        setp(sky.get_component_by_class(unreal.SkyLightComponent), "intensity", SKY_INTENSITY)
    log("月=%s 空=%s に下げました" % (MOON_INTENSITY, SKY_INTENSITY))


def s_save():
    unreal.EditorAssetLibrary.save_directory(GAME_DIR, only_if_is_dirty=False, recursive=True)
    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    except Exception as e:  # noqa
        log("  (レベル保存不可) %s" % e)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


def main():
    log("=== 森のセットアップ開始 ===")
    step("環境確認", s_env)
    step("画像取り込み", s_import_tex, ["環境確認"])
    step("材質を作る", s_materials, ["画像取り込み"])
    step("木・岩の取り込み", s_import_trees, ["材質を作る"])
    step("前回の生成物を消す", s_clear, ["環境確認"])
    step("地面・道・足もと", s_ground, ["材質を作る", "前回の生成物を消す"])
    step("木・岩を散らす", s_scatter, ["木・岩の取り込み", "地面・道・足もと"])
    step("倍率の補正", s_fix_scale, ["木・岩を散らす"])
    step("霧", s_fog, ["環境確認"])
    step("夜の明るさ", s_night, ["環境確認"])
    step("保存", s_save, ["環境確認"])
    log("SUMMARY: " + ", ".join("%s=%s" % (k, v) for k, v in RESULTS.items()))
    failed = [k for k, v in RESULTS.items() if v == "FAIL"]
    if failed:
        log_err("失敗した手順: %s  → 出力ログを「KD」で絞って全部コピーして、Claudeに送ってください" % ", ".join(failed))
    else:
        log("完了。レベルを見回して確認してください（重いときは TREE_COUNT を減らす）")
    write_log_file()


main()
