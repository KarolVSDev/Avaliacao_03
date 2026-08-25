# Validações para ECO válida, incompleta e com dado inválido


"""
Módulo de Testes Unitários de Validação e Gateway
Arquivo: tests/test_ecos.py
Disciplina: Técnicas de Hyperautomation — Prof. Moisés Levy
Autor: João (Equipe 02)
"""

import pytest
from src.validator import ECOValidatorGateway, GatewayAction, ECOModel


# =====================================================================
# 1. TESTE DO CENÁRIO 01 — NORMAL (normal_ECO_00125.txt)
# =====================================================================
def test_cenario_01_normal_processamento_automatico():
    """
    Testa uma ECO válida com todos os 15 campos e regras atendidas.
    Esperado: GatewayAction.PROSSEGUIR_SISTEMA
    """
    payload_normal = {
        "eco_id": "ECO-00125",
        "titulo_alteracao": "Atualização do layout do módulo de refrigeração",
        "solicitante": "Ana Souza",
        "area_solicitante": "Engenharia",
        "email_solicitante": "ana.souza@matriz.example",
        "data_recebimento": "2026-08-20",
        "prioridade": "Alta",
        "status_atual": "Recebido",
        "justificativa_tecnica": "Adequação do posicionamento do componente para melhoria de montagem.",
        "codigo_item": "ITEM-REF-220",
        "tipo_mudanca": "Layout",
        "categoria": "Módulos",
        "sufixo": "BRA",
        "custo_estimado_usd": 0.0,
        "data_alvo_implementacao": "2026-09-15"
    }

    action, eco_obj, msg = ECOValidatorGateway.process(payload_normal)

    # Asserções do Cenário 01
    assert action == GatewayAction.PROSSEGUIR_SISTEMA
    assert isinstance(eco_obj, ECOModel)
    assert eco_obj.eco_id == "ECO-00125"
    assert eco_obj.custo_estimado_usd == 0.0
    assert eco_obj.data_alvo_implementacao == "2026-09-15"
    assert "aprovada" in msg.lower() or "sucesso" in msg.lower()


# =====================================================================
# 2. TESTE DO CENÁRIO 02 — AMBÍGUO (ambiguo_ECO_00126.txt)
# =====================================================================
@pytest.mark.parametrize("data_ausente", [None, "", "   ", "none", "null", "N/A"])
def test_cenario_02_ambiguo_data_alvo_ausente(data_ausente):
    """
    Testa uma ECO com ausência da data de implementação alvo.
    Esperado: GatewayAction.VALIDACAO_HUMANA
    """
    payload_ambiguo = {
        "eco_id": "ECO-00126",
        "titulo_alteracao": "Substituição de conector de placa-mãe",
        "solicitante": "Carlos Mendes",
        "categoria": "Canal de PC",
        "sufixo": "WZ",
        "custo_estimado_usd": 1200.0,
        "data_alvo_implementacao": data_ausente  # Variações de ausência
    }

    action, eco_obj, msg = ECOValidatorGateway.process(payload_ambiguo)

    # Asserções do Cenário 02
    assert action == GatewayAction.VALIDACAO_HUMANA
    assert eco_obj is not None
    assert "data de implementação" in msg.lower() or "ausente" in msg.lower()


# =====================================================================
# 3. TESTE DO CENÁRIO 03 — ERRO (erro_ECO_00127.txt)
# =====================================================================
def test_cenario_03_erro_orcamento_negativo():
    """
    Testa uma ECO contendo orçamento inválido de -500 USD.
    Esperado: GatewayAction.REJEITAR_E_REGISTRAR
    """
    payload_erro = {
        "eco_id": "ECO-00127",
        "titulo_alteracao": "Troca de painel frontal",
        "categoria": "DisplayMedia",
        "sufixo": "WR",
        "custo_estimado_usd": -500.0,  # Valor inválido de teste
        "data_alvo_implementacao": "2026-10-01"
    }

    action, eco_obj, msg = ECOValidatorGateway.process(payload_erro)

    # Asserções do Cenário 03
    assert action == GatewayAction.REJEITAR_E_REGISTRAR
    assert eco_obj is None
    assert "negativo" in msg.lower() or "orçamento" in msg.lower()


# =====================================================================
# 4. TESTES COMPLEMENTARES DE REGRAS DE NEGÓCIO (PDD)
# =====================================================================
def test_regra_negocio_sufixo_invalido():
    """
    Garante que sufixos fora de ('WZ', 'WR', 'WP', 'BRA') sejam rejeitados.
    """
    payload = {
        "eco_id": "ECO-00128",
        "categoria": "Módulos",
        "sufixo": "INVAL_99",
        "custo_estimado_usd": 250.0,
        "data_alvo_implementacao": "2026-11-01"
    }

    action, eco_obj, msg = ECOValidatorGateway.process(payload)

    assert action == GatewayAction.REJEITAR_E_REGISTRAR
    assert eco_obj is None
    assert "sufixo" in msg.lower()


def test_regra_negocio_categoria_invalida():
    """
    Garante que categorias fora de ('DisplayMedia', 'Canal de PC', 'Módulos') sejam rejeitadas.
    """
    payload = {
        "eco_id": "ECO-00129",
        "categoria": "CategoriaDesconhecida",
        "sufixo": "BRA",
        "custo_estimado_usd": 300.0,
        "data_alvo_implementacao": "2026-11-01"
    }

    action, eco_obj, msg = ECOValidatorGateway.process(payload)

    assert action == GatewayAction.REJEITAR_E_REGISTRAR
    assert eco_obj is None
    assert "categoria" in msg.lower()


def test_regra_formato_id_invalido():
    """
    Garante que IDs que não sigam o padrão 'ECO-XXXX' ou 'ECO_XXXX' sejam rejeitados.
    """
    payload = {
        "eco_id": "ID_ERRADO_123",
        "categoria": "DisplayMedia",
        "sufixo": "BRA",
        "custo_estimado_usd": 500.0,
        "data_alvo_implementacao": "2026-11-01"
    }

    action, eco_obj, msg = ECOValidatorGateway.process(payload)

    assert action == GatewayAction.REJEITAR_E_REGISTRAR
    assert eco_obj is None
    assert "formato de id" in msg.lower() or "id" in msg.lower()