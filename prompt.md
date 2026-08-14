# ICA Mock Assessment — Authoring Spec

Este arquivo é a especificação que **o assistente (esta sessão de LLM)** segue ao
gerar desafios de treino no estilo Industry Coding Assessment (ICA).
Não há geração via API externa: o assistente escreve os arquivos diretamente.

O objetivo é produzir assessments que se pareçam com o ICA real usado por empresas
de tecnologia, para treino pessoal.

## Características do assessment

* Implementado em Python.
* Um único sistema que evolui (uma solução no `solution.py` do desafio).
* Exatamente 4 níveis progressivos.
* Revela um nível por vez. NUNCA revele requisitos de níveis futuros antes de o
  candidato passar o nível atual.
* Foco em design de software, gestão de estado e regras de negócio.
* Evite algoritmos avançados (programação dinâmica, grafos, matemática complexa).
* Exija extensibilidade: escolhas ruins de design cedo devem doer nos níveis finais.
* Domínios de negócio realistas (banking, inventário, estacionamento, file storage,
  pedidos, billing, entregas, RH, warehouse, ticketing, logística, frota...).
* Sem APIs externas, rede, banco de dados ou frameworks.

## Dificuldade

* Level 1: 10-15 min — criação de entidade e operações simples.
* Level 2: 10-15 min — operações adicionais, validações, transições de estado.
  Constrói direto sobre o Level 1, sem exigir redesign.
* Level 3: complexidade significativa — querying, ranking, filtragem, histórico,
  auditoria, scheduling, busca ou agregação. Expõe modelagem fraca.
* Level 4: comportamento avançado dependente dos níveis anteriores — snapshots,
  execução adiada, rollback, analytics, expiração, versionamento, prioridade.

Um Senior forte deve achar desafiador mas factível em ~70 min.

## Regras de interface

* O candidato implementa tudo em um único módulo, importado como `from solution import ...`.
* Defina uma interface pública explícita e estável (classe e/ou funções de topo) com
  assinaturas claras. Os testes importam e chamam exatamente essa interface.
* Cada nível ESTENDE a interface dos níveis anteriores — nunca renomeie nem quebre
  métodos já introduzidos. Reutilize exatamente os mesmos nomes e assinaturas.
* Métodos retornam valores Python simples (str, int, bool, list, dict, None) — nunca `print`.
* Use retornos explícitos para falhas previstas (ex.: `None`, `False`, `""`); não levante
  exceção em violações de regra de negócio esperadas, salvo se o requisito pedir.

## Layout em disco

`challenges/` é a biblioteca, particionada por formato de assessment. ICA é um
formato (`src/formats/ica.py`), então seus desafios ficam em `challenges/ica/`.
Os dois nomes viram segmentos de URL (ex.: `/ica/warehouse_inventory`), com
arquivos planos dentro do desafio (sem subdiretórios por nível):

```
challenges/
  progress.db                  # estado (progresso + timer), gitignored
  ica/                          # um formato
    warehouse_inventory/        # um desafio (o nome da pasta é o id/rota)
      challenge.json            # metadados: {"title", "timebox_minutes"} (ex.: 60)
      solution.py               # a única solução, evolui nível a nível (o candidato edita)
      level_1.md                # requisitos do nível 1 (legível)
      level_1_public_tests.py   # testes públicos do nível 1 (unittest, runnable)
      level_1_hidden_tests.py   # testes ocultos do nível 1 (unittest, runnable)
      level_2.md  level_2_public_tests.py  level_2_hidden_tests.py
      ...  level_4_*            # criados só após o candidato passar o nível anterior
```

Os módulos de teste são módulos top-level (sem pacote/`__init__.py`), rodados com
`cwd` na pasta do desafio. No Level 1, o starter da interface também é gravado em
`solution.py` para o candidato começar. Nos níveis seguintes, descreva os novos
métodos no `level_N.md` (o candidato estende o mesmo `solution.py`).

## Regras de teste (por nível)

Gere módulos `unittest` REAIS e executáveis. O serviço (`main.py`) os roda com
`cwd` na pasta do desafio (ex.: `challenges/ica/warehouse_inventory/`), então cada
teste deve começar com:

```python
import unittest
from solution import ...   # a interface daquele nível
```

### `public_test.py`

* 5 a 10 testes visíveis cobrindo exemplos representativos e edge cases.
* Cada método de teste com nome descritivo e asserção clara.
* DEVE falhar (erro/assertion) contra uma solução vazia/não implementada.

### `hidden_test.py`

* 10 a 20 testes: falhas de validação, condições de contorno, operações duplicadas,
  transições de estado inválidas, problemas de ordenação.
* Nomes de método auto-descritivos (em falha, só o nome aparece — nunca o código).
* No `README.md` inclua apenas a lista "HIDDEN TESTS CHECK FOR" (descrições), nunca o código.

### Testes de performance

Nos níveis em que a complexidade importa (tipicamente L3/L4), inclua ao menos um
teste com **entrada grande** (ex.: dezenas de milhares de operações). Cada teste
roda sob um orçamento de tempo por caso (`ICA_CASE_TIMEOUT`, padrão 5s, via
`SIGALRM` no harness): uma solução ineficiente (ex.: O(n²) — lista onde deveria
ser dict) estoura o orçamento e é reportada como erro "time budget exceeded".
Dimensione o N para que uma solução correta O(n)/O(n log n) rode com folga (bem
abaixo do orçamento) e a quadrática claramente o exceda — assim não há flakiness.

## Avaliação (feita pelo runner, não pela LLM)

* Gate determinístico: para "passar" um nível, TODOS os testes — públicos E ocultos —
  de `level1..N` (regressão) devem passar. Ambos bloqueiam o avanço, como no ICA real.
* Os públicos são visíveis (exemplos); os ocultos não têm o código exposto, mas contam
  igualmente para o resultado. Testes de performance ficam nos ocultos.
* Cada teste tem um orçamento de tempo (`ICA_CASE_TIMEOUT`); estourar = erro (útil
  para acusar soluções lentas nos testes de performance).

## Reveal incremental

Gere e escreva apenas o nível atual. Só crie `levelN+1/` depois que o candidato
avisar que passou o nível N. Nunca antecipe requisitos futuros.

## Randomização

A cada novo desafio, escolha domínio, entidades, regras de negócio e complexidade
de Level 3/4 diferentes, mantendo dificuldade comparável a um ICA real.
