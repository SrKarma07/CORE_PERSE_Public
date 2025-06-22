from __future__ import annotations
import json
import pathlib
import typer

from src.infrastructure.xmi_parser import XMIParser
from src.metrics.structural import WMC, ATFD, TCC
from src.metrics.architectural import FanInOut, LRC
from src.detectors.god_class import GodClassDetector
from src.detectors.hub_like import HubLikeDependencyDetector

app = typer.Typer(help=" – detector de God Class y Hub-Like Dependency.")


@app.command()
def analyse(
    xmi: pathlib.Path = typer.Argument(..., help="Archivo .xmi a analizar"),
    config: pathlib.Path = typer.Option(..., "-c", "--config", help="config.json"),
    out: pathlib.Path = typer.Option("report.json", "-o", "--out", help="Salida JSON"),
):
    """Procesa el XMI y genera un informe."""
    cfg = json.loads(config.read_text())
    model = XMIParser().parse(xmi)

    calculators = dict(
        wmc=WMC(),
        atfd=ATFD(),
        tcc=TCC(),
        fan=FanInOut(),
        lrc=LRC(),
    )
    god_detector = GodClassDetector(cfg, calculators)
    hub_detector = HubLikeDependencyDetector()

    report = {
        "god_class": god_detector.detect(model),
        "hub_like": hub_detector.detect(model),
    }
    out.write_text(json.dumps(report, indent=2))
    typer.echo(f"Informe escrito en {out}")


if __name__ == "__main__":
    app()
