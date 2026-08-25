"""
main.py — Orquestrador Principal do Robô de ECOs
Integra: Leitura (André) -> Extração (André) -> Validação/Gateway (João) -> Playwright (Caroline)
"""

import json
import logging
from pathlib import Path

# from src.leitura_email import LeitorEmails
# from src.extracao_eco import ExtratorECO
# from src.validator import ECOValidatorGateway, GatewayAction
# from src.bot_playwright import registrar_eco
from leitura_email import LeitorEmails
from extracao_eco import ExtratorECO
from validator import ECOValidatorGateway, GatewayAction
from bot_playwright import registrar_eco

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("eco_automation.main")

PASTA_EMAILS = Path(__file__).parent.parent / "emails_matriz"


def main():
    logger.info("Iniciando o ciclo de processamento de ECOs...")
    
    leitor = LeitorEmails(pasta=PASTA_EMAILS)
    extrator = ExtratorECO()

    emails = leitor.buscar_novos_emails()
    logger.info("Total de e-mails encontrados na fila: %d", len(emails))

    resultados_processamento = []

    for email in emails:
        print("\n" + "=" * 70)
        logger.info(f"Processando arquivo: {email.nome_arquivo}")

        # ETAPA 1 & 2: Leitura e Extração (André)
        eco_extraida = extrator.extrair(email.conteudo, nome_arquivo=email.nome_arquivo)
        leitor.marcar_como_processado(email)

        # Prepara os dados brutos para o formato que o validador do João espera
        dados_brutos = eco_extraida.to_dict()
        
        # Mapeia as chaves para corresponder ao ECOModel do validator.py
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
            # Valores simulados/padrão para categoria e sufixo exigidos pelo PDD do validador
            "categoria": "DisplayMedia" if "Display" in str(dados_brutos.get("Categoria_Mudanca")) else "Módulos",
            "sufixo": "BRA",
            "custo_estimado_usd": dados_brutos.get("Estimativa_Orcamento", 0),
            "data_alvo_implementacao": dados_brutos.get("Data_Implementacao_Alvo"),
        }

        # ETAPA 3: Validação e Gateway de Decisão (João)
        action, eco_obj, mensagem_gateway = ECOValidatorGateway.process(dados_validator)
        logger.info(f"Gateway decidiu: {action.value} — {mensagem_gateway}")

        # ETAPA 4: Automação Web / Fallback / Bloqueio (Caroline via Playwright)
        # Mapeia a ação do gateway para os cenários esperados pelo bot_playwright.py
        if action == GatewayAction.PROSSEGUIR_SISTEMA:
            cenario = "normal"
        elif action == GatewayAction.VALIDACAO_HUMANA:
            cenario = "ambiguo"
        else:
            cenario = "erro"

        # Executa o bot web enviando os dados originais extraídos
        resultado_web = registrar_eco(dados_brutos, cenario=cenario)

        # Agrega o resultado final da ECO
        resultado_final = {
            "arquivo": email.nome_arquivo,
            "gateway_action": action.value,
            "mensagem_gateway": mensagem_gateway,
            "status_web": resultado_web.get("status"),
            "evidencia": resultado_web.get("evidencia"),
            "dados": dados_brutos,
        }
        resultados_processamento.append(resultado_final)

    # Salva o consolidado final na raiz
    caminho_json = Path(__file__).parent.parent / "ecos_processadas.json"
    caminho_json.write_text(json.dumps(resultados_processamento, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Processamento concluído. Relatório salvo em: %s", caminho_json.resolve())


if __name__ == "__main__":
    main()