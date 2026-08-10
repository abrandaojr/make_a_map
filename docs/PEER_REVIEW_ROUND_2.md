# Peer review — rodada 2: ampliacao das receitas

## Transparencia e metodo

Esta e uma **revisao simulada por dez papeis editoriais e cientificos**, feita
para testar o plano depois da inclusao de seis familias de mapas. Nenhuma pessoa
do *The Economist*, da *Science*, da AAAS, da *Nature* ou da Springer Nature foi
consultada; os nomes indicam apenas lentes de revisao. Este documento nao
representa aprovacao, parceria ou endosso dessas publicacoes.

O painel foi distribuido assim:

1. **Economist 1 — editor de graficos:** clareza da tese e hierarquia visual.
2. **Economist 2 — cartografo:** contexto, rotulos e economia de elementos.
3. **Economist 3 — editor de dados:** classificacao, legenda e incerteza.
4. **Economist 4 — diretor de arte:** consistencia sem uniformidade mecanica.
5. **Science 1 — editor cientifico:** correspondencia entre afirmacao e dado.
6. **Science 2 — revisor de metodos geoespaciais:** CRS, escala e validacao.
7. **Science 3 — editor de producao:** reducao, formatos e legibilidade.
8. **Nature 1 — editor de figuras:** simplicidade e leitura interdisciplinar.
9. **Nature 2 — especialista em acessibilidade:** cor, redundancia e texto.
10. **Nature 3 — editor de reproducibilidade:** proveniencia, integridade e
    arquivos editaveis.

As observacoes foram contrastadas com referencias publicas oficiais: a pagina
[Graphic detail do The Economist](https://www.economist.com/graphic-detail), as
[orientacoes de figuras de um Science Partner Journal](https://spj.science.org/page/remotesensing/for-authors),
o [guia de figuras da Nature](https://research-figure-guide.nature.com/) e o
[guia de formatacao da Nature](https://www.nature.com/nature/for-authors/formatting-guide).
A orientacao da Science Partner Journals nao deve ser confundida com uma regra
universal da revista *Science*; o perfil final sempre deve seguir as instrucoes
do periodico-alvo vigentes na submissao.

## Consenso do painel

- As seis receitas sao uma boa cobertura inicial, mas devem compartilhar
  contratos e componentes, nao um layout rigido nem codigo copiado.
- O arquivo mestre de 7.5 x 7.5 polegadas e util para producao interna, mas nao
  equivale ao tamanho final no periodico. Todo mapa precisa de teste automatico
  e visual na largura de uma e duas colunas.
- O globo obrigatorio deve ser tratado como componente de localizacao
  responsivo: presente no mestre, legivel na reducao e incapaz de encobrir dado.
- A edicao, fonte, licenca, data de acesso, CRS e transformacoes devem acompanhar
  cada camada. Uma URL sem hash ou edicao fixada nao constitui proveniencia.
- Mapas quantitativos precisam declarar universo, denominador, metodo de
  classificacao e tratamento de `zero`, `sem dados` e `fora do universo`.
- Propriedade rural e zona de compra exigem um bloqueio de privacidade e
  divulgacao, nao apenas uma nota. Dados comerciais ou identificadores
  sensiveis nao podem aparecer por padrao.
- A paridade bilingue deve ser semantica e geometrica; textos maiores em
  `pt-BR` devem acionar reflow ou falha explicita, nunca reducao silenciosa.
- PDF/SVG editaveis sao a saida cientifica preferencial; PNG a 300 dpi continua
  como preview e entrega raster. Perfis de submissao devem ser separados do
  mestre, pois formatos e dimensoes variam entre periodicos.

## Achados por lente editorial

### Quatro revisores no estilo The Economist

O grupo aprovou a paleta contida, anotacoes diretas e titulos que comunicam uma
conclusao, mas rejeitou a ideia de que toda receita deva parecer o mapa da
Amazonia Legal. Recomendou uma pergunta editorial por figura, contexto em cinza,
uma unica cor de enfase quando possivel e legenda curta. O mapa de municipio e
o de bairro precisam de hierarquia multiescala; o de propriedade deve evitar a
aparencia enganosa de precisao quando os limites forem aproximados. O modo
`editorial` pode usar uma manchete, desde que a afirmacao seja calculada a partir
do dado e registrada no manifesto. A pagina oficial [Graphic detail](https://www.economist.com/graphic-detail)
foi usada apenas como referencia publica de pratica, nao como especificacao.

### Tres revisores no estilo Science

O grupo condicionou a aceitacao a contratos de metodo por receita: campo e
unidade, regra de inclusao, data de referencia, CRS analitico, operacoes
geometricas, perdas em joins e incerteza. Recomendou vetor editavel, raster com
pelo menos 300 dpi quando aplicavel, linhas e simbolos que sobrevivam a reducao
e maximo aproveitamento da area de dados. Esses pontos sao consistentes com as
[orientacoes publicas do Journal of Remote Sensing](https://spj.science.org/page/remotesensing/for-authors),
um Science Partner Journal; requisitos da revista-alvo prevalecem. Para zona de
compra, um poligono derivado sem periodo e algoritmo reproduzivel deve falhar.

### Tres revisores no estilo Nature

O grupo pediu figuras simples, compreensiveis fora da especialidade e testadas
no tamanho publicado. A [orientacao oficial de paineis](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/)
indica 89 mm para uma coluna, 183 mm para duas e altura maxima de 170 mm, alem de
texto editavel e fontes incorporadas; por isso, o mestre quadrado nao pode ser o
unico preflight. O [guia de formatacao](https://www.nature.com/nature/for-authors/formatting-guide)
reforca simplicidade, barras de escala e parcimonia de cor e detalhe. O painel
recomendou descricao acessivel, verificacao CVD e escala de cinza, legenda
externa opcional e remocao automatica de detalhe que nao sobreviva a reducao.

## Decisoes de maturidade das receitas

| Receita | Decisao para alpha | Condicoes antes de uso real |
|---|---|---|
| Bioma brasileiro | **Alpha prioritaria** | Malha e ano do IBGE fixados; bioma parametrico; contexto dos demais biomas; area calculada no CRS adequado. |
| Municipio | **Alpha prioritaria** | Geocodigo obrigatorio; estado e Brasil como contexto; suporte inicial apenas ao limite municipal oficial. |
| Bairro | **Experimental** | Fonte municipal explicita, schema por provedor e aviso de cobertura; sem promessa de malha nacional uniforme. |
| Propriedade rural | **Experimental restrita** | Entrada fornecida/autorizada pelo usuario; validacao topologica; politica de mascaramento; nenhum identificador sensivel por padrao. |
| Zona de compra de frigorifico | **Prototipo bloqueado para publicacao** | Metodo, periodo, universo e sensibilidade documentados; aprovacao de dados e etica; incerteza representada. |
| Amazonia Legal por municipios | **Alpha prioritaria** | Pertencimento territorial e ano fixados; fixture reduzida; legenda distingue zero, ausente e fora do universo; limite de categorias. |

As tres receitas prioritarias devem provar primeiro o motor comum. As duas
experimentais podem existir como schemas e fixtures sinteticos, mas nao devem
ser anunciadas como prontas para pesquisa. A zona de compra deve permanecer
somente como contrato e exemplo sintetico ate passar revisao de metodo e dados.

## Mudancas de implementacao aceitas

1. Criar schemas versionados por receita, com camadas obrigatorias/opcionais,
   campos, unidades, CRS analitico e CRS de desenho.
2. Implementar uma matriz de capacidades para que cada receita declare escala,
   legenda, rotulos, estatistica e niveis de inset, evitando condicionais ad hoc.
3. Adicionar perfis de preflight `master-7.5`, `single-column` e
   `double-column`; os dois ultimos validam reducao sem mudar o arquivo mestre.
4. Tornar obrigatorios testes de contraste, CVD, escala de cinza, tamanho minimo
   de texto/linha e ausencia de informacao codificada apenas por cor.
5. Introduzir validadores tematicos: geocodigo e join, classes e ausencias,
   periodo e universo, topologia e calculo de area/distancia.
6. Criar um gate de divulgacao para propriedade rural e zona de compra, com
   classificacao de sensibilidade e confirmacao humana registrada.
7. Gerar uma legenda/caption externa bilingue e descricao curta/longa a partir
   dos mesmos valores semanticos usados no mapa.
8. Registrar no manifesto a receita e versao, hashes de entrada e saida,
   parametros de classificacao, estatisticas exibidas e resultados de QA.
9. Fornecer fixtures sinteticos pequenos para todas as receitas; testes oficiais
   com dados completos ficam separados dos testes offline.
10. Exigir aprovacao humana cartografica, cientifica e editorial para promover
    qualquer receita de `experimental` para `stable`.

## Funcionalidades adiadas

- Rotulagem automatica geral de ruas, parcelas e milhares de municipios.
- Roteamento, isocronas e inferencia de fornecedores para zonas de compra.
- Ingestao automatica de CAR/SIGEF ou dados comerciais e reconciliacao de
  titularidade; alem de complexa, essa frente exige governanca propria.
- Uma malha nacional normalizada de bairros, que nao existe como produto unico
  adequado a todos os municipios.
- Perfis certificados para *Science*, *Nature* ou qualquer outro periodico.
- Otimizacao cartografica por IA, mapas interativos, plugins e publicacao web.
- Catalogo amplo de basemaps: a alpha permanece centrada em cartografia oficial
  do IBGE e contexto mundial licenciado apenas para o globo.

## Decisao GO/NO-GO

**GO para alpha interna; NO-GO para producao.** Ha consenso para implementar o
motor compartilhado e entregar primeiro as receitas de bioma, municipio e
Amazonia Legal por municipios com fixtures offline e exemplos bilingues. Bairro
e propriedade rural entram apenas como experimentais; zona de compra nao pode
gerar uma figura publicavel nesta fase.

A alpha somente passa quando os contratos, proveniencia, paridade bilingue,
dimensoes, globo, exportacao atomica, manifesto e testes de reducao forem
verificados automaticamente, e a revisao humana for registrada. Qualquer
divergencia geografica entre idiomas, dado sem edicao/hash, classe ambigua,
exposicao de dado sensivel, texto ilegivel no perfil-alvo ou saida parcial
implica **NO-GO**. Promocao para producao exige evidencia de uso real, auditoria
das receitas e verificacao das regras atuais do periodico especifico.
