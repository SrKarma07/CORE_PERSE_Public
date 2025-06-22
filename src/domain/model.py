from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class UMLAttribute:
    name: str
    type_: str | None = None


@dataclass
class UMLOperation:
    name: str
    parameter_types: List[str] = field(default_factory=list)


@dataclass
class UMLClass:
    id_: str
    name: str
    attributes: List[UMLAttribute] = field(default_factory=list)
    operations: List[UMLOperation] = field(default_factory=list)
    outgoing: Set[str] = field(default_factory=set)     # ids
    incoming: Set[str] = field(default_factory=set)     # ids
    package: str | None = None


@dataclass
class UMLModel:
    classes: Dict[str, UMLClass] = field(default_factory=dict)
