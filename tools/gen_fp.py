"""プロジェクト専用フットプリント（SynthCap.pretty）を生成する。
  - PJ-342（SHOU HAN、C668606）3.5mm 6ピンSMDステレオジャック
      寸法の出典: docs/PJ-342_datasheet_C668606.pdf 1ページ目「PCB 端子寸法図 TOP VIEW」
      原点 = 本体前面（プラグ挿入側）の中心、プラグは -X 側から入る。バレルは x=-2 まで突き出す
      端子: 3=Tip、6=Ring、2・5=Sleeve（挿入口に最も近い2本）、4・7=検出スイッチ（未使用）
  - EC12E（KiCad標準）の信号パッドだけをSMD化したもの。MP（取り付け足）は貫通穴のまま
"""
import os
import re

KICAD_FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SynthCap.pretty")

HDR = '''(footprint "%s"
	(version 20260206)
	(generator "pcbnew")
	(generator_version "10.0")
	(layer "F.Cu")
	(descr "%s")
	(tags "%s")
	(property "Reference" "REF**"
		(at 5 -6 0)
		(layer "F.SilkS")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(property "Value" "%s"
		(at 5 6 0)
		(layer "F.Fab")
		(effects
			(font
				(size 1 1)
				(thickness 0.15)
			)
		)
	)
	(attr smd)
'''


MODEL = '''	(model "${KIPRJMOD}/SynthCap.3dshapes/%s"
		(offset
			(xyz %s)
		)
		(scale
			(xyz %s)
		)
		(rotate
			(xyz %s)
		)
	)
'''


def rect(x0, y0, x1, y1, layer, w):
    return '''	(fp_rect
		(start %g %g)
		(end %g %g)
		(stroke
			(width %g)
			(type solid)
		)
		(fill no)
		(layer "%s")
	)
''' % (x0, y0, x1, y1, w, layer)


def smd(name, x, y, w, h):
    return '''	(pad "%s" smd rect
		(at %g %g)
		(size %g %g)
		(layers "F.Cu" "F.Paste" "F.Mask")
	)
''' % (name, x, y, w, h)


def npth(x, y, d):
    return '''	(pad "" np_thru_hole circle
		(at %g %g)
		(size %g %g)
		(drill %g)
		(layers "*.Cu" "*.Mask")
	)
''' % (x, y, d, d, d)


def jack():
    name = "Jack_3.5mm_SHOUHAN_PJ-342_SMD"
    s = HDR % (name, "SHOU HAN PJ-342 3.5mm stereo jack, 6-pin SMD, horizontal (docs/PJ-342_datasheet_C668606.pdf)",
               "jack audio 3.5mm SMD PJ-342", name)
    s += rect(0, -3.2, 12, 3.2, "F.Fab", 0.1)          # 本体 12 x 6.4
    s += rect(-2, -2.5, 0, 2.5, "F.Fab", 0.1)          # バレル（突き出し2mm、径約5）
    s += rect(-2.3, -4.85, 12.45, 4.85, "F.CrtYd", 0.05)
    s += '''	(fp_line
		(start -2.3 -4.85)
		(end -2.3 4.85)
		(stroke
			(width 0.2)
			(type solid)
		)
		(layer "F.SilkS")
	)
'''
    # (名前, x, y, 幅, 高さ)   y はTOP VIEWの下向きが+
    for n, x, y, w, h in (("S", 2.2, -3.6, 1.5, 2.0),   # 端子2
                          ("T", 9.5, -3.6, 1.5, 2.0),   # 端子3
                          ("", 11.5, -3.3, 1.5, 2.6),   # 端子4（Tip検出スイッチ）
                          ("S", 2.2, 3.6, 1.5, 2.0),    # 端子5
                          ("R", 5.5, 3.6, 1.5, 2.0),    # 端子6
                          ("", 11.0, 3.6, 1.5, 2.0)):   # 端子7（Ring検出スイッチ）
        s += smd(n, x, y, w, h)
    s += npth(2.4, 0, 1.5) + npth(9.4, 0, 1.5)
    # 簡易3Dモデル（VRMLは0.1inch単位なので 1/2.54 倍する）
    s += MODEL % ("PJ-342.wrl", "0 0 0", "0.3937 0.3937 0.3937", "0 0 0")
    s += ")\n"
    return name, s


def encoder():
    name = "RotaryEncoder_Alps_EC12E-Switch_Vertical_H20mm_SMDpads"
    s = open(os.path.join(KICAD_FP, "Rotary_Encoder.pretty",
                          "RotaryEncoder_Alps_EC12E-Switch_Vertical_H20mm.kicad_mod")).read()
    s = s.replace('(footprint "RotaryEncoder_Alps_EC12E-Switch_Vertical_H20mm"', '(footprint "%s"' % name, 1)
    s = re.sub(r'\n\t\(model .*?\n\t\)\n', "\n", s, flags=re.S)       # 3Dモデル参照（絶対パス）を除去
    # プロジェクト内にコピーしたモデルを、元と同じ位置合わせで付け直す
    s = s.rstrip()[:-1].rstrip() + "\n" + MODEL % ("EC11E-05SW.STEP", "7.5 -2 -12", "1 1 1", "-0 -0 90") + ")\n"
    s = re.sub(r'\t\(property "Value" "[^"]*"', '\t(property "Value" "%s"' % name, s, count=1)

    def conv(m):
        b = m.group(0)
        b = re.sub(r'thru_hole (rect|circle)', 'smd rect', b, count=1)
        b = re.sub(r'\t\t\(drill [^\n]*\n', '', b)
        b = b.replace('(layers "*.Cu" "*.Mask")', '(layers "F.Cu" "F.Paste" "F.Mask")')
        b = re.sub(r'\t\t\(remove_unused_layers no\)\n', '', b)
        b = re.sub(r'\t\t\(zone_layer_connections\n.*?\n\t\t\)\n', '', b, flags=re.S)
        return b
    s = re.sub(r'\t\(pad "(?:A|B|C|S1|S2)" thru_hole .*?\n\t\)\n', conv, s, flags=re.S)
    s = s.replace("(attr through_hole)", "(attr through_hole)")
    return name, s


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, text in (jack(), encoder()):
        with open(os.path.join(OUT, name + ".kicad_mod"), "w") as f:
            f.write(text)
        print("wrote", name)
    tbl = os.path.join(os.path.dirname(OUT), "fp-lib-table")
    with open(tbl, "w") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "SynthCap")(type "KiCad")'
                '(uri "${KIPRJMOD}/SynthCap.pretty")(options "")(descr "SynthCap project footprints"))\n)\n')
    print("wrote", tbl)


if __name__ == "__main__":
    main()
