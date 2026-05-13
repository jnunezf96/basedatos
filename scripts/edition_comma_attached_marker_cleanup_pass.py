#!/usr/bin/env python3
"""Clean comma-split person/object markers in rendered standard text.

Some Molina/BNF rows keep a first-person or object marker attached to the
preceding word before a comma, e.g. ``tlanini, nenemi``.  In rendered
``Texto estandarizado`` these should behave like the other deconjugated rows:
``tlani nenemi``.  This pass is exact and evidence-driven; ambiguous words
ending in ``-ni`` are only reported for review.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "edition_comma_attached_marker_cleanup_report.jsonl"
REVIEW_PATH = ROOT / "scripts" / "edition_comma_attached_marker_review.jsonl"

TEXT_FIELD = "Texto estandarizado"
ID_FIELD = "record_id"

# record_id: (expected rendered text, replacement rendered text, reason)
CURATED_FIXES: dict[str, tuple[str, str, str]] = {
    "1780-bnf-361:001500": (
        "tlatolticanino, nahuatia",
        "tlatoltica nahuatia",
        "tlatoltica + nino marker",
    ),
    "1780-bnf-361:003386": (
        "tonallini, quittitia",
        "tonalli quittitia",
        "parallel Molina row has tonalli quittitia",
    ),
    "1780-bnf-361:005857": (
        "yuallini, quitztoc",
        "yualli quiitztoc",
        "parallel Molina row has yualli quiitztoc",
    ),
    "1780-bnf-361:005994": (
        "yuiyannite, matoca",
        "yuiyan matoca",
        "yuiyan + nite marker",
    ),
    "1571-molina-1:005916": (
        "yeni, yoli",
        "ye yoli",
        "reviewed: ye + ni marker",
    ),
    "1571-molina-1:009451": (
        "cualani tlahuelcuini",
        "cualanini, tlahuelcuini",
        "review corrected: lexical cualanini",
    ),
    "1571-molina-1:011435": (
        "aicni, huellamati",
        "aic huellamati",
        "aic + ni marker",
    ),
    "1571-molina-1:011728": (
        "huecani, tlachia",
        "hueca tlachia",
        "reviewed: hueca + ni marker",
    ),
    "1571-molina-1:012064": (
        "huelni, palani",
        "huel palani",
        "huel + ni marker",
    ),
    "1571-molina-1:012067": (
        "huelnite, mictia",
        "huel mictia",
        "huel + nite marker",
    ),
    "1571-molina-1:012974": (
        "icni, tlamatzoa",
        "ic tlamatzoa",
        "ic + ni marker",
    ),
    "1571-molina-1:012975": (
        "icni, xonexca",
        "ic xonexca",
        "ic + ni marker",
    ),
    "1571-molina-1:012976": (
        "icni, xonexca",
        "ic xonexca",
        "ic + ni marker",
    ),
    "1571-molina-1:012987": (
        "icnite, ixmotla",
        "ic ixmotla",
        "ic + nite marker",
    ),
    "1571-molina-1:012988": (
        "icnite, ixtlahuitequi",
        "ic ixtlahuitequi",
        "ic + nite marker",
    ),
    "1571-molina-1:012992": (
        "icnitla, matzoa",
        "ic matzoa",
        "ic + nitla marker",
    ),
    "1780-bnf-361:009349": (
        "ilhuicacpani, tlachia",
        "ilhuicacpan tlachia",
        "ilhuicacpan + ni marker",
    ),
    "1780-bnf-361:009802": (
        "itechni, nemi",
        "itech nemi",
        "itech + ni marker",
    ),
    "1571-molina-1:014379": (
        "itechni, nomati",
        "itech nomati",
        "itech + ni marker",
    ),
    "1780-bnf-361:009803": (
        "itechni, tlatzitzquia",
        "itech tlatzitzquia",
        "itech + ni marker",
    ),
    "1780-bnf-361:009807": (
        "itechnino, cuappiloa",
        "itech cuappiloa",
        "parallel Molina row has itech cuappiloa",
    ),
    "1780-bnf-361:009808": (
        "itechnino, piloa",
        "itech piloa",
        "parallel Molina row has itech piloa",
    ),
    "1780-bnf-361:009809": (
        "itechnino, tlatzitzquiltia",
        "itech tlatzitzquiltia",
        "itech + nino marker",
    ),
    "1780-bnf-361:009810": (
        "itechnino, tzitzquia",
        "itech tzitzquia",
        "itech + nino marker",
    ),
    "1780-bnf-361:010149": (
        "itzmolini, tehuan",
        "itzmolini tehuan",
        "reviewed comma removal",
    ),
    "1571-molina-1:015828": (
        "iznino, quixtia",
        "iz quixtia",
        "reviewed: iz + nino marker",
    ),
    "1571-molina-1:015829": (
        "iznino, quixtia",
        "iz quixtia",
        "reviewed: iz + nino marker",
    ),
    "1571-molina-1:015830": (
        "iznino, quixtia",
        "iz quixtia",
        "reviewed: iz + nino marker",
    ),
    "1780-bnf-361:010995": (
        "iznino, quixtia",
        "iz quixtia",
        "reviewed: iz + nino marker",
    ),
    "1571-molina-1:015834": (
        "iznite, quetza",
        "iz quetza",
        "reviewed: iz + nite marker",
    ),
    "1571-molina-1:015835": (
        "iznite, quetza",
        "iz quetza",
        "reviewed: iz + nite marker",
    ),
    "1780-bnf-361:010998": (
        "iznite, quetza",
        "iz quetza",
        "reviewed: iz + nite marker",
    ),
    "1780-bnf-361:015270": (
        "nohuiampani, tlachia",
        "nohuiampa tlachia",
        "parallel Molina rows have nohuiampa tlachia",
    ),
    "1780-bnf-361:015726": (
        "ocotzoticanitla, zaloa",
        "ocotzotica zaloa",
        "parallel Molina row has ocotzotica zaloa",
    ),
    "1780-bnf-361:018315": (
        "tecani, tlateca",
        "teca tlateca",
        "parallel Molina rows have teca tlateca",
    ),
    "1780-bnf-361:018325": (
        "tecanino, cayahua",
        "teca cayahua",
        "parallel Molina row has teca cayahua",
    ),
    "1780-bnf-361:018326": (
        "tecanino, motla",
        "teca motla",
        "parallel Molina row has teca motla",
    ),
    "1780-bnf-361:018965": (
        "tehuicnitla, cuania",
        "tehuic cuania",
        "tehuic + nitla marker",
    ),
    "1571-molina-1:026190": (
        "tehuicpani, tlatoa",
        "tehuicpan tlatoa",
        "tehuicpan + ni marker",
    ),
    "1780-bnf-361:018978": (
        "tehuicpani, tlatoa",
        "tehuicpan tlatoa",
        "tehuicpan + ni marker",
    ),
    "1780-bnf-361:019463": (
        "temacnite, cahua",
        "temac cahua",
        "parallel Molina row has temac cahua",
    ),
    "1780-bnf-361:020538": (
        "tepanni, moyahua",
        "tepan moyahua",
        "parallel Molina row has tepan moyahua",
    ),
    "1780-bnf-361:020967": (
        "tepozticanitla, ixpochina",
        "tepoztica ixpochina",
        "tepoztica + nitla marker",
    ),
    "1780-bnf-361:021828": (
        "tetlanni, quiztiquiza",
        "tetlan quiztiquiza",
        "tetlan + ni marker",
    ),
    "1780-bnf-361:021829": (
        "tetlanni, tlatlani",
        "tetlan tlatlani",
        "tetlan + ni marker",
    ),
    "1780-bnf-361:021836": (
        "tetlannite, calaquia",
        "tetlan calaquia",
        "tetlan + nite marker",
    ),
    "1780-bnf-361:021837": (
        "tetlannitla, cuania",
        "tetlan cuania",
        "tetlan + nitla marker",
    ),
    "1780-bnf-361:025854": (
        "tlalpaltiliaitechnino, piloa",
        "tlalpaltilia itech piloa",
        "tlalpaltilia + itech + nino marker",
    ),
    "1780-bnf-361:025861": (
        "tlalpannino, mayauhtihuetzi",
        "tlalpan mayauhtihuetzi",
        "parallel Molina row has tlalpan mayauhtihuetzi",
    ),
    "1571-molina-1:033891": (
        "caltechtli icnino, motla",
        "caltechtli ic motla",
        "caltechtli ic + nino marker",
    ),
    "1571-molina-1:034073": (
        "tlamachni, tlamamana",
        "tlamach tlamamana",
        "tlamach + ni marker",
    ),
    "1780-bnf-361:026040": (
        "tlamachni, tlamamana tlamani, tlatlailalia",
        "tlamach tlamamana tlamani tlatlailalia",
        "tlamach + ni marker",
    ),
    "1780-bnf-361:026041": (
        "tlamachnite, matoca",
        "tlamach matoca",
        "parallel Molina row has tlamach matoca",
    ),
    "1780-bnf-361:026501": (
        "tlanahuacni, quiza",
        "tlanahuac quiza",
        "parallel Molina rows have tlanahuac quiza",
    ),
    "1780-bnf-361:026502": (
        "tlanahuacni, tlateca",
        "tlanahuac tlateca",
        "parallel Molina rows have tlanahuac tlateca",
    ),
    "1571-molina-1:014633": (
        "tlaninite itta",
        "tlani itta",
        "original comma has tlani + nite marker",
    ),
    "1780-bnf-361:027048": (
        "tlani, niauh",
        "tlani yauh",
        "tlani + ni marker before yauh",
    ),
    "1780-bnf-361:027051": (
        "tlanini, nenemi",
        "tlani nenemi",
        "tlani + ni marker",
    ),
    "1780-bnf-361:027052": (
        "tlanini, palti",
        "tlani palti",
        "tlani + ni marker",
    ),
}

# User-reviewed false positives / acceptable comma rows.  Keep these out of
# the remaining review report unless their rendered value changes later.
ACCEPTED_AS_IS = {
    "1780-bnf-361:003569",
    "1571-molina-2:006849",
    "1571-molina-1:012706",
    "1571-molina-1:014316",
    "1571-molina-1:014317",
    "1780-bnf-361:009759",
    "1571-molina-1:015836",
    "1780-bnf-361:010999",
    "1571-molina-2:011791",
    "1571-molina-2:011792",
    "1571-molina-1:018191",
    "1571-molina-1:019929",
    "1780-bnf-361:013973",
    "1780-bnf-361:015607",
    "1571-molina-1:022096",
    "1571-molina-1:022590",
    "1571-molina-1:022595",
    "1780-bnf-361:016584",
    "1571-molina-1:024233",
    "1571-molina-1:025441",
    "1571-molina-1:026420",
    "1571-molina-1:026519",
    "1780-bnf-361:020412",
    "1571-molina-2:019671",
}

COMMA_MARKER_RE = re.compile(
    r"\b([a-zāēīōūáéíóúñç\[\]]+?)(nino|nite|nitla|ni),\s+([a-zāēīōūáéíóúñç]+)\b",
    re.IGNORECASE,
)


def read_rows() -> list[dict[str, object]]:
    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_rows(rows: list[dict[str, object]]) -> None:
    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes to data/data.jsonl.gz")
    args = parser.parse_args()

    rows = read_rows()
    changes: list[dict[str, object]] = []
    review: list[dict[str, object]] = []

    fixed_ids = set(CURATED_FIXES)
    for row in rows:
        record_id = str(row.get(ID_FIELD) or "")
        old_text = str(row.get(TEXT_FIELD) or "")
        if record_id in CURATED_FIXES:
            expected, replacement, reason = CURATED_FIXES[record_id]
            if old_text == expected:
                changes.append(
                    {
                        "record_id": record_id,
                        "source": row.get("Fuente"),
                        "original": row.get("Escritura original"),
                        "old_edition": old_text,
                        "new_edition": replacement,
                        "translation": row.get("Traducción"),
                        "reason": reason,
                    }
                )
                if args.apply:
                    row[TEXT_FIELD] = replacement
            elif old_text != replacement:
                review.append(
                    {
                        "record_id": record_id,
                        "source": row.get("Fuente"),
                        "original": row.get("Escritura original"),
                        "edition": old_text,
                        "translation": row.get("Traducción"),
                        "reason": f"curated expected mismatch: expected {expected!r}",
                    }
                )
            continue

        if record_id in ACCEPTED_AS_IS:
            continue

        if COMMA_MARKER_RE.search(old_text):
            review.append(
                {
                    "record_id": record_id,
                    "source": row.get("Fuente"),
                    "original": row.get("Escritura original"),
                    "edition": old_text,
                    "translation": row.get("Traducción"),
                    "reason": "remaining comma marker candidate",
                }
            )

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in changes:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    with REVIEW_PATH.open("w", encoding="utf-8") as fh:
        for item in review:
            if item.get("record_id") in fixed_ids:
                continue
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    if args.apply:
        write_rows(rows)

    print(f"changed_rows={len(changes) if args.apply else 0}")
    print(f"proposed_rows={len(changes)}")
    print(f"review_rows={sum(1 for item in review if item.get('record_id') not in fixed_ids)}")
    print(f"applied={args.apply}")
    print(f"report={REPORT_PATH}")
    print(f"review={REVIEW_PATH}")


if __name__ == "__main__":
    main()
