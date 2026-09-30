"""
NTTのディジタル公衆電話（緑）を作る部品。make_phonebooth.py から呼ばれる。
単独で見たいとき：Blenderで make_phone_only.py を実行

座標（電話機の中）：X=右、Y=奥（壁側が +Y、プレイヤー側が -Y）、Z=上。原点は「壁に付く面の下の中央」。
実物の写真を見本にしている：ななめの操作パネル・オレンジの液晶・丸いテンキー・硬貨口・カード口・SOS・下の扉（鍵穴と返却口）・
左側に掛かる丸みのある受話器と銀の金属コード。
"""
import bpy, bmesh, math, os, json
from mathutils import Vector

# ---- 大きさ（メートル） ----
W = .245          # 幅
D = .19           # 奥行き
H = .41           # 高さ
DOOR_TOP = .135   # 下の扉の高さ
PW, PH = .215, .245   # 操作パネルの大きさ（絵は 1290×1470px）
PXW, PXH = 1290., 1470.


class Builder:
    def __init__(self, tex_dir, loc):
        self.tex = tex_dir
        self.loc = Vector(loc)
        self.objs = []
        with open(os.path.join(tex_dir, 'panel_layout.json')) as f:
            self.lay = json.load(f)
        self._mats()
        # 斜面の向き（Y,Z 平面）
        p2 = Vector((0, -D, DOOR_TOP)); p3 = Vector((0, -(D - .05), H - .01))
        self.s = (p3 - p2).normalized()                       # 斜面に沿って上へ
        self.n = Vector((0, -self.s.z, self.s.y)).normalized()  # 外向きの法線（前・やや上）
        if self.n.y > 0: self.n = -self.n
        self.slope_len = (p3 - p2).length
        self.origin = p2 + self.s * ((self.slope_len - PH) / 2)  # パネル左下（x は別）

    # ---------- 画像・材質 ----------
    def img(self, fname, srgb=True):
        path = os.path.join(self.tex, fname)
        im = bpy.data.images.load(path, check_existing=True)
        im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
        im.pack()
        return im

    def mat(self, name, color=(.5, .5, .5), metallic=0., rough=.5, color_img=None, rough_img=None, normal_img=None, emis_img=None, emis_s=1., coat=0., normal_s=1.):
        m = bpy.data.materials.new(name); m.use_nodes = True
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metallic; b.inputs['Roughness'].default_value = rough
        def tex(im, target, node_out='Color'):
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = im
            nt.links.new(t.outputs[node_out], target); return t
        if color_img: tex(color_img, b.inputs['Base Color'])
        if rough_img: tex(rough_img, b.inputs['Roughness'])
        if normal_img:
            nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = normal_s
            tex(normal_img, nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
        if emis_img:
            tex(emis_img, b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emis_s
        if coat:
            for k in ('Coat Weight', 'Clearcoat'):
                if k in b.inputs: b.inputs[k].default_value = coat; break
            for k in ('Coat Roughness', 'Clearcoat Roughness'):
                if k in b.inputs: b.inputs[k].default_value = .08; break
        return m

    def _mats(self):
        self.M_GREEN = self.mat('PhoneGreen', color_img=self.img('phone_body_albedo.png'), rough_img=self.img('phone_body_rough.png', False), coat=.6)
        self.M_PANEL = self.mat('PhonePanel', color_img=self.img('phone_panel_albedo.png'), normal_img=self.img('phone_panel_normal.png', False), rough=.5, normal_s=1.2)
        self.M_LCD = self.mat('LCD', color=(.2, .1, .02), rough=.15, emis_img=self.img('phone_lcd.png'), emis_s=.9)
        self.M_KEYS = self.mat('PhoneKeys', color_img=self.img('phone_keys_atlas.png'), rough=.3)
        self.M_CHROME = self.mat('PhoneMetal', (.72, .73, .7), metallic=1., rough=.28)
        self.M_STEEL = self.mat('CordSteel', (.6, .6, .6), metallic=1., rough=.35)
        self.M_BLACK = self.mat('PhoneBlack', (.012, .012, .012), rough=.4)
        self.M_DARKGREY = self.mat('PhoneDarkGrey', (.06, .07, .065), rough=.5)

    # ---------- パネル座標 → 3D ----------
    def pp(self, u, v, h=0.):
        """パネル上の位置（u:左0〜右1, v:下0〜上1, h:浮かせる高さ）を電話機の座標にする"""
        p = self.origin + self.s * (v * PH) + self.n * h
        return Vector((-PW / 2 + u * PW, p.y, p.z))
    def px(self, x, y, h=0.):       # 絵のピクセル位置(左上原点)から
        return self.pp(x / PXW, 1 - y / PXH, h)

    # ---------- 道具 ----------
    def _finish(self, o, name, mat, smooth=True):
        o.name = name
        if mat: o.data.materials.append(mat)
        o.location = o.location + self.loc
        self.objs.append(o); return o

    def box(self, name, size, center, mat, bevel=.0015, rot=(0, 0, 0)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=rot)
        o = bpy.context.active_object; o.scale = size
        bpy.ops.object.transform_apply(scale=True)
        if bevel:
            m = o.modifiers.new('bv', 'BEVEL'); m.width = min(bevel, min(size) * .45); m.segments = 2
            bpy.ops.object.modifier_apply(modifier='bv')
        return self._finish(o, name, mat)

    def cyl(self, name, r, depth, center, mat, rot=(0, 0, 0), verts=28, bevel=0.):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=center, rotation=rot)
        o = bpy.context.active_object
        if bevel:
            m = o.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = 2
            bpy.ops.object.modifier_apply(modifier='bv')
        bpy.ops.object.shade_smooth()
        return self._finish(o, name, mat)

    def tilt(self):
        """パネルの斜面に合わせた回転（円柱・箱の軸Zを法線に合わせる）"""
        return (math.atan2(-self.n.y, self.n.z), 0, 0)

    # ---------- 本体 ----------
    def body(self):
        prof = [(0, 0), (D, 0), (D, DOOR_TOP), (D - .05, H - .01), (D - .066, H), (.03, H), (0, H - .03)]     # (奥行き, 高さ)
        bm = bmesh.new()
        vs = [bm.verts.new((-W / 2, -d, z)) for d, z in prof]
        f = bm.faces.new(vs)
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        vv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(W, 0, 0), verts=vv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new('body'); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new('Phone_Body', me); bpy.context.collection.objects.link(o)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        bv = o.modifiers.new('bv', 'BEVEL'); bv.width = .014; bv.segments = 5; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(30)
        bpy.ops.object.modifier_apply(modifier='bv')
        bpy.ops.object.shade_smooth()
        # UV
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.02); bpy.ops.object.mode_set(mode='OBJECT')
        me.materials.append(self.M_GREEN)
        o.location = o.location + self.loc; self.objs.append(o)

    # ---------- 操作パネル ----------
    def panel(self):
        c0 = self.pp(0, 0, .0006); c1 = self.pp(1, 0, .0006); c2 = self.pp(1, 1, .0006); c3 = self.pp(0, 1, .0006)
        me = bpy.data.meshes.new('panel'); me.from_pydata([c0, c1, c2, c3], [], [(0, 1, 2, 3)])
        me.uv_layers.new(name='UVMap')
        uvl = me.uv_layers.active.data
        for li, uv in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]): uvl[li].uv = uv
        me.update()
        o = bpy.data.objects.new('Phone_Panel', me); bpy.context.collection.objects.link(o)
        me.materials.append(self.M_PANEL); o.location = o.location + self.loc; self.objs.append(o)
        # 液晶
        l = self.lay['lcd']
        (ux0, uy0, ux1, uy1) = l
        a = self.px(ux0, uy0, .0018); b = self.px(ux1, uy0, .0018); c = self.px(ux1, uy1, .0018); d = self.px(ux0, uy1, .0018)
        me = bpy.data.meshes.new('lcd'); me.from_pydata([d, c, b, a], [], [(0, 1, 2, 3)]); me.uv_layers.new(name='UVMap')
        for li, uv in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]): me.uv_layers.active.data[li].uv = uv
        o = bpy.data.objects.new('Phone_LCD', me); bpy.context.collection.objects.link(o)
        me.materials.append(self.M_LCD); o.location = o.location + self.loc; self.objs.append(o)
        # 液晶のふち（少し出っ張らせた黒い枠）
        cx, cy = (ux0 + ux1) / 2, (uy0 + uy1) / 2
        rims = [((ux1 - ux0 + 24), 12, cx, uy0 - 6), ((ux1 - ux0 + 24), 12, cx, uy1 + 6), (12, (uy1 - uy0), ux0 - 6, cy), (12, (uy1 - uy0), ux1 + 6, cy)]
        for (wpx, hpx, mx, my) in rims:
            self.box('lcd_rim', (wpx / PXW * PW, .003, hpx / PXH * PH), self.px(mx, my, .0013), self.M_DARKGREY, .0005, rot=self.tilt())

    # ---------- テンキー（12個の丸いボタン） ----------
    def keys(self):
        kx0, kdx, ky0, kdy, kr = self.lay['keys']
        R = kr / PXW * PW
        rot = self.tilt()
        for i in range(12):
            r, c = divmod(i, 3)
            p = self.px(kx0 + c * kdx, ky0 + r * kdy, .0035)
            bpy.ops.mesh.primitive_cylinder_add(radius=R, depth=.007, vertices=32, location=p, rotation=rot)
            o = bpy.context.active_object
            m = o.modifiers.new('bv', 'BEVEL'); m.width = .0012; m.segments = 2
            bpy.ops.object.modifier_apply(modifier='bv')
            bpy.ops.object.shade_smooth()
            # UV：上の面だけ数字の絵の該当マスへ、それ以外は黒いところへ
            bm = bmesh.new(); bm.from_mesh(o.data); uv = bm.loops.layers.uv.verify()
            u0, v0 = c / 3., 1 - (r + 1) / 4.
            for f in bm.faces:
                top = f.normal.z > .9
                for lp in f.loops:
                    if top:
                        x, y = lp.vert.co.x / (2 * R) + .5, lp.vert.co.y / (2 * R) + .5
                        lp[uv].uv = (u0 + x / 3. * .94 + .0025, v0 + y / 4. * .94 + .0025)
                    else:
                        lp[uv].uv = (u0 + .02, v0 + .02)
            bm.to_mesh(o.data); bm.free()
            self._finish(o, 'key%d' % i, self.M_KEYS)

    # ---------- 硬貨口・カード口・ボタン ----------
    def slots(self):
        rot = self.tilt()
        cx, cy, r = self.lay['coin']
        R = r / PXW * PW
        self.cyl('coin_ring', R * .93, .006, self.px(cx, cy, .003), self.M_CHROME, rot, 36, .0012)
        self.box('coin_slit', (.0035, .0015, .034), self.px(cx, cy, .0064), self.M_BLACK, .0004, rot)
        # カード口（金属の枠＋黒い差し込み口）
        x0, y0, x1, y1 = self.lay['plate']
        self.box('card_frame', ((x1 - x0) * .55 / PXW * PW, .004, .034), self.px((x0 + x1) / 2, (y0 + y1) / 2 - 20, .003), self.M_CHROME, .002, rot)
        self.box('card_slot', ((x1 - x0) * .45 / PXW * PW, .003, .009), self.px((x0 + x1) / 2, (y0 + y1) / 2 - 20, .0055), self.M_BLACK, .0006, rot)
        # 音量ボタン（黒い小さな四角）
        for bx in (430, 540):
            self.box('vol_btn', (.0105, .003, .0085), self.px(bx, 415, .002), self.M_BLACK, .001, rot)
        # 10円・100円の丸ボタン
        for (bx, by) in ((1198, 80), (1198, 200)):
            self.cyl('coin_btn', .0062, .004, self.px(bx, by, .002), self.M_CHROME, rot, 24, .0008)
        # SOSの3つのボタン
        for i in range(3):
            self.cyl('sos_btn', .0046, .003, self.px(1000 + i * 100, 1018, .0015), self.M_BLACK, rot, 20, .0006)

    # ---------- 下の扉（鍵穴と返却口） ----------
    def lower_door(self):
        zc = DOOR_TOP / 2
        self.box('door_gap', (W - .022, .002, DOOR_TOP - .02), (0, -D + .0008, zc), self.M_BLACK, .001)
        self.box('lower_door', (W - .03, .006, DOOR_TOP - .03), (0, -D - .0015, zc), self.M_GREEN, .003)
        self.cyl('keyhole_ring', .0058, .002, (-.04, -D - .0055, zc + .002), self.M_CHROME, (math.pi / 2, 0, 0), 20)
        self.cyl('keyhole', .0022, .0026, (-.04, -D - .0062, zc + .002), self.M_BLACK, (math.pi / 2, 0, 0), 12)
        self.box('return_frame', (.036, .003, .038), (.055, -D - .0055, zc + .006), self.M_DARKGREY, .0008)
        self.box('return_slot', (.028, .003, .03), (.055, -D - .0072, zc + .006), self.M_BLACK, .0005)

    # ---------- 受話器（丸みのある緑・左側に掛かる） ----------
    def handset(self):
        hx = -W / 2 - .036
        hy = -D + .048
        zc = .275
        # 握りの部分：ゆるい弧の曲線に丸い断面をつけて、横につぶす
        bpy.ops.curve.primitive_bezier_curve_add()
        cv = bpy.context.active_object
        sp = cv.data.splines[0]; sp.bezier_points.add(2)
        pts = [(0, 0, zc + .085), (0, .016, zc), (0, 0, zc - .085)]
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        cv.data.bevel_depth = .0145; cv.data.bevel_resolution = 6; cv.data.resolution_u = 20
        cv.data.use_fill_caps = True
        bpy.ops.object.convert(target='MESH')
        g = bpy.context.active_object
        g.scale = (1.5, 1.0, 1.0); bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.shade_smooth()
        g.location = (hx, hy, 0); self._finish_hand(g, 'h_grip')
        # 耳とくちの丸み
        for name, z in (('h_ear', zc + .105), ('h_mouth', zc - .105)):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=32, ring_count=20, location=(hx, hy - .008, z))
            s = bpy.context.active_object; s.scale = (.031, .026, .034); bpy.ops.object.transform_apply(scale=True)
            bpy.ops.object.shade_smooth(); self._finish_hand(s, name)
            # 黒い受話部の穴あきプレート（前を向く）
            bpy.ops.mesh.primitive_cylinder_add(radius=.019, depth=.003, vertices=28, location=(hx, hy - .029, z), rotation=(math.pi / 2, 0, 0))
            p = bpy.context.active_object; bpy.ops.object.shade_smooth(); p.data.materials.append(self.M_BLACK)
            p.location = p.location + self.loc; p.name = name + '_plate'; self.hand_parts.append(p)
        # 銀の留め具（本体の左側面とつなぐ）
        for z in (zc + .07, zc - .07):
            self.box_h('hook_clip', (.02, .022, .014), (-W / 2 - .008, hy + .012, z))
            self.cyl_h('hook_pin', .004, .026, (-W / 2 - .026, hy + .012, z), (0, math.pi / 2, 0))

    hand_parts = []
    def _finish_hand(self, o, name):
        o.name = name; o.data.materials.append(self.M_GREEN)
        o.location = o.location + self.loc; self.hand_parts.append(o)
    def box_h(self, name, size, center):
        bpy.ops.mesh.primitive_cube_add(size=1, location=center); o = bpy.context.active_object; o.scale = size
        bpy.ops.object.transform_apply(scale=True)
        m = o.modifiers.new('bv', 'BEVEL'); m.width = .002; m.segments = 2; bpy.ops.object.modifier_apply(modifier='bv')
        o.data.materials.append(self.M_CHROME); o.name = name; o.location = o.location + self.loc; self.hand_parts.append(o)
    def cyl_h(self, name, r, depth, center, rot):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=16, location=center, rotation=rot); o = bpy.context.active_object
        bpy.ops.object.shade_smooth(); o.data.materials.append(self.M_CHROME); o.name = name; o.location = o.location + self.loc; self.hand_parts.append(o)

    # ---------- 金属のコード ----------
    def cord(self):
        hx = -W / 2 - .036; hy = -D + .048
        bpy.ops.curve.primitive_bezier_curve_add()
        cv = bpy.context.active_object
        sp = cv.data.splines[0]
        pts = [(hx, hy, .275 - .135), (hx - .022, hy - .02, .19), (hx - .012, hy - .03, .10), (hx + .03, hy - .026, .03), (-W / 2 + .05, -D + .06, -.02)]
        sp.bezier_points.add(len(pts) - 2)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        cv.data.bevel_depth = .0045; cv.data.bevel_resolution = 6; cv.data.resolution_u = 32
        bpy.ops.object.convert(target='MESH')
        c = bpy.context.active_object; bpy.ops.object.shade_smooth()
        c.name = 'Phone_Cord'; c.data.materials.append(self.M_STEEL); c.location = c.location + self.loc; self.cord_obj = c

    # ---------- まとめ ----------
    def join(self, group, name, objs):
        for o in bpy.context.selected_objects: o.select_set(False)
        objs = [o for o in objs if o]
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.join()
        r = bpy.context.active_object; r.name = name; return r

    def build(self):
        self.hand_parts = []
        self.body(); self.panel(); self.keys(); self.slots(); self.lower_door(); self.handset(); self.cord()
        # 本体の緑パーツ・パネルまわり・受話器・コードに分けて名前をつける
        green = [o for o in self.objs if o.name.startswith(('Phone_Body', 'lower_door'))]
        panel_parts = [o for o in self.objs if o.name.startswith(('Phone_Panel',))]
        lcd = [o for o in self.objs if o.name.startswith('Phone_LCD')]
        import re
        keys = [o for o in self.objs if re.match(r'^key\d+', o.name)]
        metal_dark = [o for o in self.objs if o.name.startswith(('coin', 'card', 'vol', 'sos', 'keyhole', 'return', 'door_gap', 'lcd_rim'))]
        out = []
        for objs, nm in ((green, 'Phone_Body'), (panel_parts, 'Phone_Panel'), (lcd, 'Phone_LCD'), (keys, 'Phone_Keys'), (metal_dark, 'Phone_Details'), (self.hand_parts, 'Phone_Handset')):
            if objs: out.append(self.join(nm, nm, objs))
        out.append(self.cord_obj)
        return out


def build_phone(tex_dir, loc):
    return Builder(tex_dir, loc).build()
