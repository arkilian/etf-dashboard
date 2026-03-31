# Guia do Investidor (PT-PT)

## Objetivo deste guia

Este documento explica como usar a aplicação do ponto de vista de investimento.

Não é um manual técnico. É um guia prático para:
- analisar ETFs de forma estruturada;
- identificar empresas mais fortes dentro de cada ETF;
- comparar qualidade e risco entre diferentes ETFs;
- apoiar decisões de estudo e acompanhamento de carteira.

---

## 1. O que a app faz por si

A aplicação pega nas holdings de um ETF (as empresas que o ETF detém) e transforma isso em:
- métricas financeiras por empresa;
- score de qualidade;
- score de risco;
- tags de classificação (ex.: qualidade alta, dívida elevada, crescimento, etc.);
- filtros para encontrar rapidamente o tipo de empresa que procura.

Na prática, permite responder perguntas como:
- “Este ETF tem empresas de qualidade?”
- “O ETF está carregado de empresas com risco elevado?”
- “Quais são as 10 melhores empresas dentro deste ETF segundo os critérios definidos?”

---

## 2. Como usar no dia a dia (fluxo simples)

1. Selecionar o ETF (ou ETFs) no menu lateral.
2. Ativar enriquecimento com dados de mercado (`yfinance`).
3. Aplicar filtros de investimento (High Quality, Compounders, Value, Growth).
4. Ajustar o intervalo de `quality_score`.
5. Ordenar por `quality_score` para ver primeiro as empresas mais robustas.
6. Rever:
   - resumo por ETF;
   - top 10 empresas;
   - tabela completa.

---

## 3. Como interpretar os indicadores

### Quality Score (0 a 10)

Mede força operacional e financeira.

Em geral:
- `8-10`: perfil forte / qualidade elevada;
- `5-7`: razoável / misto;
- `0-4`: fragilidade relativa.

### Risk Score

Mede sinais de risco financeiro e de volatilidade.

Em geral:
- baixo: estrutura mais defensiva;
- alto: maior sensibilidade a ciclos, dívida ou instabilidade.

### Tags

As tags ajudam a ler rapidamente o perfil da empresa:
- `High Quality`: qualidade elevada;
- `Cash Machine`: boa rentabilidade com geração de caixa;
- `High Debt`: alavancagem elevada;
- `Speculative`: crescimento com fragilidade nos lucros/caixa;
- `Expensive`: valuation exigente;
- `Value`: valuation mais conservador;
- `Growth`: perfil de crescimento.

---

## 4. Como comparar ETFs com critério

Use a secção de análise por ETF para comparar:
- média de qualidade;
- média de risco;
- percentagem de empresas de alta qualidade.

Leitura prática:
- ETF com qualidade média alta e risco médio controlado tende a ser mais robusto;
- ETF com qualidade baixa e risco alto pode exigir maior tolerância ao risco;
- ETF com boa qualidade mas valuation exigente pode ser interessante, mas requer disciplina de entrada.

---

## 5. Estratégias de análise que funcionam bem

### Estratégia A: Qualidade primeiro

- Ativar `High Quality`;
- ordenar por `quality_score`;
- verificar tags para excluir empresas com `High Debt` se necessário.

### Estratégia B: Compounders

- Ativar `Compounders`;
- procurar empresas com crescimento sustentável e geração de caixa.

### Estratégia C: Value disciplinado

- Ativar `Value`;
- confirmar que não está a captar apenas “barato com problemas”.

### Estratégia D: Crescimento com controlo de risco

- Ativar `Growth`;
- cruzar com `risk_score` para evitar extremos.

---

## 6. Boas práticas para decisões de investimento

- Não decidir com base num único indicador.
- Cruzar score, tags e contexto setorial.
- Evitar concentração excessiva num único setor.
- Repetir análise em vários ETFs comparáveis.
- Usar a app como apoio à decisão, não como recomendação automática.

---

## 7. Limitações importantes

- Alguns dados podem estar em falta no fornecedor (`yfinance`).
- Certos tickers podem ter menor cobertura.
- Scores e tags são regras objetivas, não substituem análise qualitativa (gestão, vantagem competitiva, contexto macro).

---

## 8. Checklist rápido antes de investir

1. O ETF tem percentagem relevante de empresas `High Quality`?
2. O `risk_score` médio está alinhado com o meu perfil?
3. O top 10 por score faz sentido para a minha estratégia?
4. Há excesso de empresas `High Debt` ou `Speculative`?
5. Estou confortável com setores e geografias dominantes?

Se a maioria das respostas for positiva, o ETF merece análise mais aprofundada.

---

## 9. Conclusão

Esta aplicação ajuda a transformar uma lista de holdings numa leitura de investimento prática e comparável.

Use-a para:
- filtrar ruído;
- acelerar triagem;
- melhorar consistência na análise de ETFs.
