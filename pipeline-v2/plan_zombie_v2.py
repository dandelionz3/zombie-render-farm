#!/usr/bin/env python3
# plan_zombie_v2.py — generator plan.json film Zombie Apocalypse v2 "DARAH TERAKHIR".
# Satu baris per frame (f 0..1439). Per frame: rig tiap karakter, sudut lengan/kaki
# (walk/run cycle prosedural + shamble zombie), intensitas lampu, kamera, flag.
# Murni Python (tanpa bpy) — jalan di VM maupun di kernel Kaggle.
#   python3 plan_zombie.py [plan.json]
import json
import math
import os
import sys

N = 1440
OX = 40.0  # offset interior toko (sama dengan build_scene_zombie_v2.py)
CX = -80.0  # v2: offset klinik/lab
GX = 80.0  # v2: offset gerbang kota
IMPACT = 1258  # v2: frame virus terbakar di tubuh Boss (flash putih 2 frame: 1258-1259)
EYE_RED_START, EYE_RED_END = 1386, 1391  # mata SHADOW merah tepat 6 frame


def clamp(x, a, b):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def seg_t(f, a, b):
    """Progress 0..1 di dalam [a,b]."""
    return clamp((f - a) / max(1, b - a), 0.0, 1.0)


def shake(f, amp, freq=1.7):
    """Goyang deterministik (handheld) — tanpa random."""
    return amp * (math.sin(f * 0.9 * freq) * 0.6 + math.sin(f * 2.3 * freq + 1.3) * 0.4)


def walk_cycle(phase, amp, arm_amp=None):
    """Ayun kaki/lengan berlawanan + bob. phase dalam radian."""
    if arm_amp is None:
        arm_amp = amp * 0.8
    return {
        "legL": amp * math.sin(phase),
        "legR": -amp * math.sin(phase),
        "armL": -arm_amp * math.sin(phase),
        "armR": arm_amp * math.sin(phase),
        "bob": 0.045 * abs(math.cos(phase)),
    }


def char(x=0, y=0, z=0, rot=0, lean=0, squash=1.0, crouch=0.0, pitch=0.0,
         head_tilt=0, head_turn=0, armL=0, armR=0, legL=0, legR=0,
         eye_red=False, vis=True, mouthW=1.0, mouthH=1.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "rot": round(rot, 2),
            "lean": round(lean, 2), "squash": round(squash, 3), "crouch": round(crouch, 3),
            "pitch": round(pitch, 2), "head_tilt": round(head_tilt, 2),
            "head_turn": round(head_turn, 2), "armL": round(armL, 2), "armR": round(armR, 2),
            "legL": round(legL, 2), "legR": round(legR, 2),
            "eye_red": bool(eye_red), "vis": bool(vis),
            "mouthW": round(mouthW, 2), "mouthH": round(mouthH, 2)}


def hidden():
    return char(vis=False)


def cam(x, y, z, tx, ty, tz, focus, lens, roll=0.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
            "tx": round(tx, 3), "ty": round(ty, 3), "tz": round(tz, 3),
            "focus": round(focus, 2), "lens": round(lens, 1),
            "roll": round(roll, 2)}  # v2: Dutch angle (derajat, sekitar sumbu pandang)


def lights(siren=0, lamp=300, dusk=60, flash=0, shop=0, moon=400, spot=0, bite=0,
           clinic=0, gate=0):
    return {"siren": round(siren, 1), "lamp": round(lamp, 1), "dusk": round(dusk, 1),
            "flash": round(flash, 1), "shop": round(shop, 1), "moon": round(moon, 1),
            "spot": round(spot, 1), "bite": round(bite, 1),
            "clinic": round(clinic, 1), "gate": round(gate, 1)}  # v2: lampu klinik + gerbang


def zombie_shamble(x, y, f, phase0=0.0, rot=0, speed=0.35):
    """Zombie: kaki +-12 derajat lambat, lengan ke depan ~70 derajat, kepala miring."""
    ph = phase0 + f * 0.055 * speed
    return char(x, y, 0, rot=rot + 4 * math.sin(f * 0.05),
                lean=8, head_tilt=14 + 4 * math.sin(f * 0.07), head_turn=8 * math.sin(f * 0.04),
                armL=70 + 8 * math.sin(ph), armR=66 + 8 * math.sin(ph + 1.2),
                legL=12 * math.sin(ph), legR=-12 * math.sin(ph), eye_red=True)


def ped_walk(x, y, f, phase0, rot, amp=22):
    ph = phase0 + f * 0.11
    c = walk_cycle(ph, amp)
    return char(x, y, c["bob"], rot=rot, lean=4, head_tilt=0, head_turn=0,
                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])


rows = []
for f in range(N):
    chars = {}
    props = {"pipe": {"hide": True, "x": 0, "y": 0, "z": -5, "rx": 0, "rz": 0},
             "door_rot": 0.0, "door_y": -4.7, "door_z": 1.3, "door_hide": True,
             "smoke": False, "hands_z": 0.0, "flash_cone": False,
             "vial": False}  # v2: vial di tangan kiri SHADOW (S2/S5/S6)
    flash_white = False

    # ================= S1 HOOK v2 (0-71): horde 2-3x padat, Dutch 10d, api purge =================
    if f < 72:
        t = seg_t(f, 0, 71)
        sh_y = lerp(3.5, -2.0, t)
        ph = f * 0.55  # lari cepat
        c = walk_cycle(ph, 40)
        chars["SH"] = char(0, sh_y, c["bob"], rot=0, lean=12, head_tilt=-4,
                           armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])
        # v2: horde 8 zombie berlapis (depan-belakang-samping, rapat)
        for i, (zx, zo) in enumerate(((-1.6, 2.6), (0.4, 3.4), (1.8, 2.9), (-2.8, 3.8),
                                      (2.6, 4.2), (-0.8, 4.6), (3.4, 3.0), (-3.6, 2.4))):
            chars[f"Z{i + 1}"] = zombie_shamble(zx, sh_y + zo, f, phase0=i * 2.1, rot=0)
        chars["BOSS"] = hidden(); chars["P1"] = hidden(); chars["P2"] = hidden(); chars["VIC"] = hidden()
        # v2: Dutch angle 10d + punch-in tele (SHADOW + horde memenuhi frame)
        cx, cy, cz = 0, lerp(-5.2, -3.4, smooth(t)), lerp(1.5, 1.35, smooth(t))
        chars_cam = cam(cx + shake(f, 0.06), cy, cz + shake(f + 9, 0.03),
                        0, sh_y, 1.3, abs(cy - sh_y), lerp(100, 55, smooth(t)), roll=10)
        flick = 450 if (f // 5) % 2 == 0 else 40
        sir = 900 if (f // 4) % 2 == 0 else 60
        li = lights(siren=sir, lamp=flick, dusk=0, moon=260, spot=0)
    # ================= S2 v2 (72-215): klinik/lab gelap — monitor V-13 + vial =================
    elif f < 216:
        props["vial"] = True
        if f < 140:
            # SHADOW berjalan ke meja lab (dari barat, lalu hadap monitor di utara)
            t = seg_t(f, 72, 140)
            sh_x = lerp(CX - 5.0, CX + 2.2, smooth(t))
            ph = f * 0.16
            c = walk_cycle(ph, 25)
            chars["SH"] = char(sh_x, -1.0, c["bob"], rot=lerp(70, 180, smooth(seg_t(f, 120, 140))),
                               lean=5, armL=c["armL"], armR=c["armR"],
                               legL=c["legL"], legR=c["legR"])
            chars_cam = cam(lerp(CX - 4.0, CX + 2.2, smooth(t)), -5.2, 1.8,
                            sh_x, -1.0, 1.1, 5.5, lerp(52, 46, t))
        else:
            # di meja: berbalik 3/4 ke kamera (f140-165) — wajah terlihat, monitor di belakang bahu
            t = seg_t(f, 140, 215)
            turn = smooth(seg_t(f, 140, 165))
            chars["SH"] = char(CX + 2.2, 0.8, 0, rot=lerp(180, -40, turn), lean=6,
                               head_tilt=lerp(18, 0, smooth(t)), head_turn=lerp(0, 20, turn),
                               armL=lerp(20, 55, smooth(t)), armR=30, legL=0, legR=0)
            chars_cam = cam(lerp(CX - 1.0, CX + 0.6, smooth(t)), lerp(-4.4, -2.0, smooth(t)),
                            lerp(1.7, 1.55, smooth(t)),
                            CX + 2.2, 0.8, 1.45, lerp(5.5, 3.0, smooth(t)), lerp(46, 62, t))
        chars["P1"] = hidden(); chars["P2"] = hidden()
        for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "BOSS", "VIC"):
            chars[z] = hidden()
        props["flash_cone"] = True
        li = lights(siren=0, lamp=0, dusk=0, moon=60, spot=700, clinic=170)
    # ================= S3 OUTBREAK (216-407) =================
    elif f < 408:
        # fase: 216-280 tracking pria | 280-320 kejang | 320-360 bangkit | 340-380 ECU mata | 380-407 SHADOW membeku
        vic_crouch = 0.0
        vic_eye = False
        vic_x, vic_y = 0.0, 1.0
        if f < 280:
            t = seg_t(f, 216, 280)
            vic_crouch = 0.55 * smooth(t)
            vic = char(vic_x, vic_y, 0, rot=0, lean=18, crouch=vic_crouch,
                       head_tilt=22, armL=10, armR=10, legL=0, legR=0)
            chars_cam = cam(lerp(-1, -0.5, t), lerp(-6.5, -3.8, t), lerp(1.9, 1.6, t),
                            vic_x, vic_y, 1.2, abs(-3.8 - vic_y) + 1.5, lerp(48, 55, t))
        elif f < 320:
            j = 0.06 * math.sin(f * 1.4)
            vic = char(vic_x + j, vic_y, 0, rot=0, lean=18, crouch=0.55,
                       head_tilt=22 + 10 * math.sin(f * 1.1), head_turn=12 * math.sin(f * 1.3),
                       armL=25, armR=25, legL=6, legR=-6)
            chars_cam = cam(-0.5, -3.8, 1.6, vic_x, vic_y, 1.1, 4.8, 55)
        elif f < 360:
            t = seg_t(f, 320, 360)
            vic_crouch = lerp(0.55, 0.0, smooth(t))
            vic_eye = f >= 340
            vic = char(vic_x, vic_y, 0, rot=0, lean=lerp(18, 8, smooth(t)), crouch=vic_crouch,
                       head_tilt=lerp(22, 8, smooth(t)), armL=lerp(25, 70, smooth(t)),
                       armR=lerp(25, 66, smooth(t)), eye_red=vic_eye)
            chars_cam = cam(-0.5, -3.8, 1.6, vic_x, vic_y, 1.2, 4.8, 55)
        elif f < 380:
            # extreme close-up mata merah
            vic = zombie_shamble(vic_x, vic_y, f, phase0=0, rot=0)
            chars_cam = cam(0.25, -0.7, 1.55, vic_x, vic_y - 0.05, 1.48, 1.7, 72)
        else:
            vic = zombie_shamble(vic_x, vic_y, f, phase0=0, rot=0)
            # cut ke SHADOW membeku di tepi frame
            chars["SH"] = char(-4.5, 0.5, 0, rot=35, lean=0, head_tilt=-6, head_turn=-18,
                               armL=0, armR=0, legL=0, legR=0, mouthH=1.4)
            chars_cam = cam(-5.2, -3.2, 1.5, -4.5, 0.5, 1.3, 3.9, 58)
        chars["VIC"] = vic
        if f < 380:
            chars["SH"] = char(-4.5, 0.5, 0, rot=35, lean=0, head_tilt=-6,
                               armL=0, armR=0, legL=0, legR=0)
        # kerumunan mundur
        chars["P1"] = ped_walk(lerp(-2, -8, seg_t(f, 216, 407)), -1.5, f, 1.0, rot=-60, amp=26)
        chars["P2"] = ped_walk(lerp(3, 9, seg_t(f, 216, 407)), 2.0, f, 3.0, rot=60, amp=26)
        for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "BOSS"):
            chars[z] = hidden()
        li = lights(siren=350 + 250 * math.sin(f * 0.25), lamp=320, dusk=0, moon=260, spot=0)
    # ================= S4 CHAOS (408-647): lari kencang, sirene menyapu =================
    elif f < 648:
        t = seg_t(f, 408, 647)
        sh_x = lerp(-8, 8, t)
        ph = f * 0.62
        c = walk_cycle(ph, 42)
        # menoleh ke belakang berkala
        look_back = -55 if (f % 72) < 36 else 0
        chars["SH"] = char(sh_x, 0, c["bob"], rot=60, lean=13,
                           head_turn=look_back, head_tilt=-4,
                           armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])
        # v2: horde 8 — mengejar dari semua sisi (belakang + samping + depan)
        for i, (zo, zy) in enumerate(((3.2, 1.6), (4.0, -1.5), (3.6, 2.4), (4.6, -2.4),
                                      (5.2, 0.8), (4.4, 3.0), (-2.8, 2.2), (-3.4, -2.0))):
            chars[f"Z{i + 1}"] = zombie_shamble(sh_x - zo, zy, f,
                                                phase0=i * 1.7, rot=60, speed=0.8)
        chars["P1"] = char(lerp(6, -7, t), -2.0, 0.03, rot=-60, lean=12,
                           armL=-35, armR=35, legL=38 * math.sin(f * 0.5), legR=-38 * math.sin(f * 0.5))
        chars["P2"] = char(lerp(-6, 7, t), 2.4, 0.03, rot=60, lean=12,
                           armL=35, armR=-35, legL=38 * math.sin(f * 0.5 + 1), legR=-38 * math.sin(f * 0.5 + 1))
        chars["BOSS"] = hidden(); chars["VIC"] = hidden()
        props["smoke"] = True
        # v2: Dutch sesekali (9/-10d) + shake kuat + kamera TIMUR (hadap barat):
        # Shadow lari ke arah kamera, horde mengejar terlihat di belakangnya
        dutch = 9 if (f % 96) < 48 else -10
        chars_cam = cam(sh_x + 2.5 + shake(f, 0.09), -4.2 + shake(f + 5, 0.05), 1.6 + shake(f + 11, 0.04),
                        sh_x - 1.0, 0.3, 1.2, 5.0, 48, roll=dutch)
        sir = 750 + 750 * (0.5 + 0.5 * math.sin(f * 0.55))
        li = lights(siren=sir, lamp=260 + 90 * math.sin(f * 0.3), dusk=0, moon=260, spot=0)
    # ================= S5 SURVIVAL (648-863): jongkok di toko, senter menyapu =================
    elif f < 864:
        t = seg_t(f, 648, 863)
        props["vial"] = True  # v2: vial di tangan kiri
        sweep = 26 * math.sin(f * 0.045)  # senter menyapu kiri-kanan
        chars["SH"] = char(OX - 3.6, 0.6, 0, rot=0, lean=6, crouch=0.85,
                           head_tilt=6, head_turn=sweep * 0.5,
                           armL=15, armR=55 + sweep, legL=18, legR=-14)
        for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "BOSS", "P1", "P2", "VIC"):
            chars[z] = hidden()
        props["hands_z"] = 0.14 * abs(math.sin(f * 0.35))  # gedor berirama
        props["flash_cone"] = True
        # kamera TETAP di (OX-4.5, -3.5): pan cepat ke pintu, TAHAN di pintu, pan kembali
        if f < 710:
            # wajah SHADOW 3/4 dari barat-daya (senter menyapu)
            chars_cam = cam(OX - 4.5, -3.5, 1.6, OX - 3.6, 0.6, 1.15, 4.3, lerp(46, 50, seg_t(f, 648, 710)))
        elif f < 740:
            # pan cepat ke pintu kaca
            u = smooth(seg_t(f, 710, 740))
            chars_cam = cam(OX - 4.5, -3.5, 1.6,
                            lerp(OX - 3.6, OX, u), lerp(0.6, -5.0, u), lerp(1.15, 1.3, u),
                            lerp(4.3, 5.3, u), 50)
        elif f < 800:
            # TAHAN di pintu: tangan zombie menggedor
            chars_cam = cam(OX - 4.5, -3.5, 1.6, OX, -5.0, 1.3, 5.3, 50)
        elif f < 830:
            # pan kembali ke SHADOW
            u = smooth(seg_t(f, 800, 830))
            chars_cam = cam(OX - 4.5, -3.5, 1.6,
                            lerp(OX, OX - 3.6, u), lerp(-5.0, 0.6, u), lerp(1.3, 1.15, u),
                            lerp(5.3, 4.3, u), 50)
        else:
            # TAHAN di SHADOW + slow zoom-in
            chars_cam = cam(OX - 4.5, -3.5, 1.6, OX - 3.6, 0.6, 1.15, 4.3,
                            lerp(50, 58, seg_t(f, 830, 863)))
        # v2: denyut gigitan merah di close-up lengan (f>=830)
        bite = (14 + 10 * math.sin(f * 0.35)) if f >= 830 else 0
        li = lights(siren=0, lamp=0, dusk=0, moon=50, shop=110, spot=1900, bite=bite)
    # ================= S6 DISCOVERY (864-1103) =================
    elif f < 1104:
        if f < 960:
            # dolly-in ke kertas di meja
            t = seg_t(f, 864, 960)
            chars["SH"] = char(lerp(OX - 3.6, OX + 3.0, smooth(t)), lerp(0.6, 1.6, smooth(t)), 0,
                               rot=lerp(0, 100, smooth(t)), lean=6, crouch=lerp(0.85, 0.25, smooth(t)),
                               head_tilt=18, armL=10, armR=45)
            chars_cam = cam(OX + 3.5, lerp(-2.5, -0.6, smooth(t)), lerp(1.7, 1.5, smooth(t)),
                            OX + 3.3, 2.5, 0.95, 3.2, lerp(48, 58, t))
        elif f < 1020:
            # close-up wajah membaca -> menatap lengan
            t = seg_t(f, 960, 1020)
            chars["SH"] = char(OX + 3.0, 1.6, 0, rot=lerp(100, -20, smooth(seg_t(f, 960, 990))), lean=4, crouch=0.15,
                               head_tilt=lerp(18, 30, smooth(t)), head_turn=lerp(0, -25, smooth(t)),
                               armL=lerp(10, -55, smooth(t)), armR=45)
            chars_cam = cam(OX + 1.0, -1.2, 1.6, OX + 3.0, 1.6, 1.4, 3.4, 48)
        else:
            # tegak, determined
            t = seg_t(f, 1020, 1103)
            chars["SH"] = char(OX + 3.0, 1.6, 0, rot=lerp(-20, 20, smooth(t)), lean=lerp(4, 8, smooth(t)),
                               crouch=lerp(0.15, 0.0, smooth(t)), head_tilt=lerp(30, 0, smooth(t)),
                               head_turn=0, armL=lerp(-55, 0, smooth(t)), armR=lerp(45, 10, smooth(t)),
                               mouthH=0.8)
            chars_cam = cam(OX + 2.6, lerp(0.2, -1.5, smooth(t)), 1.6, OX + 3.0, 1.6, 1.2, 3.4, lerp(62, 50, t))
        for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "BOSS", "P1", "P2", "VIC"):
            chars[z] = hidden()
        props["flash_cone"] = True
        props["vial"] = True  # v2: vial di tangan kiri
        li = lights(siren=0, lamp=0, dusk=0, moon=50, shop=120, spot=2000)
    # ================= S7 v2 CLIMAX (1104-1295): Boss gigit lengan SHADOW — TANPA pipa =================
    elif f < 1296:
        # pintu jebol 1104-1120; Boss masuk 1110-1180; dekati SHADOW 1180-1230;
        # gigit lengan 1230-1258; flash putih 1258-1259; Boss roboh 1260-1295
        props["door_hide"] = False
        props["door_rot"] = -85 * smooth(seg_t(f, 1104, 1120))
        props["door_y"] = lerp(-4.7, -3.9, smooth(seg_t(f, 1104, 1120)))
        props["door_z"] = lerp(1.3, 0.2, smooth(seg_t(f, 1104, 1120)))
        boss_t = smooth(seg_t(f, 1110, 1180))
        boss_x, boss_y = OX, lerp(-6.5, -2.2, boss_t)
        stomp = 0.06 * abs(math.sin(f * 0.35)) if f < 1180 else 0
        boss_armR = 0
        boss_pitch = 0
        boss_lean = 6
        boss_head_tilt = 6
        boss_xj = 0.0
        if 1180 <= f < 1230:
            u = seg_t(f, 1180, 1230)
            boss_y = lerp(-2.2, -1.5, smooth(u))  # mendekat ke SHADOW
            boss_armR = -55 * smooth(u)  # tangan meraih lengan SHADOW
            boss_lean = 6 + 12 * math.sin(u * math.pi)
            boss_head_tilt = 6 + 14 * smooth(u)
        elif 1230 <= f < 1260:
            # MENGGIGIT lengan kiri SHADOW; Boss bergetar saat darah membakar virus
            boss_y = -1.5
            boss_armR = -55
            boss_lean = 18
            boss_head_tilt = 32  # kepala menunduk ke lengan
            boss_xj = 0.05 * math.sin(f * 2.0)
        elif f >= 1260:
            u = seg_t(f, 1260, 1295)
            boss_y = -1.5
            boss_armR = lerp(-55, 20, smooth(u))
            boss_pitch = -82 * smooth(seg_t(f, 1262, 1295))  # roboh ke belakang
            boss_head_tilt = lerp(32, 10, smooth(u))
            boss_lean = 6
        chars["BOSS"] = char(boss_x + boss_xj, boss_y, stomp, rot=180, lean=boss_lean, pitch=boss_pitch,
                             head_tilt=boss_head_tilt, armL=55, armR=boss_armR,
                             legL=14 * math.sin(f * 0.35), legR=-14 * math.sin(f * 0.35),
                             eye_red=True)
        # SHADOW: TIDAK mengayun pipa — dia menyodorkan lengan kirinya ke Boss
        if f < 1210:
            chars["SH"] = char(OX - 0.5, -1.0, 0, rot=0, lean=4, head_tilt=0,
                               armL=0, armR=-75, legL=0, legR=0)
        elif f < 1230:
            u = smooth(seg_t(f, 1210, 1230))
            chars["SH"] = char(OX - 0.5, -1.0, 0, rot=0, lean=lerp(4, -6, u),
                               head_tilt=lerp(0, -8, u), armL=lerp(0, 75, u), armR=-75,
                               legL=0, legR=0)
        elif f < 1260:
            # lengan kiri disodorkan, tubuh menahan sakit
            chars["SH"] = char(OX - 0.5, -1.0, 0, rot=0, lean=-6, head_tilt=-8,
                               armL=75, armR=-40, legL=8, legR=-8)
        else:
            u = smooth(seg_t(f, 1260, 1295))
            chars["SH"] = char(lerp(OX - 0.5, OX - 2.0, u), -1.0, 0, rot=lerp(0, 30, u),
                               lean=lerp(-6, 6, u), head_tilt=lerp(-8, 0, u),
                               armL=lerp(75, 0, u), armR=lerp(-40, 10, u), legL=0, legR=0)
        for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "P1", "P2", "VIC"):
            chars[z] = hidden()
        props["flash_cone"] = True
        # v2: pipa TIDAK dipakai — props["pipe"] tetap hide=True (default)
        flash_white = IMPACT <= f <= IMPACT + 1
        # kamera: low-angle reveal -> ECU wajah Boss dari utara (f1144-1179, dipertahankan v1) ->
        # shake saat gigitan -> dolly-in ke wajah Boss saat darah membakarnya -> zoom-out saat roboh
        if 1144 <= f < 1180:
            chars_cam = cam(41.8, boss_y + 3.0, 2.0, 40.0, boss_y, 2.05, 3.5, 68)
        elif f < 1180:
            t = seg_t(f, 1104, 1180)
            chars_cam = cam(OX + 2.5, -3.8, 1.0, OX, boss_y, 2.2, 4.5, lerp(58, 50, t))
        elif f < 1240:
            # dari barat: Shadow (depan) + Boss (belakang) saat mendekat — lengan terlihat
            chars_cam = cam(OX - 5.0 + shake(f, 0.06), -0.8, 1.7 + shake(f + 3, 0.04),
                            OX - 0.7, -1.3, 1.6, 4.8, 44)
        elif f < 1270:
            u = seg_t(f, 1240, 1270)
            chars_cam = cam(OX - 5.0 + shake(f, 0.08), -0.8, 1.7,
                            OX - 0.7, -1.3, 1.6, 4.8, lerp(50, 62, u))
        else:
            t = seg_t(f, 1270, 1295)
            chars_cam = cam(OX + 3.5, lerp(-2.0, -3.5, smooth(t)), lerp(1.6, 1.9, smooth(t)),
                            OX, -2.2, 1.0, 5.5, lerp(52, 44, t))
        li = lights(siren=0, lamp=0, dusk=0, moon=60, shop=140, spot=900,
                    flash=2500 if flash_white else 0)
    # ================= S8 v2 TWIST (1296-1439): gerbang kota + 2 tentara =================
    else:
        # SHADOW terhuyung ke gerbang; ECU mata; mata merah 1386-1391; senyum tipis
        eye_red = EYE_RED_START <= f <= EYE_RED_END
        bite = 0
        if f >= 1330:
            bite = 18 + 12 * math.sin(f * 0.3)
        if f < 1360:
            # terhuyung ke gerbang (langkah goyah)
            t = seg_t(f, 1296, 1360)
            wob = 0.25 * math.sin(f * 0.5)
            chars["SH"] = char(GX - 2.5 + wob, lerp(-2.5, 0.2, smooth(t)), 0.02 * abs(math.sin(f * 0.4)),
                               rot=180, lean=9, head_tilt=12, head_turn=-10,
                               armL=10, armR=5,
                               legL=14 * math.sin(f * 0.3), legR=-14 * math.sin(f * 0.3),
                               eye_red=eye_red)
            chars_cam = cam(GX - 1.5, lerp(-5.5, -4.0, smooth(t)), 1.7,
                            GX - 2.0, 0.0, 1.2, 4.5, 50)
        elif f < 1392:
            # dolly-in ke extreme close-up mata — kamera dari UTARA (sisi gerbang):
            # Shadow menghadap utara (ke gerbang/kamera), wajah + mata terlihat
            t = seg_t(f, 1360, 1392)
            chars["SH"] = char(GX - 1.0, 0.2, 0, rot=180, lean=6,
                               head_tilt=lerp(12, 0, smooth(t)), head_turn=-10,
                               armL=10, armR=5, legL=0, legR=0, eye_red=eye_red)
            chars_cam = cam(lerp(GX + 1.5, GX + 0.2, smooth(t)), lerp(2.6, 1.6, smooth(t)),
                            lerp(1.6, 1.5, smooth(t)), GX - 1.0, 0.2, 1.48, lerp(4.5, 1.6, smooth(t)), 70)
        else:
            # senyum tipis + pull-back: Shadow berbalik menghadap kamera (selatan),
            # gerbang + 2 tentara terlihat di belakangnya
            t = seg_t(f, 1392, 1439)
            # v2: bergeser ke kiri saat berbalik — tentara kiri (GX-1.0) tidak tertutup badannya
            chars["SH"] = char(lerp(GX - 1.0, GX - 1.5, smooth(t)), 0.2, 0, rot=lerp(180, 0, smooth(t)), lean=6,
                               head_tilt=0, head_turn=-10,
                               armL=10, armR=5, legL=0, legR=0, eye_red=eye_red,
                               mouthW=1.7, mouthH=0.6)
            chars_cam = cam(lerp(GX - 1.0, GX - 0.5, smooth(t)), lerp(-1.4, -4.6, smooth(t)),
                            lerp(1.5, 1.8, smooth(t)), GX, 1.2, 1.4, lerp(1.6, 4.5, smooth(t)),
                            lerp(70, 40, t))  # v2: target tengah gerbang (tentara ±1.0 masuk frame)
        chars["BOSS"] = hidden()
        for z in ("Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "P1", "P2", "VIC"):
            chars[z] = hidden()
        props["door_hide"] = True  # panel pintu toko tidak relevan di gerbang
        props["flash_cone"] = False
        li = lights(siren=0, lamp=0, dusk=0, moon=80, shop=0, spot=250, bite=bite, gate=900)

    # v2 fix cone senter (19 Nov): mesh cone SH_FlashCone dari dekat/samping
    # terbaca seperti gelembung/balon (f_0201, f_0831) — sembunyikan HANYA di
    # frame close-up; Spot (SH_FlashSpot) TETAP menyala, pencahayaan tidak
    # berubah. Rentang plan-f: S2 180-215, S5 830-863, S6 960-1020. Di luar
    # itu cone tetap tampil sebagai berkas. Pendekatan (b) — dipilih karena
    # paling aman: tanpa mengubah material/geometri, tanpa risiko ke frame lain.
    if (180 <= f <= 215) or (830 <= f <= 863) or (960 <= f <= 1020):
        props["flash_cone"] = False

    rows.append({"f": f, "t": round(f / 24.0, 4), "chars": chars, "lights": li,
                 "cam": chars_cam, "props": props, "flash_white": flash_white})


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plan.json")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    print(f"WROTE {out}: {len(rows)} rows")
    # self-checks
    assert len(rows) == N
    assert rows[0]["f"] == 0 and rows[-1]["f"] == N - 1
    reds = [r["f"] for r in rows if r["chars"]["SH"]["eye_red"]]
    assert reds == list(range(EYE_RED_START, EYE_RED_END + 1)), f"eye_red frames: {reds}"
    flashes = [r["f"] for r in rows if r["flash_white"]]
    assert flashes == [IMPACT, IMPACT + 1], f"flash frames: {flashes}"
    print(f"CHECK OK: SH eye_red frames {reds}, flash frames {flashes}")


if __name__ == "__main__":
    main()
