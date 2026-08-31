# 🚀 Avaliação 03 — Automação de Processamento de ECOs (RPA & DevOps)

Sistema automatizado de ponta a ponta para leitura, validação inteligente, processamento web via Playwright, relatórios e persistência de Ordens de Mudança de Engenharia (ECOs), empacotado em container Docker com esteira de CI/CD integrada via GitHub Actions e publicação no GitHub Container Registry (GHCR).

---

## 🛠️ Tecnologias Utilizadas
* **Python 3.10+** (Linguagem principal)
* **Playwright** (Automação web e captura de evidências visuais)
* **Pydantic** (Validação rigorosa de dados e regras de negócio)
* **Pandas / Openpyxl** (Manipulação de planilhas e relatórios)
* **Docker & Docker Compose** (Containerização e portabilidade)
* **GitHub Actions** (Esteira de CI/CD automatizada)
* **GHCR (GitHub Container Registry)** (Repositório de imagens Docker)

---

## 📂 Arquitetura e Organização do Projeto

```text
├── .github/workflows/       # Esteira de CI/CD (GitHub Actions)
├── emails_matriz/           # Fila de arquivos de e-mail de entrada (Simulação)
├── evidencias/              # Prints de tela gerados pelo Playwright (.png)
├── data/                    # Planilha mestra oficial de controle (.xlsx)
├── src/                     # Código-fonte principal da automação
│   ├── main.py              # Orquestrador principal com Circuit Breaker
│   ├── extracao_eco.py      # Extrator de dados dos arquivos de ECO
│   ├── leitura_email.py     # Leitor e gerenciador da fila de e-mails
│   ├── validator.py         # Gateway de validação de regras de negócio
│   └── bot_playwright.py    # Automação de preenchimento do formulário web
├── Dockerfile               # Configuração da imagem Docker
├── docker-compose.yml       # Orquestração local dos containers
├── requirements.txt         # Dependências do projeto
├── ecos_processadas.json    # Relatório geral de processamento
└── README.md



#executando fluxo de atividades