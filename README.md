# yakyuugame

パワプロ風3D野球ゲーム（Three.js / 単一HTML）。NPB12球団＋MLB30球団、ペナント・オフシーズン・ドラフト・育成などを実装。

`index.html` をブラウザで開くと遊べます（Three.js r128 と Google Fonts はCDNから読み込み）。

## モーションキャプチャ
投球・送球（CMU 124_01/124_02）、打撃（124_07）、走り（143_01, 09_01）は、
[CMU Graphics Lab Motion Capture Database](http://mocap.cs.cmu.edu/)（Bruce Hahne氏 / cgspeed によるBVH変換版）の
データを、`tools/mocap/` のスクリプトでゲーム内の姿勢（骨盤・体幹・手足の位置）に変換して `index.html` に埋め込んでいます。

- 変換手順: BVHを `tools/mocap/` に置き `python3 gen.py` → `mc_data.json` を生成
- 元データ: https://github.com/una-dinosauria/cmu-mocap
- The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217.
