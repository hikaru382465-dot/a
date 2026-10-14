import bpy, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="gz/6b20397cea9496bdc06fa8ea99c60ad4.fbx")
o=bpy.data.objects['node_0']
print('rot',o.rotation_euler[:],'scale',o.scale[:],'loc',o.location[:])
bpy.context.view_layer.objects.active=o; o.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
vs=[v.co for v in o.data.vertices]
mn=Vector((min(v.x for v in vs),min(v.y for v in vs),min(v.z for v in vs)))
mx=Vector((max(v.x for v in vs),max(v.y for v in vs),max(v.z for v in vs)))
print('bounds',mn[:],mx[:])
s=1.6/mx.z
o.scale=(s,s,s); bpy.ops.object.transform_apply(scale=True)
# origin: feet center
cx=(mn.x+mx.x)/2*s; cy=(mn.y+mx.y)/2*s
for v in o.data.vertices: v.co.x-=cx; v.co.y-=cy
bpy.ops.object.shade_smooth()
m=o.modifiers.new('dec','DECIMATE'); m.ratio=25000/len(o.data.polygons)
bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.mode_set(mode='OBJECT')
me=o.data; me.calc_loop_triangles(); print('tris',len(me.loop_triangles),'polys',len(me.polygons))
o.name='Ghost'
for i in bpy.data.images:
    if i.size[0]>2048: i.scale(2048,2048)
    i.filepath_raw="//gout/"+i.name; i.file_format='PNG'; i.save()
bpy.ops.export_scene.fbx(filepath="gout/ghost.fbx",path_mode='COPY',embed_textures=False,apply_unit_scale=True,object_types={'MESH'})
bpy.ops.wm.save_as_mainfile(filepath="gout/ghost.blend")
