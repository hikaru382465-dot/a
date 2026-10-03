"""
Unreal Engine 5 用：電話ボックスを一括セットアップするスクリプト

やること：FBX取り込み → 画像取り込み → 材質を作る → メッシュに材質を割り当て → 新しいレベルに配置
          → 月・空・霧・ポストプロセス・蛍光灯の光 → ドアの回転軸（DoorHinge）を作る
何度実行しても同じ結果になる（前回の自動生成物はタグ KD_Auto で消してから作り直す）。

使い方（UEエディタ）：
  1. 編集 → プラグイン → 「Python Editor Script Plugin」をオン → 再起動
  2. Output Log の入力欄を「Cmd」にして次を実行（パスは自分の場所に。区切りは / ）
       py "C:/…/a/games/koushu-denwa/unreal/setup_phonebooth.py"
  3. 終わったら Output Log を「KD」で絞ってコピー、または Saved/Logs/KD_setup.txt をClaudeに送る

⚠ Claudeは Unreal を実行できないため、API名の違い・エラーが出る可能性がある。
   失敗した手順は [KD][FAIL] と原因が出る（他の手順は続けて実行される）。
"""
import os
import sys
import math
import traceback
import datetime

import unreal

# ---------------- 書き換えてよい設定 ----------------
REPO_ROOT = ""                      # 例 "C:/Users/hikaru/a" 。空なら、このファイルの場所から自動で求める
GAME_DIR = "/Game/KoushuDenwa"
LEVEL_PATH = GAME_DIR + "/Maps/L_Booth"
TAG = "KD_Auto"
DOOR_OPEN_YAW = 100.0               # ドアを開くときの回転（効果を見る用。逆に開くなら -100 にする）
# --------------------------------------------------

LOG_LINES = []


def _log_path():
    try:
        return os.path.join(unreal.Paths.project_saved_dir(), "Logs", "KD_setup.txt")
    except Exception:
        return os.path.join(os.path.expanduser("~"), "KD_setup.txt")


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


# ---------------- 手順を安全に実行する枠 ----------------
STATE = {}
RESULTS = {}


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
    """プロパティを設定。名前が違う等で失敗しても止めず、ログに残す。"""
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception as e:
        log("  (設定できず) %s = %r : %s" % (prop, value, str(e).splitlines()[0] if str(e) else e))
        return False


def setp_override(settings, prop, value):
    """PostProcessSettings 用：値と override_◯◯ を両方セット"""
    ok = setp(settings, prop, value)
    setp(settings, "override_" + prop, True)
    return ok


# ---------------- パス ----------------
def repo_root():
    if REPO_ROOT:
        return REPO_ROOT
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        raise RuntimeError("REPO_ROOT を書き換えてください（このスクリプトの場所を取得できませんでした）")
    return os.path.normpath(os.path.join(here, "..", "..", ".."))


def fbx_path():
    return os.path.join(repo_root(), "games", "koushu-denwa", "assets", "unreal", "PhoneBooth.fbx")


def tex_dir():
    return os.path.join(repo_root(), "games", "koushu-denwa", "assets", "tex")


# ---------------- 1) 環境確認 ----------------
def s_env():
    log("エンジン: %s" % unreal.SystemLibrary.get_engine_version())
    log("日時: %s" % datetime.datetime.now().isoformat(timespec="seconds"))
    log("REPO: %s" % repo_root())
    if not os.path.exists(fbx_path()):
        raise FileNotFoundError("FBXが見つかりません: " + fbx_path())
    STATE["tools"] = unreal.AssetToolsHelpers.get_asset_tools()
    STATE["eal"] = unreal.EditorAssetLibrary


def interchange(enabled):
    try:
        unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX %d" % (1 if enabled else 0))
    except Exception as e:  # noqa
        log("  (Interchange切り替え不可) %s" % e)


# ---------------- 2) FBX取り込み ----------------
def import_fbx(scale):
    ui = unreal.FbxImportUI()
    setp(ui, "import_mesh", True)
    setp(ui, "import_as_skeletal", False)
    setp(ui, "import_materials", False)
    setp(ui, "import_textures", False)
    setp(ui, "automated_import_should_detect_type", False)
    setp(ui, "mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property("static_mesh_import_data")
    setp(d, "combine_meshes", False)             # 名前（Door 等）を残す
    setp(d, "build_nanite", False)
    setp(d, "auto_generate_collision", False)
    setp(d, "transform_vertex_to_absolute", True)  # 全部品の原点を世界原点にそろえる
    setp(d, "import_uniform_scale", float(scale))
    t = unreal.AssetImportTask()
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("replace_existing_settings", True)
    t.set_editor_property("save", True)
    t.set_editor_property("filename", fbx_path())
    t.set_editor_property("destination_path", GAME_DIR + "/Meshes")
    t.set_editor_property("options", ui)
    STATE["tools"].import_asset_tasks([t])
    paths = list(t.get_editor_property("imported_object_paths"))
    if not paths:
        paths = [p for p in STATE["eal"].list_assets(GAME_DIR + "/Meshes", recursive=True, include_folder=False)]
    return paths


def mesh_height(mesh):
    b = mesh.get_bounds()
    return b.box_extent.z * 2.0


def find_mesh(suffix):
    for p in STATE["mesh_paths"]:
        if p.split(".")[0].endswith(suffix) or p.endswith(suffix):
            a = unreal.EditorAssetLibrary.load_asset(p)
            if a:
                return a
    return None


def s_import_fbx():
    interchange(False)
    try:
        paths = import_fbx(1.0)
        STATE["mesh_paths"] = paths
        log("取り込んだメッシュ数: %d" % len(paths))
        frame = find_mesh("Booth_Frame")
        if frame is None:
            raise RuntimeError("Booth_Frame が見つかりません。取り込み結果: %s" % paths)
        h = mesh_height(frame)
        log("Booth_Frame の高さ = %.2f" % h)
        if h < 10:
            log("大きさが 1/100 だったので scale=100 で取り込み直します")
            STATE["mesh_paths"] = import_fbx(100.0)
            frame = find_mesh("Booth_Frame")
            log("取り込み直し後の高さ = %.2f（230前後なら正常）" % mesh_height(frame))
    finally:
        interchange(True)


# ---------------- 3) 画像取り込み ----------------
TEX_FILES = [
    "phone_panel_albedo.png", "phone_panel_normal.png", "phone_lcd.png", "phone_keys_atlas.png",
    "phone_body_albedo.png", "phone_body_rough.png", "caution_sticker.png", "info_panel.png",
    "bronze_color.png", "bronze_rough.png", "glass_color.png", "glass_rough.png", "glass_dirt.png",   # 古び（汚れ）
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
            log("  (読み込めず) " + name)
            continue
        if "normal" in name:
            setp(a, "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            setp(a, "srgb", False)
        elif "rough" in name or name == "glass_dirt":
            setp(a, "compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            setp(a, "srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        STATE["tex"][name] = a


# ---------------- 4) 材質を作る ----------------
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


def c3(mat, r, g, b, y=0):
    e = x_(mat, unreal.MaterialExpressionConstant3Vector, -600, y)
    e.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return e


def c1(mat, v, y=0):
    e = x_(mat, unreal.MaterialExpressionConstant, -600, y)
    e.set_editor_property("r", float(v))
    return e


def tex_node(mat, tex, y=0, normal=False):
    e = x_(mat, unreal.MaterialExpressionTextureSample, -800, y)
    e.set_editor_property("texture", tex)
    if normal:
        e.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    return e


def mul(mat, a, b, y=0):
    e = x_(mat, unreal.MaterialExpressionMultiply, -400, y)
    mel.connect_material_expressions(a, "", e, "A")
    mel.connect_material_expressions(b, "", e, "B")
    return e


def finish(mat):
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)


def mk_solid(name, color, metallic, rough, spec=0.5):
    m = new_material(name)
    mel.connect_material_property(c3(mat=m, r=color[0], g=color[1], b=color[2], y=-200), "", MP.MP_BASE_COLOR)
    mel.connect_material_property(c1(m, metallic, 0), "", MP.MP_METALLIC)
    mel.connect_material_property(c1(m, rough, 100), "", MP.MP_ROUGHNESS)
    mel.connect_material_property(c1(m, spec, 200), "", MP.MP_SPECULAR)
    finish(m)
    return m


def mk_textured(name, albedo, rough_tex=None, rough_const=0.5, metallic=0.0, tint=1.0):
    m = new_material(name)
    base = tex_node(m, albedo, -200)
    if tint != 1.0:      # 色を暗く・明るく（1より小さいと暗い）
        base = mul(m, base, c1(m, tint, -150), -200)
    mel.connect_material_property(base, "", MP.MP_BASE_COLOR)
    if rough_tex is not None:
        mel.connect_material_property(tex_node(m, rough_tex, 100), "R", MP.MP_ROUGHNESS)
    else:
        mel.connect_material_property(c1(m, rough_const, 100), "", MP.MP_ROUGHNESS)
    mel.connect_material_property(c1(m, metallic, 200), "", MP.MP_METALLIC)
    finish(m)
    return m


def s_materials():
    T = STATE["tex"]
    M = {}
    # 色だけの材質（リニア色, 金属感, 粗さ）
    for name, col, met, rg in [
        ("Bronze", (0.30, 0.19, 0.10), 1.0, 0.35),
        ("Steel", (0.60, 0.60, 0.62), 1.0, 0.30),
        ("GrayPaint", (0.12, 0.12, 0.13), 0.2, 0.60),
        ("PhoneMetal", (0.55, 0.55, 0.55), 1.0, 0.40),
        ("CordSteel", (0.50, 0.50, 0.50), 1.0, 0.40),
        ("PhoneBlack", (0.02, 0.02, 0.02), 0.0, 0.50),
        ("PhoneDarkGrey", (0.06, 0.06, 0.06), 0.0, 0.55),
        ("Book0", (0.03, 0.08, 0.25), 0.0, 0.8), ("Book1", (0.35, 0.30, 0.03), 0.0, 0.8),
        ("Book2", (0.45, 0.45, 0.42), 0.0, 0.8), ("Book3", (0.04, 0.12, 0.06), 0.0, 0.8),
    ]:
        M[name] = mk_solid("M_" + name, col, met, rg)
    # 画像つきの材質
    if "bronze_color" in T:       # 枠：ブラシ目・白い腐食粉・さび
        M["Bronze"] = mk_textured("M_Bronze", T["bronze_color"], T.get("bronze_rough"), metallic=0.85)
    if "phone_body_albedo" in T:
        M["PhoneGreen"] = mk_textured("M_PhoneGreen", T["phone_body_albedo"], T.get("phone_body_rough"), tint=0.7)   # ひかるが調整した値（0.7）
    if "phone_keys_atlas" in T:
        M["PhoneKeys"] = mk_textured("M_PhoneKeys", T["phone_keys_atlas"], rough_const=0.3)
    if "caution_sticker" in T:
        M["CautionSticker"] = mk_textured("M_CautionSticker", T["caution_sticker"], rough_const=0.5)
    if "info_panel" in T:
        M["InfoPanel"] = mk_textured("M_InfoPanel", T["info_panel"], rough_const=0.4)
    # 操作パネル（法線マップつき）
    if "phone_panel_albedo" in T:
        m = new_material("M_PhonePanel")
        mel.connect_material_property(tex_node(m, T["phone_panel_albedo"], -200), "", MP.MP_BASE_COLOR)
        if "phone_panel_normal" in T:
            mel.connect_material_property(tex_node(m, T["phone_panel_normal"], 0, normal=True), "", MP.MP_NORMAL)
        mel.connect_material_property(c1(m, 0.5, 200), "", MP.MP_ROUGHNESS)
        finish(m)
        M["PhonePanel"] = m
    # 液晶（光る）
    if "phone_lcd" in T:
        m = new_material("M_LCD")
        t = tex_node(m, T["phone_lcd"], -100)
        mel.connect_material_property(mul(m, t, c1(m, 4.0, 60), -100), "", MP.MP_EMISSIVE_COLOR)
        mel.connect_material_property(mul(m, tex_node(m, T["phone_lcd"], 120), c1(m, 0.3, 200), 120), "", MP.MP_BASE_COLOR)
        mel.connect_material_property(c1(m, 0.2, 300), "", MP.MP_ROUGHNESS)
        finish(m)
        M["LCD"] = m
    # ガラス（半透明。汚れの濃いところは不透明・ざらざらに）
    m = new_material("M_Glass")
    setp(m, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    setp(m, "translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    setp(m, "two_sided", True)
    if "glass_color" in T and "glass_rough" in T:
        gc = tex_node(m, T["glass_color"], -200)
        mel.connect_material_property(mul(m, gc, c1(m, 0.45, -250), -200), "", MP.MP_BASE_COLOR)   # 汚れ（くもり）が暗い画面でも見えるよう明るめ
        mel.connect_material_property(gc, "A", MP.MP_OPACITY)                     # 画像のアルファ＝汚れの濃さ
        mel.connect_material_property(tex_node(m, T["glass_rough"], 0), "R", MP.MP_ROUGHNESS)
    else:
        mel.connect_material_property(c3(m, 0.02, 0.025, 0.022, -200), "", MP.MP_BASE_COLOR)
        mel.connect_material_property(c1(m, 0.15, -100), "", MP.MP_OPACITY)
        mel.connect_material_property(c1(m, 0.04, 0), "", MP.MP_ROUGHNESS)
    mel.connect_material_property(c1(m, 0.6, 100), "", MP.MP_SPECULAR)
    finish(m)
    M["Glass"] = m
    # 蛍光灯（Unlit・光る。Flicker でちらつかせられる）
    m = new_material("M_Tube")
    setp(m, "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    flick = x_(m, unreal.MaterialExpressionScalarParameter, -800, 100)
    setp(flick, "parameter_name", "Flicker")
    setp(flick, "default_value", 1.0)
    base = mul(m, c3(m, 1.0, 0.90, 0.78, -100), c1(m, 25.0, 0), -100)   # 古い蛍光灯は黄ばむ
    mel.connect_material_property(mul(m, base, flick, 0), "", MP.MP_EMISSIVE_COLOR)
    finish(m)
    M["Tube"] = m
    STATE["mats"] = M
    log("作った材質: %s" % ", ".join(sorted(M)))


# ---------------- 5) メッシュに材質・コリジョンを設定 ----------------
def s_assign():
    M = STATE["mats"]
    sm_sub = None
    try:
        sm_sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception as e:  # noqa
        log("  (StaticMeshEditorSubsystem なし) %s" % e)
    for p in STATE["mesh_paths"]:
        mesh = unreal.EditorAssetLibrary.load_asset(p)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        slots = mesh.get_editor_property("static_materials")
        for i, sm in enumerate(slots):
            sname = str(sm.get_editor_property("material_slot_name")).split(".")[0]
            sname = sname.replace("M_", "")
            mat = M.get(sname)
            if mat is None:
                log("  (材質なし) %s のスロット '%s'" % (mesh.get_name(), sname))
                continue
            mesh.set_material(i, mat)
        nm = mesh.get_name()
        try:
            if nm.endswith(("Booth_Frame", "Booth_Glass", "Booth_Interior", "Booth_Roof")):
                bs = mesh.get_editor_property("body_setup")
                bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            elif nm.endswith("Door") and sm_sub is not None:
                sm_sub.add_simple_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX)
        except Exception as e:  # noqa
            log("  (コリジョン設定不可) %s : %s" % (nm, e))
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)


# ---------------- 6) レベルと配置 ----------------
def eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


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


def s_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = False
    try:
        ok = les.new_level(LEVEL_PATH)
    except Exception as e:  # noqa
        log("  (new_level 失敗) %s" % e)
    log("新しいレベル: %s（%s）" % (LEVEL_PATH, ok))
    STATE["les"] = les
    # 前回の自動生成物を消す
    n = 0
    for a in eas().get_all_level_actors():
        try:
            if TAG in [str(t) for t in a.get_editor_property("tags")]:
                eas().destroy_actor(a)
                n += 1
        except Exception:  # noqa
            pass
    log("前回の自動生成物を削除: %d" % n)


def s_place():
    STATE["actors"] = {}
    for p in STATE["mesh_paths"]:
        mesh = unreal.EditorAssetLibrary.load_asset(p)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        nm = mesh.get_name()
        a = spawn(unreal.StaticMeshActor)
        comp = a.get_component_by_class(unreal.StaticMeshComponent)
        comp.set_static_mesh(mesh)
        tag_actor(a, nm)
        setp(comp, "mobility", unreal.ComponentMobility.MOVABLE if nm.endswith("Door") else unreal.ComponentMobility.STATIC)
        STATE["actors"][nm.split("_", 1)[-1] if nm.startswith("PhoneBooth_") else nm] = a
    # 地面（Engine の板を 100 倍）
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    if plane:
        g = spawn(unreal.StaticMeshActor, (0, 0, -1))
        g.get_component_by_class(unreal.StaticMeshComponent).set_static_mesh(plane)
        g.set_actor_scale3d(unreal.Vector(100, 100, 1))
        tag_actor(g, "Ground")
    log("配置したActor: %s" % ", ".join(sorted(STATE["actors"])))


def actor_by_suffix(suffix):
    for k, a in STATE["actors"].items():
        if k.endswith(suffix):
            return a
    return None


# ---------------- 7) 光・霧・ポストプロセス ----------------
def s_lighting():
    # 月
    sun = spawn(unreal.DirectionalLight, (0, 0, 500), (0, -35.0, 40.0))
    tag_actor(sun, "Moon")
    c = sun.get_component_by_class(unreal.DirectionalLightComponent)
    setp(c, "intensity", 0.5)
    setp(c, "use_temperature", True)
    setp(c, "temperature", 9000.0)
    setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
    # 空
    sky = spawn(unreal.SkyLight, (0, 0, 400))
    tag_actor(sky, "SkyLight")
    sc = sky.get_component_by_class(unreal.SkyLightComponent)
    setp(sc, "real_time_capture", True)
    setp(sc, "intensity", 0.3)
    setp(sc, "mobility", unreal.ComponentMobility.MOVABLE)
    try:
        tag_actor(spawn(unreal.SkyAtmosphere), "SkyAtmosphere")
    except Exception as e:  # noqa
        log("  (SkyAtmosphere なし) %s" % e)
    # 霧
    fog = spawn(unreal.ExponentialHeightFog, (0, 0, 100))
    tag_actor(fog, "Fog")
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    setp(fc, "fog_density", 0.03)
    setp(fc, "fog_height_falloff", 0.2)
    if not setp(fc, "fog_inscattering_luminance", unreal.LinearColor(0.02, 0.025, 0.03, 1.0)):
        setp(fc, "fog_inscattering_color", unreal.LinearColor(0.02, 0.025, 0.03, 1.0))
    setp(fc, "volumetric_fog", True)
    setp(fc, "volumetric_fog_scattering_distribution", 0.6)
    setp(fc, "volumetric_fog_albedo", unreal.Color(204, 204, 217, 255))
    setp(fc, "volumetric_fog_extinction_scale", 1.5)
    setp(fc, "volumetric_fog_distance", 3000.0)
    # ポストプロセス
    ppv = spawn(unreal.PostProcessVolume)
    tag_actor(ppv, "PostProcess")
    setp(ppv, "unbound", True)
    s = ppv.get_editor_property("settings")
    setp_override(s, "dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
    setp_override(s, "reflection_method", unreal.ReflectionMethod.LUMEN)
    setp_override(s, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    setp_override(s, "auto_exposure_apply_physical_camera_exposure", False)
    setp_override(s, "auto_exposure_bias", -7.8)   # ひかるが調整した値。この版は大きいほど明るい
    setp_override(s, "bloom_intensity", 0.8)
    setp_override(s, "vignette_intensity", 0.55)
    setp_override(s, "film_grain_intensity", 0.25)
    setp_override(s, "scene_fringe_intensity", 0.6)
    setp_override(s, "color_saturation", unreal.Vector4(0.85, 0.85, 0.85, 1.0))
    ppv.set_editor_property("settings", s)   # 構造体は取り出して戻さないと反映されない


def horizontal_axes():
    """Door の形から、幅の軸（長い方）と奥行きの軸（短い方）を求める"""
    door = actor_by_suffix("Door")
    o, e = door.get_actor_bounds(False)
    return ("x", "y") if e.x >= e.y else ("y", "x")


def s_tubes():
    frame = actor_by_suffix("Booth_Frame")
    o, e = frame.get_actor_bounds(False)
    width_ax, depth_ax = horizontal_axes()
    log("幅の軸=%s 奥行きの軸=%s / Frame中心=(%.1f,%.1f,%.1f) 半径=(%.1f,%.1f,%.1f)" % (width_ax, depth_ax, o.x, o.y, o.z, e.x, e.y, e.z))
    z = o.z + e.z - 25.0
    yaw = 0.0 if depth_ax == "y" else 90.0     # 光源の長い方を奥行きにそろえる
    for sgn in (-1, 1):
        loc = [o.x, o.y, z]
        loc[0 if width_ax == "x" else 1] += sgn * 27.0
        r = spawn(unreal.RectLight, tuple(loc), (0, -90.0, yaw))
        tag_actor(r, "TubeLight_%s" % ("L" if sgn < 0 else "R"))
        c = r.get_component_by_class(unreal.RectLightComponent)
        setp(c, "mobility", unreal.ComponentMobility.MOVABLE)
        setp(c, "intensity_units", unreal.LightUnits.LUMENS)
        setp(c, "intensity", 1500.0)   # ひかるが調整した値
        setp(c, "use_temperature", True)
        setp(c, "temperature", 5000.0)
        setp(c, "light_color", unreal.Color(235, 255, 230, 255))
        setp(c, "source_width", 85.0)
        setp(c, "source_height", 3.0)
        setp(c, "barn_door_angle", 88.0)
        setp(c, "attenuation_radius", 600.0)
        setp(c, "volumetric_scattering_intensity", 1.5)


# ---------------- 8) ドアの回転軸 ----------------
def s_door():
    door = actor_by_suffix("Door")
    handset = actor_by_suffix("Phone_Handset")
    if door is None:
        raise RuntimeError("Door のActorがありません")
    o, e = door.get_actor_bounds(False)
    width_ax, _ = horizontal_axes()
    ho = handset.get_actor_bounds(False)[0] if handset else o
    # 受話器は蛍光側ではなく「左」側にある＝蝶番も左。受話器に近い端を蝶番にする
    d_c = getattr(o, width_ax)
    d_e = getattr(e, width_ax)
    h_c = getattr(ho, width_ax)
    end = d_c - d_e if abs((d_c - d_e) - h_c) <= abs((d_c + d_e) - h_c) else d_c + d_e
    inward = 1.0 if end < d_c else -1.0
    loc = [o.x, o.y, o.z - e.z]
    loc[0 if width_ax == "x" else 1] = end + inward * 1.0
    hinge = spawn(unreal.StaticMeshActor, tuple(loc))
    tag_actor(hinge, "DoorHinge")
    setp(hinge.get_component_by_class(unreal.StaticMeshComponent), "mobility", unreal.ComponentMobility.MOVABLE)
    door.attach_to_actor(hinge, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    log("DoorHinge を作成: (%.1f, %.1f, %.1f)。ドアを開くときは DoorHinge の Yaw を %.0f または %.0f にして向きを確かめる" % (loc[0], loc[1], loc[2], DOOR_OPEN_YAW, -DOOR_OPEN_YAW))


# ---------------- 9) 保存 ----------------
def s_save():
    unreal.EditorAssetLibrary.save_directory(GAME_DIR, only_if_is_dirty=False, recursive=True)
    try:
        STATE["les"].save_current_level()
    except Exception as e:  # noqa
        log("  (レベル保存不可) %s" % e)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


def main():
    log("=== 電話ボックス セットアップ開始 ===")
    step("環境確認", s_env)
    step("FBX取り込み", s_import_fbx, ["環境確認"])
    step("画像取り込み", s_import_tex, ["環境確認"])
    step("材質を作る", s_materials, ["画像取り込み"])
    step("材質の割り当て", s_assign, ["FBX取り込み", "材質を作る"])
    step("レベル作成", s_level, ["環境確認"])
    step("電話ボックスを配置", s_place, ["FBX取り込み", "レベル作成"])
    step("光・霧・ポストプロセス", s_lighting, ["レベル作成"])
    step("蛍光灯の光", s_tubes, ["電話ボックスを配置"])
    step("ドアの回転軸", s_door, ["電話ボックスを配置"])
    step("保存", s_save, ["レベル作成"])
    summary = ", ".join("%s=%s" % (k, v) for k, v in RESULTS.items())
    log("SUMMARY: " + summary)
    failed = [k for k, v in RESULTS.items() if v == "FAIL"]
    if failed:
        log_err("失敗した手順: %s  → Output Log を「KD」で絞って全部コピーして、Claudeに送ってください" % ", ".join(failed))
    else:
        log("完了。レベル %s を開いて確認してください" % LEVEL_PATH)
    write_log_file()


main()
