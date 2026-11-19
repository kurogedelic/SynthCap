"""kicad-cli の出力を JLCPCB PCBA 用の BOM / CPL 形式に変換する。
  kicad-cli pcb export pos ... -o jlcpcb/pos_raw.csv
  kicad-cli sch export bom ... -o jlcpcb/bom_raw.csv
  python3 tools/jlc_export.py
"""
import csv
import os

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jlcpcb")

with open(os.path.join(D, "bom_raw.csv")) as f, open(os.path.join(D, "SynthCap_BOM_JLC.csv"), "w", newline="") as g:
    w = csv.writer(g)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for r in csv.DictReader(f):
        refs = []
        for part in r["Reference"].split(","):
            if "-" in part:  # "C5-C8" を展開
                a, b = part.split("-")
                pre = a.rstrip("0123456789")
                refs += [pre + str(i) for i in range(int(a[len(pre):]), int(b[len(pre):]) + 1)]
            else:
                refs.append(part)
        w.writerow([r["Value"], ",".join(refs), r["Footprint"].split(":")[1], r["LCSC"]])

with open(os.path.join(D, "pos_raw.csv")) as f, open(os.path.join(D, "SynthCap_CPL_JLC.csv"), "w", newline="") as g:
    w = csv.writer(g)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in csv.DictReader(f):
        w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm", "Top" if r["Side"] == "top" else "Bottom",
                    "%g" % float(r["Rot"])])
print("wrote", D)
