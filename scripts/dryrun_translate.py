"""5-sample dry run for Latin translation pipeline. Key is read from env only."""
import json, os, sys
from anthropic import Anthropic

SAMPLES = [
    ("1353153.0", "diluo. eluo. is.",            "Desleir otra cosa."),
    ("1355321.0", "do cômeatû.",                 "Dar licencia el capitán."),
    ("1353814.0", "verbosus. a. û. loquax.",     "Palabrero."),
    ("1345795.0", "diecula. ?.",                 "Día pequeño."),
    ("1345204.0", "marinus. a. û.",              "Marino cosa de la mar."),
]

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

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY missing")
    client = Anthropic()
    for eid, latin, sp_ctx in SAMPLES:
        user = f"LATIN_ORIG: {latin}\nSPANISH_CONTEXT: {sp_ctx}"
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=1024,
            thinking={"type": "adaptive"},
            system=SYSTEM,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        print("=" * 72)
        print(f"eid={eid}")
        print(f"  LATIN_ORIG:  {latin}")
        print(f"  SPANISH_CTX: {sp_ctx}")
        try:
            parsed = json.loads(text)
            print(f"  → latin_modern:        {parsed['latin_modern']}")
            print(f"  → spanish_translation: {parsed['spanish_translation']}")
        except Exception as e:
            print(f"  RAW (parse failed: {e}):\n{text}")
        print(f"  usage: in={msg.usage.input_tokens} out={msg.usage.output_tokens}")

if __name__ == "__main__":
    main()
