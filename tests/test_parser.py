from infrastructure.xmi_parser import XMIParser
from pathlib import Path


def test_simple_xmi():
    model = XMIParser().parse(Path("samples/sample.xmi"))
    assert "cls_ui_1" in model.classes
    assert model.classes["cls_service_1"].name == "AccountManager"
