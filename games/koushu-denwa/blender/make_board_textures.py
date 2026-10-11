"""掲示板用の木の板の画像（色・凹凸・粗さ）を作る。numpy と Pillow だけで動く。
   python make_board_textures.py  →  assets/tex/game/wood_color.png, wood_normal.png, wood_rough.png（1024、つなげて使える）"""
import os
import numpy as np
from PIL import Image

N = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "tex", "game")
rng = np.random.default_rng(55)


def tile_noise(res):
    """つなぎ目のない、なめらかなノイズ（0〜1）"""
    a = rng.random((res, res))
    f = np.fft.fft2(a)
    return a, f


def smooth(ax_sigma_x, ax_sigma_y):
    """周波数を絞って、つなぎ目のないノイズを作る（x方向とy方向でなめらかさを変える＝木目のすじ）"""
    a = rng.standard_normal((N, N))
    fx = np.fft.fftfreq(N)[None, :]
    fy = np.fft.fftfreq(N)[:, None]
    g = np.exp(-((fx * ax_sigma_x) ** 2 + (fy * ax_sigma_y) ** 2) * 60.0)
    r = np.real(np.fft.ifft2(np.fft.fft2(a) * g))
    r = (r - r.min()) / (r.max() - r.min())
    return r


grain = smooth(1.5, 90.0)          # 縦に長いすじ
fine = smooth(4.0, 260.0)
cloud = smooth(25.0, 25.0)
h = 0.55 * grain + 0.3 * fine + 0.15 * cloud
# 板の継ぎ目（4枚の横板）
plank = (np.arange(N)[None, :] // (N // 4)) * np.ones((N, 1))
edge = np.abs((np.arange(N)[None, :] % (N // 4)) - 0.0) * np.ones((N, 1))
seam = np.exp(-np.minimum(edge, (N // 4) - edge) / 3.0)
h = h - 0.35 * seam
h = np.clip((h - 0.5) * 1.8 + 0.5, 0, 1)                       # 木目のコントラストを強める
shade = 0.85 + 0.12 * ((plank * 37) % 5) / 5.0
col = np.zeros((N, N, 3))
base = np.array([0.34, 0.24, 0.15])
dark = np.array([0.16, 0.10, 0.06])
t = np.clip(h, 0, 1)[..., None]
col = dark + (base - dark) * t
col *= shade[..., None]
col *= (0.82 + 0.3 * cloud)[..., None]                       # 古びたムラ
col = np.clip(col, 0, 1)
Image.fromarray((col * 255).astype(np.uint8)).transpose(Image.TRANSPOSE).save(os.path.join(OUT, "wood_color.png"))

dy, dx = np.gradient(h * 6.0)      # （保存のとき x/y を入れかえるので、法線の x/y も入れかわる）
nx, ny, nz = -dx * 4.0, -dy * 4.0, np.ones_like(h)
l = np.sqrt(nx * nx + ny * ny + nz * nz)
nrm = np.stack([ny / l, nx / l, nz / l], -1) * 0.5 + 0.5
Image.fromarray((nrm * 255).astype(np.uint8)).transpose(Image.TRANSPOSE).save(os.path.join(OUT, "wood_normal.png"))

rough = np.clip(0.78 + 0.17 * (1 - h) + 0.05 * fine, 0, 1)
Image.fromarray((rough * 255).astype(np.uint8)).transpose(Image.TRANSPOSE).save(os.path.join(OUT, "wood_rough.png"))
print("wood_color / wood_normal / wood_rough を作りました")
