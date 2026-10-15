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
line=np.exp(-(dz/0.0006)**2)*mx
lipc=np.array([172,48,58],np.float32)
rows=(Hh-1-vs_)   # PIL rows from top
sub=arr[rows[:,None],us[None,:]]
mixed=sub*(1-M_[...,None])+((sub*0.35+lipc*0.65))*M_[...,None]
mixed=mixed*(1-0.55*line[...,None])+np.array([55,12,18],np.float32)*(0.55*line[...,None])
hl=np.exp(-((dz+0.0050)/0.0018)**2)*mx*0.25
mixed=mixed+(255-mixed)*hl[...,None]*0.35
arr[rows[:,None],us[None,:]]=mixed
PI.fromarray(arr.clip(0,255).astype(np.uint8)).save('gout/Ghost_albedo.png')
for m in me.materials:
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and nd.image.name=='texture_pbr_20250901.png':
            nd.image=bpy.data.images.load('gout/Ghost_albedo.png',check_existing=True)
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
n0=len(bm.verts)
# --- 1. cut hole
fe=[e for e in bm.edges if all(abs(v.co.x)<0.06 and (cz-0.050)<v.co.z<(cz+0.024) and abs(v.co.y-ly)<0.045 for v in e.verts) and any(f.normal.y<-0.1 for f in e.link_faces)]
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
teeth_meta=[]
def rbox(x,y,zc,w,d,h,ang,taper=0.0,tipsign=-1,gum=False):
    before=set(bm.verts)
    r=bmesh.ops.create_cube(bm,size=1.0,matrix=M.Translation((x,y,zc))@M.Rotation(ang,4,'Z')@M.Diagonal((w,d,h,1)))
    vs=r['verts']; es=list({e for v in vs for e in v.link_edges})
    bmesh.ops.bevel(bm,geom=vs+es,offset=min(0.0009,w*0.18),segments=2,affect='EDGES')
    new=set(bm.verts)-before
    if taper>0:
        for v in new:
            fr=(v.co.z-zc)/(h/2)*tipsign
            if fr>0:
                v.co.x=x+(v.co.x-x)*(1-taper*fr); v.co.y=y+(v.co.y-y)*(1-0.5*taper*fr)
    if not gum: teeth_meta.append((new,zc,h,tipsign,random.uniform(0.93,1.0)))
    return new
UP=[(0.0062,0.0118,0.0),(0.0048,0.0098,0.0),(0.0050,0.0110,0.35),(0.0046,0.0088,0.0),(0.0044,0.0082,0.0)]
LO=[(0.72,0.0070,0.0),(0.78,0.0074,0.0),(0.92,0.0092,0.30),(0.95,0.0080,0.0),(0.95,0.0074,0.0)]
xs=[];acc=0.0
for (w,h,t) in UP:
    xs.append(acc+w/2); acc+=w
xl=[];acc=0.0
for (w,h,t),(fw,_,_) in zip(UP,LO):
    xl.append(acc+w*fw/2); acc+=w*fw
for side in (-1,1):
    for k,(w,h,t) in enumerate(UP):
        x=side*xs[k]; slope=2*0.013*x/0.022**2; ang=math.atan(slope)*0.8+math.radians(random.uniform(-3,3))
        y=ly+0.006+0.013*(x/0.022)**2
        upper+=rbox(x,y,cz+0.0030+(h-0.0100)/2*0.9,w*1.05,0.0035,h,ang,taper=t,tipsign=-1)
        fw,fh,ft=LO[k]
        lower+=rbox(side*xl[k],y+0.0030,cz-0.0090-(0.0080-fh)/2,w*fw*1.06,0.0030,fh,ang,taper=ft,tipsign=1)
gum_up=[];gum_lo=[]
for side in (-1,1):
    for k,(w,h,t) in enumerate(UP):
        x=side*xs[k]; slope=2*0.013*x/0.022**2; ang=math.atan(slope)*0.8
        y=ly+0.006+0.013*(x/0.022)**2
        gum_up+=rbox(x,y+0.0030,cz+0.0082,w*1.04,0.0030,0.0090,ang,gum=True)
        gum_lo+=rbox(x*0.98,y+0.0085,cz-0.0112,w*0.88,0.0030,0.0055,ang,gum=True)
uv=bmesh.ops.create_uvsphere(bm,u_segments=10,v_segments=6,radius=1.0,matrix=M.Translation((0,ly+0.032,cz+0.0045))@M.Diagonal((0.0022,0.0022,0.0050,1)))
uvula=uv['verts']
tg=bmesh.ops.create_uvsphere(bm,u_segments=12,v_segments=8,radius=1.0,matrix=M.Translation((0,ly+0.020,cz-0.0112))@M.Diagonal((0.0135,0.016,0.0040,1)))
tongue=tg['verts']
# material per added geometry
for v in list(upper)+list(lower):
    for f in v.link_faces: f.material_index=2
for v in tongue:
    for f in v.link_faces: f.material_index=3
for v in list(gum_up)+list(gum_lo):
    for f in v.link_faces: f.material_index=4
for v in uvula:
    for f in v.link_faces: f.material_index=3
bmesh.ops.triangulate(bm,faces=bm.faces[:])
bm.verts.index_update()
TM=[({v.index for v in st},zc,h,ts,tint) for st,zc,h,ts,tint in teeth_meta]
ID=dict(ring={v.index for v in ring0 if v.is_valid},cav={v.index for v in new_verts},up={v.index for v in upper}|{v.index for v in gum_up}|{v.index for v in uvula},lo={v.index for v in lower}|{v.index for v in gum_lo},tg={v.index for v in tongue})
bm.to_mesh(me); bm.free()
mats=me.materials
for nm,col,rough in (('MouthInside',(0.05,0.008,0.012,1),0.4),('Teeth',(0.80,0.77,0.70,1),0.15),('Tongue',(0.66,0.27,0.29,1),0.4),('Gum',(0.62,0.22,0.25,1),0.35)):
    m=bpy.data.materials.new(nm); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=col; b.inputs['Roughness'].default_value=rough; mats.append(m)
    if nm in ('MouthInside','Teeth'):
        vc=m.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name='Col'; m.node_tree.links.new(vc.outputs['Color'],b.inputs['Base Color'])
print({k:len(v) for k,v in ID.items()},len(me.vertices))
ca=me.color_attributes.new('Col','FLOAT_COLOR','POINT')
cols=[(1,1,1,1)]*len(me.vertices)
cols=list(cols)
def lerpc(a,b,t): return tuple(a[i]+(b[i]-a[i])*t for i in range(3))+(1,)
for idxs,zc,h,ts,tint in TM:
    for i in idxs:
        z=me.vertices[i].co.z
        rootness=((z-(zc-h/2))/h) if ts==-1 else 1-((z-(zc-h/2))/h)
        rootness=max(0,min(1,rootness))
        c=lerpc((0.94,0.92,0.85),(0.80,0.66,0.46),rootness**1.6)
        base=0.96 if ts==-1 else 0.92
        cols[i]=tuple(min(1,x*tint*base) for x in c[:3])+(1,)
for i in ID['cav']:
    d=me.vertices[i].co.y-ly
    t=max(0,min(1,d/0.050))**1.3
    cols[i]=lerpc((0.70,0.20,0.22),(0.08,0.015,0.020),t)
for i,c in enumerate(cols): ca.data[i].color=c
V=me.vertices
# --- sculpt-like smoothing (Smooth brush) + gentle inflate on cheeks
adj=[[] for _ in V]
for e in me.edges:
    a,b=e.vertices; adj[a].append(b); adj[b].append(a)
newids_=ID['cav']|ID['up']|ID['lo']|ID['tg']
def ssf(t): t=max(0,min(1,t)); return t*t*(3-2*t)
reg={}
for v in V:
    i=v.index; c=v.co
    if i in newids_ or i in ID['ring']: continue
    if abs(c.x)<0.075 and abs(c.z-(cz-0.012))<0.060 and c.y>ly-0.010 and c.y<ly+0.06:
        r=math.hypot(c.x/0.075,(c.z-(cz-0.012))/0.060)
        reg[i]=1-ssf((r-0.55)/0.45)
for it in range(8):
    newp={}
    for i,w in reg.items():
        nb=[V[j].co for j in adj[i]]
        if not nb: continue
        avg=sum(nb,Vector((0,0,0)))/len(nb)
        newp[i]=V[i].co.lerp(avg,0.55*w)
    for i,p in newp.items(): V[i].co=p
for i,w in reg.items():   # inflate cheeks outward a little
    c=V[i].co
    ch=math.exp(-((abs(c.x)-0.040)**2+((c.z-cz-0.008))**2)/(2*0.020**2))
    V[i].co=c+Vector((0,-0.0012*ch*w,0))
openco={v.index:v.co.copy() for v in V}
newids0=ID['cav']|ID['up']|ID['lo']|ID['tg']
for v in V:
    i=v.index
    if i in newids0: continue
    c=openco[i]
    if abs(c.x)<0.06 and abs(c.z-cz)<0.03 and abs(c.y-ly)<0.03:
        w=math.exp(-((c.x/0.032)**2+((c.z-cz)/0.012)**2)*0.9)
        c=c+Vector((0,-0.0020*w,0)); openco[i]=c; v.co=c
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
        g2=math.exp(-(((c.x-s*0.042)**2)+((c.z-cz-0.012)**2))/(2*0.022**2))
        d+=Vector((s*0.0025*g2,-0.0028*g2,0.0065*g2))
    return d
front=lambda c: abs(c.x)<0.09 and abs(c.z-cz)<0.065 and c.y<ly+0.045 and c.y>ly-0.010
sm={}
for v in V:
    base=closed.get(v.index,openco[v.index])
    if front(openco[v.index]) and True:
        sm[v.index]=smile_delta(openco[v.index])
# basis = closed
for i,c in closed.items(): V[i].co=c
o.shape_key_add(name='Basis')
k1=o.shape_key_add(name='JawOpen'); 
# JawOpen = lower jaw rotates about hinge near the ear; upper lip/teeth stay still
HING=Vector((0,-0.010,1.44)); TH=math.radians(10)
def rot(p,w):
    t=TH*w; y=p.y-HING.y; z=p.z-HING.z
    return Vector((p.x,HING.y+y*math.cos(t)-z*math.sin(t),HING.z+y*math.sin(t)+z*math.cos(t)))
for v in V:
    i=v.index; base=v.co.copy()      # basis (closed) coordinates
    if i in ID['up']:
        k1.data[i].co=grin_teeth[i]; continue
    if i in ID['lo']:
        k1.data[i].co=rot(openco[i]+Vector((0,0,0.0075)),1.0); continue
    if i in ID['tg']:
        k1.data[i].co=rot(openco[i]+Vector((0,0.001,0.0075)),0.6); continue
    if i in mouthset:
        oz=openco[i].z
        w=ssf((cz-oz)/0.003)
        p=rot(base,w)
        if oz>cz: p.z+=0.0020*ssf((oz-cz)/0.003)    # upper lip lifts a little
        k1.data[i].co=p; continue
    c=base
    if i<len(lum) and c.y>ly-0.015 and c.y<ly+0.075 and abs(c.x)<0.085 and c.z<cz-0.0015:
        w=ssf((cz-0.0015-c.z)/0.010)*(1-ssf((abs(c.x)-0.030)/0.050))*ssf((c.z-1.325)/0.050)
        k1.data[i].co=rot(c,w)
    else:
        k1.data[i].co=c
jaw_skin=[v.index for v in V if v.index not in mouthset and v.index not in ID['up'] and v.index not in ID['lo'] and v.index not in ID['tg'] and v.index not in ID['cav'] and (k1.data[v.index].co-v.co).length>0.0006]
for it in range(10):
    newc={}
    for i in jaw_skin:
        nb=[k1.data[j].co for j in adj[i]]
        if not nb: continue
        avg=sum(nb,Vector((0,0,0)))/len(nb)
        newc[i]=k1.data[i].co.lerp(avg,0.5)
    for i,c in newc.items(): k1.data[i].co=c
print('jaw_skin',len(jaw_skin))
k2=o.shape_key_add(name='Smile')
for i,c in sm.items(): k2.data[i].co=closed.get(i,openco[i])+c
k3=o.shape_key_add(name='Grin')
for i,c in openco.items(): k3.data[i].co=(grin_teeth[i] if i in grin_teeth else closed.get(i,c).lerp(c,0.46))+sm.get(i,Vector((0,0,0)))
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
