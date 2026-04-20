"""Phase 6 — refinement pass on the 742 rows the user didn't edit.

Uses the 83 user corrections from phase 5 as few-shots (replacing the
original 25 gold EO→TE pairs). For each row, asks Claude to re-judge the
proposed TE given those corrections and either return it unchanged or
emit a revised version.

Input:  phase6_input.jsonl         (rows to refine)
        phase6_corrections.jsonl   (83 user edits, few-shots)
Output: _batch/phase6_batch_id.txt,  phase6_map.json
"""
import json
import os
import sys
from pathlib import Path

from anthropic import Anthropic

from phase4b_submit import RULE_PRIMER

HERE = Path(__file__).resolve().parent
INPUT = HERE / "phase6_input.jsonl"
CORRECTIONS = HERE / "phase6_corrections.jsonl"
STATE = HERE / "_batch"
STATE.mkdir(exist_ok=True)
BATCH_ID_PATH = STATE / "phase6_batch_id.txt"
MAP_PATH = STATE / "phase6_map.json"


TASK = """Recibirás una entrada del Vocabulario trilingüe con:
- EO: escritura original completa (varias palabras).
- TRADUCCION: glosa española (SÓLO desambiguación — nunca la copies).
- COMENTARIO: registro original (contexto adicional).
- TE_STUB: normalización provista de la palabra cabeza (inamovible).
- TE_ACTUAL: edición previamente propuesta por otro modelo.

Tu tarea es REVISAR la TE_ACTUAL. Si es correcta, devuélvela tal cual. Si
tiene errores (espacios dentro de un compuesto, -n final faltante, i→y no
aplicada, absolutivo truncado, abreviatura escribal sin expandir, préstamo
castellano mal transliterado, etc.), devuelve la versión corregida.

Aprende de los EJEMPLOS DE CORRECCIÓN: cada uno muestra una propuesta
anterior ("ANTES") y la corrección que un experto aplicó ("DESPUÉS").
Internalízalos como patrones, no como reglas mecánicas.

Devuelve EXCLUSIVAMENTE un JSON: {"te": "<edición final en una sola línea>", "changed": <true|false>, "note": "<vacío, o una frase breve justificando el cambio>"}"""


def load_corrections() -> list[dict]:
    return [json.loads(l) for l in CORRECTIONS.open(encoding="utf-8") if l.strip()]


def build_system(corrections: list[dict]) -> list[dict]:
    lines = ["EJEMPLOS DE CORRECCIÓN (ANTES → DESPUÉS):", ""]
    for c in corrections:
        lines.append(f"  EO:      {c['eo']}")
        lines.append(f"  STUB:    {c['te_stub']}")
        lines.append(f"  ANTES:   {c['was']}")
        lines.append(f"  DESPUÉS: {c['now']}")
        lines.append("")
    examples = "\n".join(lines)
    system_text = f"{RULE_PRIMER}\n\n{TASK}\n\n{examples}"
    return [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]


def build_user(row: dict) -> str:
    return "\n".join([
        f"EO: {row['eo']}",
        f"TRADUCCION: {row.get('traduccion', '')}",
        f"COMENTARIO: {row.get('comentario', '')}",
        f"TE_STUB: {row['te_stub']}",
        f"TE_ACTUAL: {row['current_te']}",
    ])


def build_request(row: dict, system: list[dict]) -> dict:
    cid = row["record_id"].replace(":", "_").replace(".", "_")
    return {
        "custom_id": cid,
        "params": {
            "model": "claude-sonnet-4-6",
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": build_user(row)}],
        },
    }


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing — export it and re-run.")

    rows = [json.loads(l) for l in INPUT.open(encoding="utf-8") if l.strip()]
    corrections = load_corrections()
    system = build_system(corrections)

    id_map = {}
    requests = []
    for row in rows:
        req = build_request(row, system)
        id_map[req["custom_id"]] = row
        requests.append(req)

    MAP_PATH.write_text(json.dumps(id_map, ensure_ascii=False))
    print(f"rows to refine: {len(rows)}", file=sys.stderr)
    print(f"few-shot corrections: {len(corrections)}", file=sys.stderr)
    print(f"system prompt chars: {len(system[0]['text'])}", file=sys.stderr)

    client = Anthropic()
    batch = client.messages.batches.create(requests=requests)
    BATCH_ID_PATH.write_text(batch.id)
    print(f"batch_id: {batch.id}", file=sys.stderr)
    print(f"processing_status: {batch.processing_status}", file=sys.stderr)
    print(f"request_counts: {batch.request_counts}", file=sys.stderr)
    print(f"\nRun phase6_refine_collect.py once the batch reports ended.", file=sys.stderr)


if __name__ == "__main__":
    main()
