"""
仮の効果音を作る（numpy だけ。録音ではなく合成なので、あとで Freesound の本物に置き換えるのがおすすめ）
  door_open.wav  … 古い扉が きしみながら開く音（約2秒）
  door_close.wav … 扉が バタン と閉まって、ガラスがふるえる音（約1.6秒）
  latch.wav      … カチャッという金属の小さな音（約0.3秒）
  safe_click.wav … 金庫のダイヤルが1目盛り進む「カリッ」（約0.05秒）
  safe_clunk.wav … 金庫のかんぬきが外れる「ガチャン」（約0.7秒）
  safe_creak.wav … 金庫のふたが、ちょうつがいをきしませて開く音（約1.1秒）
出力：assets/sounds/   使い方：python make_sounds.py
"""
import os
import wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'assets', 'sounds'))
os.makedirs(OUT, exist_ok=True)
SR = 44100
rng = np.random.default_rng(714)


def t_axis(sec):
    return np.arange(int(SR * sec)) / SR


def lowpass(x, k):
    """かんたんな平均で高い音をけずる（k が大きいほど こもる）"""
    ker = np.ones(k) / k
    return np.convolve(x, ker, mode='same')


def save(name, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.9
    p = os.path.join(OUT, name)
    with wave.open(p, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    print('保存', name, '%.1f秒' % (len(x) / SR), os.path.getsize(p) // 1024, 'KB')


def creak(sec, f0, f1):
    t = t_axis(sec)
    f = f0 + (f1 - f0) * (t / sec) ** 1.3 + 14 * np.sin(2 * np.pi * 7.0 * t)      # 音程がゆっくり上がり、ふるえる
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = sum(np.sin(ph * h) / h for h in (1, 2, 3, 5))                             # 倍音を足して きしみっぽく
    n = lowpass(rng.standard_normal(len(t)), 12)
    env = np.sin(np.pi * t / sec) ** 0.8 * (0.6 + 0.4 * np.sin(2 * np.pi * 3.3 * t + 1))
    return (0.7 * tone + 0.5 * n) * env


def thud(sec, f):
    t = t_axis(sec)
    return np.sin(2 * np.pi * f * t * (1 - 0.35 * t / sec)) * np.exp(-t * 9)


def door_open():
    x = np.zeros(int(SR * 2.4))
    c = creak(1.9, 150, 330)
    x[int(SR * 0.25):int(SR * 0.25) + len(c)] += c * 0.8
    click = lowpass(rng.standard_normal(int(SR * 0.05)), 3) * np.exp(-t_axis(0.05) * 90)
    x[:len(click)] += click * 1.2                                                    # はじめの「カチッ」
    th = thud(0.4, 70) * 0.6
    x[int(SR * 2.0):int(SR * 2.0) + len(th)] += th                                   # 最後に 戸がとまる音
    save('door_open.wav', x)


def door_close():
    x = np.zeros(int(SR * 1.8))
    t = t_axis(0.6)
    body = (thud(0.6, 55) * 1.0 + lowpass(rng.standard_normal(len(t)), 40) * np.exp(-t * 14) * 1.2)
    x[:len(body)] += body
    n = int(SR * 1.4)
    tt = t_axis(1.4)
    rattle = rng.standard_normal(n) * np.exp(-tt * 3.5) * (0.4 + 0.6 * np.sin(2 * np.pi * 35 * tt) ** 2) * 0.35   # ガラスのふるえ
    rattle = rattle - lowpass(rattle, 6)
    x[int(SR * 0.05):int(SR * 0.05) + n] += rattle
    save('door_close.wav', x)


def latch():
    t = t_axis(0.3)
    c = lowpass(rng.standard_normal(len(t)), 2) * np.exp(-t * 60)
    c2 = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 80) * 0.5
    save('latch.wav', c + c2)


def safe_click():
    t = t_axis(0.06)
    c = lowpass(rng.standard_normal(len(t)), 2) * np.exp(-t * 130)
    c2 = np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 160) * 0.5
    save('safe_click.wav', c + c2)


def safe_clunk():
    x = np.zeros(int(SR * 0.8))
    t = t_axis(0.8)
    body = (np.sin(2 * np.pi * 95 * t * (1 - 0.2 * t)) * np.exp(-t * 11) * 1.0
            + lowpass(rng.standard_normal(len(t)), 8) * np.exp(-t * 30) * 0.9)
    x[:len(body)] += body
    t2 = t_axis(0.2)
    metal = np.sin(2 * np.pi * 1450 * t2) * np.exp(-t2 * 45) * 0.45 + np.sin(2 * np.pi * 2300 * t2) * np.exp(-t2 * 60) * 0.25
    x[int(SR * 0.04):int(SR * 0.04) + len(metal)] += metal
    save('safe_clunk.wav', x)


def safe_creak():
    x = np.zeros(int(SR * 1.5))
    c = creak(0.95, 260, 620)
    x[int(SR * 0.1):int(SR * 0.1) + len(c)] += c * 0.8
    th = thud(0.25, 90) * 0.5
    x[int(SR * 1.0):int(SR * 1.0) + len(th)] += th                                   # 最後に、ふたが止まる音
    save('safe_creak.wav', x)


if __name__ == '__main__':
    door_open(); door_close(); latch(); safe_click(); safe_clunk(); safe_creak()
