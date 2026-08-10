# Regras permanentes do projeto Make Map

## Idiomas obrigatorios

Todo mapa produzido neste repositorio deve gerar duas versoes equivalentes:

- portugues brasileiro (`pt-BR`);
- ingles americano (`en-US`).

Essa regra se aplica a titulos, subtitulos, legendas, rotulos, notas, fontes,
creditos, unidades escritas por extenso e qualquer outro texto visivel.

## Consistencia entre versoes

As duas versoes devem usar os mesmos dados, recorte espacial, projecao,
classificacao, cores, simbolos, dimensoes e resolucao. Somente o idioma e as
convencoes linguisticas devem mudar.

Nao traduzir nomes proprios oficiais, siglas ou topônimos sem uma forma inglesa
consagrada. Numeros, datas e separadores devem seguir a convencao de cada
idioma quando isso nao prejudicar a comparabilidade cientifica.

## Nomes dos arquivos

Usar sufixos de idioma previsiveis:

- `<nome-do-mapa>_pt-BR.<extensao>`
- `<nome-do-mapa>_en-US.<extensao>`

Nenhum mapa e considerado concluido se uma das duas versoes estiver ausente.

## Direcao visual principal

Os mapas devem seguir uma linguagem de cartografia editorial sofisticada,
inspirada na qualidade de publicacoes jornalisticas de referencia, com o
*The New York Times* e o *The Economist* como referencias gerais de qualidade
— sem copiar suas identidades visuais, layouts proprietarios ou pecas
especificas.

Priorizar:

- narrativa visual clara e imediatamente compreensivel;
- composicao limpa, elegante e com bastante espaco em branco;
- hierarquia tipografica forte, adequada a artigos cientificos;
- paleta contida, harmoniosa e acessivel a pessoas com daltonismo;
- contraste disciplinado e uso economico de cores de destaque;
- concisao grafica e leitura rapida, inclusive em figuras pequenas;
- destaque seletivo dos dados importantes e contexto geografico discreto;
- rotulos bem posicionados, com o minimo possivel de sobreposicoes;
- legendas enxutas e integradas a composicao;
- anotacoes diretas no mapa quando forem mais claras que uma legenda;
- acabamento editorial sem sacrificar rigor, reproducibilidade ou precisao;
- bom funcionamento em cores e, quando solicitado, em escala de cinza.

Cada figura deve equilibrar beleza, clareza e rigor cientifico. Elementos
decorativos que nao contribuam para a leitura ou para o argumento devem ser
evitados.

## Tecnologia principal

Todos os mapas devem ser produzidos de forma reproduzivel em Python. Priorizar
o seguinte conjunto de ferramentas, escolhendo apenas o necessario para cada
figura:

- GeoPandas para leitura, tratamento e analise de dados vetoriais;
- Matplotlib para composicao, tipografia e exportacao de mapas estaticos;
- Shapely para operacoes geometricas;
- PyProj para projecoes e transformacoes de coordenadas;
- Rasterio e rioxarray para dados matriciais;
- Contextily somente quando um mapa-base externo for realmente necessario;
- mapclassify para classificacoes coropleticas reproduziveis.

Centralizar textos, cores, fontes, tamanhos e demais escolhas visuais em
arquivos de configuracao reutilizaveis. Evitar valores de estilo espalhados
pelos scripts.

Cada mapa deve poder ser recriado por um comando documentado, com ambiente e
dependencias declarados. Definir explicitamente o sistema de coordenadas e
registrar as fontes dos dados. Preferir formatos vetoriais (`PDF` e `SVG`) para
artigos, oferecendo tambem `PNG` ou `TIFF` em alta resolucao quando necessario.

## Escopo geografico da versao 1

A primeira versao do Make Map deve produzir exclusivamente mapas do Brasil,
incluindo o territorio nacional completo e recortes por regioes, estados,
municipios, biomas, bacias e outras unidades brasileiras.

Priorizar fontes oficiais e documentar a data e a versao de cada malha ou base,
especialmente dados do IBGE. Preservar os codigos oficiais das unidades
territoriais para permitir cruzamentos reproduziveis.

Escolher a projecao conforme a finalidade e a escala do mapa. Nao assumir
Web Mercator como padrao para figuras cientificas. Para analises de area,
distancia ou densidade, usar uma projecao adequada ao territorio e declarar o
CRS no codigo e nos metadados.

Usar nomes oficiais brasileiros na versao `pt-BR`. Na versao `en-US`, traduzir
termos descritivos e elementos editoriais, mas preservar toponimos e nomes
proprios oficiais, salvo quando houver forma inglesa amplamente consagrada.

Embora a arquitetura possa permitir expansao futura, dados, exemplos, testes e
templates da versao 1 devem ser validados apenas para o Brasil.

## Cartografia basica e dados do IBGE

Usar dados publicos oficiais do IBGE como fonte primaria da cartografia basica
do Brasil. Isso inclui, conforme a necessidade do mapa, malhas de municipios,
unidades da federacao, grandes regioes, regioes geograficas, setores censitarios
e elementos da Base Cartografica Continua do Brasil.

Em Python, priorizar o pacote `geobr` para acessar conjuntos oficiais quando o
produto e o ano necessarios estiverem disponiveis. O `geobr`, mantido no
ecossistema de pesquisa do Ipea, e uma camada de acesso; a fonte cartografica
original deve continuar sendo identificada como IBGE.

Quando o conjunto nao estiver disponivel no `geobr`, ou quando for necessario
usar a edicao oficial mais recente, baixar diretamente dos portais e servicos
do IBGE. Nao substituir silenciosamente dados do IBGE por OpenStreetMap ou por
mapas-base comerciais.

Para garantir reproducibilidade:

- declarar explicitamente o produto, a edicao ou ano e a URL de origem;
- nao usar automaticamente a opcao "mais recente" em mapas publicados;
- preservar os geocodigos oficiais do IBGE;
- manter cache local dos arquivos brutos sem altera-los;
- registrar data de acesso, CRS original e quaisquer transformacoes;
- citar o IBGE como fonte dos dados no mapa e nos metadados;
- citar tambem o `geobr` quando ele tiver sido usado para obter os dados.

A malha escolhida deve ser temporalmente compativel com os dados tematicos do
artigo. Mudancas de limites e codigos entre edicoes devem ser verificadas antes
de cruzamentos e comparacoes historicas.

## Dimensoes obrigatorias

Todos os mapas devem usar formato quadrado e dimensoes de `7.5 x 7.5`
polegadas (largura x altura). Em Matplotlib, usar:

```python
figsize = (7.5, 7.5)
```

As versoes `pt-BR` e `en-US` devem manter exatamente as mesmas dimensoes. Na
exportacao raster, a quantidade de pixels deve ser derivada dessas dimensoes e
do DPI solicitado, sem redimensionamento posterior. Para publicacao, usar por
padrao 300 DPI, resultando em `2250 x 2250` pixels; oferecer
600 DPI quando exigido pelo periodico. Exportacoes `PDF` e `SVG` devem preservar
as dimensoes fisicas e os elementos vetoriais.
