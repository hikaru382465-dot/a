"""
ガラスに貼る張り紙用の「板」を作る（Blender用）。幅0.5m × 高さ0.7m、中心が原点、おもて面は -Y 向き（Unrealでは +Y 向き）。
出力：assets/unreal/Poster.fbx   使い方：python make_poster_mesh.py
"""
import bpy, math, os
try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.path.expanduser('~')
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets', 'unreal'))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=1)
o = bpy.context.active_object
o.scale = (0.5, 0.7, 1.0)
o.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
o.name = 'Poster'; o.data.name = 'Poster'
m = bpy.data.materials.new('Poster'); o.data.materials.append(m)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, 'Poster.fbx'), use_selection=True, apply_scale_options='FBX_SCALE_UNITS',
                         path_mode='COPY', embed_textures=False, mesh_smooth_type='FACE', add_leaf_bones=False, bake_space_transform=True)
print('書き出しました:', os.path.join(OUT, 'Poster.fbx'), '法線(-Yのはず):', [round(v, 2) for v in o.data.polygons[0].normal])
