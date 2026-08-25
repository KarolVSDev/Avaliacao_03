"""
Módulo: leitura_email.py
Etapa do fluxo: E-mail -> LEITURA -> Extração

Responsável por "monitorar" a pasta de e-mails simulados (emails_matriz/)
e ler o conteúdo bruto de cada e-mail (.txt) que representa uma ECO
enviada pela matriz.

Na Avaliação 3, o "monitoramento de e-mails" e a caixa BEM são
representados localmente por arquivos .txt dentro de emails_matriz/,
então aqui simulamos:
  - a chegada de novos e-mails (varredura da pasta)
  - a leitura do conteúdo de cada e-mail
  - o controle de quais e-mails já foram processados (evita reprocessar)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger("eco_automation.leitura")


@dataclass
class EmailBruto:
    """Representa um e-mail simulado ainda não processado."""
    caminho: Path
    nome_arquivo: str
    conteudo: str


class LeitorEmails:
    """
    Simula o monitoramento de uma caixa de e-mail (BEM), varrendo uma pasta
    local com arquivos .txt (um por e-mail/ECO).

    Uso típico:
        leitor = LeitorEmails(pasta="emails_matriz")
        for email in leitor.buscar_novos_emails():
            print(email.conteudo)
    """

    def __init__(self, pasta: str | Path, extensao: str = ".txt"):
        self.pasta = Path(pasta)
        self.extensao = extensao
        # controle simples de "já processados" (em produção isso viraria
        # uma tabela no banco / arquivo de estado persistente)
        self._processados: set[str] = set()

        if not self.pasta.exists():
            raise FileNotFoundError(
                f"Pasta de e-mails não encontrada: {self.pasta.resolve()}"
            )

    def buscar_novos_emails(self) -> List[EmailBruto]:
        """
        Varre a pasta e retorna somente os e-mails ainda não processados
        nesta sessão, ordenados pelo nome do arquivo (ordem de chegada
        simulada).
        """
        arquivos = sorted(self.pasta.glob(f"*{self.extensao}"))
        novos: List[EmailBruto] = []

        for arquivo in arquivos:
            if arquivo.name in self._processados:
                continue

            try:
                conteudo = arquivo.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                conteudo = arquivo.read_text(encoding="latin-1")

            novos.append(
                EmailBruto(
                    caminho=arquivo,
                    nome_arquivo=arquivo.name,
                    conteudo=conteudo,
                )
            )
            logger.info("Novo e-mail identificado: %s", arquivo.name)

        return novos

    def marcar_como_processado(self, email: EmailBruto) -> None:
        """Marca um e-mail como já tratado, para não ser lido novamente."""
        self._processados.add(email.nome_arquivo)
        logger.info("E-mail marcado como processado: %s", email.nome_arquivo)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    leitor = LeitorEmails(pasta="../emails_matriz")
    for email in leitor.buscar_novos_emails():
        print("=" * 60)
        print(email.nome_arquivo)
        print(email.conteudo)