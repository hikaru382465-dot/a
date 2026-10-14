"""
木・岩・切り株に、当たり判定をつける（歩いて通りぬけないように）。
  - 名前に TREE_WORDS が入っているスタティックメッシュを探す（/Game のなか。エンジンの物は見ない）
  - すでに当たり判定がある物は、そのまま
  - 木：幹だけをふさぐ細い円柱（幹の太さ＝TRUNK_FRAC × 横の大きさ）。枝・葉は通りぬけられる（葉にひっかからない）
  - 岩：箱の当たり判定
  使い方（Cmd 欄）：  py "…/unreal/kd_trees_collision.py"     結果は出力ログ（KD で絞る）。やり直しても、すでにある物は変えない
"""
import unreal

TREE_WORDS = ("tree", "pine", "spruce", "fir", "conifer", "birch", "oak", "dead", "trunk", "stump", "log")
ROCK_WORDS = ("rock", "stone", "boulder", "cliff")
TRUNK_FRAC = 0.10               # 幹の太さ（メッシュの横の大きさの何割か）。通りぬけるなら大きく、ひっかかるなら小さく
EXCLUDE = ("/Engine/", "Foliage_Grass", "grass", "flower", "bush_small", "KoushuDenwa/Board", "KoushuDenwa/Safe", "KoushuDenwa/Game")

LOG = lambda m: unreal.log("[KD] " + m)
lib = unreal.EditorStaticMeshLibrary
eal = unreal.EditorAssetLibrary


def has_collision(mesh):
    try:
        return lib.get_simple_collision_count(mesh) > 0
    except Exception:  # noqa
        return False


def add_trunk(mesh):
    """幹だけの円柱（Sphyl）を、直接つける"""
    b = mesh.get_bounds()
    ex, ey, ez = b.box_extent.x, b.box_extent.y, b.box_extent.z
    r = max(8.0, min(ex, ey) * TRUNK_FRAC * 2.0)
    length = max(10.0, ez * 2.0 - r * 2.0)
    bs = mesh.get_editor_property("body_setup")
    ag = bs.get_editor_property("agg_geom")
    sp = unreal.KSphylElem()
    sp.set_editor_property("radius", float(r))
    sp.set_editor_property("length", float(length))
    sp.set_editor_property("center", unreal.Vector(b.origin.x, b.origin.y, b.origin.z))
    ag.set_editor_property("sphyl_elems", [sp])
    bs.set_editor_property("agg_geom", ag)
    mesh.set_editor_property("body_setup", bs)
    return r


def main():
    n_tree = n_rock = n_skip = n_err = 0
    for path in eal.list_assets("/Game", recursive=True, include_folder=False):
        low = path.lower()
        if any(x.lower() in low for x in EXCLUDE):
            continue
        name = low.rsplit("/", 1)[-1]
        is_tree = any(w in name for w in TREE_WORDS)
        is_rock = any(w in name for w in ROCK_WORDS)
        if not (is_tree or is_rock):
            continue
        try:
            mesh = eal.load_asset(path)
            if not isinstance(mesh, unreal.StaticMesh):
                continue
            if has_collision(mesh):
                n_skip += 1
                continue
            if is_tree:
                try:
                    r = add_trunk(mesh)
                    LOG("木に幹の当たり判定をつけました: %s（半径 %.0fcm）" % (path, r))
                except Exception as e:  # noqa
                    lib.add_simplified_collisions(mesh, unreal.ScriptingCollisionShapeType.CAPSULE, True)
                    LOG("木に、円柱の当たり判定をつけました（幹だけには、できませんでした: %s）: %s" % (e, path))
                n_tree += 1
            else:
                lib.add_simplified_collisions(mesh, unreal.ScriptingCollisionShapeType.BOX, True)
                LOG("岩に、箱の当たり判定をつけました: %s" % path)
                n_rock += 1
            eal.save_loaded_asset(mesh)
        except Exception as e:  # noqa
            n_err += 1
            unreal.log_warning("[KD] 当たり判定をつけられません: %s : %s" % (path, e))
    LOG("おわり：木 %d・岩 %d に当たり判定をつけた／すでにあった %d／失敗 %d。レベルを保存（Ctrl+S）してください" % (n_tree, n_rock, n_skip, n_err))


main()
