from src.domain.model import UMLClass, UMLModel


class FanInOut:
    def calc_in(self, cls: UMLClass) -> int:
        return len(cls.incoming)

    def calc_out(self, cls: UMLClass) -> int:
        return len(cls.outgoing)


class LRC:
    """Layer-Responsibility Count (cuántas capas toca una clase)."""

    UI = ("ui", "presentation")
    DAO = ("dao", "repository")
    SERVICE = ("service", "logic")

    def _layer(self, package: str | None) -> str:
        if not package:
            return "unknown"
        p = package.lower()
        if any(k in p for k in self.UI):
            return "ui"
        if any(k in p for k in self.DAO):
            return "dao"
        if any(k in p for k in self.SERVICE):
            return "service"
        return "other"

    def calc(self, cls: UMLClass, model: UMLModel) -> int:
        layers = {self._layer(cls.package)}
        for dep in cls.outgoing:
            layers.add(self._layer(model.classes[dep].package))
        return len(layers)
