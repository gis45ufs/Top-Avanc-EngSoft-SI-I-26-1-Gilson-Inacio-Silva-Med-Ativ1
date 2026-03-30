#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
processar.py

Atividade Avaliativa 1 - TÓPICOS AVANÇADOS EM ENG. SOFT. SI I
Domínio Médico - Equipe 2 - Gilson Inacio da Silva - Mat: 202611005730

O script:
1) Lê dataset.json (M2 auxiliar com 325 itens, podendo conter item vazio)
2) Lê usmle_questions.json (M2 com gabarito explicado)
3) Tenta ler questions_w_answers.jsonl (M1 K-QA aberto) se existir
4) Separa automaticamente o lote do Gilson Inacio:
   - abertas 86 a 100
   - múltipla escolha 136 a 162
5) Exporta CSVs em outputs/
6) Deixa templates prontos para preencher respostas dos 3 LLMs e a avaliação

Como usar:
    python scripts/processar.py

Opcional:
    python scripts/processar.py --modelos "GPT-4o Mini" "Claude 3.5 Sonnet" "Gemini 2.0 Flash"

Observações:
- O script usa dataset.json como referência de numeração oficial das questões de múltipla escolha.
- O arquivo usmle_questions.json anexado tem 324 itens, enquanto dataset.json tem 325.
- Há pelo menos uma questão vazia em dataset.json. Por isso, o script faz o pareamento
  por texto normalizado da pergunta, em vez de confiar cegamente no índice.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# =========================
# CONFIGURAÇÃO DO ALUNO
# =========================
ALUNO = "Gilson Inácio da Silva"
EQUIPE = "Equipe 2 - Medicina"
ABERTAS_INICIO = 86
ABERTAS_FIM = 100
MC_INICIO = 136
MC_FIM = 162

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

DATASET_JSON = DATA_DIR / "dataset.json"
USMLE_JSON = DATA_DIR / "usmle_questions.json"
KQA_JSONL = DATA_DIR / "questions_w_answers.jsonl"

DEFAULT_MODELOS = [
    "MODELO_1",
    "MODELO_2",
    "MODELO_3",
]


# =========================
# FUNÇÕES UTILITÁRIAS
# =========================
def normalizar_texto(texto: Any) -> str:
    if texto is None:
        return ""
    texto = str(texto)
    texto = texto.replace("\u2013", "-").replace("\u2014", "-")
    texto = texto.replace("\u00a0", " ")
    texto = re.sub(r"\(MC-NJ\)\s*-\s*Step\s*\d+", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto).strip().lower()
    return texto


def carregar_json(caminho: Path) -> List[Dict[str, Any]]:
    with caminho.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    if not isinstance(dados, list):
        raise ValueError(f"Esperava uma lista em {caminho}, mas veio {type(dados).__name__}")
    return dados


def carregar_jsonl(caminho: Path) -> List[Dict[str, Any]]:
    dados: List[Dict[str, Any]] = []
    with caminho.open("r", encoding="utf-8") as f:
        for linha_num, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                obj = json.loads(linha)
                if isinstance(obj, dict):
                    dados.append(obj)
            except json.JSONDecodeError as e:
                print(f"[AVISO] Linha inválida no JSONL ({linha_num}): {e}")
    return dados


def garantir_pastas() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_get_case_insensitive(d: Dict[str, Any], *nomes: str, default: Any = "") -> Any:
    if not isinstance(d, dict):
        return default
    mapa = {str(k).lower(): k for k in d.keys()}
    for nome in nomes:
        chave_real = mapa.get(nome.lower())
        if chave_real is not None:
            return d[chave_real]
    return default


def juntar_valor(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, list):
        partes = []
        for item in valor:
            item_str = str(item).strip()
            if item_str:
                partes.append(item_str)
        return " | ".join(partes)
    if isinstance(valor, dict):
        partes = []
        for k, v in valor.items():
            partes.append(f"{k}: {v}")
        return " | ".join(partes)
    return str(valor).strip()


def escrever_csv(caminho: Path, linhas: List[Dict[str, Any]], campos: List[str]) -> None:
    with caminho.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for linha in linhas:
            writer.writerow({campo: linha.get(campo, "") for campo in campos})


def padronizar_opcoes(opcoes: Any) -> Dict[str, str]:
    base = {"A": "", "B": "", "C": "", "D": "", "E": "", "F": "", "G": "", "H": "", "I": "", "J": ""}
    if isinstance(opcoes, dict):
        for k, v in opcoes.items():
            base[str(k).strip().upper()] = juntar_valor(v)
    return base


# =========================
# M2 - MÚLTIPLA ESCOLHA
# =========================
def construir_lookup_usmle(usmle_dados: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    duplicados = 0
    for idx, item in enumerate(usmle_dados, start=1):
        pergunta = item.get("question", "")
        norm = normalizar_texto(pergunta)
        if not norm:
            continue
        if norm in lookup:
            duplicados += 1
        lookup[norm] = {
            "usmle_source_index": idx,
            "question": pergunta,
            "options": item.get("options", {}),
            "answer": item.get("answer", ""),
            "explanation": item.get("explanation", ""),
            "references": item.get("references", []),
        }
    if duplicados:
        print(f"[AVISO] {duplicados} perguntas duplicadas encontradas em usmle_questions.json")
    return lookup


def exportar_curadoria_mc(dataset_mc: List[Dict[str, Any]], usmle_lookup: Dict[str, Dict[str, Any]]) -> None:
    linhas: List[Dict[str, Any]] = []
    sem_match = 0

    for official_id in range(MC_INICIO, MC_FIM + 1):
        idx = official_id - 1
        item = dataset_mc[idx] if 0 <= idx < len(dataset_mc) else {}
        pergunta = item.get("question", "") if isinstance(item, dict) else ""
        opcoes = padronizar_opcoes(item.get("options", {})) if isinstance(item, dict) else padronizar_opcoes({})
        answer_dataset = item.get("answer", "") if isinstance(item, dict) else ""

        match = usmle_lookup.get(normalizar_texto(pergunta), None)
        if match is None:
            sem_match += 1
            match = {
                "usmle_source_index": "",
                "answer": "",
                "explanation": "",
                "references": [],
            }

        linha = {
            "official_id": official_id,
            "student": ALUNO,
            "team": EQUIPE,
            "dataset_source_index": official_id,
            "usmle_source_index": match.get("usmle_source_index", ""),
            "question": pergunta,
            "option_A": opcoes.get("A", ""),
            "option_B": opcoes.get("B", ""),
            "option_C": opcoes.get("C", ""),
            "option_D": opcoes.get("D", ""),
            "option_E": opcoes.get("E", ""),
            "option_F": opcoes.get("F", ""),
            "option_G": opcoes.get("G", ""),
            "option_H": opcoes.get("H", ""),
            "option_I": opcoes.get("I", ""),
            "correct_answer_dataset": answer_dataset,
            "correct_answer_usmle": match.get("answer", ""),
            "difficulty": "",
            "specialty": "",
            "reference_used": juntar_valor(match.get("references", [])),
            "explanation": juntar_valor(match.get("explanation", "")),
            "curator_notes": "",
        }
        linhas.append(linha)

    campos = [
        "official_id",
        "student",
        "team",
        "dataset_source_index",
        "usmle_source_index",
        "question",
        "option_A",
        "option_B",
        "option_C",
        "option_D",
        "option_E",
        "option_F",
        "option_G",
        "option_H",
        "option_I",
        "correct_answer_dataset",
        "correct_answer_usmle",
        "difficulty",
        "specialty",
        "reference_used",
        "explanation",
        "curator_notes",
    ]
    escrever_csv(OUTPUT_DIR / "curadoria_mc.csv", linhas, campos)
    print(f"[OK] curadoria_mc.csv gerado com {len(linhas)} questões do lote {MC_INICIO}-{MC_FIM}.")
    if sem_match:
        print(f"[AVISO] {sem_match} questões do lote de múltipla escolha não encontraram pareamento em usmle_questions.json.")


# =========================
# M1 - K-QA ABERTAS
# =========================
def exportar_curadoria_abertas(kqa_dados: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    linhas: List[Dict[str, Any]] = []

    if not kqa_dados:
        for official_id in range(ABERTAS_INICIO, ABERTAS_FIM + 1):
            linhas.append({
                "official_id": official_id,
                "student": ALUNO,
                "team": EQUIPE,
                "kqa_source_index": official_id,
                "question": "BAIXE o arquivo questions_w_answers.jsonl e rode o script novamente.",
                "gold_answer": "",
                "must_have": "",
                "nice_to_have": "",
                "sources": "",
                "icd_10_diag": "",
                "difficulty": "",
                "specialty": "",
                "reference_used": "",
                "curator_notes": "",
            })
        print("[AVISO] questions_w_answers.jsonl não encontrado. curadoria_abertas.csv foi gerado como template vazio.")
    else:
        for official_id in range(ABERTAS_INICIO, ABERTAS_FIM + 1):
            idx = official_id - 1
            item = kqa_dados[idx] if 0 <= idx < len(kqa_dados) else {}
            question = safe_get_case_insensitive(item, "Question", "question", default="")
            gold = safe_get_case_insensitive(item, "Free_form_answer", "free_form_answer", default="")
            must_have = safe_get_case_insensitive(item, "Must_have", "must_have", default="")
            nice_to_have = safe_get_case_insensitive(item, "Nice_to_have", "nice_to_have", default="")
            sources = safe_get_case_insensitive(item, "Sources", "sources", default="")
            icd = safe_get_case_insensitive(item, "ICD_10_diag", "icd_10_diag", default="")

            linhas.append({
                "official_id": official_id,
                "student": ALUNO,
                "team": EQUIPE,
                "kqa_source_index": official_id,
                "question": juntar_valor(question),
                "gold_answer": juntar_valor(gold),
                "must_have": juntar_valor(must_have),
                "nice_to_have": juntar_valor(nice_to_have),
                "sources": juntar_valor(sources),
                "icd_10_diag": juntar_valor(icd),
                "difficulty": "",
                "specialty": "",
                "reference_used": juntar_valor(sources),
                "curator_notes": "",
            })
        print(f"[OK] curadoria_abertas.csv gerado com {len(linhas)} questões do lote {ABERTAS_INICIO}-{ABERTAS_FIM}.")

    campos = [
        "official_id",
        "student",
        "team",
        "kqa_source_index",
        "question",
        "gold_answer",
        "must_have",
        "nice_to_have",
        "sources",
        "icd_10_diag",
        "difficulty",
        "specialty",
        "reference_used",
        "curator_notes",
    ]
    escrever_csv(OUTPUT_DIR / "curadoria_abertas.csv", linhas, campos)
    return linhas


def exportar_template_respostas(curadoria_abertas: List[Dict[str, Any]], modelos: List[str]) -> None:
    modelos = (modelos + DEFAULT_MODELOS)[:3]
    linhas: List[Dict[str, Any]] = []

    for item in curadoria_abertas:
        linhas.append({
            "official_id": item.get("official_id", ""),
            "student": ALUNO,
            "team": EQUIPE,
            "question": item.get("question", ""),
            "gold_answer": item.get("gold_answer", ""),
            "must_have": item.get("must_have", ""),
            "nice_to_have": item.get("nice_to_have", ""),
            "sources": item.get("sources", ""),
            "model_1_name": modelos[0],
            "model_1_answer": "",
            "model_2_name": modelos[1],
            "model_2_answer": "",
            "model_3_name": modelos[2],
            "model_3_answer": "",
            "observations": "",
        })

    campos = [
        "official_id",
        "student",
        "team",
        "question",
        "gold_answer",
        "must_have",
        "nice_to_have",
        "sources",
        "model_1_name",
        "model_1_answer",
        "model_2_name",
        "model_2_answer",
        "model_3_name",
        "model_3_answer",
        "observations",
    ]
    escrever_csv(OUTPUT_DIR / "respostas_llms.csv", linhas, campos)
    print(f"[OK] respostas_llms.csv gerado com {len(linhas)} linhas (1 por questão aberta).")


def exportar_template_avaliacao(curadoria_abertas: List[Dict[str, Any]], modelos: List[str]) -> None:
    modelos = (modelos + DEFAULT_MODELOS)[:3]
    linhas: List[Dict[str, Any]] = []

    for item in curadoria_abertas:
        official_id = item.get("official_id", "")
        for modelo in modelos:
            linhas.append({
                "official_id": official_id,
                "student": ALUNO,
                "team": EQUIPE,
                "model_name": modelo,
                "clinical_correctness_0_2": "",
                "completeness_0_2": "",
                "alignment_with_gold_0_2": "",
                "safety_0_2": "",
                "clarity_0_2": "",
                "total_score_0_10": "",
                "comments": "",
            })

    campos = [
        "official_id",
        "student",
        "team",
        "model_name",
        "clinical_correctness_0_2",
        "completeness_0_2",
        "alignment_with_gold_0_2",
        "safety_0_2",
        "clarity_0_2",
        "total_score_0_10",
        "comments",
    ]
    escrever_csv(OUTPUT_DIR / "avaliacao_llms.csv", linhas, campos)
    print(f"[OK] avaliacao_llms.csv gerado com {len(linhas)} linhas ({len(curadoria_abertas)} questões x 3 modelos).")


# =========================
# RELATÓRIO DE SANIDADE
# =========================
def relatorio_sanidade(dataset_mc: List[Dict[str, Any]], usmle_dados: List[Dict[str, Any]]) -> None:
    vazias = []
    for idx, item in enumerate(dataset_mc, start=1):
        pergunta = item.get("question", "") if isinstance(item, dict) else ""
        if not str(pergunta).strip():
            vazias.append(idx)

    print("\n========== SANIDADE DOS ARQUIVOS ==========")
    print(f"dataset.json: {len(dataset_mc)} itens")
    print(f"usmle_questions.json: {len(usmle_dados)} itens")
    if vazias:
        print(f"[AVISO] dataset.json possui questões vazias nos índices oficiais: {vazias}")
    else:
        print("[OK] Nenhuma questão vazia encontrada em dataset.json")

    if len(dataset_mc) != 325:
        print("[AVISO] dataset.json não tem 325 itens. Confira o arquivo.")
    if len(usmle_dados) != 325:
        print("[AVISO] usmle_questions.json não tem 325 itens. O script vai parear por texto para evitar erro de índice.")
    print("==========================================\n")


# =========================
# MAIN
# =========================
def main() -> None:
    parser = argparse.ArgumentParser(description="Processa os datasets da Atividade 1 do domínio médico.")
    parser.add_argument(
        "--modelos",
        nargs="*",
        default=DEFAULT_MODELOS,
        help="Nomes dos 3 modelos que você vai usar nas questões abertas.",
    )
    args = parser.parse_args()

    garantir_pastas()

    if not DATASET_JSON.exists():
        print(f"[ERRO] Arquivo não encontrado: {DATASET_JSON}")
        sys.exit(1)
    if not USMLE_JSON.exists():
        print(f"[ERRO] Arquivo não encontrado: {USMLE_JSON}")
        sys.exit(1)

    dataset_mc = carregar_json(DATASET_JSON)
    usmle_dados = carregar_json(USMLE_JSON)
    relatorio_sanidade(dataset_mc, usmle_dados)

    usmle_lookup = construir_lookup_usmle(usmle_dados)
    exportar_curadoria_mc(dataset_mc, usmle_lookup)

    kqa_dados = None
    if KQA_JSONL.exists():
        kqa_dados = carregar_jsonl(KQA_JSONL)
        print(f"[OK] questions_w_answers.jsonl encontrado com {len(kqa_dados)} linhas.")
    else:
        print(f"[AVISO] Arquivo ausente: {KQA_JSONL}")
        print("[AVISO] Baixe o K-QA original e coloque em data/questions_w_answers.jsonl")

    curadoria_abertas = exportar_curadoria_abertas(kqa_dados)
    exportar_template_respostas(curadoria_abertas, args.modelos)
    exportar_template_avaliacao(curadoria_abertas, args.modelos)

    print("\nConcluído.")
    print(f"Saídas geradas em: {OUTPUT_DIR}")
    print("Arquivos esperados:")
    print(" - curadoria_abertas.csv")
    print(" - curadoria_mc.csv")
    print(" - respostas_llms.csv")
    print(" - avaliacao_llms.csv")


if __name__ == "__main__":
    main()
