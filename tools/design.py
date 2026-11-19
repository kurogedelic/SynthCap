"""SynthCap 回路定義（単一ソース）。
gen_sch.py（回路図）と gen_pcb.py（基板）の両方がこのファイルを読む。
KiCad付属のPython 3.9でも動くように、標準ライブラリだけを使う。

構成: CardputerZero Cap / CH32V303CBT6 / USB MIDI（EXTの1・3番ピン）
     CV x2（内蔵DAC → LMV324で1.5倍 → 0〜4.9V）、Gate x2、Clock入出力
     MIDI入出力（TRS Type A、3.3V）、EC12Eエンコーダ x4
"""

# 回路図シンボルの部品定義
# (ref, lib_id, value, footprint, lcsc, sch_xy, {pin: net}, opts)
# unit: 複数ユニットを持つシンボルのユニット番号（ref が同じでも別エントリ）
# opts: dnp / bom=False（手はんだ部品）/ unit

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C805 = "Capacitor_SMD:C_0805_2012Metric"
FP_JACK = "SynthCap:Jack_3.5mm_SHOUHAN_PJ-342_SMD"
FP_ENC = "SynthCap:RotaryEncoder_Alps_EC12E-Switch_Vertical_H20mm_SMDpads"

LCSC_R = {"10": "C22859", "33": "C23140", "220": "C22962", "1k": "C21190",
          "1.5k": "C22843", "4.7k": "C23162", "10k": "C25804", "20k": "C4184",
          "47k": "C25819", "100k": "C25803"}
LCSC_C = {"15pF": "C1644", "22pF": "C1653", "100nF": "C14663", "1uF": "C15849", "10uF": "C15850"}

P = []  # 全部品


def add(ref, lib, value, fp, lcsc, xy, pins, **o):
    P.append(dict(ref=ref, lib=lib, value=value, fp=fp, lcsc=lcsc, xy=xy,
                  pins=pins, unit=o.get("unit", 1), dnp=o.get("dnp", False),
                  bom=o.get("bom", True), rot=o.get("rot", 0)))


def R(ref, val, a, b, xy, **o):
    add(ref, "Device:R", val, FP_R, LCSC_R[val], xy, {"1": a, "2": b}, **o)


def C(ref, val, a, b, xy, **o):
    fp = FP_C805 if val == "10uF" else FP_C
    add(ref, "Device:C", val, fp, LCSC_C[val], xy, {"1": a, "2": b}, **o)


# ---------------------------------------------------------------- 電源
# EXT pin6 5VOUT → +5V（本体側のロードスイッチPYG13_HAT_ENで給電制御）
# EXT pin2 5VIN はCap→本体方向の入力なので未接続
add("J1", "Connector_Generic:Conn_02x07_Odd_Even", "CardputerZero EXT",
    "Connector_PinHeader_2.54mm:PinHeader_2x07_P2.54mm_Horizontal", "", (35, 45),
    {"1": "USB_DP", "2": None, "3": "USB_DM", "4": "GND", "5": "NRST", "6": "+5V",
     "7": None, "8": None, "9": None, "10": None, "11": "EXT_G9", "12": "EXT_P12",
     "13": None, "14": "EXT_P14"}, bom=False)
add("U2", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3",
    "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "C6186", (90, 35),
    {"1": "GND", "2": "+3V3", "3": "+5V"})
C("C1", "10uF", "+5V", "GND", (75, 50))
C("C2", "10uF", "+3V3", "GND", (105, 50))
C("C3", "100nF", "+3V3", "GND", (115, 50))
add("FB1", "Device:FerriteBead_Small", "BLM18PG121SN1D", "Inductor_SMD:L_0603_1608Metric",
    "C14709", (130, 35), {"1": "+3V3", "2": "VDDA"})
C("C4", "1uF", "VDDA", "GND", (140, 50))
C("C5", "100nF", "VDDA", "GND", (150, 50))
for i, (n, xy) in enumerate([("+5V", (75, 70)), ("GND", (90, 70)), ("VDDA", (105, 70))]):
    add("#FLG%02d" % (i + 1), "power:PWR_FLAG", "PWR_FLAG", "", "", xy, {"1": n}, bom=False)

# ---------------------------------------------------------------- MCU
MCU = {
    "1": "+3V3",  # VBAT
    "2": "LED", "3": None, "4": None,
    "5": "OSC_IN", "6": "OSC_OUT", "7": "NRST",
    "8": "GND", "9": "VDDA",
    "10": "ENC3_A", "11": "ENC3_B",
    "12": "CM0_RXD",   # PA2 USART2_TX → CM0 UART_RXD(G15)
    "13": "CM0_TXD",   # PA3 USART2_RX ← CM0 UART_TXD(G14)
    "14": "DAC1", "15": "DAC2",
    "16": "ENC1_A", "17": "ENC1_B",
    "18": "GATE1_D", "19": "GATE2_D", "20": "BOOT1",
    "21": "MIDI_TX", "22": "MIDI_RX",  # USART3
    "23": "GND", "24": "+3V3",
    "25": "ENC1_SW", "26": "ENC2_SW", "27": "ENC3_SW", "28": "ENC4_SW",
    "29": "ENC4_A", "30": "ENC4_B",  # PA8/PA9 TIM1
    "31": None,
    "32": "USB_DM", "33": "USB_DP",
    "34": "SWDIO", "35": "GND", "36": "+3V3", "37": "SWCLK",
    "38": None,
    "39": None,  # PB3（未使用）
    "40": None, "41": None,
    "42": "ENC2_A", "43": "ENC2_B",  # PB6/PB7 TIM4
    "44": "BOOT0",
    "45": "CLKO_D", "46": "CLK_IN",  # PB8/PB9
    "47": "GND", "48": "+3V3",
}
add("U1", "MCU_WCH_RiscV:CH32V30xCxTx", "CH32V303CBT6", "Package_QFP:LQFP-48_7x7mm_P0.5mm",
    "C7494374", (200, 120), MCU)
C("C6", "100nF", "+3V3", "GND", (160, 60))
C("C7", "100nF", "+3V3", "GND", (170, 60))
C("C8", "100nF", "+3V3", "GND", (180, 60))
C("C9", "10uF", "+3V3", "GND", (190, 60))
C("C10", "100nF", "NRST", "GND", (150, 95))
# NRST: EXT 5番(G22)からCM0が駆動する。本体側のレベル変換ICは弱い出力なので、プルアップは100kと弱くする
R("R1", "100k", "+3V3", "NRST", (140, 95))
# BOOT0: CM0のG9（SPI0_MISO、起動時は本体側でプルダウン）で書き込みモードに入れる
R("R2", "1k", "EXT_G9", "BOOT0", (140, 120))
R("R3", "100k", "BOOT0", "GND", (150, 120))
R("R4", "10k", "BOOT1", "GND", (260, 100))
add("Y1", "Device:Crystal_GND24", "8MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "C367183", (145, 150), {"1": "OSC_IN", "2": "GND", "3": "OSC_OUT", "4": "GND"})
C("C11", "15pF", "OSC_IN", "GND", (135, 165))
C("C12", "15pF", "OSC_OUT", "GND", (155, 165))
R("R5", "1k", "LED", "LED_K", (140, 75))
add("D1", "Device:LED", "LED", "LED_SMD:LED_0603_1608Metric", "C2286", (150, 75),
    {"1": "LED_K", "2": "+3V3"})  # PC13がLowで点灯
# USB D+プルアップ（CH32V303は内蔵プルアップあり。念のための未実装パッド）
R("R6", "1.5k", "+3V3", "USB_DP", (260, 135), dnp=True)
# SWD（WCH-LinkE）用パッド。未実装
add("J7", "Connector_Generic:Conn_01x04", "SWD", "Connector_PinHeader_1.27mm:PinHeader_1x04_P1.27mm_Vertical",
    "", (270, 160), {"1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "GND"}, dnp=True, bom=False)

# UART（予備）: 公式の写真（Capインターフェース図）と回路図では、MISOの隣（12番）がG14=CM0のTX、
# CS1の隣（14番）がG15=CM0のRX。ドキュメントの表だけ逆になっている。写真と回路図に合わせる。
# 念のため両方に1kを直列に入れて、逆でも壊れないようにしている
R("R28", "1k", "EXT_P12", "CM0_TXD", (60, 100))
R("R29", "1k", "EXT_P14", "CM0_RXD", (60, 115))

# ---------------------------------------------------------------- CV / Gate 出力
# LMV324: 非反転増幅で1.5倍（Rf=10k, Rg=20k）。電源は+5V
OPA = [("A", 1, "DAC1", "CV1", 300, 30), ("B", 2, "DAC2", "CV2", 300, 70),
       ("C", 3, "GATE1_D", "GATE1", 300, 110), ("D", 4, "GATE2_D", "GATE2", 300, 150)]
OPA_PINS = {1: ("3", "2", "1"), 2: ("5", "6", "7"), 3: ("10", "9", "8"), 4: ("12", "13", "14")}
rn = 7
for name, unit, inp, out, x, y in OPA:
    pp, pn, po = OPA_PINS[unit]
    add("U3", "Amplifier_Operational:LMV324", "LMV324IDR", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        "C7974", (x, y), {pp: inp, pn: out + "_FB", po: out + "_O"}, unit=unit)
    R("R%d" % rn, "10k", out + "_O", out + "_FB", (x + 20, y)); rn += 1
    R("R%d" % rn, "20k", out + "_FB", "GND", (x + 30, y)); rn += 1
    R("R%d" % rn, "220", out + "_O", out, (x + 40, y)); rn += 1   # 出力保護
add("U3", "Amplifier_Operational:LMV324", "LMV324IDR", "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "C7974", (300, 190), {"4": "+5V", "11": "GND"}, unit=5)
C("C13", "100nF", "+5V", "GND", (315, 190))
# rn == 19

# ---------------------------------------------------------------- Clock 入出力
# 出力: PB8 → NPN → 1kプルアップ(+5V)。ファーム側で論理反転して出す
R("R19", "1k", "CLKO_D", "Q1_B", (40, 230))
add("Q1", "Transistor_BJT:MMBT3904", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", "C20526",
    (55, 230), {"1": "Q1_B", "2": "GND", "3": "CLK_OUT"})
R("R20", "1k", "+5V", "CLK_OUT", (70, 230))
# 入力: 0〜10V、負電圧にも耐える。約1.2Vでスイッチ、PB9には反転して入る
R("R21", "100k", "CLK_IN_J", "Q2_B", (90, 230))
R("R22", "100k", "Q2_B", "GND", (100, 230))
add("D2", "Device:D", "1N4148W", "Diode_SMD:D_SOD-123", "C81598", (110, 245),
    {"1": "Q2_B", "2": "GND"})
add("Q2", "Transistor_BJT:MMBT3904", "MMBT3904", "Package_TO_SOT_SMD:SOT-23", "C20526",
    (125, 230), {"1": "Q2_B", "2": "GND", "3": "CLK_IN"})
R("R23", "10k", "+3V3", "CLK_IN", (140, 230))

# ---------------------------------------------------------------- MIDI（TRS Type A）
# Type A: Tip = DIN pin5（電流シンク側）、Ring = DIN pin4（電流ソース側）
# IN: Ring → 220Ω → フォトカプラLED → Tip
R("R24", "220", "MIDI_IN_R", "OPTO_A", (40, 270))
add("D3", "Device:D", "1N4148W", "Diode_SMD:D_SOD-123", "C81598", (55, 285),
    {"1": "OPTO_A", "2": "MIDI_IN_T"})
add("U4", "Isolator:TLP2310", "TLP2362", "Package_SO:SO-5-6_4.55x3.7mm_P1.27mm", "C37658",
    (75, 270), {"1": "OPTO_A", "3": "MIDI_IN_T", "4": "GND", "5": "MIDI_RX", "6": "+3V3"})
R("R25", "4.7k", "+3V3", "MIDI_RX", (95, 270))   # TLP2362はオープンコレクタ出力
C("C14", "100nF", "+3V3", "GND", (105, 270))
# OUT（3.3V版の推奨値: ソース側33Ω、シンク側10Ω）
R("R26", "33", "+3V3", "MIDI_OUT_R", (130, 270))
R("R27", "10", "MIDI_TX", "MIDI_OUT_T", (140, 270))

# ---------------------------------------------------------------- ジャック（裏面、手はんだ）
JACKS = [("J2", "MIDI IN", {"T": "MIDI_IN_T", "R": "MIDI_IN_R", "S": None}),
         ("J3", "MIDI OUT", {"T": "MIDI_OUT_T", "R": "MIDI_OUT_R", "S": "GND"}),
         ("J4", "CLOCK IO", {"T": "CLK_OUT", "R": "CLK_IN_J", "S": "GND"}),
         ("J5", "OUT1 CV/GATE", {"T": "CV1", "R": "GATE1", "S": "GND"}),
         ("J6", "OUT2 CV/GATE", {"T": "CV2", "R": "GATE2", "S": "GND"})]
for i, (ref, val, pins) in enumerate(JACKS):
    add(ref, "Connector_Audio:AudioJack3", val, FP_JACK, "C668606", (385, 30 + i * 30), pins)

# ---------------------------------------------------------------- エンコーダ（手はんだ）
for i in range(4):
    n = i + 1
    add("SW%d" % n, "Device:RotaryEncoder_Switch_MP", "EC12E", FP_ENC, "",
        (200 + i * 45, 250),
        {"A": "ENC%d_A" % n, "B": "ENC%d_B" % n, "C": "GND", "S1": "ENC%d_SW" % n,
         "S2": "GND", "MP": "GND"}, bom=False)
