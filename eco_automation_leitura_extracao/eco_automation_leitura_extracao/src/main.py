"""
main.py — Demonstração das etapas: E-mail -> Leitura -> Extração

Executa o fluxo nos 3 cenários obrigatórios da avaliação:
  1) normal_ECO_00125.txt  (deve extrair os 15 campos sem faltas)
  2) ambiguo_ECO_00126.txt (deve faltar Data_Implementacao_Alvo)
  3) erro_ECO_00127.txt    (extrai tudo, mas orçamento vem "-500" -> a
                             VALIDAÇÃO, próxima etapa, é quem vai barrar isso)

Rode a partir da pasta src/:
    python main.py
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
        resultados.append(eco)

        print("\n" + "=" * 70)
        print(f"Arquivo: {email.nome_arquivo}")
        print(json.dumps(eco.to_dict(), indent=2, ensure_ascii=False))
        if eco.campos_ausentes:
            print(f"⚠️  Campos ausentes: {eco.campos_ausentes}")
        else:
            print("✅ Todos os 15 campos extraídos com sucesso.")

    return resultados


if __name__ == "__main__":
    main()
