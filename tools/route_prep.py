import sys, pcbnew
src, dsn, nozone = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
b = pcbnew.LoadBoard(src)
mm = pcbnew.FromMM
X0, X1, Y0, Y1 = 85.0, 165.0, 42.75, 74.75
W, T = 0.45, 2.7
def keep(pts):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(z)
keep([(X0,Y0),(X1,Y0),(X1,Y0+W),(X0,Y0+W)]); keep([(X0,Y1-W),(X1,Y1-W),(X1,Y1),(X0,Y1)])
keep([(X0,Y0),(X0+W,Y0),(X0+W,Y1),(X0,Y1)]); keep([(X1-W,Y0),(X1,Y0),(X1,Y1),(X1-W,Y1)])
for cx, sx in ((X0,1),(X1,-1)):
    for cy, sy in ((Y0,1),(Y1,-1)):
        keep([(cx,cy),(cx+sx*T,cy),(cx,cy+sy*T)])
if nozone:
    for z in [z for z in b.Zones() if not z.GetIsRuleArea()]: b.Remove(z)
for n,c in sorted(set((t.GetNetname(), t.GetNetClassName()) for fp in b.GetFootprints() for t in fp.Pads())):
    if c != "Default": print(n, c)
print("export", pcbnew.ExportSpecctraDSN(b, dsn))
