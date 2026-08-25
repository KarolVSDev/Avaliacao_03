# Automação web para preenchimento do formulário fake

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

from src.logger_config import logger

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
EVIDENCIAS_DIR = BASE_DIR / "evidencias"

# Ordem/nome dos campos definidos em web/formulario_eco_fake.html,
# que correspondem aos 15 campos obrigatórios de controle_mestre_ecos.xlsx
CAMPOS_FORMULARIO = [
    "Codigo_ECO",
    "Titulo_Alteracao",
    "Area_Solicitante",
    "Nome_Engenheiro_Responsavel",
    "Email_Solicitante",
    "Data_Recebimento",
    "Nivel_Prioridade",
    "Status_Atual",
    "Justificativa_Tecnica",
    "Codigo_Item_Afetado",
    "Categoria_Mudanca",
    "Impacto_Custos",
    "Estimativa_Orcamento",
    "Unidade_Fabril",
    "Data_Implementacao_Alvo",
]


def _form_url() -> str:
    """Resolve a URL do formulário a partir do .env (ECO_URL) com fallback para o arquivo local."""
    url = os.getenv("ECO_URL")
    if url:
        return url
    caminho_local = BASE_DIR / "web" / "formulario_eco_fake.html"
    return caminho_local.resolve().as_uri()


def _print_evidencia(page: Page, codigo_eco: str, etapa: str) -> str:
    """Salva um print da tela como evidência do processamento em evidencias/."""
    EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"{codigo_eco}_{etapa}_{timestamp}.png"
    caminho = EVIDENCIAS_DIR / nome_arquivo
    page.screenshot(path=str(caminho), full_page=True)
    logger.info(f"[{codigo_eco}] Evidência salva em '{caminho}'")
    return str(caminho)


def preencher_formulario(page: Page, dados: dict) -> None:
    """Preenche os 15 campos do formulário com os dados já validados por João (validator.py)."""
    for campo in CAMPOS_FORMULARIO:
        valor = dados.get(campo, "")
        valor = "" if valor is None else str(valor)
        page.fill(f"#{campo}", valor)


def registrar_eco(dados_validados: dict, cenario: str, page: Page | None = None) -> dict:
    """
    Registra uma ECO no sistema web fake, de acordo com o cenário classificado
    por João (validator.py):

      - "normal"  -> preenche e envia o formulário automaticamente.
      - "ambiguo" -> preenche o formulário como rascunho, mas NÃO envia sozinho;
                     encaminha para validação humana.
      - "erro"    -> bloqueia o registro antes de qualquer interação com o formulário.

    Retorna um dicionário com o status final e o caminho da evidência gerada.
    """
    codigo_eco = dados_validados.get("Codigo_ECO", "DESCONHECIDO")

    if cenario == "erro":
        logger.error(
            f"[{codigo_eco}] Registro bloqueado — dados inválidos recusados pelo validator. "
            "Formulário não será acessado."
        )
        return {"codigo_eco": codigo_eco, "status": "BLOQUEADO", "evidencia": None}

    gerenciar_navegador = page is None
    playwright_ctx = None
    browser = None

    if gerenciar_navegador:
        playwright_ctx = sync_playwright().start()
        browser = playwright_ctx.chromium.launch(headless=True)
        page = browser.new_page()

    try:
        page.goto(_form_url())
        preencher_formulario(page, dados_validados)

        if cenario == "ambiguo":
            evidencia = _print_evidencia(page, codigo_eco, "pendente_validacao_humana")
            logger.warning(
                f"[{codigo_eco}] Dados incompletos (ex.: data de implementação ausente) — "
                "formulário preenchido, porém encaminhado para validação humana antes do envio."
            )
            return {
                "codigo_eco": codigo_eco,
                "status": "PENDENTE_VALIDACAO_HUMANA",
                "evidencia": evidencia,
            }

        # cenario == "normal"
        page.click("button")
        page.wait_for_selector("#msg:not(:empty)")
        mensagem = page.inner_text("#msg")
        evidencia = _print_evidencia(page, codigo_eco, "confirmacao")

        if "sucesso" in mensagem.lower():
            logger.info(f"[{codigo_eco}] ECO registrada com sucesso. Retorno do sistema: '{mensagem}'")
            status = "REGISTRADO"
        else:
            logger.error(f"[{codigo_eco}] Sistema retornou mensagem inesperada: '{mensagem}'")
            status = "FALHA_REGISTRO"

        return {
            "codigo_eco": codigo_eco,
            "status": status,
            "mensagem_sistema": mensagem,
            "evidencia": evidencia,
        }

    except Exception as exc:
        logger.error(f"[{codigo_eco}] Erro inesperado durante a automação web: {exc}")
        raise
    finally:
        if gerenciar_navegador:
            browser.close()
            playwright_ctx.stop()


if __name__ == "__main__":
    dados_exemplo = {
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
    resultado = registrar_eco(dados_exemplo, cenario="normal")
    print(resultado)
