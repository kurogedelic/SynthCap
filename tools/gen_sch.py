"""design.py から SynthCap.kicad_sch を生成する。
配線は描かず、各ピン端にネットラベルを置いて接続する（ラベル方式）。
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from sexpr import Q, dump, find, findall, parse  # noqa: E402
import design  # noqa: E402

SYMDIR = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
ROOT_UUID = "75f5d6c1-e47f-48e9-8ddf-ef27851330ea"  # 既存の回路図のUUIDを引き継ぐ
OUT = os.path.join(os.path.dirname(__file__), "..", "SynthCap.kicad_sch")
NS = uuid.UUID("6b1d6a64-1d0e-4f43-9b7e-5a1c0de5ca9a")
G = 1.27


def uid(*k):
    return Q(str(uuid.uuid5(NS, "/".join(map(str, k)))))


def snap(v):
    return round(round(v / G) * G, 4)


_libs = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libs:
        with open(os.path.join(SYMDIR, lib + ".kicad_sym")) as f:
            tree = parse(f.read())[0]
        _libs[lib] = {e[1]: e for e in findall(tree, "symbol")}
    syms = _libs[lib]
    sym = syms[name]
    ext = find(sym, "extends")
    if ext:
        parent = lib_symbol(lib + ":" + ext[1])
        pname = parent[1].split(":")[1]
        props = findall(sym, "property")
        new = [e for e in parent if not (isinstance(e, list) and e[0] == "property")]
        # 子のプロパティを親の位置に挿入
        idx = next(i for i, e in enumerate(new) if isinstance(e, list) and e[0] == "symbol")
        new = new[:idx] + props + new[idx:]
        new[1] = Q(lib + ":" + name)
        out = []
        for e in new:
            if isinstance(e, list) and e[0] == "symbol":
                e = list(e)
                e[1] = Q(e[1].replace(pname + "_", name + "_", 1))
            out.append(e)
        return out
    s = list(sym)
    s[1] = Q(lib + ":" + name)
    return s


def sym_pins(libsym, unit):
    name = libsym[1].split(":")[1]
    pins = []
    for sub in findall(libsym, "symbol"):
        suffix = sub[1][len(name) + 1:]
        u, st = (int(v) for v in suffix.split("_"))
        if u not in (0, unit) or st not in (0, 1):
            continue
        for p in findall(sub, "pin"):
            at = find(p, "at")
            num = find(p, "number")[1]
            pins.append((str(num), float(at[1]), float(at[2]), int(float(at[3]))))
    return pins


def pin_names(lib_id, unit):
    ls = lib_symbol(lib_id)
    name = ls[1].split(":")[1]
    out = {}
    for sub in findall(ls, "symbol"):
        u, st = (int(v) for v in sub[1][len(name) + 1:].split("_"))
        if u not in (0, unit) or st not in (0, 1):
            continue
        for p in findall(sub, "pin"):
            nm = find(p, "name")[1]
            out[str(find(p, "number")[1])] = "" if nm in ("~", "") else str(nm)
    return out


def font(hide=False, justify=None):
    e = ["effects", ["font", ["size", 1.27, 1.27]]]
    if justify:
        e.append(["justify"] + justify)
    if hide:
        e.append(["hide", "yes"])
    return e


LABEL_DIR = {0: (180, ["right", "bottom"]), 180: (0, ["left", "bottom"]),
             90: (270, ["right", "bottom"]), 270: (90, ["left", "bottom"])}


def main():
    items = []
    used = {}
    labels = {}
    ncs = set()
    for p in design.P:
        lid = p["lib"]
        if lid not in used:
            used[lid] = lib_symbol(lid)
        ls = used[lid]
        X, Y = snap(p["xy"][0]), snap(p["xy"][1])
        su = uid(p["ref"], p["unit"])
        p["sch_uuid"] = str(su)
        pins = sym_pins(ls, p["unit"])
        pin_nums = {pn for pn, *_ in pins}
        unknown = set(p["pins"]) - pin_nums
        assert not unknown, (p["ref"], unknown)
        missing = pin_nums - set(p["pins"])
        assert not missing, (p["ref"], p["unit"], missing)
        is_power = lid.startswith("power:")
        props = [
            ["property", Q("Reference"), Q(p["ref"]), ["at", X + 2.54, Y - 1.27, 0],
             font(hide=is_power, justify=["left"])],
            ["property", Q("Value"), Q(p["value"]), ["at", X + 2.54, Y + 1.27, 0],
             font(justify=["left"])],
            ["property", Q("Footprint"), Q(p["fp"]), ["at", X, Y, 0], font(hide=True)],
            ["property", Q("Datasheet"), Q(""), ["at", X, Y, 0], font(hide=True)],
        ]
        if p["lcsc"]:
            props.append(["property", Q("LCSC"), Q(p["lcsc"]), ["at", X, Y, 0], font(hide=True)])
        sym = ["symbol", ["lib_id", Q(lid)], ["at", X, Y, 0], ["unit", p["unit"]],
               ["exclude_from_sim", "no"], ["in_bom", "yes" if p["bom"] else "no"],
               ["on_board", "no" if is_power else "yes"], ["dnp", "yes" if p["dnp"] else "no"],
               ["uuid", su]] + props
        for pn, px, py, pa in pins:
            sym.append(["pin", Q(pn), ["uuid", uid(p["ref"], p["unit"], "pin", pn)]])
        sym.append(["instances", ["project", Q("SynthCap"),
                                  ["path", Q("/" + ROOT_UUID), ["reference", Q(p["ref"])],
                                   ["unit", p["unit"]]]]])
        items.append(sym)
        for pn, px, py, pa in pins:
            net = p["pins"][pn]
            pt = (round(X + px, 4), round(Y - py, 4))
            if net is None:
                ncs.add(pt)
            else:
                prev = labels.get(pt)
                assert prev is None or prev[0] == net, (p["ref"], pn, prev, net)
                labels[pt] = (net, pa)

    for (x, y), (net, pa) in sorted(labels.items()):
        ang, just = LABEL_DIR[pa]
        items.append(["label", Q(net), ["at", x, y, ang], ["fields_autoplaced", "yes"],
                      font(justify=just), ["uuid", uid("label", x, y)]])
    for x, y in sorted(ncs):
        items.append(["no_connect", ["at", x, y], ["uuid", uid("nc", x, y)]])

    sch = ["kicad_sch", ["version", "20250114"], ["generator", Q("eeschema")],
           ["generator_version", Q("9.0")], ["uuid", Q(ROOT_UUID)], ["paper", Q("A3")],
           ["title_block", ["title", Q("SynthCap - CardputerZero Cap")],
            ["rev", Q("0.1")], ["comment", 1, Q("CH32V303CBT6 / USB MIDI / CV x2 / Gate x2 / Clock / TRS MIDI")],
            ["comment", 2, Q("tools/design.py から自動生成")]],
           ["lib_symbols"] + list(used.values())] + items + \
          [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]
    with open(OUT, "w") as f:
        f.write(dump(sch) + "\n")
    print("wrote", os.path.abspath(OUT), len(design.P), "symbols,", len(labels), "labels,", len(ncs), "NC")


if __name__ == "__main__":
    main()
