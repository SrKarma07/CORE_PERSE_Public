from metrics.structural import WMC, ATFD, TCC
from infrastructure.xmi_parser import XMIParser
from pathlib import Path


def test_wmc_value():
    model = XMIParser().parse(Path("samples/sample.xmi"))
    cls = model.classes["cls_service_1"]
    assert WMC().calc(cls) == 5
