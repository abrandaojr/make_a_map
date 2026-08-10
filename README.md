# Make a Map

Sistema Python para cartografia editorial e científica do Brasil. Cada build
gera conjuntamente versões em português brasileiro (`pt-BR`) e inglês
americano (`en-US`) a partir dos mesmos dados e valores semânticos.

Status: **alpha interna**. As receitas possuem maturidade explícita; um build
bem-sucedido não equivale a aprovação editorial ou científica.

## Começo rápido

```bash
make setup
make doctor
make templates
make map
make test
```

O exemplo completo usa os limites oficiais da Amazônia Legal 2024 e a malha de
Unidades da Federação 2024 do IBGE. Os arquivos são verificados por SHA-256 e o
globo usa Natural Earth 5.1.2 como contexto mundial em domínio público.

As saídas ficam em `outputs/legal-amazon/latest/`:

- PNG, PDF e SVG em `pt-BR` e `en-US`;
- manifesto JSON com fontes, hashes, CRS, estatísticas e estado de revisão;
- caption e descrição acessível em ambos os idiomas.

O mestre tem exatamente 7,5 × 7,5 polegadas. O PNG padrão possui 2250 × 2250
pixels a 300 dpi.

## CLI

```bash
make-a-map templates
make-a-map new meu-mapa --template municipality
make-a-map build legal-amazon --offline
make-a-map doctor
```

`--offline` exige que todos os arquivos oficiais já estejam no cache e impede
acesso à rede.

## Galeria inicial

| Receita | Maturidade | Observação |
|---|---|---|
| `legal-amazon-municipalities` | experimental | vertical slice governado |
| `biome` | experimental | bioma brasileiro selecionável |
| `municipality` | experimental | locator por geocódigo IBGE |
| `neighborhood` | concept | exige fonte municipal oficial |
| `rural-property` | concept/sensitive | revisão humana e privacidade obrigatórias |
| `slaughterhouse-purchasing-zone` | concept/sensitive | método, período e divulgação obrigatórios |

Veja [o plano](docs/IMPLEMENTATION_PLAN.md), a
[primeira revisão](docs/PEER_REVIEW.md), a
[segunda revisão](docs/PEER_REVIEW_ROUND_2.md) e o
[guia de contribuição](docs/CONTRIBUTING.md).

## Fontes

- IBGE, Limites da Amazônia Legal, edição 2024.
- IBGE, Malha de Unidades da Federação, edição 2024.
- Natural Earth, Admin 0 Countries 1:110m, versão 5.1.2, domínio público.

Os dados brutos ficam em `data/raw/`, fora do Git. O catálogo versionado em
`data/sources.json` mantém URLs exatas, edições, tamanhos e checksums esperados.
