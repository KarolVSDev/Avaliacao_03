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