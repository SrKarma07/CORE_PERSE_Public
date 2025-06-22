# src/cli.py
from __future__ import annotations
import json, pathlib, typer

from src.infrastructure.xmi_parser import XMIParser
from src.metrics.structural import WMC, ATFD, TCC
from src.metrics.architectural import FanInOut, LRC
from src.detectors.god_class import GodClassDetector
from src.detectors.hub_like import HubLikeDependencyDetector

app = typer.Typer(help="Detector de God Class y Hub-Like Dependency.")

@app.command()
def analyse(
    xmi: pathlib.Path = typer.Argument(..., exists=True, readable=True,
                                       help="Archivo .xmi a analizar"),
    config: pathlib.Path = typer.Option(..., "-c", "--config",
                                        exists=True, readable=True,
                                        help="config.json con rangos iniciales"),
    context: pathlib.Path | None = typer.Option(
        None, "--context", "-ctx", exists=True, readable=True,
        help="Resumen de la tesis para calibrar umbrales"),
    out: pathlib.Path = typer.Option("report.json", "-o", "--out",
                                     help="Archivo JSON de salida"),
                                     metrics_out: pathlib.Path = typer.Option(
        "metricas.json", "--metrics-out", help="Archivo JSON con umbrales calibrados"),
) -> None:
    """Procesa el XMI y genera el informe."""
    cfg = json.loads(config.read_text(encoding="utf-8"))
    model = XMIParser().parse(xmi)

    if context:
        from src.calibration.calibrator import Calibrator
        ctx_txt = context.read_text(encoding="utf-8")
        cfg = Calibrator(cfg).calibrate(model, ctx_txt)
        print(f"[CAL]  score_godclass={cfg.get('score_godclass', 0.75):.2f} – "
        f"score_suspicious={cfg.get('score_suspicious', 0.50):.2f}")
    
    # --- ⬇⬇  NUEVO: exportar métricas calibradas  ⬇⬇ ---
    metrics_out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    typer.echo(f"📊 Umbrales calibrados → {metrics_out}")
    # ---------------------------------------------------

    calculators = dict(wmc=WMC(), atfd=ATFD(), tcc=TCC(),
                       fan=FanInOut(), lrc=LRC())

    report = {
        "god_class": GodClassDetector(cfg, calculators).detect(model),
        "hub_like": HubLikeDependencyDetector().detect(model),
    }
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    typer.echo(f"✅ Informe escrito en {out}")

if __name__ == "__main__":
    app()
