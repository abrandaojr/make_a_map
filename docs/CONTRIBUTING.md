# Contribuindo com o Make a Map

Este repositório trata um mapa como um produto reproduzível, não como uma
imagem isolada. Toda mudança deve preservar o contrato bilíngue, a proveniência
dos dados e a legibilidade no tamanho final de publicação.

## Ambiente local

Use Python 3.12 e instale o projeto em modo editável:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

Os testes obrigatórios não acessam a rede. Nunca introduza um download em um
teste unitário; use `tmp_path` e fixtures sintéticas pequenas. Downloads reais
do IBGE pertencem a smoke tests explícitos e não bloqueantes.

## Contrato de uma contribuição

- Gere sempre `pt-BR` e `en-US` a partir dos mesmos objetos de dados.
- Mantenha a figura em 7.5 x 7.5 polegadas; PNG padrão em 2250 x 2250 pixels.
- Preserve o inset de globo e a geometria oficial do Brasil.
- Declare CRS, edição, URL fixa, licença e SHA-256 das fontes.
- Não espalhe cores, fontes ou espaçamentos em scripts: amplie tokens
  semânticos do tema quando necessário.
- Nunca altere silenciosamente classificação, recorte ou geometria entre os
  idiomas.
- Use dados sintéticos ou anonimizados em exemplos de propriedade rural,
  fornecedores e zonas de compra.

## Adicionando uma receita

Uma receita é uma família de composição, não uma figura pronta. Ela deve
declarar camadas obrigatórias e opcionais, campos, CRS recomendado, maturidade,
fontes esperadas e comportamento da legenda. Inclua traduções completas e um
fixture offline sem dados pessoais ou comerciais.

Receitas sensíveis devem falhar de forma segura: propriedade rural exige
revisão/autorizacão antes da publicação; zona de compra exige período, método e
tratamento explícito de informações comerciais. Não inclua coordenadas reais,
CAR, nomes de proprietários, fornecedores ou identificadores indiretos nas
fixtures versionadas.

## Verificação antes do pull request

Execute:

```bash
ruff check src tests
pytest
```

Na revisão visual, confira os dois idiomas em 100% e na largura aproximada de
uma coluna de periódico. Verifique hierarquia, texto cortado, contraste,
distinção em escala de cinza, fonte dos dados e posição do globo. O pull request
deve explicar a decisão cartográfica e indicar como reproduzir a saída.
