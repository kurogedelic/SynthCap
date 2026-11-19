import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
print("import", pcbnew.ImportSpecctraSES(b, sys.argv[2]))
for z in b.Zones(): z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
tr = list(b.GetTracks())
print("tracks", sum(t.GetClass()=="PCB_TRACK" for t in tr), "vias", sum(t.GetClass()=="PCB_VIA" for t in tr))
pcbnew.SaveBoard(sys.argv[3], b)
