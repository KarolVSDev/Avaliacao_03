# Documentação da equipe para o professor

# Orientações para a equipe

André (E-mail $\rightarrow$ Análise $\rightarrow$ Extração):

    Entrega esperada: Um módulo (parser.py ou similar) que lê os arquivos de texto em emails_matriz/ (como normal_ECO_00125.txt, ambiguo_ECO_00126.txt e erro_ECO_00127.txt) e retorna um dicionário estruturado com os dados extraídos (número da ECO, orçamento, data alvo, etc.).

João (Validação > Gateway):

    Entrega esperada: Um módulo de regras de negócio (validator.py) que recebe os dados extraídos pelo André, confere com os 15 campos obrigatórios do controle_mestre_ecos.xlsx e classifica o fluxo nos 3 cenários obrigatórios:  
        - Cenário Normal >  Aprovado para seguir.
        - Cenário Ambíguo >  Detecta ausência (ex: falta da data de implementação) e direciona para validação humana.  
        - Cenário de Erro > Detecta dado inválido (ex: orçamento de -500 USD) e aciona o bloqueio.  


Caroline (Sistema >  Registro):

    Entrega esperada: A automação web com Playwright (bot_playwright.py) que interage com o formulário local web/formulario_eco_fake.html, preenche os campos validados, lida com o feedback da tela, além de registrar os logs e evidências (prints).





# Automação Inteligente de ECOs (Engineering Change Orders)
> **Disciplina:** Técnicas de Hyperautomation | **Professor:** Moisés Levy  
> **Instituição:** Polo de Inovação IFAM / FAEPIT  
> **Equipe:** Equipe 02

---

## 1. Descrição do Projeto
Esta solução de **Hyperautomation** foi desenvolvida para automatizar o processo ponta a ponta de recebimento, leitura, validação e registro de *Engineering Change Orders (ECOs)*. 

O robô monitora e lê e-mails simulados enviados pela matriz, extrai as informações estruturadas, valida os dados obrigatórios com base na planilha mestre, interage com um sistema web simulado via **Playwright** e trata exceções de forma inteligente.

---

## 2. Divisão da Equipe
O projeto foi estruturado utilizando o versionamento via **Git Flow**, com tarefas divididas por módulos:

* **André:** E-mail $\rightarrow$ Análise $\rightarrow$ Extração (Leitura dos arquivos `.txt` e estruturação dos dados).
* **João:** Validação $\rightarrow$ Gateway (Regras de negócio, verificação dos 15 campos obrigatórios do controle mestre e roteamento dos cenários)[cite: 4].
* **Caroline & Colega:** Sistema $\rightarrow$ Registro (Automação web com Playwright preenchendo o `formulario_eco_fake.html` e registro de evidências)[cite: 4].
* **Ana Karoline (Você):** Integração Geral, Arquitetura, Infraestrutura (Docker, Docker Compose com fuso `TZ=America/Manaus`), Testes Automatizados com `pytest` e Gestão do Repositório[cite: 4].

---

## 3. Instruções de Execução (Docker Compose)
O ambiente da aplicação é totalmente conteinerizado, garantindo isolamento e o fuso horário padrão exigido (`America/Manaus`)[cite: 4].

### Pré-requisitos
* Ter o **Docker** e o **Docker Compose** instalados e rodando na sua máquina.

### Como rodar o projeto e os testes:
1. Abra o terminal na raiz do projeto (`02_AUTOMACAO_ECOS`).
2. Execute o comando de construção e execução via Docker Compose:
   ```bash
   docker compose up --build