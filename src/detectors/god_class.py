# src/detectors/god_class.py
from __future__ import annotations

from typing import Dict, Any
from src.domain.model import UMLModel


class GodClassDetector:
    """
    Calcula el GodClassScore y clasifica la clase como:
        • god-class      (score ≥  score_godclass)
        • suspicious     (score ≥  score_suspicious)
        • normal         (score  < score_suspicious)
    Los umbrales y rangos de normalización provienen de `cfg`,
    de modo que el detector se adapta a los valores calculados
    dinámicamente por el Calibrator.  Si los umbrales no existen
    en la configuración, se usan 0.75 y 0.50 como valores
    por defecto (estándar de la literatura).
    """

    def __init__(self, cfg: Dict[str, Any], calculators: Dict[str, Any]) -> None:
        self.cfg = cfg
        self.wmc = calculators["wmc"]
        self.atfd = calculators["atfd"]
        self.tcc = calculators["tcc"]
        self.lrc = calculators["lrc"]
        self.fan = calculators["fan"]

        # Umbrales de decisión (heredados o recalibrados)
        self.thr_godclass = cfg.get("score_godclass", 0.75)
        self.thr_susp     = cfg.get("score_suspicious", 0.50)

    # ------------------------------------------------------------------ #
    def detect(self, model: UMLModel):
        findings = []

        for cls in model.classes.values():
            # ---------- métricas brutas -------------------------------- #
            w   = self.wmc.calc(cls)
            a   = self.atfd.calc(cls)
            t   = self.tcc.calc(cls)
            fi  = self.fan.calc_in(cls)
            fo  = self.fan.calc_out(cls)
            lrc = self.lrc.calc(cls, model)

            # ---------- normalización 0-1 ------------------------------ #
            w_n   = self._norm(w,  "wmc")
            a_n   = self._norm(a,  "atfd")
            fi_n  = min(fi  / max(self.cfg.get("fanin_max",  1), 1), 1)
            fo_n  = min(fo  / max(self.cfg.get("fanout_max", 1), 1), 1)
            lrc_n = min(lrc / max(self.cfg.get("lrc_max",    1), 1), 1)
            t_n   = 1 - t  # menor cohesión = peor

            # ---------- puntuaciones parciales ------------------------- #
            p_base = 0.4 * w_n + 0.3 * a_n + 0.3 * t_n
            p_arq  = 0.4 * lrc_n + 0.3 * fo_n + 0.3 * fi_n

            # Semántica aún no integrada: placeholder para el futuro
            score = 0.5 * p_base + 0.3 * p_arq

            # ---------- clasificación ---------------------------------- #
            if score >= self.thr_godclass:
                label = "god-class"
            elif score >= self.thr_susp:
                label = "suspicious"
            else:
                # DEBUG ↓ (puedes desactivar esta línea si ya no la necesitas)
                print(
                    f"[DEBUG] {cls.name:20}  score={score:.2f}  "
                    f"WMC={w}  ATFD={a}  TCC={t:.2f}  "
                    f"FanIn={fi}  FanOut={fo}  LRC={lrc}"
                )
                continue

            # ---------- reporte --------------------------------------- #
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
    def _norm(self, x: float, key: str) -> float:
        """
        Normalización min-max.  Devuelve 0.0 cuando el denominador es 0.
        """
        rng = self.cfg.get(f"{key}_max", 1) - self.cfg.get(f"{key}_min", 0)
        if rng == 0:
            return 0.0
        return (x - self.cfg.get(f"{key}_min", 0)) / rng
