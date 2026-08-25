"""
Módulo: extracao_eco.py
Etapa do fluxo: E-mail -> Leitura -> EXTRAÇÃO -> (Validação)

Responsável por transformar o texto bruto de um e-mail de ECO nos
15 campos obrigatórios definidos em controle_mestre_ecos.xlsx, que são
os MESMOS campos (mesmo id/name) usados no formulario_eco_fake.html:

  Codigo_ECO, Titulo_Alteracao, Area_Solicitante,
  Nome_Engenheiro_Responsavel, Email_Solicitante, Data_Recebimento,
  Nivel_Prioridade, Status_Atual, Justificativa_Tecnica,
  Codigo_Item_Afetado, Categoria_Mudanca, Impacto_Custos,
  Estimativa_Orcamento, Unidade_Fabril, Data_Implementacao_Alvo

Os e-mails da matriz não seguem um layout 100% padronizado
(ex.: "Título da alteração:" no normal_ECO_00125 vs "Título:" no
ambiguo_ECO_00126), então cada campo é buscado por uma LISTA de
possíveis rótulos (aliases), não por um único texto fixo.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, fields
from typing import Dict, List, Optional

logger = logging.getLogger("eco_automation.extracao")

# Ordem oficial dos 15 campos (igual à planilha mestre e ao formulário web)
CAMPOS_OBRIGATORIOS = [
    "Codigo_ECO",
    "Titulo_Alteracao",
    "Area_Solicitante",
    "Nome_Engenheiro_Responsavel",
    "Email_Solicitante",
    "Data_Recebimento",
    "Nivel_Prioridade",
    "Status_Atual",
    "Justificativa_Tecnica",
    "Codigo_Item_Afetado",
    "Categoria_Mudanca",
    "Impacto_Custos",
    "Estimativa_Orcamento",
    "Unidade_Fabril",
    "Data_Implementacao_Alvo",
]

# Para cada campo, a lista de rótulos (em PT-BR, como aparecem nos e-mails)
# que podem introduzir aquele valor. A busca é case-insensitive.
ALIASES: Dict[str, List[str]] = {
    "Codigo_ECO": ["ECO", "Código", "Codigo"],
    "Titulo_Alteracao": ["Título da alteração", "Título", "Titulo"],
    "Area_Solicitante": ["Área solicitante", "Solicitante", "Área"],
    "Nome_Engenheiro_Responsavel": ["Engenheiro responsável", "Engenheiro"],
    "Email_Solicitante": ["E-mail solicitante", "E-mail"],
    "Data_Recebimento": ["Data de recebimento", "Recebimento"],
    "Nivel_Prioridade": ["Prioridade"],
    "Status_Atual": ["Status atual", "Status"],
    "Justificativa_Tecnica": ["Justificativa técnica", "Justificativa"],
    "Codigo_Item_Afetado": ["Código do item afetado", "Código do item", "Item"],
    "Categoria_Mudanca": ["Categoria da mudança", "Categoria"],
    "Impacto_Custos": ["Impacto em custos"],
    "Estimativa_Orcamento": ["Estimativa de orçamento", "Orçamento"],
    "Unidade_Fabril": ["Unidade fabril"],
    "Data_Implementacao_Alvo": ["Data de implementação alvo", "Implementação alvo"],
}


@dataclass
class ECOExtraida:
    """Estrutura com os 15 campos extraídos de um e-mail de ECO."""
    Codigo_ECO: Optional[str] = None
    Titulo_Alteracao: Optional[str] = None
    Area_Solicitante: Optional[str] = None
    Nome_Engenheiro_Responsavel: Optional[str] = None
    Email_Solicitante: Optional[str] = None
    Data_Recebimento: Optional[str] = None
    Nivel_Prioridade: Optional[str] = None
    Status_Atual: Optional[str] = None
    Justificativa_Tecnica: Optional[str] = None
    Codigo_Item_Afetado: Optional[str] = None
    Categoria_Mudanca: Optional[str] = None
    Impacto_Custos: Optional[str] = None
    Estimativa_Orcamento: Optional[str] = None
    Unidade_Fabril: Optional[str] = None
    Data_Implementacao_Alvo: Optional[str] = None

    # metadados úteis para a etapa de validação (não fazem parte dos 15
    # campos oficiais, mas ajudam o Gateway a decidir o roteamento)
    arquivo_origem: Optional[str] = None
    campos_ausentes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Retorna apenas os 15 campos oficiais, na ordem da planilha/form."""
        return {c: getattr(self, c) for c in CAMPOS_OBRIGATORIOS}


class ExtratorECO:
    """
    Extrai os 15 campos obrigatórios de uma ECO a partir do texto bruto
    de um e-mail, usando busca por rótulo (label) + valor na mesma linha.
    """

    def extrair(self, conteudo_email: str, nome_arquivo: str = "") -> ECOExtraida:
        eco = ECOExtraida(arquivo_origem=nome_arquivo)

        for campo, rotulos in ALIASES.items():
            valor = self._buscar_valor(conteudo_email, rotulos)
            if valor is not None:
                valor = self._normalizar(campo, valor)
            setattr(eco, campo, valor)

        eco.campos_ausentes = [
            campo for campo in CAMPOS_OBRIGATORIOS if not getattr(eco, campo)
        ]

        if eco.campos_ausentes:
            logger.warning(
                "AVISO | %s: campos ausentes -> %s",
                nome_arquivo,
                ", ".join(eco.campos_ausentes),
            )
        else:
            logger.info("INFO | %s: todos os 15 campos extraídos.", nome_arquivo)

        return eco

    @staticmethod
    def _buscar_valor(texto: str, rotulos: List[str]) -> Optional[str]:
        """
        Procura, linha a linha, por um rótulo seguido de ':' e retorna o
        que vem depois. Tenta os rótulos na ordem (o mais específico
        primeiro), retornando no primeiro que casar.
        """
        for rotulo in rotulos:
            # ex.: "Título da alteração: Atualização do layout..."
            padrao = rf"^{re.escape(rotulo)}\s*:\s*(.+)$"
            m = re.search(padrao, texto, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                valor = m.group(1).strip()
                if valor:
                    return valor
        return None

    @staticmethod
    def _normalizar(campo: str, valor: str) -> str:
        """Pequenas normalizações por campo (maiúsculas, remover ' USD', etc.)."""
        if campo == "Estimativa_Orcamento":
            # remove sufixos como "USD" para deixar só o número
            valor = re.sub(r"[^\d\-.,]", "", valor).strip()
        elif campo == "Codigo_ECO":
            valor = valor.upper()
        return valor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    exemplo = """ECO: ECO-00125
Título da alteração: Atualização do layout do módulo de refrigeração
Área solicitante: Engenharia
Engenheiro responsável: Ana Souza
E-mail solicitante: ana.souza@matriz.example
Data de recebimento: 2026-08-20
Prioridade: Alta
Status atual: Recebido
Justificativa técnica: Adequação do posicionamento do componente.
Código do item afetado: ITEM-REF-220
Categoria da mudança: Layout
Impacto em custos: Não
Estimativa de orçamento: 0
Unidade fabril: Manaus
Data de implementação alvo: 2026-09-15"""

    extrator = ExtratorECO()
    eco = extrator.extrair(exemplo, "normal_ECO_00125.txt")
    import json
    print(json.dumps(eco.to_dict(), indent=2, ensure_ascii=False))