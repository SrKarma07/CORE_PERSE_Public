# src/cli.py
from __future__ import annotations
import json, pathlib, typer

from src.infrastructure.xmi_parser import XMIParser
from src.metrics.structural import WMC, ATFD, TCC
from src.metrics.architectural import FanInOut, LRC
from src.detectors.god_class import GodClassDetector
from src.detectors.hub_like import HubLikeDependencyDetector

app = typer.Typer(help="Detector de God Class y Hub-Like Dependency.")

# --------------------------------------------------------------------------- #
@app.command()
def analyse(
    # ---------- archivos de entrada ---------------------------------- #
    xmi: pathlib.Path = typer.Argument(
        ...,
        exists=True, readable=True,
        help="Diagrama UML en formato .xmi"),
    config: pathlib.Path = typer.Option(
        ...,
        "-c", "--config",
        exists=True, readable=True,
        help="config.json con rangos iniciales (fallback)"),
    # ---------- calibración clásica ---------------------------------- #
    context: pathlib.Path | None = typer.Option(
        None,
        "--context", "-ctx",
        exists=True, readable=True,
        help="Resumen de la tesis (TXT) para calibrar con percentiles"),
    # ---------- calibración IA --------------------------------------- #
    pdf: pathlib.Path | None = typer.Option(
        None,
        "--pdf",
        exists=True, readable=True,
        help="PDF completo de la tesis (requerido si usas --ai-calibrate)"),
    ai_calibrate: bool = typer.Option(
        False,
        "--ai-calibrate",
        help="Pedir a ChatGPT que sugiera umbrales"),
    # ---------- salidas ---------------------------------------------- #
    out: pathlib.Path = typer.Option(
        "report.json",
        "-o", "--out",
        help="Archivo JSON con el informe final"),
    metrics_out: pathlib.Path = typer.Option(
        "metricas.json",
        "--metrics-out",
        help="Archivo JSON donde se guardan los umbrales efectivos"),
) -> None:
    """
    Procesa el XMI y genera:

      • report.json     → resultado de God-Class / Hub-Like
      • metricas.json   → umbrales utilizados (calibrados o AI)
    """
    # ------------------------------------------------------------------ #
    cfg = json.loads(config.read_text(encoding="utf-8"))
    model = XMIParser().parse(xmi)

    # ---------- 1 · calibración IA ------------------------------------ #
    if ai_calibrate:
        if not pdf:
            typer.secho("❌  Debes pasar --pdf cuando usas --ai-calibrate.",
                         fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        from src.calibration.ai_calibrator import AICalibrator
        cfg = AICalibrator().suggest_thresholds(model, pdf)
        typer.secho("[AI]  Umbrales sugeridos por ChatGPT aplicados.",
                     fg=typer.colors.GREEN)

    # ---------- 2 · calibración clásica (percentiles + contexto) ------ #
    elif context:
        from src.calibration.calibrator import Calibrator
        ctx_txt = context.read_text(encoding="utf-8")
        cfg = Calibrator(cfg).calibrate(model, ctx_txt)
        typer.echo(
            f"[CAL]  score_godclass={cfg.get('score_godclass', 0.75):.2f} – "
            f"score_suspicious={cfg.get('score_suspicious', 0.50):.2f}"
        )

    # (si no hay ni --ai-calibrate ni --context → se usan valores del config)

    # ---------- 3 · guardar umbrales efectivos ------------------------ #
    metrics_out.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    typer.echo(f"📊 Umbrales efectivos → {metrics_out}")

    # ---------- 4 · detección ----------------------------------------- #
    calculators = dict(
        wmc=WMC(), atfd=ATFD(), tcc=TCC(), fan=FanInOut(), lrc=LRC()
    )

    report = {
        "god_class": GodClassDetector(cfg, calculators).detect(model),
        "hub_like": HubLikeDependencyDetector().detect(model),
    }
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    typer.echo(f"✅ Informe escrito en {out}")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    app()
