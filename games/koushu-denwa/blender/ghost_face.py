import bpy, bmesh, math, random, numpy as np
from mathutils import Vector, Matrix as M
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath="gout/ghost.blend")
o=bpy.data.objects['Ghost']; me=o.data
cz=1.403
# --- lum per vertex (hair detection)
img=bpy.data.images['texture_pbr_20250901.png']; W,H=img.size; px=np.array(img.pixels[:]).reshape(H,W,4)
vuv={}; uvd=me.uv_layers.active.data
for l in me.loops: vuv[l.vertex_index]=uvd[l.index].uv[:]
lum_by_co={}
def lum_of(i):
    u,v=vuv[i]; c=px[min(H-1,int(v*H)),min(W-1,int(u*W))]; return float((c[0]+c[1]+c[2])/3)
lum=[lum_of(i) for i in range(len(me.vertices))]
bvh=BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get())
ly=bvh.ray_cast(Vector((0,-1,cz)),Vector((0,1,0)))[0].y; print('ly',ly)
# lip paint
from PIL import Image as PI
pts=[(v.co.x,v.co.z,*vuv[v.index]) for v in me.vertices if abs(v.co.x)<0.05 and abs(v.co.z-cz)<0.03 and abs(v.co.y-ly)<0.02 and lum[v.index]>0.12]
A=np.array([[1,p[0],p[1]] for p in pts]); cu=np.linalg.lstsq(A,np.array([p[2] for p in pts]),rcond=None)[0]; cv=np.linalg.lstsq(A,np.array([p[3] for p in pts]),rcond=None)[0]
print('uvfit pts',len(pts))
src=PI.open('gout/texture_pbr_20250901.png').convert('RGB'); arr=np.array(src).astype(np.float32)
Hh,Ww=arr.shape[:2]
J=np.array([[cu[1],cu[2]],[cv[1],cv[2]]]); Ji=np.linalg.inv(J)
u0=cu[0]; v0=cv[0]
us=np.arange(int(max(0,(cu[0]-0.06*abs(cu[1])-0.04)*Ww)),int(min(Ww,(cu[0]+0.06*abs(cu[1])+0.04)*Ww)))
vs_=np.arange(int(max(0,(cv[0]-0.05*abs(cv[2])-0.04)*Hh)),int(min(Hh,(cv[0]+0.05*abs(cv[2])+0.04)*Hh)))
uu,vv=np.meshgrid(us/Ww,vs_/Hh)   # v from bottom, rows from bottom
d=np.stack([uu-u0,vv-v0],-1)@Ji.T
X=d[...,0]; Z=d[...,1]
def ss(t): t=np.clip(t,0,1); return t*t*(3-2*t)
dz=Z; up=np.clip(dz/0.0085,0,2); lo=np.clip(-dz/0.0105,0,2)
band=np.where(dz>=0,1-ss((up-0.85)/0.4),1-ss((lo-0.85)/0.4))
band=np.where(np.abs(dz)<0.0004,1,band)
mx=1-ss((np.abs(X)-0.021)/0.011)
M_=(band*mx*0.85).astype(np.float32)
lipc=np.array([172,48,58],np.float32)
rows=(Hh-1-vs_)   # PIL rows from top
sub=arr[rows[:,None],us[None,:]]
mixed=sub*(1-M_[...,None])+((sub*0.35+lipc*0.65))*M_[...,None]
arr[rows[:,None],us[None,:]]=mixed
PI.fromarray(arr.clip(0,255).astype(np.uint8)).save('gout/Ghost_albedo.png')
for m in me.materials:
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and nd.image.name=='texture_pbr_20250901.png':
            nd.image=bpy.data.images.load('gout/Ghost_albedo.png',check_existing=True)
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
n0=len(bm.verts)
# --- 1. cut hole
fe=[e for e in bm.edges if all(abs(v.co.x)<0.05 and abs(v.co.z-cz)<0.024 and abs(v.co.y-ly)<0.03 for v in e.verts) and any(f.normal.y<-0.1 for f in e.link_faces)]
bmesh.ops.subdivide_edges(bm,edges=fe,cuts=2,use_grid_fill=True)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
sel=[f for f in bm.faces if (lambda c:(c.x/0.027)**2+((c.z-cz)/0.0095)**2<1 and abs(c.y-ly)<0.03 and f.normal.y<-0.15)(f.calc_center_median())]
print('hole faces',len(sel))
selset=set(sel)
bedges=[e for f in sel for e in f.edges if sum(1 for lf in e.link_faces if lf in selset)==1]
bedges=list(set(bedges))
ring0=set(v for e in bedges for v in e.verts)
bmesh.ops.delete(bm,geom=sel,context='FACES_ONLY')
bm.edges.ensure_lookup_table()
bedges=[e for e in bedges if e.is_valid]
print('boundary edges',len(bedges))
HX=0.027; HU=0.0075; HL=0.0135; PW=2.6
for v in ring0:
    if not v.is_valid: continue
    a=v.co.x/HX; hz=HU if v.co.z>=cz else HL; b=(v.co.z-cz)/hz
    sct=(abs(a)**PW+abs(b)**PW)**(-1/PW)
    v.co.x=a*sct*HX; v.co.z=cz+b*sct*hz
new_verts=set(); new_faces=[]
cur=bedges
steps=((0.006,0.97),(0.008,0.9),(0.010,0.75),(0.010,0.55),(0.008,0.35))
for dy,sc in steps:
    r=bmesh.ops.extrude_edge_only(bm,edges=cur)
    geom=r['geom']
    nv=[g for g in geom if isinstance(g,bmesh.types.BMVert)]
    ne=[g for g in geom if isinstance(g,bmesh.types.BMEdge)]
    nf=[g for g in geom if isinstance(g,bmesh.types.BMFace)]
    new_faces+=nf
    for v in nv:
        v.co.y+=dy; v.co.x*=sc; v.co.z=cz+(v.co.z-cz)*sc
        new_verts.add(v)
    cur=[e for e in ne if all(v in set(nv) for v in e.verts) and len(e.link_faces)==1]
fill=bmesh.ops.holes_fill(bm,edges=cur,sides=len(cur)+2)
new_faces+=fill['faces']
for f in new_faces:
    f.material_index=1
    c=f.calc_center_median()
    if abs(f.normal.y)>0.8:   # back wall: should face -y
        if f.normal.y>0: f.normal_flip()
    else:
        toward=Vector((-c.x,0,-(c.z-cz)))
        if f.normal.dot(toward)<0: f.normal_flip()
print('cavity verts',len(new_verts),'ring',len(ring0))
# --- 2. teeth + tongue
random.seed(7)
upper=[];lower=[];
def rbox(x,y,zc,w,d,h,ang):
    before=set(bm.verts)
    r=bmesh.ops.create_cube(bm,size=1.0,matrix=M.Translation((x,y,zc))@M.Rotation(ang,4,'Z')@M.Diagonal((w,d,h,1)))
    vs=r['verts']; es=list({e for v in vs for e in v.link_edges})
    bmesh.ops.bevel(bm,geom=vs+es,offset=0.0007,segments=2,affect='EDGES')
    return set(bm.verts)-before
W_=[0.0056,0.0044,0.0046,0.0042,0.0040]
xs=[];acc=0.0
for k,w in enumerate(W_):
    xs.append(acc+w/2); acc+=w
for side in (-1,1):
    for k,w in enumerate(W_):
        x=side*xs[k]; slope=2*0.013*x/0.022**2; ang=math.atan(slope)*0.8
        y=ly+0.006+0.013*(x/0.022)**2
        hh=0.0100*(1.12 if k==0 else 1.0)*(1.06 if k==2 else 1.0)
        upper+=rbox(x,y,cz+0.0030+(0.0 if k else -0.0003)-0.0000,w*0.99,0.0035,hh,ang)
        # lower row: smaller, tips up
        lower+=rbox(x*0.98,y+0.0018,cz-0.0090,w*0.80,0.0030,0.0085,ang)
tg=bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=1.0,matrix=M.Translation((0,ly+0.019,cz-0.0115))@M.Diagonal((0.012,0.014,0.0035,1)))
tongue=tg['verts']
# material per added geometry
for v in list(upper)+list(lower):
    for f in v.link_faces: f.material_index=2
for v in tongue:
    for f in v.link_faces: f.material_index=3
bmesh.ops.triangulate(bm,faces=bm.faces[:])
bm.verts.index_update()
ID=dict(ring={v.index for v in ring0 if v.is_valid},cav={v.index for v in new_verts},up={v.index for v in upper},lo={v.index for v in lower},tg={v.index for v in tongue})
bm.to_mesh(me); bm.free()
mats=me.materials
for nm,col,rough in (('MouthInside',(0.05,0.008,0.012,1),0.4),('Teeth',(0.80,0.77,0.70,1),0.25),('Tongue',(0.55,0.2,0.22,1),0.45)):
    m=bpy.data.materials.new(nm); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=col; b.inputs['Roughness'].default_value=rough; mats.append(m)
print({k:len(v) for k,v in ID.items()},len(me.vertices))
V=me.vertices
openco={v.index:v.co.copy() for v in V}
mouthset=ID['ring']|ID['cav']
closed={}
for i in mouthset:
    c=openco[i]; closed[i]=Vector((c.x,c.y,cz+(c.z-cz)*0.02))
grin_teeth={}
for i in ID['lo']|ID['tg']:
    c=openco[i]; closed[i]=Vector((c.x,c.y+0.008,c.z+0.0075)); grin_teeth[i]=Vector((c.x,c.y,c.z+0.0047))
for i in ID['up']:
    c=openco[i]; closed[i]=Vector((c.x,c.y+0.008,c.z+0.004)); grin_teeth[i]=c.copy()
# smile deltas
def smile_delta(c):
    d=Vector((0,0,0))
    for s in (-1,1):
        g=math.exp(-(((c.x-s*0.027)**2)+((c.z-cz)**2))/(2*0.012**2))
        d+=Vector((s*0.006*g,-0.001*g,0.0105*g))
    return d
front=lambda c: abs(c.x)<0.07 and abs(c.z-cz)<0.05 and c.y<ly+0.045 and c.y>ly-0.03
sm={}
for v in V:
    base=closed.get(v.index,openco[v.index])
    if front(openco[v.index]) and (v.index in mouthset or v.index<len(V)-0 and lum[v.index] >0.12 if v.index<len(lum) else True):
        sm[v.index]=smile_delta(openco[v.index])
# basis = closed
for i,c in closed.items(): V[i].co=c
o.shape_key_add(name='Basis')
k1=o.shape_key_add(name='JawOpen'); 
for i,c in openco.items(): k1.data[i].co=c
k2=o.shape_key_add(name='Smile')
for i,c in sm.items(): k2.data[i].co=closed.get(i,openco[i])+c
k3=o.shape_key_add(name='Grin')
for i,c in openco.items(): k3.data[i].co=(grin_teeth[i] if i in grin_teeth else closed.get(i,c).lerp(c,0.38))+sm.get(i,Vector((0,0,0)))
# --- armature
arm=bpy.data.armatures.new('GhostRig'); ao=bpy.data.objects.new('GhostRig',arm); bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active=ao; bpy.ops.object.mode_set(mode='EDIT')
def bone(n,h,t,p=None):
    b=arm.edit_bones.new(n); b.head=h; b.tail=t
    if p: b.parent=arm.edit_bones[p]; b.use_connect=True
bone('root',(0,0,0),(0,0,0.9)); bone('spine',(0,0,0.9),(0,0,1.32),'root'); bone('neck',(0,0,1.32),(0,0,1.40),'spine'); bone('head',(0,0,1.40),(0,0,1.62),'neck')
bpy.ops.object.mode_set(mode='OBJECT')
for n in ('root','spine','neck','head'): o.vertex_groups.new(name=n)
def sstep(t): t=max(0,min(1,t)); return t*t*(3-2*t)
newids=ID['cav']|ID['up']|ID['lo']|ID['tg']
for v in V:
    z=v.co.z; i=v.index
    if i in newids: g={'head':1}
    else:
        hair = i<len(lum) and lum[i]<0.12
        if z<1.26: g={'spine':1}
        elif z<1.32: t=(z-1.26)/0.06; g={'spine':1-t,'neck':t}
        elif z<1.40: t=(z-1.32)/0.08; g={'neck':1-t,'head':t}
        else: g={'head':1}
        if hair and z<1.32 and abs(v.co.x)<0.16:
            w=sstep((z-1.0)/0.32); g={'head':w,'spine':1-w}
    for k,wt in g.items():
        if wt>0: o.vertex_groups[k].add([i],wt,'REPLACE')
o.parent=ao; mod=o.modifiers.new('Armature','ARMATURE'); mod.object=ao
# --- animation
bpy.context.view_layer.objects.active=ao; bpy.ops.object.mode_set(mode='POSE')
pb=ao.pose.bones
for b in pb: b.rotation_mode='XYZ'
for f,(r,sv,gv,jv) in ((1,(0,0,0,0)),(30,(0,0,0,0)),(90,(math.radians(90),1,0,0)),(150,(math.radians(90),0,1,0)),(180,(math.radians(90),0,1,0))):
    s=1 if r else 0
    pb['head'].rotation_euler=(math.radians(8)*s,r*0.55,0); pb['neck'].rotation_euler=(0,r*0.35,0); pb['spine'].rotation_euler=(0,r*0.10,0)
    for b in ('spine','neck','head'): pb[b].keyframe_insert('rotation_euler',frame=f)
    k2.value=sv; k3.value=gv; k1.value=jv
    for k in (k1,k2,k3): k.keyframe_insert('value',frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
ao.animation_data.action.name='Ghost_HeadTilt'
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end=180
for v in V: pass
bpy.ops.wm.save_as_mainfile(filepath="gout/ghost_face.blend")
# --- export
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath="gout/Ghost_rigged.fbx",use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,path_mode='COPY',embed_textures=False,apply_unit_scale=True,use_mesh_modifiers=False)
# --- renders
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=48; sc.render.resolution_x=800; sc.render.resolution_y=500
w=bpy.data.worlds.new('w'); sc.world=w; w.color=(0.3,0.3,0.33)
l=bpy.data.lights.new('l','SUN'); l.energy=5; lo=bpy.data.objects.new('l',l); sc.collection.objects.link(lo); lo.rotation_euler=(1.0,0,0.2)
cam=bpy.data.cameras.new('c'); co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co; cam.lens=135
for ob in bpy.data.objects:
    if ob.animation_data: ob.animation_data_clear()
if o.data.shape_keys.animation_data: o.data.shape_keys.animation_data_clear()
for p in pb: p.rotation_euler=(0,0,0)
def shot(n,j,s,g,loc=(0,-1.2,1.39),tgt=(0,0,1.39)):
    k1.value=j;k2.value=s;k3.value=g; co.location=loc; co.rotation_euler=(Vector(tgt)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"//gout/f_{n}.png"; bpy.ops.render.render(write_still=True)
shot('0',0,0,0); shot('1',1,0,0); shot('2',0,1,0); shot('3',0,0,1)
shot('4',0,0,1,loc=(0.9,-0.9,1.45))
cam.lens=200; shot('5',0,0,1,loc=(0,-1.2,1.39))
