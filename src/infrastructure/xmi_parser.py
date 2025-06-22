from __future__ import annotations
from pathlib import Path
from lxml import etree

from src.domain.model import UMLModel, UMLClass, UMLAttribute, UMLOperation


class XMIParser:
    NS = {
        "uml": "http://www.omg.org/spec/UML/20090901",
        "xmi": "http://www.omg.org/XMI",
    }

    # ------------------------------------------------------------------ #
    def parse(self, file: Path | str) -> UMLModel:
        p = Path(file)
        if not p.exists():
            raise FileNotFoundError(p.resolve())
        root = etree.parse(str(p)).getroot()
        model = UMLModel()

        # ---------- 1 · clases / interfaces -----------------------------
        for node in root.xpath(
            ".//packagedElement[@xmi:type='uml:Class' or @xmi:type='uml:Interface']",
            namespaces=self.NS,
        ):
            cls = UMLClass(
                id_=node.get(f"{{{self.NS['xmi']}}}id"),
                name=node.get("name", "<unnamed>"),
                package=self._package_of(node),
            )
            # atributos
            for att in node.xpath("./ownedAttribute"):
                cls.attributes.append(UMLAttribute(att.get("name"), att.get("type")))
            # operaciones
            for op in node.xpath("./ownedOperation"):
                cls.operations.append(
                    UMLOperation(
                        op.get("name"),
                        [p.get("type") for p in op.xpath("./ownedParameter")],
                    )
                )
            model.classes[cls.id_] = cls

        # ---------- 1.b · clientDependency (sin prefijo) -----------------
        for dep in root.xpath(".//clientDependency"):
            client_id = dep.getparent().get(f"{{{self.NS['xmi']}}}id")
            supplier_id = dep.get("supplier")
            self._add_edge(model, client_id, supplier_id)

        # ---------- 2 · packagedElement Dependency / Association ---------
        for rel in root.xpath(
            ".//packagedElement[@xmi:type='uml:Dependency' "
            "or @xmi:type='uml:Association']",
            namespaces=self.NS,
        ):
            client = rel.get("client") or rel.get("memberEnd")
            supplier = rel.get("supplier") or rel.get("memberEnd")
            self._add_edge(model, client, supplier)

        print(f"[PARSE]  clases cargadas: {len(model.classes)}")  # debug opcional
        return model

    # ------------------------------------------------------------------ #
    @staticmethod
    def _add_edge(model: UMLModel, client_id: str | None, supplier_id: str | None):
        if (
            client_id
            and supplier_id
            and client_id in model.classes
            and supplier_id in model.classes
            and client_id != supplier_id
        ):
            model.classes[client_id].outgoing.add(supplier_id)
            model.classes[supplier_id].incoming.add(client_id)

    # ------------------------------------------------------------------ #
    def _package_of(self, element) -> str | None:
        p = element.getparent()
        while p is not None:
            if p.tag.endswith("Package"):
                return p.get("name")
            p = p.getparent()
        return None
