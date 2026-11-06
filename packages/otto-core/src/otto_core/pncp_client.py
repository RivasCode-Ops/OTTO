from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Iterator

import httpx

from otto_core.config import load_yaml


class PncpClient:
    def __init__(self, config: dict | None = None) -> None:
        self.cfg = config or load_yaml("ingest.yaml")
        self.base_url = self.cfg.get("base_url", "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao")
        self.page_size = int(self.cfg.get("tamanho_pagina", 50))
        self.pause = float(self.cfg.get("pausa_entre_paginas_seg", 0.3))
        self.max_retries = int(self.cfg.get("max_retries", 3))

    def fetch_publicacoes(
        self,
        uf: str,
        data_inicial: date,
        data_final: date,
        modalidade: int,
    ) -> Iterator[dict[str, Any]]:
        di = data_inicial.strftime("%Y%m%d")
        df = data_final.strftime("%Y%m%d")
        pagina = 1

        while True:
            params = {
                "dataInicial": di,
                "dataFinal": df,
                "codigoModalidadeContratacao": modalidade,
                "uf": uf,
                "tamanhoPagina": self.page_size,
                "pagina": pagina,
            }
            payload = self._get(params)
            items = payload.get("data") or []
            if not items:
                break
            for item in items:
                yield item
            total_paginas = payload.get("totalPaginas") or payload.get("totalPages")
            if total_paginas is not None and pagina >= int(total_paginas):
                break
            if len(items) < self.page_size:
                break
            pagina += 1
            time.sleep(self.pause)

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        last_err: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=60.0) as client:
                    r = client.get(self.base_url, params=params)
                    if r.status_code == 429:
                        time.sleep(2 ** attempt)
                        continue
                    r.raise_for_status()
                    return r.json()
            except Exception as e:
                last_err = e
                time.sleep(1 + attempt)
        raise RuntimeError(f"PNCP falhou após {self.max_retries} tentativas: {last_err}")

    def collect_window(
        self,
        days: int | None = None,
        ufs: list[str] | None = None,
        modalidades: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        days = days or int(self.cfg.get("janela_dias_padrao", 7))
        ufs = ufs or list(self.cfg.get("ufs", ["PI"]))
        modalidades = modalidades or [int(m) for m in self.cfg.get("modalidades", [6])]
        data_final = date.today()
        data_inicial = data_final - timedelta(days=max(1, days))

        out: list[dict[str, Any]] = []
        seen: set[str] = set()

        for uf in ufs:
            for mod in modalidades:
                for raw in self.fetch_publicacoes(uf, data_inicial, data_final, mod):
                    from otto_core.normalize import extract_numero_controle

                    key = extract_numero_controle(raw)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(raw)
        return out
