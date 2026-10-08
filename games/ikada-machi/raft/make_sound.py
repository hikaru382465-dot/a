# art/sound の録音を、軽い MP3 にして raft/sound_data.js に埋め込む。
# 使い方：python3 make_sound.py    （音を差し替えたら、もう一度実行する）
import base64, json, pathlib, subprocess, tempfile
here = pathlib.Path(__file__).parent
src = here.parent / 'art' / 'sound'
# 名前: (ファイル, 音量の倍率, 最大の長さ秒)
use = {
    'splash': ('splash_04.ogg', 1.0, 1.2), 'splash2': ('splash_08.ogg', 1.0, 1.0), 'splash3': ('splash_14.ogg', 1.0, 0.8),
    'haul': ('splash_02.ogg', 0.9, 0.8),
    'bubble1': ('bubble_01.ogg', 1.0, 0.7), 'bubble2': ('bubble_02.ogg', 1.0, 0.4), 'bubble3': ('bubble_03.ogg', 0.8, 0.6),
    'rain': ('loop_rain.ogg', 1.0, 6.8), 'drag': ('loop_water_02.ogg', 1.0, 7.0),
    'wave1': ('wave_01.flac', 1.0, 3), 'wave2': ('wave_02.flac', 1.0, 3.3), 'wave3': ('wave_03.flac', 1.0, 2.4), 'wave4': ('wave_04.flac', 1.0, 2.1)
}
out = {}
for k, (f, vol, dur) in use.items():
    with tempfile.NamedTemporaryFile(suffix='.mp3') as t:
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(src / f), '-t', str(dur), '-ac', '1', '-ar', '32000', '-af', f'volume={vol},loudnorm=I=-20:TP=-2:LRA=7', '-c:a', 'libmp3lame', '-b:a', '56k', t.name], check=True)
        out[k] = 'data:audio/mpeg;base64,' + base64.b64encode(open(t.name, 'rb').read()).decode()
(here / 'sound_data.js').write_text('window.RAFT.soundData = ' + json.dumps(out) + ';\n', encoding='utf-8')
print('sound_data.js', (here / 'sound_data.js').stat().st_size, 'bytes', list(out))
