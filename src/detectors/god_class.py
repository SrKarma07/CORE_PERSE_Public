from __future__ import annotations
from src.domain.model import UMLModel
from typing import Dict


class GodClassDetector:
    """Calcula el GodClassScore y clasifica."""

    def __init__(self, cfg: Dict[str, float], calculators):
        self.cfg = cfg
        self.wmc = calculators["wmc"]
        self.atfd = calculators["atfd"]
        self.tcc = calculators["tcc"]
        self.lrc = calculators["lrc"]
        self.fan = calculators["fan"]

    # ------------------------------------------------------------------ #
    def detect(self, model: UMLModel):
        findings = []
        for cls in model.classes.values():
            # métricas
            w = self.wmc.calc(cls)
            a = self.atfd.calc(cls)
            t = self.tcc.calc(cls)
            fi = self.fan.calc_in(cls)
            fo = self.fan.calc_out(cls)
            lrc = self.lrc.calc(cls, model)

            # normalización lineal 0-1
            w_n = self._norm(w, "wmc")
            a_n = self._norm(a, "atfd")
            fi_n = min(fi / self.cfg["fanin_max"], 1)
            fo_n = min(fo / self.cfg["fanout_max"], 1)
            lrc_n = min(lrc / self.cfg["lrc_max"], 1)
            t_n = 1 - t  # menor cohesión = peor

            p_base = 0.4 * w_n + 0.3 * a_n + 0.3 * t_n
            p_arq = 0.4 * lrc_n + 0.3 * fo_n + 0.3 * fi_n
            score = 0.5 * p_base + 0.3 * p_arq  # sin semántica de momento

            if score >= 0.75:
                label = "god-class"
            elif score >= 0.5:
                label = "suspicious"
            else:
                # DEBUG ↓  quita cuando no lo necesites
                print(f"[DEBUG] {cls.name:20}  score={score:.2f}  "
                f"WMC={w}  ATFD={a}  TCC={t:.2f}  "
                f"FanIn={fi}  FanOut={fo}  LRC={lrc}")
                continue

            findings.append(
                {
                    "class": cls.name,
                    "score": round(score, 2),
                    "label": label,
                    "metrics": {
                        "WMC": w,
                        "ATFD": a,
                        "TCC": round(t, 2),
                        "FanIn": fi,
                        "FanOut": fo,
                        "LRC": lrc,
                    },
                }
            )
        return findings

    # ------------------------------------------------------------------ #
    def _norm(self, x, key):
        return (x - self.cfg[f"{key}_min"]) / (
            self.cfg[f"{key}_max"] - self.cfg[f"{key}_min"]
        ) if (self.cfg[f"{key}_max"] - self.cfg[f"{key}_min"]) else 0.0
