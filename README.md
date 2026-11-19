# zombie-render-farm

Render farm GitHub Actions (Eevee) untuk film **Zombie Apocalypse Blender 3D**
— 60 dtk, 24 fps, 1440 frame, format 9:16 (540×960, utama) + 16:9 (960×540).
Scene prosedural dari primitif Blender, tanpa file .blend / aset impor.
Repo ini HANYA berisi pipeline render; sumber desain + audio ada di
`~/workspace/shorts/zombie-3d/` (DESIGN.md).

## Pipeline (`pipeline/`)

- `build_scene_zombie.py` — bangun scene lengkap (2 set, 9 karakter vinyl-toy,
  lampu malam, kamera). Setting B7 via env `FS_*` (samples 8, ray OFF,
  volumetrics tile 16, DOF ON, motion blur ON, subsurf 1, bevel 0).
- `plan_zombie.py` — generator `plan.json` (1440 baris, satu per frame).
- `plan.json` — per frame: rig tiap karakter, lampu, kamera, props, flag
  (mata merah SHADOW f1386–1391, flash putih f1258–1259, beat ECU wajah
  Boss dari utara f1144–1179 di S7).
- `animate_zombie.py` — mainkan plan.json, keyframe tiap frame (LINEAR),
  render Eevee per rentang. CLI:
  `blender -b --factory-startup -P animate_zombie.py -- <out_dir> --start N --end N --plan plan.json --res 540 960 --lensk 0.62`
  (9:16; 16:9: `--res 960 540 --lensk 1.00`). Frame Blender = plan f + 1.

## Workflows (`.github/workflows/`, dipicu manual dari tab Actions)

- `render-test.yml` — uji 120 frame: rentang tersibuk S4 (Blender 501–560),
  9:16 60 frame + 16:9 60 frame, 20 job × 6 frame, upload artifact per job.
  Verifikasi: semua frame ada tanpa gap + piksel-identik vs render lokal
  Eevee pada frame yang sama (mean abs diff < 1).
- `render-full.yml` — full run 2880 frame (2 format × 1440), 40 job × 72 frame,
  tiap job zip frame-nya lalu upload sebagai asset ke Release yang dibuat
  dulu dari luar (`gh release create <tag>` sebelum trigger).
  **JANGAN trigger sebelum render-test lolos.**
- `render-missing.yml` — (nanti, pola rubik-render-farm) re-render chunk
  yang gagal / frame yang hilang dari full run.

## Pola yang dipakai

Diadaptasi dari `rubik-render-farm` (terbukti: full run 3660 frame):
actions/cache Blender 4.5.3, download Blender dengan retry loop, keberhasilan
dinilai dari FILE FRAME (bukan exit code Blender — Mesa bisa segfault saat
teardown setelah semua frame tersimpan), repo PUBLIK supaya menit gratis.
