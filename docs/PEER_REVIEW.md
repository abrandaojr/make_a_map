# Peer review do plano — Make a Map alpha

## Metodo e painel

Este documento registra um **peer review simulado por dez funcoes
especializadas**; nao representa consulta a dez pessoas reais. O objetivo foi
submeter o plano aos riscos que uma equipe editorial, cientifica e de
engenharia encontraria em producao.

1. **Cartografia:** politica de projecao; QA de geometria e joins;
   simplificacao dependente da escala; rotulagem.
2. **Design systems:** taxonomia de tokens; layouts por slots; tipografia
   fixada; receitas e versionamento.
3. **Engenharia de dados:** checksums esperados; downloads atomicos; lock de
   datasets; linhagem raw/processed; hash compartilhado do dado preparado.
4. **Internacionalizacao:** paridade estrita de chaves; numeros e unidades
   tipados; terminologia; QA de overflow e glifos.
5. **Acessibilidade:** descricao curta e longa; testes de reducao, CVD e escala
   de cinza; nenhuma codificacao apenas por cor; ordem de leitura.
6. **Publicacao cientifica:** perfis de periodicos; preflight de fontes em PDF,
   SVG e TIFF; legendas externas; neutralidade e citacoes.
7. **Qualidade:** ambiente deterministico; testes estruturais, semanticos e
   perceptuais em camadas; injecao de falhas; saidas atomicas.
8. **Experiencia de desenvolvimento:** CLI estavel; scaffolding; `doctor`;
   builds transacionais; schemas versionados; erros estruturados.
9. **Performance:** SLOs cold/warm; orcamento de tamanho vetorial; cache de
   dados preparados; locks para concorrencia.
10. **Direcao editorial:** uma fatia vertical completa com fixture sintetica;
    aprovacoes humanas formais; disciplina de escopo para a alpha.

## Consenso de prioridade

### P0 — bloqueia a alpha interna

- Especificacao declarativa e validada, com schemas versionados e erros claros.
- Uma unica fonte de valores semanticos para gerar `pt-BR` e `en-US`, com
  paridade estrita de chaves e nenhuma divergencia cartografica entre idiomas.
- Tema semantico centralizado, tipografia fixada e um conjunto pequeno de
  layouts por slots; valores de estilo nao podem ficar dispersos nos mapas.
- Dados oficiais do IBGE com edicao e URL fixas, checksum esperado, download
  atomico, cache com lock e linhagem entre bruto, processado e figura.
- Politica explicita de projecao, QA de geometrias/joins e separacao entre
  geometria analitica e geometria simplificada para desenho.
- Globo ortografico com contexto mundial completo e Brasil destacado por
  geometria oficial.
- Exportacao transacional de PNG, PDF e SVG, seguida de manifesto com hashes,
  fonte, CRS, transformacoes, parametros e arquivos produzidos.
- PNG exatamente `2250 x 2250` a 300 dpi e vetores com `7.5 x 7.5` polegadas.
- CLI estavel e testes offline com fixture sintetica, cobrindo contratos,
  idiomas, dimensoes, falhas de download e atomicidade.
- Uma fatia vertical completa: Amazonia Legal regenerada pela API comum nos
  dois idiomas, acompanhada de documentacao para repetir o processo.

### P1 — aceito para a alpha quando couber sem fragilizar P0

- Modos limitados `scientific` e `editorial`, com estatistica, legenda e
  anotacao opcionais.
- Numeros e unidades tipados, glossario terminologico e verificacao de overflow
  e cobertura de glifos.
- Descricoes acessiveis curta e longa, ordem de leitura declarada e testes
  manuais em reducao, CVD e escala de cinza; informacao nunca apenas por cor.
- Comando `doctor`, scaffolding de novo mapa e mensagens de erro estruturadas.
- Preflight basico de fontes no PDF, integridade do SVG e tamanho dos vetores;
  perfil generico para legenda externa e citacoes cientificas.
- Testes estruturais e semanticos obrigatorios, com fixture visual de referencia
  para revisao perceptual assistida por humano.
- Cache do dado preparado, lock de concorrencia e medicoes iniciais de build
  cold/warm e tamanho de saida, sem prometer SLO antes de obter uma baseline.
- Checklist de aprovacao humana cartografica, editorial e cientifica.

### P2 — backlog posterior a alpha

- Perfis completos e preflight especifico para varios periodicos, incluindo
  TIFF e regras particulares de submissao.
- Testes perceptuais automatizados e portaveis entre sistemas operacionais.
- SLOs formais de performance e orcamentos rigorosos por tipo de figura.
- Receitas publicas versionadas e catalogo amplo de componentes e temas.

## Sugestoes incorporadas nesta alpha

Foram aceitos: especificacao declarativa; valores semanticos compartilhados
entre os dois idiomas; validacao estrita; tema semantico; poucos layouts
componiveis; dados oficiais travados e rastreaveis; globo com contexto mundial;
exportacao atomica de PNG/PDF/SVG e manifesto; CLI; testes offline com fixture
visual; e documentacao operacional. A alpha deve provar o sistema de ponta a
ponta antes de ampliar sua superficie.

## Itens explicitamente adiados

- Rotulagem automatica geral e resolucao sofisticada de colisoes.
- Grande variedade de mapas tematicos e componentes especializados.
- Otimizacao abrangente de rasters e pipeline TIFF de producao.
- Arquitetura de plugins e integracoes externas.
- Mapas web ou interativos.
- Abstracao ampla de todo o catalogo `geobr`; a alpha cobre somente os datasets
  necessarios a fatia vertical e deixa uma interface extensivel.

Esses itens nao podem entrar como excecoes ad hoc. Cada um exige proposta,
dono, criterio de aceite e impacto de manutencao antes de ser promovido.

## Decisao go/no-go

**GO para alpha interna; NO-GO para producao.** O time deve entregar primeiro
uma unica fatia vertical completa — Amazonia Legal mais fixture sintetica — e
coletar evidencia de repetibilidade, custo de manutencao e qualidade. A alpha so
e aceita quando todos os P0 passam offline, as duas versoes sao semanticamente
equivalentes, os tres formatos e o manifesto sao publicados atomicamente e as
aprovacoes humanas cartografica, editorial e cientifica ficam registradas.

Dimensao incorreta, dado sem lock/checksum, divergencia entre idiomas, saida
parcial, globo sem contexto mundial ou ausencia de proveniencia implica
**NO-GO**. A promocao para producao requer nova revisao baseada no uso real;
itens P1/P2 nao autorizam relaxar nenhum criterio P0.
