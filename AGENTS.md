# AGENTS.md

## Projeto
Dashboard Streamlit em Python para análise de ETFs e ações.

## Objetivo inicial
- Ler dados de holdings de ETFs
- Suportar vários ETFs, não apenas um
- Obter dados de mercado via yfinance
- Construir dashboard Streamlit modular

## Regras técnicas
- Python 3.11+
- Streamlit como frontend
- yfinance para preços e métricas simples
- pandas para tratamento de dados
- código modular e fácil de expandir
- evitar lógica gigante num único ficheiro
- criar funções pequenas e testáveis

## Estrutura funcional
- `app/data_sources/etf_holdings.py`: loaders de constituintes de ETFs
- `app/data_sources/yfinance_client.py`: integração com yfinance
- `app/pages/`: páginas do dashboard
- `data/etf_lists/`: listas base de holdings em CSV

## Convenções
- nomes em inglês no código
- comentários curtos e úteis
- docstrings nas funções principais
- sempre atualizar README quando houver mudanças grandes

## Roadmap inicial
1. carregar lista de holdings de um ETF a partir de CSV
2. enriquecer cada ticker com dados via yfinance
3. mostrar tabela no Streamlit
4. criar filtro por setor, país, peso, market cap
5. permitir trocar de ETF por ficheiro ou configuração