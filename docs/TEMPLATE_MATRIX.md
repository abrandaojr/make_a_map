# Matriz de receitas

| Receita | Tipo | Maturidade | Gramática | Foco | Principal bloqueio |
|---|---|---|---|---|---|
| Bioma | temático | experimental | mapa + argumento | um bioma selecionado | edição e cálculo de área |
| Município | locator | experimental | foco único | geocódigo IBGE | malha e ano compatíveis |
| Bairro | locator | concept | locator local | limite municipal oficial | não há malha nacional uniforme |
| Propriedade rural | sensível | concept | foco local | polígono autorizado | privacidade e status jurídico |
| Zona de compra | sensível | concept | mapa analítico | método e período | fornecedores e incerteza |
| Amazônia Legal municipal | temático | experimental | coropleta densa | indicador municipal | joins, classes e ausências |

## Regras comuns

- Produzir `pt-BR` e `en-US` na mesma execução.
- Usar mestre quadrado de 7,5 × 7,5 polegadas e globo ortográfico.
- Declarar pergunta, universo, período, fonte, edição, CRS e limitações.
- Tratar `zero`, `sem dados`, `suprimido` e `fora do universo` como estados
  semanticamente diferentes.
- Não promover uma receita acima de `experimental` sem revisão humana.
- Receitas sensíveis falham fechadas: não geram saída pública sem aprovação.
