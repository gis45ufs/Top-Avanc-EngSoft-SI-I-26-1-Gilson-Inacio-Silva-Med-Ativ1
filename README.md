Repositório individual da **Atividade Avaliativa 1** da disciplina **Tópicos Avançados em Engenharia de Software e SI I**, no **domínio médico**.

**Discente:** Gilson Inácio da Silva  
**Matrícula:** 202611005730  
**Programa:** Pós-Graduação em Ciência da Computação  
**Equipe:** Equipe 2 - Medicina  

## Escopo individual

Este repositório documenta a parte individual correspondente a:

- **Questões abertas:** 86 a 100
- **Questões de múltipla escolha:** 136 a 162

## O que foi realizado

### 1. Curadoria das questões abertas
Foram organizados e revisados os seguintes elementos para as questões 86–100:

- enunciado da pergunta;
- resposta padrão-ouro;
- campos `must_have` e `nice_to_have`;
- dificuldade;
- especialidade;
- referência utilizada;
- notas do curador.

### 2. Curadoria das questões de múltipla escolha
Para as questões 136–162 foram organizados:

- enunciado;
- alternativas;
- gabarito;
- dificuldade;
- especialidade;
- referência clínica;
- explicação técnica;
- notas do curador.

### 3. Inferência com LLMs
As questões abertas foram submetidas a três modelos:

- GPT-5.4 Thinking
- Claude 4.6 Sonnet
- Gemini 3.0

### 4. Avaliação das respostas
As respostas geradas pelos modelos foram comparadas com a resposta padrão-ouro do dataset K-QA com base nos critérios:

- `clinical_correctness_0_2`
- `completeness_0_2`
- `alignment_with_gold_0_2`
- `safety_0_2`
- `clarity_0_2`
- `total_score_0_10`

## Estrutura do repositório

```text
Top-Avanc-EngSoft-SI-I-26-1-Gilson-Inacio-Silva-Med-Ativ1/
├── README.md
├── data/
│   ├── dataset.json
│   ├── questions_w_answers.jsonl
│   └── usmle_questions.json
├── scripts/
│   └── processar.py
├── outputs/
│   ├── curadoria_abertas.csv
│   ├── curadoria_mc.csv
│   ├── respostas_llms.csv
│   ├── avaliacao_llms.csv
│   └── Workbook_Equipe2_Medicina_Atividade1_Gilson_Inacio_da_Silva.xlsx
└── relatorio/
    ├── Relatorio_Individual_Gilson_Inacio_Silva_Atividade1.pdf
    └── Relatorio_Individual_Gilson_Inacio_Silva_Atividade1.docx
```

## Principais arquivos

### Pasta `data/`
Contém os arquivos-base utilizados na atividade:

- `dataset.json`
- `questions_w_answers.jsonl`
- `usmle_questions.json`

### Pasta `scripts/`
Contém o script usado para organizar e gerar as saídas:

- `processar.py`

### Pasta `outputs/`
Contém os artefatos principais da execução:

- `curadoria_abertas.csv`
- `curadoria_mc.csv`
- `respostas_llms.csv`
- `avaliacao_llms.csv`
- `Workbook_Equipe2_Medicina_Atividade1_Gilson_Inacio_da_Silva.xlsx`

### Pasta `relatorio/`
Contém a documentação final do trabalho individual:

- `Relatorio_Individual_Gilson_Inacio_Silva_Atividade1.pdf`
- `Relatorio_Individual_Gilson_Inacio_Silva_Atividade1.docx`

## Metodologia resumida

A metodologia adotada privilegiou avaliação supervisionada por critérios clínicos, em vez de depender apenas de métricas lexicais. Essa decisão foi motivada pelo fato de que, em medicina, respostas semanticamente próximas podem ainda assim ser clinicamente inadequadas ou inseguras.

No presente recorte individual:

- as **questões abertas** receberam inferência com três LLMs e avaliação estruturada;
- as **questões de múltipla escolha** foram integralmente curadas e documentadas;
- os resultados foram consolidados em CSVs e em um workbook final.

## Observação importante

Este repositório preserva exatamente os artefatos efetivamente produzidos no recorte individual da atividade. Não foram adicionadas métricas automáticas não calculadas nem experimentos não executados, para manter coerência entre documentação e evidências.

## Relatório

O relatório individual final está disponível em:

- `relatorio/Relatorio_Individual_Gilson_Inacio_Silva_Atividade1.pdf`
- `relatorio/Relatorio_Individual_Gilson_Inacio_Silva_Atividade1.docx`

## Vídeo

Adicionar aqui o link do vídeo quando estiver disponível.

Exemplo:

```text
Vídeo: [colar link aqui]
```

## Referências principais

- K-QA: *A Real World Medical Q&A Benchmark*
- *Large Language Models in Medicine*
- Fontes clínicas registradas nas planilhas (`UpToDate`, `MedlinePlus`, `Cleveland Clinic`, entre outras)

## Declaração

Este repositório corresponde à minha contribuição individual para a Atividade Avaliativa 1, no domínio médico, conforme o lote designado.
