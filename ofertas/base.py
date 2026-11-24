"""
Estruturas comuns usadas por todo o sistema de ofertas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class StatusLoja(str, Enum):
    ATIVA = "ativa"
    PENDENTE_API = "pendente_api"
    SEM_ACESSO = "sem_acesso_autorizado"


@dataclass
class Produto:
    loja: str
    id_produto: str
    nome: str
    preco: float
    url: str
    disponivel: bool = True
    url_imagem: Optional[str] = None
    moeda: str = "BRL"
    data_consulta: datetime = field(default_factory=datetime.now)

    @property
    def chave_unica(self) -> str:
        return f"{self.loja}:{self.id_produto}"


@dataclass
class AlertaPreco:
    termo_busca: str
    preco_alvo: float
    id_alerta: Optional[str] = None
    ativo: bool = True
    guild_id: Optional[int] = None   # servidor onde foi criado
