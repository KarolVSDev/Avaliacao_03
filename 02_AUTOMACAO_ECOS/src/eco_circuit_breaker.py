"""
Mecanismo de Circuit Breaker para evitar loops e tentativas infinitas
em caso de falhas consecutivas no sistema web simulado.
"""

import time
from logger_config import logger, disparar_alerta_critico


class CircuitBreakerOpenException(Exception):
    """Exceção lançada quando o circuito está aberto (bloqueado por excesso de falhas)."""
    pass


class CircuitBreaker:
    def __init__(self, limite_falhas: int = 3, tempo_recuperacao: int = 10):
        self.limite_falhas = limite_falhas
        self.tempo_recuperacao = tempo_recuperacao  # em segundos
        self.falhas_consecutivas = 0
        self.estado = "FECHADO"  # FECHADO, ABERTO, SEMI-ABERTO
        self.tempo_ultima_falha = 0.0

    def registrar_sucesso(self):
        """Reseta o contador se a operação for bem-sucedida."""
        if self.falhas_consecutivas > 0:
            logger.info("Circuit Breaker: Operação bem-sucedida. Resetando contador de falhas.")
        self.falhas_consecutivas = 0
        self.estado = "FECHADO"

    def registrar_falha(self, codigo_eco: str):
        """Incrementa falhas e abre o circuito se atingir o limite."""
        self.falhas_consecutivas += 1
        self.tempo_ultima_falha = time.time()
        
        logger.warning(
            f"Circuit Breaker: Falha detectada ({self.falhas_consecutivas}/{self.limite_falhas}) "
            f"para a ECO {codigo_eco}."
        )

        if self.falhas_consecutivas >= self.limite_falhas:
            self.estado = "ABERTO"
            msg = (
                f"Circuit Breaker ABERTO devido a {self.falhas_consecutivas} falhas consecutivas. "
                "Novas execuções bloqueadas temporariamente para proteger o sistema."
            )
            disparar_alerta_critico(msg, codigo_eco=codigo_eco)

    def verificar_estado(self):
        """Verifica se o circuito pode tentar reabrir (semi-aberto) ou se continua bloqueado."""
        if self.estado == "ABERTO":
            tempo_decorrido = time.time() - self.tempo_ultima_falha
            if tempo_decorrido > self.tempo_recuperacao:
                self.estado = "SEMI-ABERTO"
                logger.info("Circuit Breaker: Tempo de recuperação atingido. Mudando para SEMI-ABERTO (tentativa controlada).")
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit Breaker BLOQUEADO. Aguarde {int(self.tempo_recuperacao - tempo_decorrido)}s para novas tentativas."
                )