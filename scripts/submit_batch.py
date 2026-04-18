"""Submit the 153? Trilingüe Latin translation batch. Saves batch_id + dedup map."""
import gzip, hashlib, json, os, sys
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "data.jsonl.gz"
OUT_DIR = ROOT / "scripts" / "_batch_state"
OUT_DIR.mkdir(exist_ok=True)
MAP_PATH = OUT_DIR / "latin_dedup_map.json"
BATCH_ID_PATH = OUT_DIR / "batch_id.txt"

SYSTEM = """Eres un lexicógrafo experto en latín tardío medieval/renacentista y español clásico. Trabajas sobre glosas latinas del *Vocabulario trilingüe* castellano-latino-náhuatl (ca. 1540-1550, tradición de Nebrija).

Para cada glosa latina escaneada recibirás:
- LATIN_ORIG: la cadena latina tal como aparece en el impreso, con abreviaturas escribales
- SPANISH_CONTEXT: la voz española a la que esa glosa latina sirve de traducción en el vocabulario. **Úsala sólo como ayuda para desambiguar** (resolver un `?`, elegir entre sentidos de una palabra polisémica, confirmar categoría gramatical). No la copies ni la parafrasees en tu salida.

Devuelve un JSON con dos campos:

1. "latin_modern": la misma glosa con abreviaturas expandidas y ortografía regularizada, preservando el orden y el contenido léxico. Reglas:
   - `9` final → `-us`   (`acchiu9` → `acclivus`)
   - `û` / `ô` → vocal + `m`/`n` según el paradigma (`cômeatû` → `commeatum`; `û` neutro adj. → `-um`)
   - `. e.` tras nom. masc. → adj. 3ª decl.: `, -e`   (`accliuis. e.` → `acclivis, -e`)
   - `. a. û.` tras nom. masc. → adj. 1ª-2ª: `, -a, -um`
   - `. onis.` / `. inis.` / `. tionis.` → gen. 3ª decl.: `, -onis` / `, -inis` / `, -tionis`
   - `. is.` tras 1ª pers. verbal → 2ª pers. sg.: `, -is`
   - `. as.` → `, -as` ;  `. are.` / `. ere.` / `. ire.` → infinitivos
   - `?` → si SPANISH_CONTEXT permite inferir la forma estándar con seguridad, escríbela; si no, mantén `?`
   - `u` consonántica → `v` (`auus` → `avus`, `uerbosus` → `verbosus`)
   - Sinónimos separados por `.` se preservan con `;`   (`verbosus, -a, -um; loquax`)
   - Mantén el `.` final

2. "spanish_translation": una traducción **fiel y breve** del latín al español moderno. Norma general: una sola glosa corta y ajustada al sentido literal del latín, con sinónimos separados por `;`. Debe poder sustituir a la glosa latina en un diccionario bilingüe.
   - Por defecto: una o pocas palabras, sin oraciones completas ni explicación gramatical.
     Ej.: `marinus, -a, -um` → "Marino; de la mar."   ·   `verbosus; loquax` → "Verboso; locuaz."   ·   `diluo; eluo` → "Desleír; diluir."
   - Sólo añade **más información si es necesaria** para que la traducción no sea opaca o ambigua: (a) si el latín es una locución (`commeatum dare`) indica la construcción; (b) si la palabra latina está omitida/abreviada de modo ambiguo y SPANISH_CONTEXT resuelve la duda, recoge ese sentido; (c) si dos sinónimos latinos tienen matices distintos relevantes, glósalos con una nota mínima entre paréntesis.
   - No catalogues declinación/conjugación en la traducción salvo que sea imprescindible para distinguir el sentido.
   - No copies SPANISH_CONTEXT literalmente; tu traducción debe reflejar el latín, coincidiendo con ese contexto en el sentido.

Devuelve EXCLUSIVAMENTE un objeto JSON válido, sin texto antes ni después, sin bloques markdown. Formato exacto:
{"latin_modern": "...", "spanish_translation": "..."}"""


def latin_key(s: str) -> str:
    return "lat_" + hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def collect_unique():
    """Returns {custom_id: {"latin": str, "spanish_ctx": str}}."""
    unique = {}
    total_entries = 0
    with gzip.open(DATA, "rt", encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("Fuente") != "153? Trilingüe":
                continue
            c = r.get("Comentario", "")
            parts = [p.strip() for p in c.split("<br />")]
            if len(parts) < 4:
                continue
            latin = parts[3].strip()
            if not latin:
                continue
            total_entries += 1
            cid = latin_key(latin)
            if cid in unique:
                continue
            # line 2 (Spanish modernized) is part index 1 after split-by-<br />,
            # structured as "<orig>  >  <modern>"; take modern after ">"
            sp_line = parts[1]
            if ">" in sp_line:
                spanish_ctx = sp_line.split(">", 1)[1].strip()
            else:
                spanish_ctx = sp_line
            unique[cid] = {"latin": latin, "spanish_ctx": spanish_ctx}
    print(f"Total 153? Trilingüe entries with Latin line: {total_entries}", file=sys.stderr)
    print(f"Unique Latin strings: {len(unique)}", file=sys.stderr)
    return unique


def build_request(custom_id: str, latin: str, sp: str) -> dict:
    return {
        "custom_id": custom_id,
        "params": {
            "model": "claude-opus-4-7",
            "max_tokens": 1024,
            "thinking": {"type": "adaptive"},
            "system": [
                {
                    "type": "text",
                    "text": SYSTEM,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [
                {
                    "role": "user",
                    "content": f"LATIN_ORIG: {latin}\nSPANISH_CONTEXT: {sp}",
                }
            ],
        },
    }


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing")
    unique = collect_unique()
    # persist dedup map so the patch step can undo the hashing
    MAP_PATH.write_text(json.dumps(unique, ensure_ascii=False))
    print(f"Wrote {MAP_PATH}", file=sys.stderr)

    requests = [
        build_request(cid, info["latin"], info["spanish_ctx"])
        for cid, info in unique.items()
    ]
    print(f"Submitting {len(requests)} requests to batch API...", file=sys.stderr)

    client = Anthropic()
    batch = client.messages.batches.create(requests=requests)
    BATCH_ID_PATH.write_text(batch.id)
    print(f"batch_id: {batch.id}", file=sys.stderr)
    print(f"processing_status: {batch.processing_status}", file=sys.stderr)
    print(f"request_counts: {batch.request_counts}", file=sys.stderr)


if __name__ == "__main__":
    main()
