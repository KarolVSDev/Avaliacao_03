# Regras de negócio, 15 campos e detecção de erros/ambiguidade
# Regras de negócio, 15 campos e detecção de erros/ambiguidade


"""Módulo: Validação e Gateway de Decisão
Autor: João (Equipe 02)
Disciplina: Técnicas de Hyperautomation — Prof. Moisés Levy"""

import re
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, field_validator, ValidationError

# Import defensivo do logger configurado pela equipe
try:
    from src.logger_config import logger
except ImportError:
    try:
        from logger_config import logger
    except ImportError:
        from loguru import logger


# =====================================================================
# 1. ENUM DE AÇÕES DO GATEWAY
# =====================================================================
class GatewayAction(str, Enum):
    PROSSEGUIR_SISTEMA = "PROSSEGUIR_SISTEMA"      # Cenário 01: Normal -> Playwright (Caroline)
    VALIDACAO_HUMANA = "VALIDACAO_HUMANA"          # Cenário 02: Ambíguo -> Fila de Análise Manual
    REJEITAR_E_REGISTRAR = "REJEITAR_E_REGISTRAR"  # Cenário 03: Dado Inválido -> Registro de Erro


# =====================================================================
# 2. REGRAS DE NEGÓCIO E CATÁLOGOS PERMITIDOS (PDD)
# =====================================================================
ALLOWED_SUFFIXES = ("WZ", "WR", "WP", "BRA")
ALLOWED_CATEGORIES = ("DisplayMedia", "Canal de PC", "Módulos")


# =====================================================================
# 3. SCHEMA DOS 15 CAMPOS OBRIGATÓRIOS DO CONTROLE MESTRE
# =====================================================================
class ECOModel(BaseModel):
    eco_id: str
    titulo_alteracao: Optional[str] = "Não informado"
    solicitante: Optional[str] = "Não informado"
    area_solicitante: Optional[str] = "Engenharia"
    email_solicitante: Optional[str] = "contato@empresa.com"
    data_recebimento: Optional[str] = None
    prioridade: Optional[str] = "Média"
    status_atual: Optional[str] = "Recebido"
    justificativa_tecnica: Optional[str] = "Sem justificativa"
    codigo_item: Optional[str] = "N/A"
    tipo_mudanca: Optional[str] = "Layout"
    categoria: str
    sufixo: str
    custo_estimado_usd: float
    data_alvo_implementacao: Optional[str] = None

    # Validação do Formato do ID (Ex: ECO-00125 ou ECO_00125)
    @field_validator("eco_id")
    def validate_eco_id(cls, v: str) -> str:
        v_clean = str(v).strip().upper()
        if not re.match(r"^ECO[-_]\d+$", v_clean):
            raise ValueError(f"Formato de ID inválido: '{v}'. Esperado padrão ECO-XXXXX ou ECO_XXXXX")
        return v_clean

    # Regra Cenário 03: Orçamento não pode ser negativo (-500 USD)
    @field_validator("custo_estimado_usd")
    def validate_budget(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Orçamento inválido ({v} USD). Valores negativos não são permitidos.")
        return v

    # Regra PDD: Categoria autorizada
    @field_validator("categoria")
    def validate_category(cls, v: str) -> str:
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"Categoria '{v}' fora do catálogo permitido: {ALLOWED_CATEGORIES}")
        return v

    # Regra PDD: Sufixo autorizado
    @field_validator("sufixo")
    def validate_suffix(cls, v: str) -> str:
        if v not in ALLOWED_SUFFIXES:
            raise ValueError(f"Sufixo '{v}' inválido. Sufixos permitidos: {ALLOWED_SUFFIXES}")
        return v


# =====================================================================
# 4. CLASSE DO GATEWAY DE DECISÃO
# =====================================================================
class ECOValidatorGateway:
    @staticmethod
    def process(raw_data: Dict[str, Any]) -> Tuple[GatewayAction, Optional[ECOModel], str]:
        """
        Recebe o dicionário de dados brutos extraídos do e-mail (.txt),
        valida os 15 campos e regras de negócio, e decide o fluxo.

        Retorna:
            (GatewayAction, ECOModel instanciado ou None, mensagem_de_log)
        """
        eco_id = raw_data.get("eco_id", "ID_NAO_ENCONTRADO")

        # Conversão defensiva para valores numéricos
        data_copy = raw_data.copy()
        if "custo_estimado_usd" in data_copy:
            try:
                data_copy["custo_estimado_usd"] = float(data_copy["custo_estimado_usd"])
            except (ValueError, TypeError):
                msg_erro = f"Orçamento '{data_copy['custo_estimado_usd']}' não é um número válido."
                logger.error(f"ERRO - {msg_erro}")
                return GatewayAction.REJEITAR_E_REGISTRAR, None, msg_erro

        # --- ETAPA 1: Validação de Tipos, Valores e Domínio (Cenário 03 - Erro) ---
        try:
            eco_obj = ECOModel(**data_copy)
        except ValidationError as err:
            detalhes = "; ".join([f"{e['loc'][0]}: {e['msg']}" for e in err.errors()])
            msg_erro = f"Dado Inválido detectado na ECO {eco_id}: {detalhes}"
            logger.error(f"ERRO - {msg_erro}")
            return GatewayAction.REJEITAR_E_REGISTRAR, None, msg_erro

        # --- ETAPA 2: Validação de Ambiguidade / Campo Obrigatório Ausente (Cenário 02 - Ambíguo) ---
        target_date = eco_obj.data_alvo_implementacao
        if not target_date or str(target_date).strip().lower() in ["", "none", "null", "n/a", "undefined"]:
            msg_ambiguo = f"Data de implementação alvo ausente na ECO {eco_id}."
            logger.warning(f"AVISO - {msg_ambiguo} Encaminhando para validação humana.")
            return GatewayAction.VALIDACAO_HUMANA, eco_obj, msg_ambiguo

        # --- ETAPA 3: Fluxo Aprovado com Sucesso (Cenário 01 - Normal) ---
        msg_sucesso = f"ECO {eco_id} validada com sucesso em todos os campos."
        logger.info(f"INFO - {msg_sucesso}")
        return GatewayAction.PROSSEGUIR_SISTEMA, eco_obj, msg_sucesso
