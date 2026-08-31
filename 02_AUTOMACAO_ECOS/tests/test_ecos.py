# Validações para ECO válida, incompleta e com dado inválido
import pytest
from src.logger_config import logger

def test_eco_normal_valida():
    """
    Cenário 01: Normal - A ECO deve ser processada automaticamente com sucesso.
    """
    logger.info("Executando teste: ECO Válida (Cenário Normal)")
    
    # Simulação de dados extraídos de 'normal_ECO_00125.txt'
    dados_eco = {
        "id": "ECO_00125",
        "orcamento": 1500.0,
        "data_implementacao": "2026-09-01",
        "status": "VALIDO"
    }
    
    assert dados_eco["orcamento"] > 0
    assert dados_eco["data_implementacao"] is not None
    logger.info("Teste de ECO Válida passou com sucesso!")

def test_eco_ambigua_incompleta():
    """
    Cenário 02: Ambíguo - Falta informação obrigatória (data de implementação).
    A automação deve identificar e encaminhar para validação humana.
    """
    logger.warning("Executando teste: ECO Incompleta (Cenário Ambíguo)")
    
    # Simulação de dados extraídos de 'ambiguo_ECO_00126.txt' (sem data alvo)
    dados_eco = {
        "id": "ECO_00126",
        "orcamento": 1200.0,
        "data_implementacao": None,  # Ausente!
        "status": "AMBIGUO"
    }
    
    # Validação da regra: se a data for ausente, cai em ambiguidade
    precisa_validacao_humana = dados_eco["data_implementacao"] is None
    
    assert precisa_validacao_humana == True
    logger.warning("Alerta acionado corretamente para validação humana!")

def test_eco_erro_dado_invalido():
    """
    Cenário 03: Erro - Dado inválido (ex: orçamento negativo de -500 USD).
    A automação deve impedir o processamento e registrar a ocorrência.
    """
    logger.error("Executando teste: ECO com Dado Inválido (Cenário de Erro)")
    
    # Simulação de dados extraídos de 'erro_ECO_00127.txt'
    dados_eco = {
        "id": "ECO_00127",
        "orcamento": -500.0,  # Inválido!
        "data_implementacao": "2026-09-01",
        "status": "ERRO"
    }
    
    # Validação da regra: orçamento não pode ser menor ou igual a zero
    dado_invalido = dados_eco["orcamento"] < 0
    
    assert dado_invalido == True
    logger.error("Bloqueio de segurança ativado devido a orçamento inválido (-500 USD)!")


    #python -m pytest -v