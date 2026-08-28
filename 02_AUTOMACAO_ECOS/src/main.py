"""
main.py — Orquestrador Principal com Circuit Breaker, Gravação na Planilha Mestra e Playwright
"""

import json
import logging
from pathlib import Path
import pandas as pd

from leitura_email import LeitorEmails
from extracao_eco import ExtratorECO
from validator import ECOValidatorGateway, GatewayAction
from bot_playwright import registrar_eco
from eco_circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from logger_config import disparar_alerta_critico

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eco_automation.main")

PASTA_EMAILS = Path(__file__).parent.parent / "emails_matriz"
PLANILHA_MESTRA = Path(__file__).parent.parent / "data" / "controle_mestre_ecos.xlsx"


def salvar_na_planilha_mestra(dados_eco: dict, status_processamento: str):
    """Insere ou atualiza o registro da ECO na planilha mestra oficial da empresa."""
    try:
        if PLANILHA_MESTRA.exists():
            df = pd.read_excel(PLANILHA_MESTRA)
        else:
            df = pd.DataFrame()

        # Cria linha com os dados da ECO
        nova_linha = {
            "Codigo_ECO": dados_eco.get("Codigo_ECO"),
            "Titulo_Alteracao": dados_eco.get("Titulo_Alteracao"),
            "Area_Solicitante": dados_eco.get("Area_Solicitante"),
            "Nome_Engenheiro_Responsavel": dados_eco.get("Nome_Engenheiro_Responsavel"),
            "Email_Solicitante": dados_eco.get("Email_Solicitante"),
            "Data_Recebimento": dados_eco.get("Data_Recebimento"),
            "Nivel_Prioridade": dados_eco.get("Nivel_Prioridade"),
            "Status_Atual": dados_eco.get("Status_Atual"),
            "Justificativa_Tecnica": dados_eco.get("Justificativa_Tecnica"),
            "Codigo_Item_Afetado": dados_eco.get("Codigo_Item_Afetado"),
            "Categoria_Mudanca": dados_eco.get("Categoria_Mudanca"),
            "Impacto_Custos": dados_eco.get("Impacto_Custos"),
            "Estimativa_Orcamento": dados_eco.get("Estimativa_Orcamento"),
            "Unidade_Fabril": dados_eco.get("Unidade_Fabril"),
            "Data_Implementacao_Alvo": dados_eco.get("Data_Implementacao_Alvo"),
            "Status_Automacao": status_processamento
        }

        # Adiciona ao DataFrame e salva
        df_novo = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        df_novo.to_excel(PLANILHA_MESTRA, index=False)
        logger.info(f"[{dados_eco.get('Codigo_ECO')}] Planilha mestra atualizada com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao salvar na planilha mestra: {e}")


def main():
    logger.info("Iniciando o ciclo automatizado de processamento de ECOs...")
    
    leitor = LeitorEmails(pasta=PASTA_EMAILS)
    extrator = ExtratorECO()
    cb = CircuitBreaker(limite_falhas=3, tempo_recuperacao=5)

    emails = leitor.buscar_novos_emails()
    logger.info("Total de e-mails identificados na fila: %d", len(emails))

    resultados_processamento = []

    for email in emails:
        print("\n" + "=" * 70)
        logger.info(f"Processando arquivo: {email.nome_arquivo}")

        try:
            cb.verificar_estado()
        except CircuitBreakerOpenException as cbe:
            logger.error(f"BLOQUEIO CRÍTICO: {cbe}")
            disparar_alerta_critico(str(cbe), codigo_eco=email.nome_arquivo)
            break

        eco_extraida = extrator.extrair(email.conteudo, nome_arquivo=email.nome_arquivo)
        leitor.marcar_como_processado(email)
        dados_brutos = eco_extraida.to_dict()

        dados_validator = {
            "eco_id": dados_brutos.get("Codigo_ECO", "ECO-00000"),
            "titulo_alteracao": dados_brutos.get("Titulo_Alteracao"),
            "solicitante": dados_brutos.get("Nome_Engenheiro_Responsavel"),
            "area_solicitante": dados_brutos.get("Area_Solicitante"),
            "email_solicitante": dados_brutos.get("Email_Solicitante"),
            "data_recebimento": dados_brutos.get("Data_Recebimento"),
            "prioridade": dados_brutos.get("Nivel_Prioridade"),
            "status_atual": dados_brutos.get("Status_Atual"),
            "justificativa_tecnica": dados_brutos.get("Justificativa_Tecnica"),
            "codigo_item": dados_brutos.get("Codigo_Item_Afetado"),
            "tipo_mudanca": dados_brutos.get("Categoria_Mudanca"),
            "categoria": "DisplayMedia" if "Display" in str(dados_brutos.get("Categoria_Mudanca")) else "Módulos",
            "sufixo": "BRA",
            "custo_estimado_usd": dados_brutos.get("Estimativa_Orcamento", 0),
            "data_alvo_implementacao": dados_brutos.get("Data_Implementacao_Alvo"),
        }

        action, eco_obj, mensagem_gateway = ECOValidatorGateway.process(dados_validator)
        logger.info(f"Gateway decidiu: {action.value} — {mensagem_gateway}")

        if action == GatewayAction.PROSSEGUIR_SISTEMA:
            cenario = "normal"
        elif action == GatewayAction.VALIDACAO_HUMANA:
            cenario = "ambiguo"
        else:
            cenario = "erro"

        try:
            resultado_web = registrar_eco(dados_brutos, cenario=cenario)
            if resultado_web.get("status") == "FALHA_REGISTRO":
                cb.registrar_falha(dados_brutos.get("Codigo_ECO", "GERAL"))
            else:
                cb.registrar_sucesso()
        except Exception as exc:
            cb.registrar_falha(dados_brutos.get("Codigo_ECO", "GERAL"))
            logger.error(f"Erro crítico na automação web: {exc}")
            resultado_web = {"status": "ERRO_SISTEMA", "evidencia": None}

        # Atualiza a planilha mestra oficial com o status correspondente
        salvar_na_planilha_mestra(dados_brutos, status_processamento=resultado_web.get("status"))

        resultado_final = {
            "arquivo": email.nome_arquivo,
            "gateway_action": action.value,
            "mensagem_gateway": mensagem_gateway,
            "status_web": resultado_web.get("status"),
            "evidencia": resultado_web.get("evidencia"),
            "dados": dados_brutos,
        }
        resultados_processamento.append(resultado_final)

    caminho_json = Path(__file__).parent.parent / "ecos_processadas.json"
    caminho_json.write_text(json.dumps(resultados_processamento, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Processamento finalizado. Relatório salvo em: %s", caminho_json.resolve())


if __name__ == "__main__":
    main()