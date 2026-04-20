"""Phase 4b — submit the 826 partials to the Anthropic Batch API.

Pure-API pass: Claude Sonnet 4.6, Batch (50% discount), cached system prompt
carrying the Trilingüe rule primer and 25 gold EO→TE few-shots. The rules
module is NOT consulted at inference time — it only informs the few-shots
and the prose rule primer.

Input:  scripts/trilingue/partials.jsonl  (from phase 1)
Output: scripts/trilingue/_batch/batch_id.txt,  partials_map.json

Run phase4c_collect.py once the batch is complete to fetch and parse results.
"""
import json
import os
import random
import sys
from pathlib import Path

from anthropic import Anthropic

HERE = Path(__file__).resolve().parent
PAIRS = HERE / "pairs.jsonl"
PARTIALS = HERE / "partials.jsonl"
STATE = HERE / "_batch"
STATE.mkdir(exist_ok=True)
BATCH_ID_PATH = STATE / "batch_id.txt"
MAP_PATH = STATE / "partials_map.json"


RULE_PRIMER = """Reglas de ortografía del *Vocabulario trilingüe* (ca. 1540) → edición moderna del náhuatl clásico.

La "Escritura original" (EO) usa convenciones escribales del s. XVI influidas por el castellano de la época; la "edición" (TE) la regulariza. Transformaciones regulares:

- Acentos agudos se eliminan: á→a, é→e, í→i, ó→o, ú→u.
- ç → z siempre. (Excepción: «çu» frecuentemente vale /zo/ → zo.)
- ^ es abreviatura escribal de «ui»: q^ = qui.
- qua, quo → cua, cuo. (que, qui se mantienen.)
- v usada como semivocal /w/ → hu en todas las posiciones.
- u intervocálica (= /w/) → hu: nauatilli → nahuatilli.
- u inicial ante vocal → hu: uei → huei.
- Tras l, x: lua→lhua, xua→xhua (inserción de h).
- o intervocálica entre vocales abiertas (= /w/) → hu: tlatelchioalli → tlatelchihualli.
- n ante labial → m: ontzonpa → ontzompa.
- Coda silábica: hu + {c, t, q} → uh + consonante: canahuconetl → canauhconetl.
- i intervocálica (= /y/) entre vocales abiertas → y: tetzoiotl → tetzoyotl.
- Prefijo de sujeto 1sg «ni-» se elimina en la citación: nitlatlapíqui → tlatlapiqui.
  Los prefijos de objeto/reflexivo (te-, tla-, mo-, ne-, nic-, nino-…) se conservan.
- s ante vocal a veces → z.

Alternancias lexicalmente condicionadas (no son regla mecánica — requieren juicio):
- i ↔ y en contextos ambiguos.
- u ↔ o en morfemas con variación escribal (teu-/teo-).
- La edición a veces elimina además prefijos de objeto (tla-, te-) cuando cita sólo la raíz.
- Algunas formas añaden morfemas ausentes en EO (locativo -yan, -h, -n, -i de enlace).

El "stub" (TE_STUB) ya provee la normalización correcta de la palabra cabeza; respétalo literalmente, sin alterarlo. Tu tarea es producir la edición COMPLETA del EO: normaliza las demás palabras siguiendo las reglas y el juicio léxico, y combínalas con el stub en el orden original."""


TASK = """Recibirás una entrada del Vocabulario trilingüe con transcripción parcial de la columna náhuatl ("+ "= incompleta). Tienes:
- EO: la escritura original completa (varias palabras).
- TRADUCCION: la glosa española (úsala como señal de desambiguación; NO la copies).
- COMENTARIO: el registro original con folio y línea latina (contexto adicional).
- TE_STUB: la normalización ya provista de la palabra cabeza.

Produce la edición COMPLETA normalizada del EO, tratando el TE_STUB como inamovible.

Devuelve EXCLUSIVAMENTE un JSON: {"te": "<edición completa en una sola línea>", "note": "<vacío, o una frase breve si la normalización de alguna palabra no EO-cabeza es incierta>"}"""


def pick_few_shots(n: int = 25) -> list[dict]:
    """Diverse few-shots from the gold corpus — cover the main rule patterns."""
    pairs = [json.loads(l) for l in PAIRS.open(encoding="utf-8") if l.strip()]
    # Bias toward multi-token pairs (more useful signal for multi-word partials).
    single = [p for p in pairs if p["category"] == "single_token" and p["eo"] != p["te"]]
    multi = [p for p in pairs if p["category"] == "aligned_multi"]
    random.seed(42)
    random.shuffle(single)
    random.shuffle(multi)

    picked = []
    # 10 multi-token (primary signal for multi-word EO→TE).
    picked += multi[:10]
    # 15 single-token covering different rule patterns.
    wanted_patterns = ["ç", "^", "v", "ni", "qua", "ó", "í", "á", "é", "ll", "auh", "iah", "eo"]
    for pat in wanted_patterns:
        for p in single:
            if pat in p["eo"] and p not in picked:
                picked.append(p)
                break
    # Fill the rest.
    for p in single:
        if p not in picked and len(picked) < n:
            picked.append(p)
    return picked[:n]


def build_system(few_shots: list[dict]) -> list[dict]:
    # Cache the whole primer+task+examples block — it's reused per request.
    examples_lines = ["Ejemplos (EO → TE):", ""]
    for p in few_shots:
        examples_lines.append(f"  EO: {p['eo']}")
        examples_lines.append(f"  TE: {p['te']}")
        examples_lines.append("")
    examples = "\n".join(examples_lines)
    system_text = f"{RULE_PRIMER}\n\n{TASK}\n\n{examples}"
    return [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]


def build_user(row: dict) -> str:
    parts = [
        f"EO: {row['eo']}",
        f"TRADUCCION: {row.get('traduccion', '')}",
        f"COMENTARIO: {row.get('comentario', '')}",
        f"TE_STUB: {row['te_stub']}",
    ]
    return "\n".join(parts)


def build_request(row: dict, system: list[dict]) -> dict:
    # Batch API custom_id: ^[a-zA-Z0-9_-]{1,64}$ — colons/dots aren't allowed.
    cid = row["record_id"].replace(":", "_").replace(".", "_")
    return {
        "custom_id": cid,
        "params": {
            "model": "claude-sonnet-4-6",
            "max_tokens": 512,
            "system": system,
            "messages": [{"role": "user", "content": build_user(row)}],
        },
    }


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing — export it and re-run.")

    partials = [json.loads(l) for l in PARTIALS.open(encoding="utf-8") if l.strip()]
    few_shots = pick_few_shots()
    system = build_system(few_shots)

    # Persist the id → partial map so the collector can join results back.
    id_map = {}
    requests = []
    for row in partials:
        req = build_request(row, system)
        id_map[req["custom_id"]] = row
        requests.append(req)

    MAP_PATH.write_text(json.dumps(id_map, ensure_ascii=False))
    print(f"partials: {len(partials)}", file=sys.stderr)
    print(f"few-shots embedded: {len(few_shots)}", file=sys.stderr)
    print(f"system prompt chars: {len(system[0]['text'])}", file=sys.stderr)

    client = Anthropic()
    batch = client.messages.batches.create(requests=requests)
    BATCH_ID_PATH.write_text(batch.id)
    print(f"batch_id: {batch.id}", file=sys.stderr)
    print(f"processing_status: {batch.processing_status}", file=sys.stderr)
    print(f"request_counts: {batch.request_counts}", file=sys.stderr)
    print(f"\nRun phase4c_collect.py once the batch reports ended.", file=sys.stderr)


if __name__ == "__main__":
    main()
