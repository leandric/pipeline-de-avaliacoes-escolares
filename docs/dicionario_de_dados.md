# Dicionário de dados — base fake de avaliações

Arquivo gerado por [`gerar_base_fake.py`](../src/pipeline/generation/gerar_base_fake.py) em `data/base_fake_avaliacoes.csv`.

Todos os dados são fictícios.

## Formato do arquivo

| Item | Valor |
|---|---|
| Codificação | UTF-8 |
| Separador | vírgula |
| Aspas | todos os campos entre aspas (preserva os espaços em branco de `respostas`) |
| Cabeçalho | sim, na primeira linha |
| Granularidade | **uma linha por aluno e disciplina** (uma prova respondida) |
| Chave natural | `ra` + `disciplina` |

## Colunas

| Coluna | Tipo | Descrição | Valores / formato |
|---|---|---|---|
| `ra` | texto | Registro do aluno. Único por aluno; se repete em uma linha por disciplina. | 8 dígitos, de `10000000` a `99999999` |
| `nome` | texto | Nome completo fictício do aluno. Não é único. | Ex.: `Henry Gabriel Alves Sousa` |
| `escola` | texto | Unidade em que o aluno estuda. | `Unidade Centro`, `Unidade Norte`, `Unidade Sul` |
| `ano_letivo` | inteiro | Ano letivo da avaliação. | `2026` |
| `segmento` | texto | Segmento de ensino. | `Fundamental`, `Médio` |
| `serie` | texto | Série ou ano do aluno. | Fundamental: `6º ano`, `7º ano`, `8º ano`, `9º ano`. Médio: `1ª série`, `2ª série`, `3ª série` |
| `turma` | texto | Identificação da turma dentro da escola e da série. | Letra (`A`, `B`, ...). Após `Z`, vira `A1`, `B1`, ... |
| `periodo` | texto | Turno da turma. Igual para todas as linhas do mesmo aluno. | `Manhã`, `Tarde`, `Integral` |
| `disciplina` | texto | Disciplina da prova. | Veja a tabela de disciplinas abaixo |
| `data_prova` | data | Data de aplicação. É a mesma para todas as versões e turmas da mesma série e disciplina. | ISO `AAAA-MM-DD`, entre `2026-03-01` e `2026-06-29` |
| `versao` | texto | Versão da prova que o aluno fez. | `A`, `B`, `C`, `D` |
| `id_prova` | texto | Identificador da prova (série + disciplina + versão). | `{código da série}-{código da disciplina}-{versão}`, ex.: `EM3-GEO-D` |
| `respostas` | texto | Respostas marcadas pelo aluno, uma por questão, na ordem da prova. | Exatamente 50 caracteres. Veja a legenda abaixo |
| `gabarito` | texto | Respostas corretas da prova, na ordem das questões. | Exatamente 50 caracteres, cada um de `A` a `E` |
| `pesos_perguntas` | texto | Peso de cada questão, na ordem das questões. | 50 números separados por vírgula, ponto decimal, 4 casas. A soma é sempre `1` |

### Legenda de `respostas`

| Caractere | Significado |
|---|---|
| `A` a `E` | Alternativa marcada |
| ` ` (espaço) | Em branco: o aluno não respondeu |
| `*` | Resposta invalidada pelo sistema (mais de uma alternativa marcada) |

### Códigos de série (`id_prova`)

| Código | Série | Segmento |
|---|---|---|
| `EF6` | 6º ano | Fundamental |
| `EF7` | 7º ano | Fundamental |
| `EF8` | 8º ano | Fundamental |
| `EF9` | 9º ano | Fundamental |
| `EM1` | 1ª série | Médio |
| `EM2` | 2ª série | Médio |
| `EM3` | 3ª série | Médio |

### Disciplinas (`disciplina` e código no `id_prova`)

| Disciplina | Código | Fundamental | Médio |
|---|---|:---:|:---:|
| Português | `POR` | ✓ | ✓ |
| Matemática | `MAT` | ✓ | ✓ |
| Ciências | `CIE` | ✓ | |
| Física | `FIS` | | ✓ |
| Química | `QUI` | | ✓ |
| Biologia | `BIO` | | ✓ |
| História | `HIS` | ✓ | ✓ |
| Geografia | `GEO` | ✓ | ✓ |
| Inglês | `ING` | ✓ | ✓ |

## Regras da base

- **Mesma prova, mesmo conteúdo.** Todas as linhas com o mesmo `id_prova` têm o mesmo `gabarito` e os mesmos `pesos_perguntas`, em qualquer escola ou turma.
- **Versões distribuídas na turma.** Dentro de cada turma, as versões A, B, C e D são divididas de forma equilibrada entre os alunos, separadamente por disciplina. Um aluno pode ter versões diferentes em disciplinas diferentes.
- **Turmas.** Cada turma tem entre 30 e 40 alunos e todos fazem as mesmas disciplinas. Uma turma é identificada por `escola` + `serie` + `turma`.
- **Posição é a questão.** O caractere *n* de `respostas` e de `gabarito` e o valor *n* de `pesos_perguntas` se referem à mesma questão (de 1 a 50).
- **Sem nota.** A base não traz nota nem acerto calculado. Isso será derivado no pipeline.
- **Última turma pode estar incompleta.** O gerador recebe o número de linhas e corta no total pedido, então a última turma pode ter alunos sem todas as disciplinas.

## Exemplo

```csv
"ra","nome","escola","ano_letivo","segmento","serie","turma","periodo","disciplina","data_prova","versao","id_prova","respostas","gabarito","pesos_perguntas"
"97226012","Henry Gabriel Alves Sousa","Unidade Sul","2026","Médio","2ª série","A","Integral","Português","2026-06-01","A","EM2-POR-A","CE BCECEBBDDBEECDAACCBDEECDDDBEDB CCECABCBBBAADDEA","CECDCDCEBBDDBEECDEACCBDEECDDDBEDBACEECABCBBBAABDEA","0.0182,0.0282,0.0210,..."
```

No exemplo, `pesos_perguntas` foi abreviado; no arquivo real são 50 valores. A resposta tem espaços em branco, que indicam questões não respondidas.
