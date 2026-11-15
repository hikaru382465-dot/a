"""書き出した .glb を、別のBlenderの空の場面に読み込んで、中身を数える。
使い方: blender -b -P check_glb.py -- ファイル.glb"""
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index("--") + 1]
bpy.ops.import_scene.gltf(filepath=path)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
lights = [o for o in bpy.data.objects if o.type == "LIGHT"]
tris = sum(len(o.data.polygons) for o in meshes)
print("CHECK meshes", len(meshes), "lights", len(lights), "faces", tris, "materials", len(bpy.data.materials), "images", len(bpy.data.images))
for o in bpy.data.objects:
    if o.type == "MESH":
        ys = [v.co.z for v in o.data.vertices]
        if not ys: print("EMPTY", o.name)
bb = [o.dimensions for o in meshes if o.name.startswith("floor")]
print("CHECK floor dims", [tuple(round(x, 2) for x in d) for d in bb])
