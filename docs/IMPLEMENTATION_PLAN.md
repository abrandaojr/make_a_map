# Make a Map — plano de melhoria do sistema editorial

## Objetivo

Transformar o prototipo atual em um sistema Python reutilizavel para produzir
mapas cientificos do Brasil, em `pt-BR` e `en-US`, com identidade editorial
consistente, dados oficiais rastreaveis e verificacoes automaticas. O sistema
deve reduzir decisoes repetidas, impedir divergencias entre idiomas e tornar a
producao de uma figura nova uma tarefa de configuracao, nao de recomposicao.

## Principios de produto

1. **Uma fonte de verdade:** tema, textos, dimensoes e componentes vivem em
   modulos compartilhados.
2. **Dados antes do desenho:** fonte, edicao, CRS e transformacoes sao parte do
   contrato de cada mapa.
3. **Bilingue por construcao:** uma figura so e concluida quando ambos os
   idiomas passam pelos mesmos dados e layout.
4. **Composicao modular:** titulo, mapa principal, legenda, escala, estatistica,
   anotacoes, globo e fonte sao componentes independentes.
5. **Dois modos editoriais:** `scientific` usa titulo descritivo; `editorial`
   permite uma manchete sustentada pelos dados.
6. **Saida previsivel:** 7.5 x 7.5 polegadas; PNG a 300 dpi e vetores PDF/SVG.
7. **Falhar cedo:** textos ausentes, CRS indefinido, dados sem proveniencia ou
   saida incompleta interrompem a geracao.

## Arquitetura proposta

```text
make_a_map/
├── pyproject.toml
├── Makefile
├── src/make_a_map/
│   ├── cli.py              # comando unico de geracao
│   ├── contracts.py        # especificacoes e validacao
│   ├── theme.py            # identidade visual
│   ├── i18n.py             # textos e verificacao bilingue
│   ├── data.py             # downloads, cache e proveniencia
│   ├── layout.py           # scientific/editorial
│   ├── export.py           # PNG/PDF/SVG e QA de dimensoes
│   └── components/
│       ├── globe.py
│       ├── legend.py
│       ├── scale.py
│       └── source.py
├── maps/
│   └── legal_amazon.py     # somente dados e narrativa do exemplo
├── tests/
├── outputs/
└── docs/
```

## Frentes de implementacao

### 1. Contratos e configuracao

- Criar dataclasses imutaveis para figura, fonte, textos e estatisticas.
- Validar idiomas obrigatorios, dimensoes, modo, CRS e extensoes.
- Manter o mapa especifico pequeno e declarativo.

### 2. Identidade visual

- Consolidar paleta, tipografia, espessuras e espacamentos em `Theme`.
- Usar uma pilha de fontes abertas com fallback reproduzivel.
- Garantir contraste por tom e contorno, sem depender apenas de cor.
- Definir tokens em vez de valores dispersos pelo codigo.

### 3. Layout responsivo ao conteudo

- Implementar modos `scientific` e `editorial`.
- Permitir estatistica opcional e reposicionar elementos quando ausente.
- Reservar areas seguras para titulo, mapa, fonte e globo.
- Tratar comprimentos diferentes entre portugues e ingles sem reduzir fontes
  silenciosamente.

### 4. Componentes cartograficos

- Escala derivada de unidades projetadas e validada contra o CRS.
- Globo ortografico com continentes mundiais neutros e Brasil destacado.
- Legenda com distincao redundante e suporte a itens variaveis.
- Fonte e notas com quebra controlada e metadados de proveniencia.

### 5. Dados e reprodutibilidade

- Downloads oficiais com URL fixa, cache, hash SHA-256 e edicao declarada.
- Preservar arquivos brutos e registrar acesso, CRS e transformacoes.
- Separar geometria analitica da geometria simplificada para desenho.
- Usar IBGE como fonte primaria da cartografia do Brasil.

### 6. Exportacao e desempenho

- Gerar os dois idiomas em uma unica execucao.
- Verificar 2250 x 2250 pixels e 300 dpi no PNG.
- Preservar tamanho fisico em PDF/SVG.
- Simplificar apenas copias de renderizacao para evitar vetores gigantes.
- Gravar manifest JSON com arquivos, hashes, fontes, CRS e parametros.

### 7. Qualidade

- Testes unitarios para traducao, nomes, dimensoes, hashes e contratos.
- Teste de integracao que gera as duas versoes com dados sinteticos/offline.
- Smoke test do exemplo oficial quando a rede estiver disponivel.
- QA para texto cortado, ausencia de elementos e divergencia entre idiomas.
- GitHub Actions para testes sem depender de downloads externos.

### 8. Experiencia da equipe

- CLI simples: `python -m make_a_map build legal-amazon`.
- `make setup`, `make map`, `make test` e `make qa`.
- Guia curto para criar um novo mapa copiando um exemplo declarativo.
- Checklist editorial e cientifico antes da publicacao.

### 9. Galeria inicial de templates

Entregar receitas declarativas para os seguintes casos, todas com versoes
`pt-BR` e `en-US`, globo de localizacao, formato mestre de 7.5 x 7.5 polegadas e
os mesmos contratos de proveniencia e QA:

1. **Bioma brasileiro:** destaque de um bioma selecionavel (Amazonia como
   exemplo), com os demais biomas como contexto e limites estaduais opcionais.
2. **Municipio:** localizacao de um municipio dentro do estado e do Brasil, com
   suporte a limites urbanos/rurais quando a fonte oficial permitir.
3. **Bairro:** recorte intraurbano com municipio e estado como contexto; exigir
   fonte municipal oficial, pois o IBGE nao mantem uma malha nacional unica de
   bairros para todos os usos.
4. **Propriedade rural:** poligono focal, confrontantes/contexto e elementos
   ambientais opcionais; nunca publicar coordenadas ou identificadores
   sensiveis sem revisao e autorizacao explicitas.
5. **Zona de compra de frigorifico:** area de abastecimento derivada e
   documentada, com municipios, fornecedores ou distancias conforme o metodo;
   exigir definicao de periodo, criterio de inclusao e tratamento de dados
   comerciais sensiveis.
6. **Amazonia Legal por municipios:** municipios com codificacao categorica ou
   quantitativa, classificacao declarada, cores acessiveis e distincao explicita
   entre `zero`, `sem dados` e `fora do universo`.

As receitas devem ser familias de composicao, nao copias do mapa da Amazonia
Legal. Cada uma deve declarar camadas obrigatorias/opcionais, CRS recomendado,
fonte esperada, campos necessarios, comportamento da legenda, validacoes e um
fixture sintetico pequeno para testes offline. A CLI deve permitir listar e
criar um mapa a partir delas, por exemplo:

```text
make-a-map templates
make-a-map new meu-mapa --template municipality
```

## Criterios de aceite

- Uma execucao gera `pt-BR` e `en-US` a partir dos mesmos objetos de dados.
- Nenhuma cor, fonte, dimensao ou posicao principal fica no script do mapa.
- O globo mostra contexto mundial e usa o limite oficial do Brasil.
- O mapa funciona com ou sem bloco estatistico.
- PNGs medem exatamente 2250 x 2250 a 300 dpi.
- PDF e SVG existem, e o SVG deixa de ter tamanho excessivo.
- Manifesto identifica fonte, edicao, URL, hash, CRS e arquivos produzidos.
- Testes offline passam e a documentacao permite criar um novo mapa.

## Fora do escopo desta iteracao

- Mapas fora do Brasil.
- Mapas web interativos.
- Integracao com bases comerciais.
- Sistema completo de diagramacao do artigo ou submissao ao periodico.
