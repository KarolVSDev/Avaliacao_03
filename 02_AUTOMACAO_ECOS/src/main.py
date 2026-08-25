"""
main.py — Demonstração das etapas: E-mail -> Leitura -> Extração -> Salvamento JSON
"""

import json
import logging
from pathlib import Path

from leitura_email import LeitorEmails
from extracao_eco import ExtratorECO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("eco_automation.main")

PASTA_EMAILS = Path(__file__).parent.parent / "emails_matriz"


def main():
    leitor = LeitorEmails(pasta=PASTA_EMAILS)
    extrator = ExtratorECO()

    emails = leitor.buscar_novos_emails()
    logger.info("Total de e-mails encontrados: %d", len(emails))

    resultados = []

    for email in emails:
        eco = extrator.extrair(email.conteudo, nome_arquivo=email.nome_arquivo)
        leitor.marcar_como_processado(email)
        
        # Adiciona o dicionário (incluindo os metadados úteis) na lista
        dados_eco = eco.to_dict()
        dados_eco["_arquivo_origem"] = eco.arquivo_origem
        dados_eco["_campos_ausentes"] = eco.campos_ausentes
        
        resultados.append(dados_eco)

        print("\n" + "=" * 70)
        print(f"Arquivo: {email.nome_arquivo}")
        print(json.dumps(dados_eco, indent=2, ensure_ascii=False))
        if eco.campos_ausentes:
            print(f"⚠️ Campos ausentes: {eco.campos_ausentes}")
        else:
            print("✅ Todos os 15 campos extraídos com sucesso.")

    # SALVA O JSON NA RAIZ DO PROJETO
    caminho_json = Path(__file__).parent.parent / "ecos_extraidas.json"
    caminho_json.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Arquivo JSON gerado com sucesso em: %s", caminho_json.resolve())

    return resultados


if __name__ == "__main__":
    main()