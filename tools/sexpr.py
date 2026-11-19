"""最小限のS式パーサ/シリアライザ（KiCadファイル用）。"""
import re

_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


class Q(str):
    """クォート付き文字列"""


def parse(s):
    stack = [[]]
    pos = 0
    n = len(s)
    while pos < n:
        m = _tok.match(s, pos)
        if not m:
            if s[pos:].strip() == "":
                break
            raise ValueError("parse error at %d" % pos)
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            x = stack.pop()
            stack[-1].append(x)
        elif m.group(3) is not None:
            stack[-1].append(Q(m.group(3)[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        else:
            stack[-1].append(m.group(4))
    return stack[0]


def dump(x, ind=0):
    if isinstance(x, list):
        if not x:
            return "()"
        simple = all(not isinstance(e, list) for e in x)
        if simple:
            return "(" + " ".join(dump(e) for e in x) + ")"
        out = "(" + dump(x[0])
        for e in x[1:]:
            if isinstance(e, list):
                out += "\n" + "\t" * (ind + 1) + dump(e, ind + 1)
            else:
                out += " " + dump(e)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(x, Q):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(x, float):
        s = ("%.4f" % x).rstrip("0").rstrip(".")
        return "0" if s == "-0" else s
    return str(x)


def find(x, key):
    for e in x:
        if isinstance(e, list) and e and e[0] == key:
            return e
    return None


def findall(x, key):
    return [e for e in x if isinstance(e, list) and e and e[0] == key]
