# src/calibration/ai_calibrator.py
from __future__ import annotations

import json, os, re, textwrap 
from typing import Dict, List, Any

import openai
from PyPDF2 import PdfReader
from dotenv import load_dotenv

from src.domain.model import UMLModel
from src.metrics.structural import WMC, ATFD
from src.metrics.architectural import FanInOut, LRC

load_dotenv()                       # lee .env si existe

class AICalibrator:
    """
    Llama a ChatGPT para sugerir los rangos de normalización y los
    umbrales `score_suspicious` / `score_godclass`, basándose en:
      • Distribución de métricas del UMLModel
      • Texto completo del PDF de la tesis
    Devuelve un dict con las mismas claves que config.json.
    """

    def __init__(self,
                 model: str = "gpt-4o-mini",
                 api_key: str | None = None) -> None:
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    # ---------- helpers ------------------------------------------------ #
    def _metric_values(self, model: UMLModel) -> Dict[str, List[int]]:
        wmc, atfd, fan, lrc = WMC(), ATFD(), FanInOut(), LRC()
        return dict(
            wmc=[wmc.calc(c) for c in model.classes.values()],
            atfd=[atfd.calc(c) for c in model.classes.values()],
            fanin=[fan.calc_in(c) for c in model.classes.values()],
            fanout=[fan.calc_out(c) for c in model.classes.values()],
            lrc=[lrc.calc(c, model) for c in model.classes.values()],
        )

    def _pdf_to_text(self, pdf_path: str | os.PathLike) -> str:
        reader = PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    def _build_prompt(self,
                      metrics: Dict[str, List[int]],
                      thesis_txt: str) -> list[dict[str, str]]:
        # resumimos la tesis a 1500 tokens aprox. (≈ 6k chars)
        thesis_excerpt = thesis_txt[:6000]

        user_msg = textwrap.dedent(f"""
        Eres un analista de ingeniería de software. 
        Recibes:
          (a) Las distribuciones de métricas WMC, ATFD, FanIn, FanOut, LRC
              en formato JSON.
          (b) Un extracto del texto de la tesis (hasta 6 000 caracteres).

        Tu tarea: devolver **SOLO** un objeto JSON con los campos
          "wmc_min", "wmc_max", "atfd_min", "atfd_max",
          "fanin_max", "fanout_max", "lrc_max",
          "score_suspicious", "score_godclass".

        – Las claves deben existir todas.
        – Usa valores float/int.
        – Fundamenta tus elecciones dentro de un campo "comments"
          (string) **fuera** del JSON para que luego pueda registrarse,
          pero no mezcles comentarios con el objeto raíz.

        ### MÉTRICAS ###
        {json.dumps(metrics)}

        ### EXTRACTO TESIS ###
        {thesis_excerpt}
        """)
        return [
            {"role": "system",
             "content": "Eres ChatGPT especializado en detección de antipatrones."},
            {"role": "user", "content": user_msg},
        ]

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Busca el primer bloque JSON en la respuesta y lo parsea.
        Si falla, levanta ValueError.
        """
        match = re.search(r'\{.*\}', text, re.S)   # greedy
        if not match:
            raise ValueError("No se encontró JSON en la respuesta.")
        return json.loads(match.group(0))

    # ---------- API pública -------------------------------------------- #
    def suggest_thresholds(self,
                           model: UMLModel,
                           pdf_path: str | os.PathLike) -> Dict[str, float]:
        metrics = self._metric_values(model)
        thesis_text = self._pdf_to_text(pdf_path)

        messages = self._build_prompt(metrics, thesis_text)
        response = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        ai_text = response.choices[0].message.content
        cfg_ai = self._extract_json(ai_text)
        return {k: float(v) for k, v in cfg_ai.items()}
