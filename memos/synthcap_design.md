# SynthCap 設計メモ（2026-11-19）

CardputerZero の EXT 2.54-14P（Cap）に挿す MIDI/CV インターフェース。

## 構成
| ブロック | 内容 |
|---|---|
| MCU | CH32V303CBT6（LQFP48、C7494374）、8MHz水晶（C367183、負荷容量12pF、C11/C12=15pF）。WCH標準の8MHzに合わせた |
| 本体との接続 | **USB MIDI**: EXT 1番(HAT_P0=D+)→PA12、3番(HAT_P1=D-)→PA11。本体をHostモードにし、PYG1_HAT_SW=HighでUSBへ切替 |
| 予備の接続 | USART2: EXT12番(G14=CM0のTX)→R28(1k)→PA3(RX)、PA2(TX)→R29(1k)→EXT14番(G15=CM0のRX)。公式の写真と回路図に合わせた（ドキュメントの表だけ逆）。1kは逆だった場合の保護。 |
| 書き込み（CpZだけで完結） | チップ内蔵のUSB ISPを使う。EXT 11番(G9)→1k→BOOT0（100kでプルダウン）、EXT 5番(G22)→NRST（R1=100kでプルアップ、C10=100nF）。CpZで G9=High → G22をLowにして離す（入力に戻す）→ `wchisp` で書き込み → G9を離す → G22でリセットしてアプリ起動。予備にSWDパッドJ7（未実装） |
| 電源 | EXT6番(5VOUT)→+5V。AMS1117-3.3（C6186）→+3V3。VDDAはフェライトビーズ経由。EXT2番(5VIN)は本体への入力なので未接続 |
| CV出力 x2 | 内蔵DAC PA4/PA5 → LMV324で1.5倍（10k/20k）→ 220Ω → OUT1/OUT2のTip。範囲は約0〜4.9V |
| Gate出力 x2 | PB0/PB1 → LMV324で1.5倍 → 220Ω → OUT1/OUT2のRing |
| Clock出力 | PB8 → MMBT3904 → 1kで+5Vにプルアップ（論理反転）→ CLOCKのTip |
| Clock入力 | CLOCKのRing → 100k/100k + 1N4148 → MMBT3904 → PB9（反転、約1.2Vでスイッチ） |
| MIDI | TRS Type A。IN: TLP2362（オープンコレクタ、4.7kでプルアップ）→ PB11(USART3 RX)。OUT: PB10 → 10Ω → Tip、+3V3 → 33Ω → Ring |
| エンコーダ | EC12E x4。A/B: PA6/PA7(TIM3)、PB6/PB7(TIM4)、PA0/PA1(TIM2)、PA8/PA9(TIM1)。SW: PB12〜PB15（内部プルアップを使う） |
| LED | PC13（Lowで点灯） |

## 基板（2026-11-19 更新: 80 × 32mm）
- 2層、両面GNDベタ。下辺にEXTヘッダー（L字、元の位置のまま）
- **表面**: エンコーダ x4（EC12E。信号パッドA/B/C/S1/S2はSMDパッド、MP（取り付け足）は貫通穴）、EXTヘッダー、SWDパッド（未実装）
- **裏面**: SMD部品すべて（ジャックも）。**JLCPCBは片面（裏面）実装だけで済む**。表のエンコーダとヘッダーは手はんだ
- ジャック（PJ-342、C668606）は上辺に5個。左から MIDI IN / MIDI OUT / CLOCK / OUT1 / OUT2。バレルが基板端から1.4mmはみ出す
  - ピン対応: 3=Tip、6=Ring、2・5=Sleeve（挿入口に近い2本）、4・7=検出スイッチ（未使用）。**図面から推定。実機で導通確認すること**
  - フットプリントは tools/gen_fp.py が docs/PJ-342_datasheet_C668606.pdf から作る（SynthCap.pretty）
- エンコーダは持っているEC12E（スルーホール品）の足を表面のSMDパッドにはんだ付けする前提（足を曲げる/短く切る）
- 配置は tools/gen_pcb.py の PLACE 表（つながる相手の近くに手で割り付け。2端子部品はパッド1の向きで指定）。配線は未
- DRC: エラー0。警告は、ジャックの位置決め穴がエンコーダ本体の下に重なること（表裏で重なるだけ）、エンコーダのシルク、はみ出し部のシルクだけ。回路図とのパリティも0件
- ERC: エラー0、警告0

## 本体への取り付け（2026-11-19、Cap LoRaの図面・公式写真・本体STLから）
- EXT端子は本体上面の中央にある2x7の**メスソケット**。上段（キーボード側）がGPIOの列（奇数ピン）、下段（背面側）が電源/I2C/UART（偶数ピン）。正面から見て1番(G26)は右側
- Capは本体の上に継ぎ足す向きに付く。基板は本体の正面と平行で、エンコーダが正面（キーボード側）、ジャックが背面側
- ネジ止め: 本体の左端から14mmと70mm（間隔56mm）に幅4.2mmの溝があり、上面から3.7mm下にM2の下穴(Ø1.6)がある。Cap LoRaは Ø4の耳（穴Ø2）をここに入れて背面からネジ止めする
- この耳の面は、L字ヘッダーで決まる基板の面とほぼ同じ高さ（推定で差0.4mm）。なので**耳は基板の外形（FR4）で作った**。幅4mm、穴Ø2.1、基板下辺から3.7mm
- 基板の角はR2。シェルは下辺を開けて、本体上面にそのまま載る形にした
- 未確認: ソケット上面の沈み込み量（0.2〜0.9mm）によって、穴の位置が上下にずれる可能性。ネジの種類（M2タッピング？）と長さ

## コスト目安（1枚あたりの部品代、JLCPCB価格）
CH32V303 $1.26、LMV324 $0.31、TLP2362 $0.46、AMS1117 $0.20、水晶 $0.10、受動部品 約$0.3 → 約$2.6
Extended部品は4種類（MCU、オペアンプ、フォトカプラ、ジャック）で、他はBasic部品。ジャック5個で約$0.9

## 生成の流れ
```
python3 tools/gen_sch.py                    # design.py → SynthCap.kicad_sch
python3 tools/gen_fp.py                     # PJ-342とEC12E(SMDパッド)のフットプリント
<KiCadのpython3> tools/gen_pcb.py           # design.py + 配置 → SynthCap.kicad_pcb と shell/layout.scad（配線は消える）
kicad-cli pcb export pos / sch export bom → python3 tools/jlc_export.py
openscad -D 'part="base"' / 'part="top"'    # shell/synthcap_shell.scad
```
注意: gen_pcb.py は基板を作り直すので、手で引いた配線は消える。配線を始めたら gen_pcb.py は使わず、KiCadの「回路図から基板を更新」で反映する。

## TODO / 要確認
- [ ] **PJ-342のピン対応（Tip=3、Ring=6、Sleeve=2/5）**を、届いたジャックで導通確認する
- [ ] EXTヘッダーの向きは公式写真と照合済み（1番が正面から見て右、奇数列がキーボード側）。実機に挿して、耳の穴とネジ穴が合うかを確認する
- [ ] 配線（Freeroutingで自動配線するか、手で引く）
- [ ] JLCのプレビューで回転を確認（SOT-223、SOIC、SO-5、LQFPは向きがずれることがある）
- [ ] エンコーダの足をSMDパッドにはんだ付けできるか試す（パッドが小さければ gen_fp.py のパッドサイズを広げる）
- [ ] シェル: ジャック高さ・軸の高さ、EC12Eの本体高さ、ノブ径を実物で測ってパラメータを合わせる。本体とのZ方向の位置合わせも
- [ ] JLC片面（裏面）実装で発注する場合の、CPLの回転（裏面は反転する）をプレビューで確認
- [ ] TLP2362の入力電流が、3.3V機器から送られるMIDI信号でも足りるか確認する
- [ ] **CpZからGPIO（G9/G22）とM5IOE1（PYG1_HAT_SW=USB、PYG13_HAT_EN）を操作する方法**を確認する。USB ISPで書き込むにはHostモードも必要
- [ ] CpZ側のレベル変換ICが弱い出力のため、G22→NRST（R1=100k）とG9→BOOT0（1k+100k）がちゃんと効くか、実機で確認する
- [ ] CH32V303のUSBD内蔵プルアップの設定（R6は未実装の予備パッド）
- [ ] ファーム: USB MIDIクラス、DACの校正（VDDA基準なので1V/octの校正テーブルを持つ）

## 配線（2026-11-19、Freerouting 1.9.0）
- 自動配線済み。DRCエラー0、未配線0、パリティ0（配線809本、ビア66個）
- ネットクラス: +5V=0.4mm、+3V3/VDDA/GND=0.25mm（0.3mmだとLQFPの電源ピンに入らず未配線が出た）、他0.2mm
- 手順: `tools/route_prep.py 基板 出力.dsn 1`（基板端0.45mmの配線禁止帯を足し、GNDベタを外してDSNを書き出す。基板は保存しない）→ `java -jar freerouting-1.9.0.jar -de x.dsn -do x.ses -mp 40 -mt 0` → `tools/route_import.py 基板 x.ses 基板`
- `-mt 0` は最適化なし。最適化ありだと15分たっても終わらなかった
- GNDベタはSMDパッドに直結、スルーホールだけサーマル
- 配線前の基板は SynthCap-backups/SynthCap_unrouted_80x32.kicad_pcb
