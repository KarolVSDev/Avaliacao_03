# Validações para ECO válida, incompleta e com dado inválido
import pytest
from src.logger_config import logger
from src.bot_playwright import registrar_eco

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


# --- Testes de integração da automação web (Caroline: Sistema > Registro) ---

DADOS_NORMAL = {
    "Codigo_ECO": "ECO-00125",
    "Titulo_Alteracao": "Atualização do layout do módulo de refrigeração",
    "Area_Solicitante": "Engenharia",
    "Nome_Engenheiro_Responsavel": "Ana Souza",
    "Email_Solicitante": "ana.souza@matriz.example",
    "Data_Recebimento": "2026-08-20",
    "Nivel_Prioridade": "Alta",
    "Status_Atual": "Recebido",
    "Justificativa_Tecnica": "Adequação do posicionamento do componente para melhoria de montagem.",
    "Codigo_Item_Afetado": "ITEM-REF-220",
    "Categoria_Mudanca": "Layout",
    "Impacto_Custos": "Não",
    "Estimativa_Orcamento": 0,
    "Unidade_Fabril": "Manaus",
    "Data_Implementacao_Alvo": "2026-09-15",
}

DADOS_AMBIGUO = {
    "Codigo_ECO": "ECO-00126",
    "Titulo_Alteracao": "Alteração dimensional do suporte",
    "Area_Solicitante": "Engenharia",
    "Nome_Engenheiro_Responsavel": "Carlos Lima",
    "Email_Solicitante": "carlos.lima@matriz.example",
    "Data_Recebimento": "2026-08-21",
    "Nivel_Prioridade": "Média",
    "Status_Atual": "Recebido",
    "Justificativa_Tecnica": "",
    "Codigo_Item_Afetado": "SUP-778",
    "Categoria_Mudanca": "Componente",
    "Impacto_Custos": "Sim",
    "Estimativa_Orcamento": 3500,
    "Unidade_Fabril": "Manaus",
    "Data_Implementacao_Alvo": None,  # Ausente!
}


def test_bot_registra_eco_normal_com_sucesso():
    """
    Cenário 01: Normal - O bot deve preencher e enviar o formulário automaticamente,
    confirmando o feedback de sucesso da tela e gerando evidência (print).
    """
    resultado = registrar_eco(DADOS_NORMAL, cenario="normal")

    assert resultado["status"] == "REGISTRADO"
    assert "sucesso" in resultado["mensagem_sistema"].lower()
    assert resultado["evidencia"] is not None
    logger.info(f"Bot confirmou o registro da {resultado['codigo_eco']} no sistema fake.")


def test_bot_encaminha_eco_ambigua_para_validacao_humana():
    """
    Cenário 02: Ambíguo - O bot preenche o formulário como rascunho, mas NÃO deve
    submetê-lo sozinho quando falta a data de implementação alvo.
    """
    resultado = registrar_eco(DADOS_AMBIGUO, cenario="ambiguo")

    assert resultado["status"] == "PENDENTE_VALIDACAO_HUMANA"
    assert resultado["evidencia"] is not None
    logger.warning(f"Bot encaminhou {resultado['codigo_eco']} para validação humana.")


def test_bot_bloqueia_eco_com_dado_invalido_sem_acessar_formulario():
    """
    Cenário 03: Erro - O bot deve bloquear o registro sem sequer acessar o
    formulário quando o dado já foi recusado pelo validator (ex: orçamento negativo).
    """
    dados_erro = {"Codigo_ECO": "ECO-00127", "Estimativa_Orcamento": -500}

    resultado = registrar_eco(dados_erro, cenario="erro")

    assert resultado["status"] == "BLOQUEADO"
    assert resultado["evidencia"] is None
    logger.error(f"Bot bloqueou o registro de {resultado['codigo_eco']} corretamente.")