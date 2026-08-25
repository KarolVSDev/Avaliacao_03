# Configuração de logs estruturados (INFO, AVISO, ERRO, CRÍTICO)

import logging
import os

def setup_logger():
    # Cria a pasta de logs se não existir
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger("AutomacaoECOS")
    logger.setLevel(logging.INFO)

    # Evita duplicação de handlers se a função for chamada mais de uma vez
    if not logger.handlers:
        # Formato do Log
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Handler para arquivo de log
        file_handler = logging.FileHandler("logs/automacao.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Handler para o console (terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Instância global pronta para ser importada nos outros módulos
logger = setup_logger()