# build_scene_zombie_v2.py — Zombie Apocalypse v2 "DARAH TERAKHIR" (vinyl-toy).
# v2 deltas (DESIGN-v2.md): gelap + rim merah + kabut 0.02, horde Z5-Z8, Boss 1.7x,
# set klinik/lab (CX=-80) + gerbang kota (GX=80), api purge, vial + cincin gigitan.
# Scene prosedural dari primitif, tanpa .blend / aset impor. Pola: build_scene_fast.py (Rubik).
# Dua set film-set (jalan kota di x~0, interior toko di x~40), 9 karakter vinyl-toy
# dengan rig empty (dibuat di animate_zombie.py), lampu malam, kamera.
# Setting render B7 via env FS_*: samples 8, raytracing OFF, volumetrics tile 16,
# DOF ON, motion blur ON, subsurf 1, bevel 0. Engine-agnostic (Principled + lampu
# fisik) — animate_zombie.py boleh switch ke Cycles + CUDA via --engine cycles.
# Run:
#   blender -b --factory-startup -P build_scene_zombie_v2.py -- <out.png> [--res 540 960]
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUT = args[0] if args else "//zombie_preview.png"
RES_X, RES_Y = (540, 960)
if "--res" in args:
    i = args.index("--res")
    RES_X, RES_Y = int(args[i + 1]), int(args[i + 2])

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- render setup B7 (Eevee default; animate boleh override ke Cycles) ----------
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"


def _set(obj, attr, value):
    if hasattr(obj, attr):
        setattr(obj, attr, value)


_set(scene.eevee, "use_raytracing", os.environ.get("FS_RAY", "0") == "1")
_set(scene.eevee, "use_shadows", True)
_set(scene.eevee, "volumetric_tile_size", os.environ.get("FS_VOLTILE", "16"))  # v2: tile 32 TIDAK valid (enum Eevee 4.5 maks 16)
_set(scene.eevee, "volumetric_end", 60.0)
scene.eevee.taa_render_samples = int(os.environ.get("FS_SAMPLES", "6"))  # v2: 8->6 (S4 lokal 47 dtk/frame > batas 40; ukur ulang)
scene.render.use_motion_blur = os.environ.get("FS_MB", "1") == "1"
_set(scene.render, "motion_blur_shutter", 0.5)

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.055, 0.059, 0.067, 1.0)  # langit malam #0E0F11
bg.inputs["Strength"].default_value = 0.45  # v2: malam jauh lebih gelap


# ---------- materials ----------
def mat(name, rgb, rough=0.45, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def emissive(name, rgb, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Color"].default_value = (*rgb, 1.0)
    b.inputs["Emission Strength"].default_value = strength
    return m


HEAD_WHITE = mat("HeadWhite", (0.913, 0.906, 0.874), 0.42)   # SHADOW #E9E7DF
HEAD_DULL = mat("HeadDull", (0.725, 0.725, 0.690), 0.55)     # zombie #B9B9B0
HOODIE = mat("Hoodie", (0.098, 0.102, 0.106), 0.6)           # #191A1B
HOODIE2 = mat("Hoodie2", (0.16, 0.16, 0.18), 0.6)            # pejalan kaki variasi
HOODIE3 = mat("Hoodie3", (0.30, 0.24, 0.16), 0.6)            # pejalan kaki variasi 2
BAG = mat("Bag", (0.22, 0.22, 0.25), 0.65)
PANTS = mat("Pants", (0.12, 0.12, 0.13), 0.6)
SHOE = mat("Shoe", (0.07, 0.07, 0.08), 0.5)
EYE_BLACK = mat("EyeBlack", (0.02, 0.02, 0.03), 0.2)
EYE_RED = emissive("EyeRed", (1.0, 0.0, 0.0), 1.2)         # mata zombie — iterasi 2: strength 1.2 (3.0 masih salmon; AgX jaga saturasi hanya di luminansi rendah)
EYE_RED_BOSS = emissive("EyeRedBoss", (1.0, 0.0, 0.0), 0.9)  # v2: AgX — merah hanya di luminansi rendah
MOUTH = mat("Mouth", (0.10, 0.02, 0.03), 0.3)
TEETH = mat("Teeth", (0.85, 0.85, 0.78), 0.4)
GROUND = mat("Ground", (0.090, 0.094, 0.102), 0.9)           # lantai #17181A
WALL = mat("Wall", (0.141, 0.149, 0.165), 0.85)               # dinding #24262A
BUILDING = mat("Building", (0.11, 0.12, 0.14), 0.9)
BUILDING2 = mat("Building2", (0.13, 0.11, 0.11), 0.9)
WIN_WARM = emissive("WinWarm", (1.0, 0.72, 0.38), 1.6)
WIN_DARK = mat("WinDark", (0.05, 0.06, 0.09), 0.4)
LAMP_GLOW = emissive("LampGlow", (1.0, 0.85, 0.55), 6.0)
SIREN_GLOW = emissive("SirenGlow", (0.827, 0.282, 0.235), 6.0)  # bahaya #D2483C
POLE = mat("Pole", (0.15, 0.15, 0.16), 0.5, metal=0.6)
CAR_RED = mat("CarRed", (0.45, 0.08, 0.06), 0.35, metal=0.4)
CAR_GLASS = mat("CarGlass", (0.05, 0.07, 0.10), 0.1, metal=0.8)
TIRE = mat("Tire", (0.03, 0.03, 0.03), 0.9)
PAPER = mat("Paper", (0.92, 0.90, 0.84), 0.7)
INK = mat("Ink", (0.05, 0.05, 0.08), 0.5)
PIPE_M = mat("Pipe", (0.6, 0.62, 0.65), 0.35, metal=0.9)
WOOD = mat("Wood", (0.35, 0.22, 0.12), 0.7)
ITEM1 = mat("Item1", (0.75, 0.25, 0.15), 0.5)
ITEM2 = mat("Item2", (0.15, 0.45, 0.65), 0.5)
ITEM3 = mat("Item3", (0.75, 0.65, 0.20), 0.5)
GLASS_M = mat("GlassDoor", (0.7, 0.8, 0.85), 0.05)
GLASS_M.blend_method = "BLEND"
GLASS_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.22
FLASH_CONE_M = mat("FlashCone", (0.91, 0.78, 0.39), 0.6)
FLASH_CONE_M.blend_method = "BLEND"
_fcb = FLASH_CONE_M.node_tree.nodes["Principled BSDF"]
_fcb.inputs["Alpha"].default_value = 0.05
_fcb.inputs["Emission Color"].default_value = (0.91, 0.78, 0.39, 1.0)
_fcb.inputs["Emission Strength"].default_value = 0.15
SMOKE_M = mat("Smoke", (0.62, 0.62, 0.64), 1.0)
SMOKE_M.blend_method = "BLEND"
SMOKE_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.05
RADIO_M = mat("Radio", (0.20, 0.16, 0.12), 0.6)
MONITOR_M = emissive("MonitorGlow", (0.10, 0.55, 0.30), 0.9)  # v2: layar monitor klinik (1.4 terlalu flat-putih)
VIAL_LIQ_M = emissive("VialLiquid", (0.85, 0.05, 0.08), 0.7)  # v2: cairan darah di vial (emissive lemah)
VIAL_GLASS_M = mat("VialGlass", (0.7, 0.8, 0.85), 0.05)  # v2: tabung vial transparan
VIAL_GLASS_M.blend_method = "BLEND"
VIAL_GLASS_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.3
BITE_M = emissive("BiteRing", (0.9, 0.08, 0.05), 0.35)  # v2: cincin bekas gigitan (0.5 terlalu tebal-terang)
FIRE_M = emissive("FireGlow", (1.0, 0.42, 0.08), 3.0)  # v2: glow api purge oranye
GATE_M = emissive("GateLight", (1.0, 1.0, 0.95), 2.5)  # v2: celah cahaya putih gerbang (4.0 blown-out)
SMOKE2_M = mat("SmokeFire", (0.25, 0.22, 0.20), 1.0)  # v2: kolom asap api purge
SMOKE2_M.blend_method = "BLEND"
SMOKE2_M.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.28
SOLDIER_M = mat("Soldier", (0.10, 0.11, 0.10), 0.7)  # v2: tentara siluet gelap
HELMET_M = mat("Helmet", (0.13, 0.14, 0.12), 0.5, metal=0.4)


def smooth(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.shade_smooth()
    o.select_set(False)


def block(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def ball(name, loc, size, m):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=32, ring_count=16)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    smooth(o)
    return o


def cylinder(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc, rotation=rot, vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def cone(name, loc, radius, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    smooth(o)
    return o


def plane(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return o


def text_obj(name, body, loc, size, m, rot=(math.radians(90), 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.name = name
    t.data.body = body
    t.data.extrude = 0.015
    t.data.size = size
    t.data.align_x = "CENTER"
    t.data.resolution_u = 16
    try:
        t.data.font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    except Exception:
        pass
    t.data.materials.append(m)
    return t


# ---------- SET 1: jalan kota (pusat x~0, jalan sepanjang sumbu X) ----------
block("ST_Ground", (0, 0, -0.1), (36, 18, 0.2), GROUND)
block("ST_Sidewalk", (0, 5.6, 0.03), (36, 3.0, 0.06), WALL)
# fasad gedung belakang (y=+7.5) + jendela emissive
_buildings = [(-13, 5.5, 5), (-7, 7.0, 6), (-1, 6.0, 5), (5, 8.0, 6), (11, 6.0, 5), (16, 7.5, 6)]
for i, (bx, bw, bh) in enumerate(_buildings):
    block(f"ST_Bldg{i}", (bx, 7.5, bh / 2), (bw, 3.0, bh), BUILDING if i % 2 == 0 else BUILDING2)
    for wy in range(2):
        for wx in range(int(bw) - 1):
            warm = ((i + wx + wy) % 3) != 0
            plane(f"ST_Win{i}_{wx}_{wy}", (bx - bw / 2 + 0.9 + wx * 1.1, 5.98, 1.6 + wy * 2.0),
                  (0.55, 0.8), WIN_WARM if warm else WIN_DARK, rot=(math.radians(90), 0, 0))
# gedung samping (menutup ujung jalan)
block("ST_BldgL", (-17.5, 0, 3.0), (3.0, 16, 6.0), BUILDING2)
block("ST_BldgR", (17.5, 0, 3.0), (3.0, 16, 6.0), BUILDING)

# tiang lampu jalan (x=-9,-3,3,9 ; y=+4.8)
for i, lx in enumerate((-9, -3, 3, 9)):
    cylinder(f"ST_LampPole{i}", (lx, 4.8, 1.6), 0.07, 3.2, POLE)
    ball(f"ST_LampHead{i}", (lx, 4.55, 3.25), (0.16, 0.16, 0.12), LAMP_GLOW)

# sirene merah di atas tiang dekat gedung (x=8, y=5.5)
cylinder("ST_SirenPole", (8, 5.5, 2.2), 0.06, 1.6, POLE)
ball("ST_SirenBulb", (8, 5.5, 3.1), (0.18, 0.18, 0.18), SIREN_GLOW)

# mobil tabrak tiang (dekat lampu x=-3), berasap di S4
block("ST_CarBody", (-2.6, 2.6, 0.45), (2.6, 1.3, 0.55), CAR_RED, rot=(0, 0, math.radians(22)))
block("ST_CarCabin", (-2.6, 2.6, 0.95), (1.4, 1.15, 0.5), CAR_GLASS, rot=(0, 0, math.radians(22)))
for _wx, _wy in ((-3.6, 2.0), (-1.6, 2.0), (-3.6, 3.2), (-1.6, 3.2)):
    cylinder(f"ST_CarWheel{_wx}_{_wy}", (_wx, _wy, 0.22), 0.24, 0.18, TIRE, rot=(math.radians(90), 0, 0))
for i in range(3):
    _sm = ball(f"ST_Smoke{i}", (-2.6 + i * 0.35, 2.6, 1.2 + i * 0.35), (0.28 + i * 0.12,) * 3, SMOKE_M)
    _sm.scale = (_sm.scale.x, _sm.scale.y, _sm.scale.z * 0.32)

# radio toko di etalase (x=2, y=6.2) + meja etalase
block("ST_Stall", (2, 6.2, 0.5), (2.2, 0.8, 1.0), WOOD)
block("ST_Radio", (2, 6.2, 1.15), (0.55, 0.3, 0.3), RADIO_M)
cylinder("ST_RadioAnt", (2.2, 6.2, 1.45), 0.015, 0.5, POLE, rot=(0, math.radians(25), 0))
# v2: api purge di cakrawala (S1 + S8) — glow oranye + kolom asap
plane("ST_FireGlow", (-13, 7.4, 2.2), (7.0, 3.2), FIRE_M, rot=(math.radians(90), 0, 0))
plane("ST_FireGlow2", (12, 7.4, 1.8), (5.0, 2.6), FIRE_M, rot=(math.radians(90), 0, 0))
for _i in range(3):
    _fs = ball(f"ST_FireSmoke{_i}", (-13 + _i * 1.2, 7.2, 3.5 + _i * 1.1), (0.9, 0.9, 1.4), SMOKE2_M)
    _fs.scale = (_fs.scale.x, _fs.scale.y, _fs.scale.z * 0.6)

# ---------- SET 1b (v2): klinik/lab gelap (S2, offset CX=-80) ----------
CX = -80.0
block("CL_Floor", (CX, 0, -0.1), (14, 10, 0.2), GROUND)
block("CL_WallBack", (CX, 4.8, 1.8), (14, 0.3, 3.6), WALL)
block("CL_WallL", (CX - 6.85, 0, 1.8), (0.3, 10, 3.6), WALL)
block("CL_WallR", (CX + 6.85, 0, 1.8), (0.3, 10, 3.6), WALL)
block("CL_WallFront", (CX, -4.8, 1.8), (14, 0.3, 3.6), WALL)
# meja lab + monitor menyala + tabung reaksi + vial
block("CL_Desk", (CX + 1.5, 2.5, 0.8), (3.4, 1.2, 0.08), WOOD)
for _lx in ((-1.5, -0.5), (1.5, -0.5), (-1.5, 0.5), (1.5, 0.5)):
    block(f"CL_DeskLeg{_lx[0]}_{_lx[1]}", (CX + 1.5 + _lx[0], 2.5 + _lx[1], 0.4), (0.1, 0.1, 0.8), POLE)
plane("CL_Monitor", (CX + 1.5, 2.9, 1.35), (1.5, 0.95), MONITOR_M, rot=(math.radians(90), 0, 0))
block("CL_MonitorStand", (CX + 1.5, 2.9, 0.95), (0.15, 0.15, 0.25), POLE)
text_obj("CL_MonitorText", "V-13", (CX + 1.5, 2.88, 1.35), 0.34, INK, rot=(math.radians(90), 0, 0))
for _i, _tx in enumerate((CX + 0.2, CX + 0.7, CX + 3.2)):
    cylinder(f"CL_Tube{_i}", (_tx, 2.2, 0.95), 0.06, 0.32, ITEM2 if _i != 2 else ITEM1)
    ball(f"CL_TubeLiq{_i}", (_tx, 2.2, 0.88), (0.05, 0.05, 0.05), VIAL_LIQ_M)
block("CL_VialBox", (CX + 3.4, 2.6, 0.9), (0.5, 0.4, 0.18), ITEM3)
# rak lab di dinding belakang
block("CL_Shelf", (CX - 4.0, 4.5, 1.6), (3.0, 0.5, 0.08), WOOD)
for _k, _im in enumerate((ITEM1, ITEM2, ITEM3)):
    cylinder(f"CL_ShelfTube{_k}", (CX - 5.0 + _k * 1.0, 4.5, 1.8), 0.08, 0.35, _im)

# ---------- SET 1c (v2): gerbang kota (S8, offset GX=80) ----------
GX = 80.0
block("GT_Ground", (GX, 0, -0.1), (16, 14, 0.2), GROUND)
block("GT_WallL", (GX - 6.5, 3.0, 2.5), (1.0, 8, 5.0), WALL)
block("GT_WallR", (GX + 6.5, 3.0, 2.5), (1.0, 8, 5.0), WALL)
block("GT_WallTop", (GX, 3.0, 4.6), (14, 1.0, 1.0), WALL)
# pintu gerbang besar (terbuka sebagian) + celah cahaya putih di tengah
block("GT_DoorL", (GX - 3.4, 3.0, 2.0), (3.2, 0.4, 4.0), POLE, rot=(0, 0, math.radians(28)))
block("GT_DoorR", (GX + 3.4, 3.0, 2.0), (3.2, 0.4, 4.0), POLE, rot=(0, 0, math.radians(-28)))
plane("GT_GapLight", (GX, 3.4, 2.0), (1.8, 4.0), GATE_M, rot=(math.radians(90), 0, 0))  # v2: selebar celah pintu
# api purge di kejauhan gerbang
plane("GT_FireGlow", (GX - 9, 6.5, 2.0), (6.0, 3.0), FIRE_M, rot=(math.radians(90), 0, 0))
# v2: 2 tentara siluet bersenjata, backlit, mengarahkan laras ke arah Shadow (ke -Y)
for _si, _sx in enumerate((-1.0, 1.0)):  # v2: tentara di tepi celah (siluet backlit, masuk frame 9:16)
    _tx = GX + _sx
    block(f"GT_Soldier{_si}_Body", (_tx, 1.2, 0.9), (0.6, 0.45, 1.1), SOLDIER_M)
    ball(f"GT_Soldier{_si}_Head", (_tx, 1.2, 1.65), (0.26, 0.24, 0.26), SOLDIER_M)
    ball(f"GT_Soldier{_si}_Helmet", (_tx, 1.2, 1.82), (0.30, 0.28, 0.18), HELMET_M)
    for _ls, _lx in (("L", -1), ("R", 1)):
        block(f"GT_Soldier{_si}_Leg{_ls}", (_tx + 0.16 * _lx, 1.2, 0.35), (0.18, 0.2, 0.7), SOLDIER_M)
    # lengan + laras senjata mengarah ke -Y (ke arah Shadow / kamera)
    block(f"GT_Soldier{_si}_Arm", (_tx, 0.85, 1.15), (0.5, 0.16, 0.16), SOLDIER_M)
    cylinder(f"GT_Soldier{_si}_Gun", (_tx, 0.25, 1.15), 0.05, 1.1, POLE, rot=(math.radians(90), 0, 0))

# ---------- SET 2: interior toko gelap (offset OX=40) ----------
OX = 40.0
block("SHOP_Floor", (OX, 0, -0.1), (14, 10, 0.2), GROUND)
block("SHOP_WallBack", (OX, 4.8, 1.8), (14, 0.3, 3.6), WALL)
block("SHOP_WallL", (OX - 6.85, 0, 1.8), (0.3, 10, 3.6), WALL)
block("SHOP_WallR", (OX + 6.85, 0, 1.8), (0.3, 10, 3.6), WALL)
# dinding depan: dua segmen + header di atas pintu kaca (pintu di x=OX, lebar 3.6)
block("SHOP_WallFrontL", (OX - 4.6, -4.8, 1.8), (4.8, 0.3, 3.6), WALL)
block("SHOP_WallFrontR", (OX + 4.6, -4.8, 1.8), (4.8, 0.3, 3.6), WALL)
block("SHOP_WallFrontTop", (OX, -4.8, 3.1), (3.6, 0.3, 1.0), WALL)
# pintu kaca + bingkai
plane("SHOP_GlassDoor", (OX, -4.8, 1.3), (3.4, 2.6), GLASS_M, rot=(math.radians(90), 0, 0))
block("SHOP_DoorFrameL", (OX - 1.8, -4.8, 1.3), (0.15, 0.15, 2.6), POLE)
block("SHOP_DoorFrameR", (OX + 1.8, -4.8, 1.3), (0.15, 0.15, 2.6), POLE)
block("SHOP_DoorFrameTop", (OX, -4.8, 2.62), (3.75, 0.15, 0.15), POLE)
# tangan zombie di luar pintu kaca (digedor berirama di S5) — rig di animate
for i, hx in enumerate((OX - 0.7, OX + 0.6)):
    block(f"SHOP_DoorHand{i}", (hx, -5.05, 1.15), (0.2, 0.55, 0.2), HEAD_DULL)
    ball(f"SHOP_DoorPalm{i}", (hx, -5.05, 1.45), (0.14, 0.14, 0.14), HEAD_DULL)
# rak toko: rak1 di barat SHADOW (SHADOW jongkok di samping rak), rak2 di dekat dinding belakang
for _rx, _ry in ((OX - 5.8, 0.8), (OX + 2.5, 3.6)):
    block(f"SHOP_Rack{_rx}_{_ry}", (_rx, _ry, 1.1), (3.0, 0.8, 2.2), WOOD)
    for _k, _im in enumerate((ITEM1, ITEM2, ITEM3)):
        block(f"SHOP_Item{_rx}_{_ry}_{_k}", (_rx - 1.0 + _k * 1.0, _ry, 2.35), (0.5, 0.5, 0.3), _im)
# meja ilmuwan (S6): kertas + tabung reaksi pecah + teks V-13
block("SHOP_Desk", (OX + 3.5, 2.5, 0.8), (2.4, 1.1, 0.08), WOOD)
for _lx in ((-1.0, -0.4), (1.0, -0.4), (-1.0, 0.4), (1.0, 0.4)):
    block(f"SHOP_DeskLeg{_lx[0]}_{_lx[1]}", (OX + 3.5 + _lx[0], 2.5 + _lx[1], 0.4), (0.1, 0.1, 0.8), POLE)
plane("SHOP_Paper1", (OX + 3.3, 2.5, 0.86), (0.7, 0.9), PAPER, rot=(0, 0, math.radians(8)))
plane("SHOP_Paper2", (OX + 4.0, 2.7, 0.86), (0.6, 0.8), PAPER, rot=(0, 0, math.radians(-12)))
text_obj("SHOP_V13Text", "V-13", (OX + 3.3, 2.5, 0.88), 0.30, INK, rot=(0, 0, math.radians(8)))
for _i, _tx in enumerate((OX + 3.0, OX + 3.9, OX + 4.3)):
    cylinder(f"SHOP_Tube{_i}", (_tx, 2.1, 0.95), 0.06, 0.3, ITEM2 if _i != 2 else ITEM1)
cylinder("SHOP_TubeBroken", (OX + 3.6, 2.9, 0.90), 0.06, 0.3, ITEM2, rot=(math.radians(90), 0, math.radians(40)))
# panel pintu yang dijebol (S7): tersembunyi s.d. S7, muncul saat Boss datang lalu jatuh
block("SHOP_DoorPanel", (OX, -4.7, 1.3), (1.8, 0.12, 2.6), WOOD).hide_render = True

# ---------- haze tipis (volume density 0.008) ----------
def haze(name, loc, scale):
    m = bpy.data.materials.new(name + "M")
    m.use_nodes = True
    nt = m.node_tree.nodes
    nt.remove(nt["Principled BSDF"])
    vol = nt.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.02  # v2: kabut tebal
    vol.inputs["Color"].default_value = (0.85, 0.88, 0.95, 1.0)
    m.node_tree.links.new(vol.outputs["Volume"], nt["Material Output"].inputs["Volume"])
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    h = bpy.context.object
    h.name = name
    h.scale = scale
    h.data.materials.append(m)
    return h


if os.environ.get("FS_VOL", "1") == "1":
    haze("ST_Haze", (0, 0, 2.0), (18, 9, 4))
    haze("SHOP_Haze", (OX, 0, 1.8), (7, 5, 2))
    haze("CL_Haze", (CX, 0, 1.8), (7, 5, 2))
    haze("GT_Haze", (GX, 0, 2.0), (8, 7, 3))
# ---------- karakter vinyl-toy ----------
# Kepala ~40% tinggi (SHADOW 1.8 unit), tiap bagian objek terpisah.
# Karakter menghadap -Y (ke arah kamera default). Rig empty dibuat di animate.
CHARS = {}


def make_character(prefix, kind, scale, base, hoodie_mat):
    """kind: shadow | zombie | boss | ped. base=(x,y,z). Return dict info rig."""
    s = scale
    bx, by, bz = base
    hip_z = 0.48 * s
    sho_z = 1.12 * s
    sho_x = 0.38 * s * (1.38 if kind == "boss" else 1.0)  # v2: bahu Boss lebih lebar
    head_z = 1.45 * s
    head_r = 0.275 * s * (1.12 if kind == "boss" else 1.0)
    head_mat = HEAD_DULL if kind in ("zombie", "boss") else HEAD_WHITE
    # VIC = pria biasa yang BERUBAH jadi zombie; SH = mata merah di twist S8:
    # keduanya butuh mata merah yang bisa dinyalakan via eye_red
    _red = kind in ("zombie", "boss") or prefix in ("VIC", "SH")
    eye_mat = EYE_RED_BOSS if kind == "boss" else (EYE_RED if _red else EYE_BLACK)
    eye_r = (0.07 * s if kind == "boss" else 0.075 * s) if _red else 0.055 * s  # v2: ~ukuran absolut v1

    def P(x, y, z):
        return (bx + x, by + y, bz + z)

    body, head, armL, armR, legL, legR = [], [], [], [], [], []
    # kaki (pivot di pinggul, di-rig di animate)
    for side, sx in (("L", -1), ("R", 1)):
        legL.append(block(f"{prefix}_Leg{side}", P(0.14 * sx * s, 0, 0.24 * s),
                          (0.17 * s, 0.2 * s, 0.42 * s), PANTS)) if side == "L" else None
        legR.append(block(f"{prefix}_Leg{side}", P(0.14 * sx * s, 0, 0.24 * s),
                          (0.17 * s, 0.2 * s, 0.42 * s), PANTS)) if side == "R" else None
        sh = block(f"{prefix}_Shoe{side}", P(0.14 * sx * s, -0.04 * s, 0.07 * s),
                   (0.2 * s, 0.3 * s, 0.12 * s), SHOE)
        (legL if side == "L" else legR).append(sh)
    # torso hoodie + kantong + tas punggung
    body.append(block(f"{prefix}_Torso", P(0, 0, 0.78 * s), (0.62 * s, 0.5 * s, 0.6 * s), hoodie_mat))
    body.append(block(f"{prefix}_Pocket", P(0, -0.26 * s, 0.68 * s), (0.3 * s, 0.04 * s, 0.2 * s), BAG))
    if kind in ("shadow", "ped"):
        body.append(block(f"{prefix}_Bag", P(0, 0.32 * s, 0.95 * s), (0.42 * s, 0.2 * s, 0.5 * s), BAG))
        body.append(block(f"{prefix}_BagFlap", P(0, 0.42 * s, 1.12 * s), (0.44 * s, 0.06 * s, 0.16 * s), HOODIE))
    if kind == "boss":
        for side, sx in (("L", -1), ("R", 1)):
            body.append(block(f"{prefix}_Pad{side}", P(0.52 * sx * s, 0, 1.15 * s),
                              (0.42 * s, 0.36 * s, 0.22 * s), HEAD_DULL))  # v2: pad bahu lebih besar
    # lengan (pivot di bahu)
    for side, sx in (("L", -1), ("R", 1)):
        lst = armL if side == "L" else armR
        lst.append(block(f"{prefix}_Arm{side}", P(sho_x * sx, 0, sho_z - 0.28 * s),
                         (0.16 * s, 0.18 * s, 0.5 * s), hoodie_mat))
        lst.append(ball(f"{prefix}_Hand{side}", P(sho_x * sx, 0, sho_z - 0.56 * s),
                        (0.09 * s,) * 3, head_mat))
    # kepala + hood + wajah
    head.append(ball(f"{prefix}_Head", P(0, 0, head_z), (head_r, head_r * 0.92, head_r), head_mat))
    head.append(ball(f"{prefix}_Hood", P(0, 0.07 * s, head_z + 0.05 * s),
                     (head_r * 1.12, head_r * 1.05, head_r * 1.05), hoodie_mat))
    eyes_black, eyes_red = [], []
    for side, sx in (("L", -1), ("R", 1)):
        eyes_black.append(ball(f"{prefix}_EyeB{side}", P(0.11 * sx * s, -0.235 * s, head_z + 0.03 * s),
                               (0.055 * s, 0.03 * s, 0.07 * s), EYE_BLACK))
        eyes_red.append(ball(f"{prefix}_EyeR{side}", P(0.11 * sx * s, -0.24 * s, head_z + 0.03 * s),
                             (eye_r, 0.032 * s, eye_r * 1.25), eye_mat))
    head.extend(eyes_black)
    head.extend(eyes_red)
    mouth = block(f"{prefix}_Mouth", P(0, -0.25 * s, head_z - 0.13 * s),
                  (0.12 * s, 0.03 * s, 0.03 * s), MOUTH)
    head.append(mouth)
    if kind in ("zombie", "boss"):
        # mulut bergerigi: kotak mulut lebih besar + gigi kecil
        mouth.scale = (0.17 * s, 0.03 * s, 0.06 * s)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        for k in range(4):
            head.append(block(f"{prefix}_Tooth{k}", P(-0.06 * s + k * 0.04 * s, -0.26 * s, head_z - 0.10 * s),
                              (0.028 * s, 0.02 * s, 0.03 * s), TEETH))
    else:
        for side, sx in (("L", -1), ("R", 1)):
            head.append(block(f"{prefix}_Brow{side}", P(0.11 * sx * s, -0.25 * s, head_z + 0.13 * s),
                              (0.12 * s, 0.03 * s, 0.03 * s), EYE_BLACK, rot=(0, 0, math.radians(-10 * sx))))
    # senter di tangan kanan SHADOW (silinder + Spot + cone) — ikut ArmRigR
    flash_parts = []
    if kind == "shadow":
        hand = Vector(P(sho_x, -0.05 * s, sho_z - 0.56 * s))
        fl = cylinder(f"{prefix}_Flash", hand, 0.05 * s, 0.22 * s, POLE, rot=(math.radians(90), 0, 0))
        flash_parts.append(fl)
        bpy.ops.object.light_add(type="SPOT", location=hand)
        spot = bpy.context.object
        spot.name = f"{prefix}_FlashSpot"
        spot.data.energy = 0.0
        spot.data.spot_size = math.radians(38)  # v2: cone senter lebih sempit
        spot.data.spot_blend = 0.5
        spot.data.color = (0.91, 0.78, 0.39)  # senter #E8C763
        spot.data.use_shadow = True  # satu-satunya spot berbayang (bayangan senter di toko)
        spot.rotation_euler = (Vector((hand.x, hand.y - 3, hand.z)) - Vector(hand)).to_track_quat("-Z", "Y").to_euler()
        flash_parts.append(spot)
        cone_obj = cone(f"{prefix}_FlashCone", (hand.x, hand.y - 0.65, hand.z), 0.35, 1.3,
                        FLASH_CONE_M, rot=(math.radians(-90), 0, 0))
        flash_parts.append(cone_obj)
        armR.extend(flash_parts)
    info = {
        "base": Vector(base), "scale": s, "kind": kind,
        "hip_z": hip_z, "sho_z": sho_z, "sho_x": sho_x, "head_z": head_z,
        "head_pivot_z": 1.18 * s,
        "body": body, "head": head, "armL": armL, "armR": armR,
        "legL": legL, "legR": legR,
        "eyes_black": eyes_black, "eyes_red": eyes_red, "mouth": mouth,
        "flash_parts": flash_parts,
    }
    CHARS[prefix] = info
    return info


make_character("SH", "shadow", 1.0, (0, 0, 0), HOODIE)
make_character("Z1", "zombie", 1.0, (-2.5, 2.0, 0), HOODIE2)
make_character("Z2", "zombie", 1.0, (1.5, 2.5, 0), HOODIE3)
make_character("Z3", "zombie", 1.0, (4.0, 1.5, 0), HOODIE2)
make_character("Z4", "zombie", 1.0, (-5.0, 3.0, 0), HOODIE3)
make_character("Z5", "zombie", 1.0, (3.0, 3.5, 0), HOODIE2)  # v2: horde padat
make_character("Z6", "zombie", 1.0, (-4.0, 1.0, 0), HOODIE3)
make_character("Z7", "zombie", 1.0, (6.0, 2.5, 0), HOODIE2)
make_character("Z8", "zombie", 1.0, (-1.0, 4.0, 0), HOODIE3)
make_character("BOSS", "boss", 1.7, (OX, -6.5, 0), HOODIE)  # v2: Boss 1.45x -> 1.7x
make_character("P1", "ped", 1.0, (-6, -1, 0), HOODIE2)
make_character("P2", "ped", 1.0, (5, -1.5, 0), HOODIE3)
make_character("VIC", "ped", 1.0, (0, 1.0, 0), HOODIE3)

# pipa besi (S7) — v2 TIDAK dipakai (props pipe hide=True di semua frame)
pipe = cylinder("Pipe", (0, 0, -5), 0.045, 1.1, PIPE_M, rot=(0, 0, math.radians(90)))
pipe.hide_render = True
# v2: vial darah di tangan KIRI Shadow (ikut ArmRigL di animate; plan: vial S2/S5/S6)
vial_tube = cylinder("VialTube", (-0.38, -0.05, 0.56), 0.05, 0.22, VIAL_GLASS_M)  # v2: tegak, transparan
vial_tube.hide_render = True
vial_liq = cylinder("VialLiquid", (-0.38, -0.05, 0.56), 0.035, 0.16, VIAL_LIQ_M)
vial_liq.hide_render = True
# v2: cincin bekas gigitan di pergelangan KANAN Shadow (ikut ArmRigR di animate)
bpy.ops.mesh.primitive_torus_add(major_radius=0.085, minor_radius=0.012, location=(0.38, -0.05, 0.62),
                                 rotation=(0, 0, 0))  # v2: cincin melingkari pergelangan vertikal
bite_ring = bpy.context.object
bite_ring.name = "BiteRing"
bite_ring.data.materials.append(BITE_M)
bite_ring.hide_render = True

# ---------- lampu ----------
def point_light(name, loc, color, energy, shadow=False):
    bpy.ops.object.light_add(type="POINT", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.shadow_soft_size = 0.5
    o.data.use_shadow = shadow
    return o


def area_light(name, loc, color, energy, size, rot, shadow=False):
    bpy.ops.object.light_add(type="AREA", location=loc)
    o = bpy.context.object
    o.name = name
    o.data.color = color
    o.data.energy = energy
    o.data.size = size
    o.data.use_shadow = shadow
    o.rotation_euler = rot
    return o


# sirene merah (jalan) — berdenyut via plan
point_light("SirenLight", (8, 5.0, 3.1), (0.83, 0.16, 0.11), 0.0)
# lampu jalan berkedip (S1) di tiang x=-3
point_light("LampFlicker", (-3, 4.4, 3.1), (1.0, 0.85, 0.55), 300.0)
# lampu jalan lain (hangat, statis)
point_light("LampWarm1", (3, 4.4, 3.1), (1.0, 0.85, 0.55), 120.0)  # v2: lebih redup
point_light("LampWarm2", (-9, 4.4, 3.1), (1.0, 0.85, 0.55), 90.0)  # v2: lebih redup
# senja hangat S2 + bulan dingin
area_light("DuskLight", (0, -8, 8), (1.0, 0.62, 0.35), 60.0, 16, (math.radians(35), 0, 0))
area_light("MoonLight", (0, 6, 10), (0.55, 0.68, 1.0), 260.0, 18, (math.radians(140), 0, 0), shadow=True)  # v2: bulan lebih redup
# interior toko
point_light("ShopLight", (OX, 0, 3.0), (1.0, 0.85, 0.6), 0.0)
# fill dingin dari sisi kamera — v2 DIKURANGI: area gelap benar-benar gelap
area_light("CameraFill", (0, -10, 6), (0.62, 0.72, 1.0), 170.0, 14, (math.radians(55), 0, 0))
area_light("ShopFill", (OX, -8, 5), (0.62, 0.72, 1.0), 110.0, 10, (math.radians(55), 0, 0))
area_light("ClinicFill", (CX, -8, 5), (0.62, 0.72, 1.0), 90.0, 10, (math.radians(55), 0, 0))
area_light("GateFill", (GX, -8, 5), (0.7, 0.75, 1.0), 100.0, 10, (math.radians(55), 0, 0))
# v2: rim light MERAH di belakang karakter utama (S1/S4/S7) — tepi tubuh menyala merah
point_light("RimRedStreet", (0, 5.5, 2.4), (1.0, 0.08, 0.05), 420.0)
point_light("RimRedShop", (OX, 4.5, 2.4), (1.0, 0.08, 0.05), 320.0)
# v2: api purge (oranye lemah) + lampu klinik + cahaya gerbang
point_light("FireLight", (-13, 6.5, 2.5), (1.0, 0.45, 0.08), 180.0)
point_light("ClinicLight", (CX, 0, 3.0), (0.55, 0.85, 0.65), 0.0)
area_light("GateLight", (GX, 3.0, 2.5), (1.0, 1.0, 0.95), 0.0, 8, (math.radians(90), 0, 0))
# flash putih 2 frame saat pukulan S7
area_light("FlashWhite", (OX, -2, 2.5), (1.0, 1.0, 1.0), 0.0, 10, (math.radians(60), 0, 0))
# denyut merah samar bekas gigitan di pergelangan SHADOW (S8) — ikut ArmRigL di animate
bpy.ops.object.light_add(type="POINT", location=(-0.38, -0.1, 0.6))
bite = bpy.context.object
bite.name = "BiteLight"
bite.data.color = (1.0, 0.1, 0.05)
bite.data.energy = 0.0

# ---------- quality pass B7: subsurf 1 di semua bagian karakter, bevel 0 ----------
SUB = int(os.environ.get("FS_SUB", "1"))
for _info in CHARS.values():
    for _part in (_info["body"] + _info["head"] + _info["armL"] + _info["armR"]
                  + _info["legL"] + _info["legR"]):
        if _part.type == "MESH" and SUB > 0:
            _s = _part.modifiers.new("Subdiv", "SUBSURF")
            _s.levels = 0
            _s.render_levels = SUB
# vinyl: clear-coat ringan di kepala + hoodie
for _m, _coat in ((HEAD_WHITE, 0.5), (HEAD_DULL, 0.4), (HOODIE, 0.3), (BAG, 0.2)):
    _b = _m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in _b.inputs:
        _b.inputs["Coat Weight"].default_value = _coat
        _b.inputs["Coat Roughness"].default_value = 0.15

# ---------- kamera default (plan yang menggerakkan per frame) ----------
bpy.ops.object.camera_add(location=(0, -6.5, 1.7))
cam = bpy.context.object
cam.data.lens = 40
look = Vector((0, 0, 1.3)) - cam.location
cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
cam.data.dof.use_dof = os.environ.get("FS_DOF", "1") == "1"
cam.data.dof.focus_distance = 6.5
cam.data.dof.aperture_fstop = 2.0
scene.camera = cam

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
