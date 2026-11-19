"""design.py から SynthCap.kicad_pcb を生成する（配線はしない）。
KiCad付属のPythonで実行すること:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/gen_pcb.py

配置方針
  - 表面(F): エンコーダ x4（信号パッドはSMD、MPは貫通穴）、EXTヘッダー、SWDパッド（未実装）
  - 裏面(B): SMD部品すべて（ジャック含む）→ JLCPCBの片面実装で済む
  - ジャックは上辺。プラグ挿入口が上を向く。バレルが基板端から少しはみ出す
  - ジャックの隣り合うすき間と、ジャックの下側にIC・受動部品を詰める（簡易パッカー）
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design  # noqa: E402
import gen_sch  # noqa: E402  （回路図UUIDの計算に使う）

ROOT = os.path.join(HERE, "..")
FPDIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
SRC = os.path.join(ROOT, "SynthCap-backups", "SynthCap_orig.kicad_pcb")
OUT = os.path.join(ROOT, "SynthCap.kicad_pcb")
LAYOUT_SCAD = os.path.join(ROOT, "shell", "layout.scad")

# ---------------------------------------------------------------- 寸法
BOARD_H = 32.0                 # 奥行き
X0, X1 = 85.0, 165.0           # 幅80mm（CardputerZero本体の幅84mmに合わせる）
Y1 = 74.75                     # 下辺（EXTヘッダー側）は固定
Y0 = Y1 - BOARD_H

CORNER_R = 2.0                 # 基板の角丸
# 本体にネジ止めする耳。本体の左端から14mmと70mm（間隔56mm）。基板は本体中央に載るので 2mm ずれる
# 本体側: 幅4.2mmの溝、上面から3.7mm下にM2の下穴(Ø1.6)。耳はØ4、穴Ø2（Cap LoRaの図面）
EAR_X = [X0 - 2.0 + 14.0, X0 - 2.0 + 70.0]
EAR_W = 4.0
EAR_HOLE_Y = 3.7               # 基板の下辺（＝本体の上面）から穴の中心まで
EAR_HOLE_D = 2.1

JX = [93.0, 109.0, 125.0, 141.0, 157.0]            # ジャック中心X（MIDI IN / MIDI OUT / CLOCK / OUT1 / OUT2）
JACK_ORIGIN_Y = Y0 + 0.6                           # 本体前面の位置。バレル先端は2mm手前（基板端から1.4mmはみ出す）
SHAFT_X = [95.0, 115.0, 135.0, 155.0]              # エンコーダのシャフト中心X
EY = Y0 + 7.25                                     # エンコーダ原点（パッドA）のY。MPがジャックのパッドより下になる位置

FRONT = {"J1", "J7", "SW1", "SW2", "SW3", "SW4"}   # それ以外は裏面
FIXED = {
    "J1": (132.625, 68.09, -90),
    "J7": (108.4, 67.6, 90),
    "SW1": (SHAFT_X[0] + 2.5, EY, -90), "SW2": (SHAFT_X[1] + 2.5, EY, -90),
    "SW3": (SHAFT_X[2] + 2.5, EY, -90), "SW4": (SHAFT_X[3] + 2.5, EY, -90),
    "U1": (98.5, 67.0, 0),
}
JACKS = ["J2", "J3", "J4", "J5", "J6"]

# 裏面の部品配置: ref: (中心x, 中心y, 向き)
#   2端子部品の向き = パッド1がある方向 "L" "R" "U" "D"（基板を表から見た座標）
#   それ以外は回転角
# つながる相手の近くに置く（ジャックのすき間、エンコーダMP穴の間、下段）
PLACE = {
    # --- 水晶（U1の左、5/6番ピンの横）
    "Y1": (90.6, 67.5, 90), "C12": (90.6, 64.4, "R"), "C11": (90.6, 70.6, "L"),
    # --- VDDA（FB1 → C4 → C5 → U1 9番）
    "FB1": (87.2, 60.7, "L"), "C4": (90.4, 60.7, "L"), "C5": (91.6, 62.5, "R"),
    # --- リセット、BOOT、LED
    "C10": (86.6, 65.9, "U"), "R1": (86.6, 69.2, "D"),
    "R4": (93.6, 60.7, "R"),
    "D1": (88.0, 73.4, "R"), "R5": (91.4, 73.4, "R"),
    "R3": (98.6, 73.4, "L"), "R2": (101.8, 73.4, "R"),
    # --- U1のバイパスコンデンサ（各電源ピンの角）
    "C8": (95.0, 73.4, "R"), "C6": (102.3, 60.8, "R"), "C7": (105.2, 71.3, "L"), "C9": (105.4, 73.2, "L"),
    # --- USBプルアップ（未実装）、UART保護抵抗（ヘッダーの左）
    "R6": (109.6, 70.0, "R"), "R28": (113.6, 71.0, "R"), "R29": (113.6, 72.8, "R"),
    # --- MIDI IN（MIDI INとMIDI OUTのすき間）: R24 → D3 → U4、出力側はU1の真上
    "R24": (101.0, 44.2, "L"), "D3": (101.0, 46.2, "L"), "U4": (101.0, 51.5, 270),
    "C14": (105.0, 58.6, "L"), "R25": (105.5, 60.8, "R"),
    # --- MIDI OUT
    "R27": (105.0, 56.9, "L"), "R26": (117.0, 47.6, "R"),
    # --- Clock出力（MIDI OUTとCLOCKのすき間。CLOCKのTipのすぐ左）
    "R19": (117.0, 49.8, "R"), "Q1": (117.0, 52.6, 0), "R20": (117.0, 55.2, "L"),
    # --- Clock入力（CLOCKとOUT1のすき間。CLOCKのRingのすぐ右）
    "D2": (133.0, 46.4, "L"), "R21": (133.0, 48.8, "L"), "R22": (133.0, 50.6, "R"),
    "Q2": (133.0, 53.4, 0), "R23": (133.4, 57.6, "L"),
    # --- 出力保護抵抗（各ジャックの端子の横）
    "R9": (137.4, 57.5, "D"), "R15": (149.0, 48.8, "R"), "R12": (149.0, 52.8, "L"), "R18": (163.2, 48.8, "D"),
    # --- 電源（ヘッダーの右）
    "U2": (138.6, 68.5, 270), "C1": (140.4, 62.6, "R"), "C2": (136.6, 62.6, "R"), "C3": (136.4, 60.6, "L"),
    # --- オペアンプ（OUT1/OUT2の下。CV側の端子がジャックを向く）
    "U3": (148.0, 64.8, 270), "C13": (148.0, 60.2, "L"),
    "R7": (144.9, 60.2, "L"), "R8": (144.9, 58.5, "R"),
    "R10": (151.1, 60.2, "R"), "R11": (152.6, 58.4, "L"),
    "R16": (144.9, 69.4, "L"), "R17": (144.9, 71.2, "R"),
    "R13": (151.1, 69.4, "R"), "R14": (151.1, 71.2, "L"),
}
DIRS = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}

TEXTS = [("MIDI IN", JX[0]), ("MIDI OUT", JX[1]), ("CLOCK", JX[2]), ("OUT1", JX[3]), ("OUT2", JX[4])]


def mm(v):
    return pcbnew.FromMM(v)


def to_mm(v):
    return pcbnew.ToMM(v)


def load_fp(fpid):
    lib, name = fpid.split(":")
    d = os.path.join(ROOT, lib + ".pretty") if lib == "SynthCap" else os.path.join(FPDIR, lib + ".pretty")
    d = os.path.abspath(d)
    fp = pcbnew.FootprintLoad(d, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def courtyard_bbox(fp):
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    b = fp.GetCourtyard(layer).BBox()
    if b.GetWidth() == 0:
        b = fp.GetBoundingBox(False)
    return (to_mm(b.GetLeft()), to_mm(b.GetTop()), to_mm(b.GetRight()), to_mm(b.GetBottom()))


def put(fp, x, y, rot, back):
    if back and not fp.IsFlipped():
        fp.SetLayerAndFlip(pcbnew.B_Cu)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def place_center(fp, cx, cy, rot, back):
    """courtyard の中心が (cx, cy) になるように置く"""
    put(fp, 0, 0, rot, back)
    b = courtyard_bbox(fp)
    ox, oy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    fp.SetPosition(pcbnew.VECTOR2I(mm(cx - ox), mm(cy - oy)))


def pack(fps, region, default_rot):
    """棚詰め。大きい部品から左→右、行が埋まったら下へ。"""
    rx0, ry0, rx1, ry1 = region
    items = []
    for ref, fp in fps:
        rot = REGION_ROT.get(ref, default_rot)
        put(fp, 0, 0, rot, True)
        b = courtyard_bbox(fp)
        items.append((ref, fp, rot, b[2] - b[0], b[3] - b[1]))
    items.sort(key=lambda t: -t[3] * t[4])
    x, y, rowh = rx0, ry0, 0.0
    out = {}
    for ref, fp, rot, w, h in items:
        if x + w > rx1 + 1e-6:
            x, y, rowh = rx0, y + rowh + GAP, 0.0
        if y + h > ry1 + 1e-6 or w > (rx1 - rx0) + 1e-6:
            raise RuntimeError("領域に入りません: %s (%.1fx%.1f) 領域=%s" % (ref, w, h, region))
        place_center(fp, x + w / 2, y + h / 2, rot, True)
        out[ref] = (x, y, w, h)
        x += w + GAP
        rowh = max(rowh, h)
    return out


def place_dir(fp, cx, cy, d):
    """2端子部品を、パッド1が d の方向を向くように (cx, cy) に置く"""
    dx, dy = DIRS[d]
    for rot in (0, 90, 180, 270):
        place_center(fp, cx, cy, rot, True)
        p1 = [p for p in fp.Pads() if p.GetNumber() == "1"][0].GetPosition()
        ox, oy = to_mm(p1.x) - cx, to_mm(p1.y) - cy
        if ox * dx + oy * dy > 0.3:
            return
    raise RuntimeError("向きが決まりません: " + fp.GetReference())


def main():
    # 元ファイルからレイヤー・設定だけを残した空の基板を作って読み込む
    src = open(SRC).read()
    i = src.index("\n\t(footprint ")
    j = src.index("\n\t(embedded_fonts")
    tmp = os.path.join(HERE, "_base.kicad_pcb")
    with open(tmp, "w") as f:
        f.write(src[:i] + src[j:])
    board = pcbnew.LoadBoard(tmp)
    os.remove(tmp)

    # 外形: 角丸 + CardputerZero本体にネジ止めする耳（Cap LoRaの図面と本体STLに合わせた）
    def seg(x0, y0, x1, y1):
        sh = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        sh.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
        sh.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetWidth(mm(0.05))
        board.Add(sh)

    def arc(x0, y0, xm, ym, x1, y1):
        sh = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        sh.SetArcGeometry(pcbnew.VECTOR2I(mm(x0), mm(y0)), pcbnew.VECTOR2I(mm(xm), mm(ym)),
                          pcbnew.VECTOR2I(mm(x1), mm(y1)))
        sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetWidth(mm(0.05))
        board.Add(sh)

    r = CORNER_R
    k = r * (1 - 0.70710678)
    seg(X0 + r, Y0, X1 - r, Y0)
    arc(X1 - r, Y0, X1 - k, Y0 + k, X1, Y0 + r)
    seg(X1, Y0 + r, X1, Y1 - r)
    arc(X1, Y1 - r, X1 - k, Y1 - k, X1 - r, Y1)
    x = X1 - r
    for ex in sorted(EAR_X, reverse=True):
        hw = EAR_W / 2
        seg(x, Y1, ex + hw, Y1)
        seg(ex + hw, Y1, ex + hw, Y1 + EAR_HOLE_Y)
        arc(ex + hw, Y1 + EAR_HOLE_Y, ex, Y1 + EAR_HOLE_Y + hw, ex - hw, Y1 + EAR_HOLE_Y)
        seg(ex - hw, Y1 + EAR_HOLE_Y, ex - hw, Y1)
        x = ex - hw
        hole = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_CIRCLE)
        hole.SetStart(pcbnew.VECTOR2I(mm(ex), mm(Y1 + EAR_HOLE_Y)))
        hole.SetEnd(pcbnew.VECTOR2I(mm(ex + EAR_HOLE_D / 2), mm(Y1 + EAR_HOLE_Y)))
        hole.SetLayer(pcbnew.Edge_Cuts)
        hole.SetWidth(mm(0.05))
        board.Add(hole)
    seg(x, Y1, X0 + r, Y1)
    arc(X0 + r, Y1, X0 + k, Y1 - k, X0, Y1 - r)
    seg(X0, Y1 - r, X0, Y0 + r)
    arc(X0, Y0 + r, X0 + k, Y0 + k, X0 + r, Y0)

    # ネット
    netnames = sorted({n for p in design.P for n in p["pins"].values() if n})
    nets = {}
    for n in netnames:
        ni = pcbnew.NETINFO_ITEM(board, "/" + n)  # 回路図のローカルラベル名に合わせる
        board.Add(ni)
        nets["/" + n] = ni
        nets[n] = ni

    # 未接続ピンは回路図と同じ名前の個別ネットにする（パリティチェック用）
    for p in design.P:
        names = gen_sch.pin_names(p["lib"], p["unit"])
        for pn, n in list(p["pins"].items()):
            if n is None and not p["lib"].startswith("power:"):
                nm = names.get(pn, "")
                key = "unconnected-(%s-%sPad%s)" % (p["ref"], nm + "-" if nm else "", pn)
                ni = pcbnew.NETINFO_ITEM(board, key)
                board.Add(ni)
                nets[key] = ni
                p.setdefault("nc_nets", {})[pn] = key

    # 部品（複数ユニットはまとめる）
    parts = {}
    for p in design.P:
        if p["lib"].startswith("power:"):
            continue
        q = parts.setdefault(p["ref"], dict(p, pins={}, uuid=str(gen_sch.uid(p["ref"], p["unit"]))))
        q["pins"].update(p["pins"])
        q["pins"].update(p.get("nc_nets", {}))
        if p["unit"] == 1:
            q["uuid"] = str(gen_sch.uid(p["ref"], 1))

    fps = {}
    for ref, p in sorted(parts.items()):
        fp = load_fp(p["fp"])
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + p["uuid"]))
        if p["lcsc"]:
            fp.SetField("LCSC", p["lcsc"])
            fp.GetField("LCSC").SetVisible(False)
        fp.SetDNP(p["dnp"])
        fp.SetExcludedFromBOM(not p["bom"])
        for pad in fp.Pads():
            pn = pad.GetNumber()
            if pn in p["pins"] and p["pins"][pn]:
                pad.SetNet(nets[p["pins"][pn]])
        board.Add(fp)
        fps[ref] = fp

    # ---- 固定位置
    for ref, (x, y, rot) in FIXED.items():
        put(fps[ref], x, y, rot, ref not in FRONT)

    # ジャック: プラグ挿入口（S端子側）が上を向く回転を探す
    for ref, x in zip(JACKS, JX):
        fp = fps[ref]
        for rot in (0, 90, 180, 270):
            put(fp, x, JACK_ORIGIN_Y, rot, True)
            sy = [to_mm(pad.GetPosition().y) for pad in fp.Pads() if pad.GetName() == "S"]
            ty = [to_mm(pad.GetPosition().y) for pad in fp.Pads() if pad.GetName() == "T"][0]
            if max(sy) < ty - 5:
                break
        else:
            raise RuntimeError("ジャックの向きが決まりません")

    # ---- 裏面の部品
    for ref, (cx, cy, d) in PLACE.items():
        if isinstance(d, str):
            place_dir(fps[ref], cx, cy, d)
        else:
            place_center(fps[ref], cx, cy, d, True)

    missing = set(parts) - set(FIXED) - set(JACKS) - set(PLACE)
    assert not missing, "配置未定義: %s" % sorted(missing)

    # 部品番号は製造図レイヤーへ（高密度なのでシルクには出さない）
    for ref, fp in fps.items():
        fp.Reference().SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)

    # 両面GNDベタ
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(nets["/GND"])
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)):
            ol.Append(mm(x), mm(y))
        z.SetLocalClearance(mm(0.3))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetZoneName("GND_" + ("F" if layer == pcbnew.F_Cu else "B"))
        board.Add(z)

    # シルク（表面）: ジャック名、基板名
    for txt, x in TEXTS:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        t.SetTextThickness(mm(0.15))
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(Y0 + 1.3)))
        board.Add(t)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("SynthCap v0.1")
    t.SetLayer(pcbnew.B_SilkS)
    t.SetMirrored(True)
    t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
    t.SetTextThickness(mm(0.15))
    t.SetPosition(pcbnew.VECTOR2I(mm(104), mm(Y1 - 1.0)))
    board.Add(t)

    board.Save(OUT)
    print("saved", os.path.abspath(OUT), len(parts), "footprints", len(nets), "nets, board %gx%g" % (X1 - X0, BOARD_H))

    # シェル用のレイアウトパラメータ
    d1 = fps["D1"].GetPosition()
    pads = list(fps["J1"].Pads())
    hx0 = min(to_mm(p.GetPosition().x) for p in pads) - 1.0
    hx1 = max(to_mm(p.GetPosition().x) for p in pads) + 1.0
    sy = EY + 7.5
    with open(LAYOUT_SCAD, "w") as f:
        f.write("// gen_pcb.py が自動生成。座標は基板左下を原点、Yは上向き（ジャック側が +Y）\n")
        f.write("pcb_w = %g;\npcb_h = %g;\n" % (X1 - X0, BOARD_H))
        f.write("jack_x = [%s];\n" % ", ".join("%g" % (x - X0) for x in JX))
        f.write("enc_x = [%s];\n" % ", ".join("%g" % (x - X0) for x in SHAFT_X))
        f.write("enc_y = %.3f;\n" % (Y1 - sy))
        f.write("led_xy = [%.3f, %.3f];\n" % (to_mm(d1.x) - X0, Y1 - to_mm(d1.y)))
        f.write("hdr_x0 = %.3f;\nhdr_x1 = %.3f;\n" % (hx0 - X0, hx1 - X0))
        f.write("ear_x = [%s];\near_w = %g;\ncorner_r = %g;\n" % (", ".join("%g" % (x - X0) for x in EAR_X), EAR_W, CORNER_R))
    print("wrote", LAYOUT_SCAD)


if __name__ == "__main__":
    main()
