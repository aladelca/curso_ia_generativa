#!/usr/bin/env python3
import argparse
import csv
import json
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


def read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())


def lexical_f1(pred: str, gold: str) -> Tuple[float, float, float]:
    pred_tokens = set(tokenize(pred))
    gold_tokens = set(tokenize(gold))
    if not pred_tokens or not gold_tokens:
        return 0.0, 0.0, 0.0
    tp = len(pred_tokens & gold_tokens)
    precision = tp / len(pred_tokens)
    recall = tp / len(gold_tokens)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def has_required_terms(text: str, required: Optional[List[str]]) -> Tuple[int, int]:
    if not required:
        return 0, 0
    present = 0
    for term in required:
        pattern = re.compile(re.escape(term.strip()), re.IGNORECASE)
        if pattern.search(text):
            present += 1
    return present, len(required)


def is_valid_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False


def structure_score(text: str) -> float:
    if is_valid_json(text):
        return 1.0
    return 0.8 if text.strip().endswith((".", ")", "]")) else 0.6


@dataclass
class ExampleScore:
    idx: int
    precision: float
    recall: float
    f1: float
    structure: float
    adequacy: float
    required_present: int
    required_total: int


def score_answer(pred: str, gold: str, required: Optional[List[str]], min_len: int, max_len: int) -> ExampleScore:
    precision, recall, f1 = lexical_f1(pred, gold)
    structure = structure_score(pred)
    length = len(tokenize(pred))
    adequacy_len = 1.0 if (min_len <= length <= max_len) else 0.7 if (length > 0) else 0.0
    req_present, req_total = has_required_terms(pred, required)
    adequacy_req = 1.0 if req_total == 0 else req_present / req_total
    adequacy = 0.6 * adequacy_len + 0.4 * adequacy_req
    return ExampleScore(-1, precision, recall, f1, structure, adequacy, req_present, req_total)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True, help="Archivo con respuestas del modelo (una por línea)")
    parser.add_argument("--gold", required=True, help="Archivo con respuestas de referencia")
    parser.add_argument("--required", help="Archivo con términos requeridos (uno por línea)")
    parser.add_argument("--min_len", type=int, default=30, help="Longitud mínima en tokens")
    parser.add_argument("--max_len", type=int, default=250, help="Longitud máxima en tokens")
    parser.add_argument("--csv", help="Ruta de salida para reporte CSV detallado")
    args = parser.parse_args()

    preds = read_lines(args.pred)
    golds = read_lines(args.gold)
    required = read_lines(args.required) if args.required else None

    n = min(len(preds), len(golds))
    rows: List[ExampleScore] = []
    for i in range(n):
        es = score_answer(preds[i], golds[i], required, args.min_len, args.max_len)
        es.idx = i
        rows.append(es)

    avg_precision = sum(r.precision for r in rows) / n if n else 0.0
    avg_recall = sum(r.recall for r in rows) / n if n else 0.0
    avg_f1 = sum(r.f1 for r in rows) / n if n else 0.0
    avg_structure = sum(r.structure for r in rows) / n if n else 0.0
    avg_adequacy = sum(r.adequacy for r in rows) / n if n else 0.0

    print(f"n={n} | P={avg_precision:.3f} R={avg_recall:.3f} F1={avg_f1:.3f} | estructura={avg_structure:.3f} | adecuación={avg_adequacy:.3f}")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "idx",
                "precision",
                "recall",
                "f1",
                "structure",
                "adequacy",
                "required_present",
                "required_total",
            ])
            for r in rows:
                writer.writerow([
                    r.idx,
                    f"{r.precision:.4f}",
                    f"{r.recall:.4f}",
                    f"{r.f1:.4f}",
                    f"{r.structure:.4f}",
                    f"{r.adequacy:.4f}",
                    r.required_present,
                    r.required_total,
                ])


if __name__ == "__main__":
    main()
