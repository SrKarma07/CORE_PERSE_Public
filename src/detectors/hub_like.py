import networkx as nx
from src.domain.model import UMLModel


class HubLikeDependencyDetector:
    """Detecta hubs mediante PageRank + umbral estadístico μ+σ."""

    def detect(self, model: UMLModel, top_k: int = 10):
        g = nx.DiGraph()
        for cls in model.classes.values():
            for tgt in cls.outgoing:
                g.add_edge(cls.name, model.classes[tgt].name)

        if not g:
            return []

        pr = nx.pagerank(g)
        mean_deg = sum(dict(g.degree()).values()) / g.number_of_nodes()
        std_deg = (sum((d - mean_deg) ** 2 for d in dict(g.degree()).values())
                   / g.number_of_nodes()) ** 0.5
        threshold = mean_deg + std_deg

        hubs = [n for n in pr if g.degree(n) > threshold]
        hubs.sort(key=lambda n: pr[n], reverse=True)
        return hubs[:top_k]
