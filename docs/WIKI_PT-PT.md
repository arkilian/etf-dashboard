# Wiki da Aplicação (PT-PT)

## 1. Visão Geral

Esta aplicação é um dashboard em Streamlit para análise de holdings de ETFs com apoio de dados do `yfinance`.

Objetivos principais:
- carregar constituintes de um ou mais ETFs a partir de ficheiros CSV;
- enriquecer posições com métricas financeiras e de mercado;
- calcular scores de qualidade e risco por empresa;
- classificar empresas com tags de investimento;
- filtrar e priorizar empresas com base em perfis de investimento.

O utilizador final consegue passar de uma simples lista de holdings para uma análise comparável, filtrável e acionável.

---

## 2. Arquitetura Funcional

Módulos principais:
- `data_loader.py`
  - carrega os CSV de ETFs;
  - normaliza dados textuais e numéricos;
  - cria candidatos de ticker para Yahoo Finance;
  - enriquece dados com `yfinance` (com cache).
- `metrics_engine.py`
  - converte campos raw em métricas financeiras normalizadas.
- `scoring.py`
  - calcula `quality_score` e `risk_score`.
- `tags.py`
  - gera classificação por tags de investimento.
- `filters.py`
  - filtros reutilizáveis (`is_high_quality`, `is_compounder`, etc.).
- `app.py`
  - interface Streamlit, filtros no sidebar, tabela principal, análise agregada por ETF.
- `app/main.py`
  - ponto de entrada de compatibilidade para correr o `app.py`.

---

## 3. Pré-Requisitos

- Python 3.11+
- Ambiente virtual ativo
- Dependências instaladas via `requirements.txt`

Instalação recomendada:
```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Como Iniciar a App

Opção A (principal):
```bash
streamlit run app.py
```

Opção B (compatibilidade):
```bash
streamlit run app/main.py
```

Após arranque, abrir no browser:
- `http://localhost:8501`

---

## 5. Estrutura e Formato dos Dados

### 5.1 Onde colocar os ficheiros de ETFs

Pasta:
- `data/etf_lists/`

Cada ficheiro `.csv` representa um ETF e aparece automaticamente na seleção da app.

### 5.2 Formato esperado do CSV

A app está preparada para exports com:
- linha 1 e linha 2 como metadados;
- linha 3 com cabeçalhos;
- colunas esperadas como:
  - `Ticker`
  - `Name`
  - `Sector`
  - `Asset Class`
  - `Market Value`
  - `Weight (%)`
  - `Shares`
  - `Price`
  - `Location`
  - `Exchange`
  - `Market Currency`

### 5.3 Números localizados

O parser aceita formatos europeus:
- separador de milhar com espaço;
- decimal com vírgula.

Exemplo:
- `1 234,56` -> `1234.56`

---

## 6. Fluxo de Processamento

Fluxo completo:
1. Seleção de um ou mais ETFs.
2. Carregamento de holdings dos CSV.
3. Enriquecimento opcional via `yfinance`.
4. Cálculo de métricas financeiras.
5. Cálculo de scores.
6. Geração de tags.
7. Aplicação de filtros.
8. Renderização da análise agregada e tabela detalhada.

---

## 7. Enriquecimento com yfinance

### 7.1 O que é obtido

Campos típicos:
- preço atual;
- market cap;
- P/E;
- price-to-sales;
- ROIC (quando disponível);
- ROE;
- margens;
- crescimento de receitas e resultados;
- free cash flow;
- debt-to-equity;
- beta.

### 7.2 Robustez do carregamento

A app:
- usa cache (`lru_cache`) para reduzir chamadas repetidas;
- tenta múltiplos símbolos para o mesmo ticker (com sufixos de bolsa);
- lida com dados em falta sem quebrar a execução;
- evita falha global por erro pontual num ticker.

---

## 8. Métricas Financeiras (metrics_engine.py)

Métricas finais usadas na análise:
- `pe_ratio`
- `price_to_sales`
- `roic`
- `roe`
- `gross_margin`
- `operating_margin`
- `net_margin`
- `revenue_growth`
- `earnings_growth`
- `free_cash_flow`
- `debt_to_equity`
- `beta`

Notas:
- rácios em formato 0-1 são convertidos para percentagem quando aplicável;
- `roic` usa proxy (`return_on_assets`) quando o valor direto não existe;
- `debt_to_equity` é normalizado para facilitar comparações.

---

## 9. Sistema de Scoring

### 9.1 Quality Score (0 a 10)

Função: `calculate_quality_score(row)`

Regras:
- ROIC > 12 -> +2
- Operating margin > 15 -> +2
- Debt/Equity < 1 -> +2
- Free cash flow > 0 -> +2
- Revenue growth > 5 -> +2

### 9.2 Risk Score (acumulativo)

Função: `calculate_risk_score(row)`

Regras:
- Debt/Equity > 2 -> +2 risco
- Free cash flow <= 0 -> +2 risco
- Beta > 1.5 -> +1 risco
- setor cíclico -> +1 risco

---

## 10. Sistema de Tags

Função: `generate_tags(row)`

Exemplos de tags:
- `High Quality`
- `Cash Machine`
- `High Debt`
- `Speculative`
- `Expensive`
- `Value`
- `Growth`

As tags são apresentadas:
- como lista interna (`tags`);
- como string amigável para tabela (`tags_display`).

---

## 11. Filtros de Investimento

Em `filters.py` existem funções reutilizáveis:
- `is_high_quality(row)`
- `is_compounder(row)`
- `is_value_stock(row)`
- `is_growth_stock(row)`

Na UI (sidebar) pode ativar:
- High Quality
- Compounders
- Value
- Growth
- intervalo de quality score

Além disso:
- filtro por setor;
- filtro por país;
- filtro por peso;
- filtro por market cap;
- filtro por tags.

---

## 12. Interface da App

### 12.1 Sidebar

Inclui:
- seleção de ETFs;
- enriquecimento com yfinance (on/off);
- limite de tickers para consulta;
- filtros de investimento;
- filtros por características da empresa;
- ordenação dos resultados.

### 12.2 Área principal

Secções:
- KPIs globais do universo filtrado;
- análise ao nível do ETF;
- top empresas por score;
- tabela completa de holdings com coloração de score.

---

## 13. Leitura dos Resultados

Sugestão de interpretação:
- começar pelo `quality_score` para identificar empresas robustas;
- validar `risk_score` para evitar concentração em risco elevado;
- usar tags para segmentação rápida (qualidade, crescimento, valuation);
- confirmar se o ETF tem peso relevante em empresas de alta qualidade;
- comparar ETFs pelo resumo agregado (média de score e % high quality).

---

## 14. Gestão de Performance

Boas práticas:
- limitar `Max tickers to query` quando estiver a explorar rapidamente;
- usar enriquecimento yfinance apenas quando necessário;
- reutilizar sessões para beneficiar do cache;
- começar com 1 ETF e depois expandir para múltiplos.

---

## 15. Resolução de Problemas (Troubleshooting)

### 15.1 Erro de import ao arrancar

Se aparecer erro de imports:
- correr `streamlit run app.py` na raiz do projeto;
- confirmar que `.venv` está ativo.

### 15.2 CSV não aparece na lista

Verificar:
- ficheiro está em `data/etf_lists/`;
- extensão `.csv`;
- formato compatível com cabeçalhos esperados.

### 15.3 Dados em falta em algumas métricas

Normal em `yfinance`.
A app foi desenhada para:
- continuar a execução;
- calcular o possível com os campos disponíveis.

### 15.4 App lenta

Reduzir:
- número de ETFs selecionados;
- limite de tickers consultados no sidebar.

---

## 16. Guia Rápido de Utilização (Passo a Passo)

1. Colocar CSV(s) de ETF em `data/etf_lists/`.
2. Arrancar a app com `streamlit run app.py`.
3. Selecionar 1 ou mais ETFs.
4. Ativar `Enrich with yfinance` para análise fundamental.
5. Ajustar filtros de investimento no sidebar.
6. Ordenar por `quality_score`.
7. Rever:
   - KPIs globais,
   - análise por ETF,
   - top 10 empresas,
   - tabela completa.

---

## 17. Extensibilidade Recomendada

Evoluções fáceis:
- adicionar novos tipos de tags em `tags.py`;
- ajustar regras de score em `scoring.py`;
- incluir novos filtros em `filters.py`;
- adicionar páginas Streamlit adicionais para comparação temporal, risco por setor e export.

---

## 18. Comandos Úteis

Instalar dependências:
```bash
pip install -r requirements.txt
```

Executar app:
```bash
streamlit run app.py
```

Executar testes (se `pytest` estiver instalado):
```bash
pytest -q
```

