"""
parser.py
=========
Módulo de LEITURA + EXTRAÇÃO de ECOs para integração com o resto da equipe.

O que ele faz:
  1. Lê os arquivos .txt da pasta emails_matriz/ (normal, ambíguo, erro)
  2. Extrai os 15 campos obrigatórios de cada ECO
  3. Retorna cada ECO como um dicionário Python simples (compatível com
     json.dumps, pandas, openpyxl e com os inputs do formulario_eco_fake.html,
     já que as chaves usadas aqui são EXATAMENTE os mesmos nomes de coluna
     de controle_mestre_ecos.xlsx / id dos campos do formulário)

Como outra parte da equipe usa (exemplos):

    from parser import parse_pasta, parse_arquivo, parse_texto

    # 1) processar a pasta toda de uma vez (uso mais comum)
    resultados = parse_pasta("emails_matriz")
    for eco in resultados:
        print(eco["Codigo_ECO"], eco["_campos_ausentes"])

    # 2) processar um único arquivo
    eco = parse_arquivo("emails_matriz/normal_ECO_00125.txt")

    # 3) processar um texto que já está em memória (ex.: veio de outro módulo)
    eco = parse_texto(texto_do_email, nome_arquivo="normal_ECO_00125.txt")

Formato do dicionário retornado (exemplo):
{
    "Codigo_ECO": "ECO-00125",
    "Titulo_Alteracao": "Atualização do layout do módulo de refrigeração",
    "Area_Solicitante": "Engenharia",
    "Nome_Engenheiro_Responsavel": "Ana Souza",
    "Email_Solicitante": "ana.souza@matriz.example",
    "Data_Recebimento": "2026-08-20",
    "Nivel_Prioridade": "Alta",
    "Status_Atual": "Recebido",
    "Justificativa_Tecnica": "Adequação do posicionamento do componente...",
    "Codigo_Item_Afetado": "ITEM-REF-220",
    "Categoria_Mudanca": "Layout",
    "Impacto_Custos": "Não",
    "Estimativa_Orcamento": "0",
    "Unidade_Fabril": "Manaus",
    "Data_Implementacao_Alvo": "2026-09-15",

    # metadados extras (prefixo "_" para não confundir com os 15 campos
    # oficiais -> quem for gravar na planilha/form deve ignorar estes):
    "_arquivo_origem": "normal_ECO_00125.txt",
    "_campos_ausentes": []      # ex.: ["Data_Implementacao_Alvo"] no cenário ambíguo
}
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger("eco_automation.parser")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

# ---------------------------------------------------------------------------
# 1) Definição dos 15 campos obrigatórios (mesma ordem/nome da planilha
#    controle_mestre_ecos.xlsx e do formulario_eco_fake.html)
# ---------------------------------------------------------------------------

CAMPOS_OBRIGATORIOS: List[str] = [
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

# Cada campo pode aparecer com rótulos diferentes conforme o e-mail
# (ex.: "Título da alteração:" no normal, "Título:" no ambíguo).
# A busca tenta cada rótulo na ordem, e usa o primeiro que casar.
ALIASES: Dict[str, List[str]] = {
    "Codigo_ECO": ["ECO", "Código", "Codigo"],
    "Titulo_Alteracao": ["Título da alteração", "Título", "Titulo"],
    "Area_Solicitante": ["Área solicitante", "Área", "Solicitante"],
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


# ---------------------------------------------------------------------------
# 2) Funções internas de extração
# ---------------------------------------------------------------------------

def _buscar_valor(texto: str, rotulos: List[str]) -> Optional[str]:
    """Procura 'Rótulo: valor' linha a linha e retorna o valor (ou None)."""
    for rotulo in rotulos:
        padrao = rf"^{re.escape(rotulo)}\s*:\s*(.+)$"
        m = re.search(padrao, texto, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            valor = m.group(1).strip()
            if valor:
                return valor
    return None


def _normalizar(campo: str, valor: str) -> str:
    """Pequenos ajustes por campo (ex.: tirar 'USD' do orçamento)."""
    if campo == "Estimativa_Orcamento":
        valor = re.sub(r"[^\d\-.,]", "", valor).strip()
    elif campo == "Codigo_ECO":
        valor = valor.upper()
    return valor


# ---------------------------------------------------------------------------
# 3) API pública do módulo
# ---------------------------------------------------------------------------

def parse_texto(texto_email: str, nome_arquivo: str = "") -> Dict[str, Union[str, None, List[str]]]:
    """
    Extrai os 15 campos de uma ECO a partir de um texto de e-mail já
    carregado em memória. Retorna um dicionário estruturado.
    """
    dados: Dict[str, Optional[str]] = {}

    for campo, rotulos in ALIASES.items():
        valor = _buscar_valor(texto_email, rotulos)
        if valor is not None:
            valor = _normalizar(campo, valor)
        dados[campo] = valor

    campos_ausentes = [c for c in CAMPOS_OBRIGATORIOS if not dados.get(c)]

    dados["_arquivo_origem"] = nome_arquivo
    dados["_campos_ausentes"] = campos_ausentes

    if campos_ausentes:
        logger.warning("AVISO | %s: campos ausentes -> %s", nome_arquivo, campos_ausentes)
    else:
        logger.info("INFO | %s: 15 campos extraídos com sucesso.", nome_arquivo)

    return dados


def parse_arquivo(caminho_arquivo: Union[str, Path]) -> Dict[str, Union[str, None, List[str]]]:
    """Lê um único arquivo .txt de e-mail e retorna o dicionário extraído."""
    caminho = Path(caminho_arquivo)
    try:
        texto = caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        texto = caminho.read_text(encoding="latin-1")
    return parse_texto(texto, nome_arquivo=caminho.name)


def parse_pasta(
    pasta_emails: Union[str, Path] = "emails_matriz",
    extensao: str = ".txt",
) -> List[Dict[str, Union[str, None, List[str]]]]:
    """
    Lê TODOS os e-mails (.txt) de uma pasta e retorna uma lista de
    dicionários estruturados, um por ECO. Esta é a função principal
    para integração: outra parte do sistema (validação, gateway,
    preenchimento web) só precisa chamar parse_pasta(...) e iterar
    sobre a lista retornada.
    """
    pasta = Path(pasta_emails)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta de e-mails não encontrada: {pasta.resolve()}")

    arquivos = sorted(pasta.glob(f"*{extensao}"))
    logger.info("Encontrados %d e-mail(s) em '%s'.", len(arquivos), pasta)

    return [parse_arquivo(arquivo) for arquivo in arquivos]


# ---------------------------------------------------------------------------
# 4) Execução direta: gera um JSON com o resultado (útil para a equipe
#    conferir rapidamente o que está sendo extraído, ou para outro módulo
#    (ex.: em outra linguagem/serviço) consumir sem precisar importar Python)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Ajuste este caminho conforme a posição do parser.py no projeto da
    # equipe. Por padrão, assume que parser.py está em src/ e a pasta
    # emails_matriz/ está um nível acima.
    pasta_padrao = Path(__file__).parent.parent / "emails_matriz"
    if not pasta_padrao.exists():
        pasta_padrao = Path("emails_matriz")  # fallback: pasta local

    resultados = parse_pasta(pasta_padrao)

    print(json.dumps(resultados, indent=2, ensure_ascii=False))

    saida = Path("ecos_extraidas.json")
    saida.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Resultado salvo em: %s", saida.resolve())
