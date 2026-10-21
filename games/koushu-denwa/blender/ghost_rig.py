import bpy, math, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="gout/ghost.blend")
o=bpy.data.objects['Ghost']; me=o.data
bpy.context.view_layer.objects.active=o
# --- Smile shape key
img=bpy.data.images['texture_pbr_20250901.png']; W,H=img.size; px=np.array(img.pixels[:]).reshape(H,W,4)
uv=me.uv_layers.active.data
vuv={}
for l in me.loops: vuv[l.vertex_index]=uv[l.index].uv
def lum(i):
    u,v=vuv[i]; c=px[min(H-1,int(v*H)),min(W-1,int(u*W))]; return (c[0]+c[1]+c[2])/3
cz=1.403; mw=0.030
from mathutils.bvhtree import BVHTree
bm_=BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get())
hit=set(); ysf=[]
for xi in np.linspace(-0.05,0.05,21):
    for zi in np.linspace(cz-0.04,cz+0.04,21):
        loc,nor,idx,d=bm_.ray_cast(Vector((xi,-1,zi)),Vector((0,1,0)))
        if loc: ysf.append((xi,zi,loc.y))
ly=bm_.ray_cast(Vector((0,-1,cz)),Vector((0,1,0)))[0].y; print('lipy',ly)
ymed=float(np.median([t[2] for t in ysf])); print('ymed',ymed,len(ysf))
face=[v.index for v in me.vertices if abs(v.co.x)<0.06 and abs(v.co.z-cz)<0.05 and abs(v.co.y-ymed)<0.025]
print('face',len(face))
o.shape_key_add(name='Basis'); sk=o.shape_key_add(name='Smile')
for i in face:
    c=me.vertices[i].co; dx=abs(c.x); dz=c.z-cz
    wgt=math.exp(-((dx-0.028)**2)/(2*0.014**2))*math.exp(-(dz**2)/(2*0.016**2))
    if dz<-0.012: wgt*=0.3
    s=1 if c.x>=0 else -1
    sk.data[i].co=Vector((c.x+s*0.010*wgt, c.y-0.002*wgt, c.z+0.016*wgt))
    # cheek lift
    # mouth centre lowers slightly
    if dx<0.014: sk.data[i].co.z-=0.0015*math.exp(-dz**2/(2*0.012**2))
gk=o.shape_key_add(name='Grin',from_mix=False)
for i in face:
    c=me.vertices[i].co; sm=sk.data[i].co.copy(); gk.data[i].co=sm
    dx=abs(c.x); dz=c.z-cz; ax=math.exp(-dx**2/(2*0.03**2))
    if -0.002<dz<0.014: gk.data[i].co.z+=0.007*ax
    elif -0.016<dz<=-0.002: gk.data[i].co.z-=0.011*ax
# teeth
import bmesh
tm=bpy.data.meshes.new('Teeth'); bm=bmesh.new()
import random; random.seed(7)
from mathutils import Matrix as M
def tooth(x,y,zc,w,h,up):
    # tapered tooth: cone, wide at gum, narrow at tip, slightly rounded
    r=bmesh.ops.create_cone(bm,cap_ends=True,segments=7,radius1=w*0.5,radius2=w*0.28,depth=h,matrix=M.Translation((x,y,zc))@M.Rotation(math.radians(random.uniform(-6,6)),4,'Y')@M.Rotation(0 if up else math.pi,4,'X'))
n=9
for k in range(n):
    t=(k+0.5)/n*2-1; x=t*0.024+random.uniform(-0.0008,0.0008); y=ly-0.002+0.012*t*t
    big=1.35 if abs(t)<0.2 else (1.0 if abs(t)<0.6 else 0.8)
    # upper row (tips point down), lower row (tips point up)
    tooth(x,y,cz+0.004+random.uniform(-0.0006,0.0006),0.0044*big+random.uniform(0,0.0008),0.011*big*random.uniform(0.85,1.1),False)
    if k%1==0: tooth(x+random.uniform(-0.0006,0.0006),y+0.001,cz-0.008+random.uniform(-0.0008,0.0008),0.0040*big,0.0095*big*random.uniform(0.8,1.15),True)
bm.to_mesh(tm); bm.free()
to=bpy.data.objects.new('Teeth',tm); bpy.context.scene.collection.objects.link(to)
mt=bpy.data.materials.new('TeethMat'); mt.use_nodes=True; mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.52,0.46,0.32,1); mt.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=0.35
to.data.materials.append(mt)
real=[v.co.copy() for v in tm.vertices]
for v in tm.vertices: v.co=Vector((0,ymed+0.02,cz))
to.shape_key_add(name='Basis'); tg=to.shape_key_add(name='Grin')
for v,r in zip(tm.vertices,real): tg.data[v.index].co=r
# --- Armature
arm=bpy.data.armatures.new('GhostRig'); ao=bpy.data.objects.new('GhostRig',arm); bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active=ao; bpy.ops.object.mode_set(mode='EDIT')
def bone(n,h,t,p=None):
    b=arm.edit_bones.new(n); b.head=h; b.tail=t
    if p: b.parent=arm.edit_bones[p]; b.use_connect=True
bone('root',(0,0,0),(0,0,0.9)); bone('spine',(0,0,0.9),(0,0,1.32),'root'); bone('neck',(0,0,1.32),(0,0,1.40),'spine'); bone('head',(0,0,1.40),(0,0,1.62),'neck')
bpy.ops.object.mode_set(mode='OBJECT')
for n in ('root','spine','neck','head'): o.vertex_groups.new(name=n)
for v in me.vertices:
    z=v.co.z
    if z<1.26: w=(1,0,0)
    elif z<1.32: t=(z-1.26)/0.06; w=(1-t,t,0)   # spine->neck
    elif z<1.40: t=(z-1.32)/0.08; w=(0,1-t,t)
    else: w=(0,0,1)
    names=('spine','neck','head')
    if z<1.26: o.vertex_groups['spine'].add([v.index],1.0,'REPLACE')
    else:
        for nm,wt in zip(names,w[:3] if z>=1.32 else (w[0],w[1],0)):
            pass
for v in me.vertices:
    z=v.co.z
    if z<1.26: g={'spine':1}
    elif z<1.32: t=(z-1.26)/0.06; g={'spine':1-t,'neck':t}
    elif z<1.40: t=(z-1.32)/0.08; g={'neck':1-t,'head':t}
    else: g={'head':1}
    for k,wt in g.items():
        if wt>0: o.vertex_groups[k].add([v.index],wt,'REPLACE')
to.parent=ao
vg=to.vertex_groups.new(name='head'); vg.add(list(range(len(tm.vertices))),1.0,'REPLACE')
tmod=to.modifiers.new('Armature','ARMATURE'); tmod.object=ao
o.parent=ao; mod=o.modifiers.new('Armature','ARMATURE'); mod.object=ao
# --- Tilt action
bpy.context.view_layer.objects.active=ao; bpy.ops.object.mode_set(mode='POSE')
pb=ao.pose.bones; 
for f,(r,s) in ((1,(0,0)),(30,(0,0)),(90,(math.radians(90),1)),(150,(math.radians(90),1))):
    pb['head'].rotation_mode='XYZ'; pb['neck'].rotation_mode='XYZ'
    pb['head'].rotation_euler=(math.radians(8)*s,r*0.55,0); pb['neck'].rotation_euler=(0,r*0.35,0); pb['spine'].rotation_euler=(0,r*0.10,0)
    pb['spine'].keyframe_insert('rotation_euler',frame=f); pb['head'].keyframe_insert('rotation_euler',frame=f); pb['neck'].keyframe_insert('rotation_euler',frame=f)
    sk.value=s; sk.keyframe_insert('value',frame=f); gk.value=s; gk.keyframe_insert('value',frame=f); tg.value=s; tg.keyframe_insert('value',frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
ao.animation_data.action.name='Ghost_HeadTilt'
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end=150
bpy.ops.wm.save_as_mainfile(filepath="gout/ghost_rig.blend")
# renders
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=32; sc.render.resolution_x=700; sc.render.resolution_y=900
w=bpy.data.worlds.new('w'); sc.world=w; w.color=(0.25,0.25,0.28)
l=bpy.data.lights.new('l','SUN'); l.energy=4; lo=bpy.data.objects.new('l',l); sc.collection.objects.link(lo); lo.rotation_euler=(0.8,0.2,0.6)
cam=bpy.data.cameras.new('c'); co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
def shot(n,fr,loc,tgt,lens):
    sc.frame_set(fr); cam.lens=lens; co.location=loc; co.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"//gout/r_{n}.png"; bpy.ops.render.render(write_still=True)


shot('c',90,(0,-3.2,0.9),(0,0,0.9),50)
for ob in bpy.data.objects:
    pass

