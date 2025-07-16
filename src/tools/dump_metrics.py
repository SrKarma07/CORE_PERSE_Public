from pathlib import Path
import json, sys, statistics as st
from src.infrastructure.xmi_parser import XMIParser
from src.metrics.structural import WMC, ATFD
from src.metrics.architectural import FanInOut, LRC

xmi = Path(sys.argv[1])
model = XMIParser().parse(xmi)

wmc, atfd, fan, lrc = WMC(), ATFD(), FanInOut(), LRC()
vals = dict(
    wmc   = [wmc.calc(c)        for c in model.classes.values()],
    atfd  = [atfd.calc(c)       for c in model.classes.values()],
    fanin = [fan.calc_in(c)     for c in model.classes.values()],
    fanout= [fan.calc_out(c)    for c in model.classes.values()],
    lrc   = [lrc.calc(c, model) for c in model.classes.values()],
)

# --- raw ---
Path("metrics_raw.json").write_text(json.dumps(vals, indent=2))

# --- stats ---
def p(val_list, q):     # percentil (0–1)
    k = max(0, min(len(val_list)-1, int(round(q*len(val_list))-1)))
    return sorted(val_list)[k]

stats = {
    m: {
        "min":  min(seq),
        "p50":  p(seq, 0.50),
        "mean": st.mean(seq),
        "p90":  p(seq, 0.90),
        "max":  max(seq),
    }
    for m, seq in vals.items()
}
stats["classes"] = len(model.classes)
Path("metrics_stats.json").write_text(json.dumps(stats, indent=2))
print("✅ metrics_raw.json  &  metrics_stats.json generados")
