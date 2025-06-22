from src.domain.model import UMLClass


class WMC:
    """Weighted Methods per Class (simplificado)."""

    def calc(self, cls: UMLClass) -> int:
        return len(cls.operations)


class ATFD:
    """Access To Foreign Data (basado en count de dependencias salientes)."""

    def calc(self, cls: UMLClass) -> int:
        return len(cls.outgoing)


class TCC:
    """Tight Class Cohesion (pares que comparten campo / total de pares)."""

    def calc(self, cls: UMLClass) -> float:
        m = cls.operations
        if len(m) < 2:
            return 1.0
        shared = 0
        total = len(m) * (len(m) - 1) / 2
        for i, mi in enumerate(m):
            for mj in m[i + 1:]:
                if self._share(mi, mj, cls):
                    shared += 1
        return shared / total

    @staticmethod
    def _share(m1, m2, cls):
        """Dos métodos comparten atributo SÓLO si el nombre coincide."""
        attrs = {att.name for att in cls.attributes}
        # Pseudo-heurística: si el nombre del atributo aparece como
        # substring en el nombre de ambos métodos → consideramos uso.
        return any(a.lower() in m1.name.lower() and a.lower() in m2.name.lower()
                   for a in attrs)
