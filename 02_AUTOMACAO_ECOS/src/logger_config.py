"""
Configuração centralizada de logs para a automação de ECOs.
Suporta INFO, WARNING, ERROR e CRITICAL conforme exigido pelo roteiro.
"""

import logging
import sys
from pathlib import Path

# Cria diretório de logs se não existir
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configuração do Logger principal
logger = logging.getLogger("eco_automation")
logger.setLevel(logging.INFO)

# Evita duplicação de handlers se já estiverem configurados
if not logger.handlers:
    # Handler para o Console (Terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # Handler para Arquivo de Log
    file_handler = logging.FileHandler(LOGS_DIR / "execucao_ecos.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)


def disparar_alerta_critico(mensagem: str, codigo_eco: str = "GERAL"):
    """Mecanismo de alerta para falhas críticas no sistema."""
    logger.critical(f"ALERTA CRÍTICO [ECO: {codigo_eco}] — {mensagem}")
    # Aqui poderíamos disparar webhook, e-mail ou notificação externa se necessário