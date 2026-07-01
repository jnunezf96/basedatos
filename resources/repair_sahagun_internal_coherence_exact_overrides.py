#!/usr/bin/env python3
"""Apply exact Sahagun Escolios internal-coherence repairs.

These are the small set of review rows where the preserved raw packet and the
row lemma/translation make the public target number unambiguous, but the
generic scorer cannot safely infer the fix.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/sahagun_internal_coherence_exact_override_proposals.tsv")
SUMMARY_PATH = Path("resources/sahagun_internal_coherence_exact_override_summary.json")
SOURCE = "1565 Sahagún Escolios"
RAW_FIELD = "Comentario_raw_1565_sahagun_escolios"
MARKER = "sahagun_internal_coherence_exact_override_2026_06_29"
COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]


P160V_CLUSTER_GLOSSES = [
    "todos temen. pret. onemauhtiloc",
    "todos lloran a voces. pret. onechoquililoc",
    "todos dan grita. pret. onetenhuitecoc",
    "lo mismo. pret. onetempapahuiloc",
    "todos dan alaridos. pret. otlacahuacac. Lo mismo pret. otlacahuatzaloc",
    "todos dan voces. pret. otzatziuac",
    "todos vocean por todas partes. pret. oyoualli motecac",
]


def p160v_cluster_witness(target: str) -> str:
    pieces = [
        "nemauhtilo",
        "nechoquililo",
        "tlachoquiztlehua in macehualti",
        "netenhuiteco",
        "netempapahuilo",
        "tlacahuaca",
        "tlacahuatzalo",
        "tzatzihua",
        "oyoualli",
    ]
    numbered = {
        "nemauhtilo": "11",
        "nechoquililo": "12",
        "netenhuiteco": "13",
        "netempapahuilo": "14",
        "tlacahuaca": "15",
        "tzatzihua": "16",
        "oyoualli": "17",
    }
    out = []
    for piece in pieces:
        text = f"<b>{piece}</b>" if piece == target else piece
        if piece in numbered:
            text = f"{text} ({numbered[piece]})"
        out.append(text)
    return (
        "<i>"
        + ", ".join(out[:5])
        + ", "
        + ", ".join(out[5:8])
        + ", "
        + out[8]
        + " moteca</i>. P_160v"
    )


OVERRIDES = {
    "1565-sahagun-escolios:000181": {
        "target_number": 24,
        "target_raw": "24",
        "definition": "cantar cantares que se llaman xochcuicatl",
        "witness_line": "<i>Auh in teteupan (23) <b>xuxuchcuico</b> (24), tlachalantoc (25), tlacahuacatoc (26)</i>. P_160v",
        "glosses": [
            (23, "por todos los templos"),
            (24, "cantar cantares que se llaman xochcuicatl"),
            (25, "hacer ruido. pret. otlachalantoca"),
            (26, "dar alaridos. pret. otlacahuacatoca"),
        ],
        "citation": {"folio_end": None, "folio_start": "160v", "manuscript": "P", "raw": "P_160v", "type": "folio"},
        "reason": "raw packet gloss 24 and row translation identify xochcuica; previous public target pointed to 23/34",
    },
    "1565-sahagun-escolios:000245": {
        "target_number": 2,
        "target_raw": "2",
        "definition": "fuerte.... noiolloteuh",
        "witness_line": "<i>Omacic oquichtli:<br/>y omacic oquichtli, <b>yollotetl</b> (2), yollotlacoaoac (3), ixtlamati (4), ixe (5), yollo, mozcalia (6)</i>. Borrador",
        "glosses": [
            (2, "fuerte.... noiolloteuh"),
            (3, "persona de recio corazón"),
            (4, "persona sabia. ca. nixtlamascauh"),
            (5, "persona prudente. ca. nixecauh, noiollocauh"),
            (6, "persona ...zada"),
        ],
        "citation": {"raw": "Borrador", "type": "draft"},
        "reason": "raw header and inline target mark yollotetl as gloss 2; previous metadata pointed at 14",
    },
    "1565-sahagun-escolios:000320": {
        "target_number": 47,
        "target_raw": "47+",
        "definition": "sentarse a esperar",
        "witness_line": "<i>Niman (43) ic compehualtique (44) in ye tlamacehua (45), mozauhque nahuilhuitl omextin (46) in tecuciztecatl. Auh niman no icuac <b>motlali</b> in tletl (47) ye tlatla (48) in oncan tlecuilco (49) quitocayotia (50) in tlecuilli teutexcalli.</i>. P_161v",
        "glosses": [
            (43, "luego"),
            (44, "comenzar. pret. onitlapehualti"),
            (45, "hacer penitencia. pret. onitlamaceuh"),
            (46, "ambos"),
            (47, "sentarse a esperar. pret. onicchixtimotlali. onicchixtimotecac"),
            (48, "arder. pret. onitlatlac"),
            (49, "hogar. caso. notlecuil"),
            (50, "nombrar. pret. onitetocayoti"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 47+ has motlali in tletl for the onicchixtimotlali half of the chixtimoteca gloss; generic rebuild could not choose among duplicate 47 targets",
    },
    "1565-sahagun-escolios:000327": {
        "target_number": 4,
        "target_raw": "4+",
        "definition": "huir de alguno",
        "witness_line": "<i>Yic cenca chocaya, huel ixpopozahuac (2), ixcuatolpopozahuac (3): auh in ye itech onaci miquiztli, zan <b>teixpampa</b> (4) yehuac, cholo, tochtitlan (5) calactihuetz (6) ipan (7) onmixeuh, ic omocueptihuetz in tochtli ome mani, maxaltic (8) in quitocayotia millaca xolotl.</i>. P_161v",
        "glosses": [
            (2, "llorar mucho"),
            (3, "hincharse los parpados de los ojos. pret. onixcuatolpopozahuac. oniquatolehuac. onixeehuac"),
            (4, "huir de alguno. pret. oteixpampanehuac. onicholo"),
            (5, "entre maíz verde"),
            (6, "entrar de presto o subitamente. pret. onicalactihuetz"),
            (7, "convertirse o tomar figura de otra cosa. pret. ipan oninixeuh. ipan oninocuep. ic oninocuep"),
            (8, "cosa doblada o cosa que esta de dos en dos en una raiz"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v has the teixpampa/cholo target in a later duplicate-number 4 span; previous public rebuild selected the first unrelated number 4",
    },
    "1565-sahagun-escolios:000426": {
        "target_number": 7,
        "target_raw": "7+",
        "definition": "convertirse o tomar figura de otra cosa",
        "witness_line": "<i>Yic cenca chocaya, huel ixpopozahuac (2), ixcuatolpopozahuac (3): auh in ye itech onaci miquiztli, zan teixpampa (4) yehuac, cholo, tochtitlan (5) calactihuetz (6) ipan (7) onmixeuh, ic <b>omocueptihuetz</b> in tochtli ome mani, maxaltic (8) in quitocayotia millaca xolotl.</i>. P_161v",
        "glosses": [
            (2, "llorar mucho"),
            (3, "hincharse los parpados de los ojos. pret. onixcuatolpopozahuac. oniquatolehuac. onixeehuac"),
            (4, "huir de alguno. pret. oteixpampanehuac. onicholo"),
            (5, "entre maíz verde"),
            (6, "entrar de presto o subitamente. pret. onicalactihuetz"),
            (7, "convertirse o tomar figura de otra cosa. pret. ipan oninixeuh. ipan oninocuep. ic oninocuep"),
            (8, "cosa doblada o cosa que esta de dos en dos en una raiz"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 7+ supplies omocueptihuetz for the ipan cuepa row; generic rebuild selected an earlier unrelated number 7",
    },
    "1565-sahagun-escolios:000575": {
        "target_number": 11,
        "target_raw": "11-",
        "definition": "hacer fiesta",
        "witness_line": "<i>Matlacpoaltica (10) ipan epoalli in ilhuiuh (11) quizaya, in <b>ilhuichihuililoya</b>.</i>. P_160r",
        "glosses": [
            (10, "cada doscientos y sesenta días"),
            (11, "hacer fiesta pret. onilhuichiuh. onilhuiquixti"),
        ],
        "citation": {"folio_end": None, "folio_start": "160r", "manuscript": "P", "raw": "P_160r", "type": "folio"},
        "reason": "raw P_160r witness contains the target verb form ilhuichihuililoya for hacer fiesta; previous public bold fell on the preceding count phrase",
    },
    "1565-sahagun-escolios:000589": {
        "target_number": 18,
        "target_raw": "18",
        "definition": "este",
        "witness_line": "<i><b>In</b> (18) hin huel imacaxo (19) huellamauhtia (20), cenca totoca in icuac moquetza (21), amo huel quixnamiqui (22) in acalli amo huellahuilteco (23), amo huel tlaxtlapalolo, ahuel ixtlapal huiloa.</i>. P_167r-168r",
        "glosses": [
            (18, "este"),
            (19, "ser temido"),
            (20, "cosa que hace espanto"),
            (21, "soplar. o estar. pret. oninoquetz"),
            (22, "ir contra otro. pret. oniquixnamic"),
            (23, "atravesar por delante"),
        ],
        "citation": {"folio_end": "168r", "folio_start": "167r", "manuscript": "P", "raw": "P_167r-168r", "type": "folio"},
        "reason": "raw P_167r-168r witness and gloss identify the short function-word target In (18); the bold audit needed an exact override for this valid short form",
    },
    "1565-sahagun-escolios:000608": {
        "target_number": 7,
        "target_raw": "7-",
        "definition": "convertirse o tomar figura de otra cosa",
        "witness_line": "<i>Yic cenca chocaya, huel ixpopozahuac (2), ixcuatolpopozahuac (3): auh in ye itech onaci miquiztli, zan teixpampa (4) yehuac, cholo, tochtitlan (5) calactihuetz (6) ipan (7) <b>onmixeuh</b>, ic omocueptihuetz in tochtli ome mani, maxaltic (8) in quitocayotia millaca xolotl.</i>. P_161v",
        "glosses": [
            (2, "llorar mucho"),
            (3, "hincharse los parpados de los ojos. pret. onixcuatolpopozahuac. oniquatolehuac. onixeehuac"),
            (4, "huir de alguno. pret. oteixpampanehuac. onicholo"),
            (5, "entre maíz verde"),
            (6, "entrar de presto o subitamente. pret. onicalactihuetz"),
            (7, "convertirse o tomar figura de otra cosa. pret. ipan oninixeuh. ipan oninocuep. ic oninocuep"),
            (8, "cosa doblada o cosa que esta de dos en dos en una raiz"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 7- supplies onmixeuh for the ipan ixehua row; generic rebuild selected an earlier unrelated number 7",
    },
    "1565-sahagun-escolios:000436": {
        "target_number": 41,
        "target_raw": "41-",
        "definition": "tomarse",
        "witness_line": "<i>In hin quilmach oncan man (41), oncan <b>mocuic</b> in tlatolli, inic itolo, tenehualo in aquin tiacauh oquichtli cuauhtlocelotl (42) tocayotilo.</i>. P_161v",
        "glosses": [
            (41, "tomarse. pret. oman. omocuic"),
            (42, "hombre diestro en las armas"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 41 occurrence has oncan mocuic for the omocuic/cui row; generic rebuild selected the short adjacent ye",
    },
    "1565-sahagun-escolios:000548": {
        "target_number": 24,
        "target_raw": "24+",
        "definition": "entenado o entenada, la mujer dice algunas veces mi entenado o entenada nochvaconeuh",
        "witness_line": "<i>Tlacpahuitectli (24), <b>chahuaconetl</b>. In tlacpahuitectli, tlacnocahualli (25), icnotl, nanmicqui (26), tamicqui (27).</i>. A_95r",
        "glosses": [
            (24, "entenado o entenada ca. notlacpahuitec, la mujer dice algunas veces mi entenado o entenada, nochvaconeuh"),
            (25, "persona huérfana ca. nocnouh"),
            (26, "persona que le murió su madre ca. nonanmicauh"),
            (27, "persona que se le murió su padre ca. notamicauh"),
        ],
        "citation": {"folio_end": None, "folio_start": "95r", "manuscript": "A", "raw": "A_95r", "type": "folio"},
        "reason": "raw A_95r witness gives chahuaconetl as the target-form witness for the nochvaconeuh/ichuaconeuh gloss; previous rebuild would bold the adjacent synonym tlacpahuitectli",
    },
    "1565-sahagun-escolios:000629": {
        "target_number": 15,
        "target_raw": "15",
        "definition": "nombre",
        "witness_line": "<i>Matlacpoaltica (10) ipan epoalli in ilhuiuh (11) quizaya, in ilhuichihuililoya. ilhuiquixtililoya ipan (12) quimattihuiya (13) in itonal (14) <b>itoca</b> naolin (15)</i>. P_160r",
        "glosses": [
            (10, "cada doscientos y sesenta días"),
            (11, "hacer fiesta. pret. onilhuichiuh. onilhuiquixti"),
            (12, "en"),
            (13, "seguirse"),
            (14, "su signo"),
            (15, "nombre"),
        ],
        "citation": {"folio_end": None, "folio_start": "160r", "manuscript": "P", "raw": "P_160r", "type": "folio"},
        "reason": "raw header NOMBRE (15) identifies the unnumbered itoca occurrence in the witness",
    },
    "1565-sahagun-escolios:000785": {
        "target_number": 11,
        "target_raw": "11",
        "definition": "temer",
        "witness_line": p160v_cluster_witness("nemauhtilo"),
        "glosses": list(zip(range(11, 18), P160V_CLUSTER_GLOSSES)),
        "citation": {"folio_end": None, "folio_start": "160v", "manuscript": "P", "raw": "P_160v", "type": "folio"},
        "reason": "raw P_160v cluster maps temer/mauhtia to nemauhtilo (11)",
    },
    "1565-sahagun-escolios:000901": {
        "target_number": 17,
        "target_raw": "17-18",
        "definition": "cuatro día o fiesta",
        "witness_line": "<i>Auh in ayamo quiza ilhuiuh achtopa (16) <b>nahuilhuitl</b> (17-18) nezahualoya (19).</i>. P_160r",
        "glosses": [
            (16, "antes"),
            ("17-18", "cuatro día o fiesta"),
            (19, "ayunar pret. oninozauh"),
        ],
        "citation": {"folio_end": None, "folio_start": "160r", "manuscript": "P", "raw": "P_160r", "type": "folio"},
        "reason": "raw P_160r witness/gloss range maps nahuilhuitl to lexical gloss 17-18; previous metadata pointed to gloss 19",
    },
    "1565-sahagun-escolios:000644": {
        "target_number": 7,
        "target_raw": "7+",
        "definition": "no puede sufrir la pena o trabajo",
        "witness_line": "<i>auh za (4) ahuelmotlapalo (5), in ye no itech onaci totonqui, zan hualtzinquiza hualtzincholoa (6), amo (7) <b>ontlayecoa</b>: ul? nappa.</i>. P_161v",
        "glosses": [
            (4, "en ninguna manera"),
            (5, "osar o atreverse. pret. oninotlapalo"),
            (6, "saltar atrás. pret. onihualtzincholo. onitzincholo"),
            (7, "no puede sufrir la pena o trabajo. pret. amo onontlayeco. a. onoconyeco"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v witness has amo (7) ontlayecoa for the no-puede-sufrir gloss; target highlight belongs on ontlayecoa rather than the negator amo",
    },
    "1565-sahagun-escolios:000653": {
        "target_number": 3,
        "target_raw": "3+",
        "definition": "persona que procede de otro, como los barbas y cejas procede de la cara",
        "witness_line": "<i>¶ Ixuiuhtli (1), tepiltzin (2), tetzon, teizti, tentzontli (3), <b>ixcuamolli</b>, tehuitzyo (4), teahuaio, tetzicuehuallo (5), tecacamayo (6), tenecauhca (7), cozcatl (8), quetzalli, tequixti (9).</i>. A_92v",
        "glosses": [
            (1, "nieto o nieta ca. noxhuiuh noxhuiuhtzi, noxuiuhticatzin"),
            (2, "persona amada querida estimada de los suyos"),
            (3, "persona que procede de otro, como los barbas y cejas procede de la cara ca. notentzon notentzontzi, nixcuamol nixcuamoltzin"),
            (4, "persona espinosa ca. notehuitzyo"),
            (5, "persona que tiene cosquillas ca. notetzicuehuallo"),
            (6, "persona que tiene boca ca. notecacamayo"),
            (7, "entrago vivo ca. nonecauhcauh o necauhcayo"),
            (8, "collar ca. nocozca"),
            (9, "persona escogida ca. notequixti"),
        ],
        "citation": {"folio_end": None, "folio_start": "92v", "manuscript": "A", "raw": "A_92v", "type": "folio"},
        "reason": "raw A_92v witness puts ixcuamolli immediately after target number 3 for the ixcuamoltzin gloss; previous rebuild would bold tentzontli",
    },
    "1565-sahagun-escolios:000666": {
        "target_number": 1,
        "target_raw": "1+",
        "definition": "nieto o nieta",
        "witness_line": "<i>¶ <b>Ixhuiuhtli</b> (1), tepiltzin (2), tetzon, teizti, tentzontli (3), ixcuamolli, tehuitzyo (4), teahuaio, tetzicuehuallo (5), tecacamayo (6), tenecauhca (7), cozcatl (8), quetzalli, tequixti (9).</i>. A_92v",
        "glosses": [
            (1, "nieto o nieta ca. noxhuiuh noxhuiuhtzi, noxuiuhticatzin"),
            (2, "persona amada querida estimada de los suyos"),
            (3, "persona que procede de otro, como los barbas y cejas procede de la cara ca. notentzon notentzontzi, nixcuamol nixcuamoltzin"),
            (4, "persona espinosa ca. notehuitzyo"),
            (5, "persona que tiene cosquillas ca. notetzicuehuallo"),
            (6, "persona que tiene boca ca. notecacamayo"),
            (7, "entrago vivo ca. nonecauhcauh o necauhcayo"),
            (8, "collar ca. nocozca"),
            (9, "persona escogida ca. notequixti"),
        ],
        "citation": {"folio_end": None, "folio_start": "92v", "manuscript": "A", "raw": "A_92v", "type": "folio"},
        "reason": "raw A_92v witness/gloss maps ixhuiuhticatzin to ixhuiuhtli (1); the generic form gate was too strict for the derived lemma",
    },
    "1565-sahagun-escolios:000674": {
        "target_number": 95,
        "target_raw": "95",
        "definition": "afear la cara a otro",
        "translation": "afear la cara a otro",
        "witness_line": "<i>Yuh yez hin, yuh (91) muchihuaz hin? Niman ic ce tlacatl ōnmotlalotiquiz (92) in teteu, ic conixhuihuitiquito (93) in tochin in yehuatl tecuciztecatl, ic conixpopoloque (94), ic <b>conixomictique</b> (95) in iuhqui axcan ic tlachie.</i>. P_161v",
        "glosses": [
            (91, "de esta manera se hará esto"),
            (92, "huir. pret. oninotlalotiquiz"),
            (93, "herir en la cara. pret. oniteixhuitec"),
            (94, "estragar la cara a alguno. pret. oniteixpopolo"),
            (95, "afear la cara a otro. pret. oniteixmicti"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 95 has conixomictique for the teixmictia gloss; generic rebuild selected the wrong duplicate-number 95 occurrence",
    },
    "1565-sahagun-escolios:000738": {
        "target_number": 3,
        "target_raw": "3+",
        "definition": "arrojarse con ímpeto para hacer algo. o darse todo a van cosa",
        "witness_line": "<i>ye no ceppa yauh tlayehecoz (1), ixquich (2) caana, ic (3) <b>momotla, quimomaca</b> in tletl:</i>. P_161v",
        "glosses": [
            (1, "probar a hacer algo. pret. onitlayeheco"),
            (2, "esforzarse para hacer algo. o poner todas las fuerzas para hacer algo"),
            (3, "arrojarse con ímpeto para hacer algo. o darse todo a van cosa. pret. ic oninomotlac. onicnomacac"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v witness has ic (3) momotla, quimomaca for the motlamaca gloss; target highlight belongs on the verbal phrase, not ic",
    },
    "1565-sahagun-escolios:000915": {
        "target_number": 7,
        "target_raw": "7+",
        "definition": "entrago vivo o necauhcayo",
        "witness_line": "<i>¶ Ixhuiuhtli (1), tepiltzin (2), tetzon, teizti, tentzontli (3), ixcuamolli, tehuitzyo (4), teahuaio, tetzicuehuallo (5), tecacamayo (6), <b>tenecauhca</b> (7), cozcatl (8), quetzalli, tequixti (9).</i>. A_92v",
        "glosses": [
            (1, "nieto o nieta ca. noxhuiuh noxhuiuhtzi, noxuiuhticatzin"),
            (2, "persona amada querida estimada de los suyos"),
            (3, "persona que procede de otro, como los barbas y cejas procede de la cara ca. notentzon notentzontzi, nixcuamol nixcuamoltzin"),
            (4, "persona espinosa ca. notehuitzyo"),
            (5, "persona que tiene cosquillas ca. notetzicuehuallo"),
            (6, "persona que tiene boca ca. notecacamayo"),
            (7, "entrago vivo ca. nonecauhcauh o necauhcayo"),
            (8, "collar ca. nocozca"),
            (9, "persona escogida ca. notequixti"),
        ],
        "citation": {"folio_end": None, "folio_start": "92v", "manuscript": "A", "raw": "A_92v", "type": "folio"},
        "reason": "raw A_92v witness puts tenecauhca on target number 7 for the necauhcayo gloss; generic similarity was too strict",
    },
    "1565-sahagun-escolios:000810": {
        "target_number": 41,
        "target_raw": "41+",
        "definition": "tomarse",
        "witness_line": "<i>In hin quilmach oncan <b>man</b> (41), oncan mocuic in tlatolli, inic itolo, tenehualo in aquin tiacauh oquichtli cuauhtlocelotl (42) tocayotilo.</i>. P_161v",
        "glosses": [
            (41, "tomarse. pret. oman. omocuic"),
            (42, "hombre diestro en las armas"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 41 occurrence has oncan man for the oman/ana row; generic rebuild selected the short adjacent ye",
    },
    "1565-sahagun-escolios:000771": {
        "target_number": 90,
        "target_raw": "90-",
        "definition": "ponerse algunas personas en pie en lugar aparente",
        "witness_line": "<i>motenehua teutexcalli, in oncan nahuilhuitl otlatlac tletl, nenecoc (87) motecpanque (88): auh nepantla (89) <b>quimōnmanque</b> (90), quimonquetzque in omextin hin, motenehua in tecuciztecatl yoan nanaoatzin.</i>. P_161v",
        "glosses": [
            (87, "como sera esto"),
            (88, "dos juntos"),
            (89, "andar camino. pret. onotlatocac"),
            (90, "ponerse algunas personas en pie en lugar aparente. pret. oniquimoman. oniquimoquetz"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 90 occurrence has quimōnmanque for the oniquimoman/motlamani row; previous generic rebuild selected a different duplicate-number 90 occurrence",
    },
    "1565-sahagun-escolios:001104": {
        "target_number": 90,
        "target_raw": "90+",
        "definition": "ponerse algunas personas en pie en lugar aparente",
        "witness_line": "<i>motenehua teutexcalli, in oncan nahuilhuitl otlatlac tletl, nenecoc (87) motecpanque (88): auh nepantla (89) quimōnmanque (90), <b>quimonquetzque</b> in omextin hin, motenehua in tecuciztecatl yoan nanaoatzin.</i>. P_161v",
        "glosses": [
            (87, "como sera esto"),
            (88, "dos juntos"),
            (89, "andar camino. pret. onotlatocac"),
            (90, "ponerse algunas personas en pie en lugar aparente. pret. oniquimoman. oniquimoquetz"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 90 occurrence has quimonquetzque for the oniquimoquetz/motlaquetza row; previous generic rebuild selected a different duplicate-number 90 occurrence",
    },
    "1565-sahagun-escolios:001141": {
        "target_number": 1,
        "target_raw": "1+",
        "definition": "el hermano mayor en linaje de oficio, dice la mujer nachtzin",
        "witness_line": "<i>Tetiachcauh (1), <b>teachcauh</b>, teteachcauh, teach, tecemitquini (2), tecenvihuilanani, tecenmamani, teixtlamachtiani (3), tetetzahuani (4).</i>. A_94v-95r",
        "glosses": [
            (1, "el hermano mayor en linaje de oficio caso. notiachcauh, noteachcauh, nachcauh, nachtze dice la mujer nachtzin"),
            (2, "persona que lleva sobre si toda la carga corporal o espiritual ca. notecemitquicauh, notecenpilancauh, notecenmamacauh"),
            (3, "persona que doctrina a sus menores ca. noteixtlamachticauh"),
            (4, "persona que releva a los chiquillos hasta que sean para el trabajo"),
        ],
        "citation": {"folio_end": "95r", "folio_start": "94v", "manuscript": "A", "raw": "A_94v-95r", "type": "folio"},
        "reason": "raw A_94v-95r target 1+ gloss gives the nachtze/teachtze kin term inside the teachcauh target group; generic rebuild left the target group unbolded",
    },
    "1565-sahagun-escolios:001162": {
        "target_number": 2,
        "target_raw": "2+",
        "definition": "persona que lleva sobre si toda la carga corporal o espiritual",
        "witness_line": "<i>Tetiachcauh (1), teachcauh, teteachcauh, teach, tecemitquini (2), tecenvihuilanani, <b>tecenmamani</b>, teixtlamachtiani (3), tetetzahuani (4).</i>. A_94v-95r",
        "glosses": [
            (1, "el hermano mayor en linaje de oficio caso. notiachcauh, noteachcauh, nachcauh, nachtze dice la mujer nachtzin"),
            (2, "persona que lleva sobre si toda la carga corporal o espiritual ca. notecemitquicauh, notecenpilancauh, notecenmamacauh"),
            (3, "persona que doctrina a sus menores ca. noteixtlamachticauh"),
            (4, "persona que releva a los chiquillos hasta que sean para el trabajo"),
        ],
        "citation": {"folio_end": "95r", "folio_start": "94v", "manuscript": "A", "raw": "A_94v-95r", "type": "folio"},
        "reason": "raw A_94v-95r witness lists tecenmamani in the target-2 group for the tecemmamani gloss; previous rebuild bolded tecemitquini",
    },
    "1565-sahagun-escolios:001297": {
        "target_number": 2,
        "target_raw": "2",
        "definition": "atribuir",
        "witness_line": "<i>Teutl ipan machoya, itech (2) <b>tlamiloya</b> in quiahuitl (3) in atl, yuh quitohuaya yeh quichihua in ticcua (4), in tiqui (5), in cualoni (6), in ihuani (7), in tonenca (8), in toyolca (8), in tocochca, in toneuhca (8).</i>",
        "glosses": [
            (2, "atribuir. pres. tetech nictlamia. pret. tetech onictlami"),
            (3, "lluvia"),
            (4, "comer pret. onitlacua"),
            (5, "beber. pret. oniquic, onitlai"),
            (6, "cosa comestible"),
            (7, "cosa buena para beber"),
            (8, "nuestro sustento"),
        ],
        "citation": {},
        "reason": "raw witness has itech (2) tlamiloya for the atribuir/tetech tlamia gloss; previous generic rebuild selected a later unrelated numbered item",
    },
    "1565-sahagun-escolios:001301": {
        "target_number": 98,
        "target_raw": "98-",
        "definition": "pararse con firmo propósito de no moverse más",
        "witness_line": "<i>In iuhqui in icuac ic omomanaco onteixtin, ye no cueleh ahuel (96) olini (97), ahuel otlatoca, zan momanque, <b>motetenmanque</b> (98): ic ye no ceppa quitoque in teteu, quentinemizque amo olini in tonatiuh cuix tiquinnelotinemizque (99) in macehualti.</i>. P_161v",
        "glosses": [
            (96, "no poder"),
            (97, "moverse. pret. onolin. oninolini"),
            (98, "pararse con firmo propósito de no moverse mas. pret. omotetenma. oninoteteuhtlali. oninoteteuhquetz"),
            (99, "mezclarse con otros. pret. onitenelo"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v has the second duplicate-number 98 span motetenmanque for this tetenmana gloss; previous public highlight selected unrelated target 99",
    },
    "1565-sahagun-escolios:001309": {
        "target_number": 98,
        "target_raw": "98+",
        "definition": "pararse con firmo propósito de no moverse mas",
        "witness_line": "<i>In iuhqui in icuac ic omomanaco onteixtin, ye no cueleh ahuel (96) olini (97), ahuel otlatoca, zan momanque, <b>motetenmanque</b> (98): ic ye no ceppa quitoque in teteu, quentinemizque amo olini in tonatiuh cuix tiquinnelotinemizque (99) in macehualti.</i>. P_161v",
        "glosses": [
            (96, "no poder"),
            (97, "moverse. pret. onolin. oninolini"),
            (98, "pararse con firmo propósito de no moverse mas. pret. omotetenma. oninoteteuhtlali. oninoteteuhquetz"),
            (99, "mezclarse con otros. pret. onitenelo"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 98+ gloss lists oninoteteuhquetz for the moteteuhquetza row; visible witness belongs to the same target-98 gloss group, not target 99",
    },
    "1565-sahagun-escolios:001310": {
        "target_number": 98,
        "target_raw": "98+",
        "definition": "pararse con firmo propósito de no moverse mas",
        "witness_line": "<i>In iuhqui in icuac ic omomanaco onteixtin, ye no cueleh ahuel (96) olini (97), ahuel otlatoca, zan momanque, <b>motetenmanque</b> (98): ic ye no ceppa quitoque in teteu, quentinemizque amo olini in tonatiuh cuix tiquinnelotinemizque (99) in macehualti.</i>. P_161v",
        "glosses": [
            (96, "no poder"),
            (97, "moverse. pret. onolin. oninolini"),
            (98, "pararse con firmo propósito de no moverse mas. pret. omotetenma. oninoteteuhtlali. oninoteteuhquetz"),
            (99, "mezclarse con otros. pret. onitenelo"),
        ],
        "citation": {"folio_end": None, "folio_start": "161v", "manuscript": "P", "raw": "P_161v", "type": "folio"},
        "reason": "raw P_161v target 98+ gloss lists oninoteteuhtlali for the moteteuhtlalia row; visible witness belongs to the same target-98 gloss group, not target 99",
    },
    "1565-sahagun-escolios:001166": {
        "target_number": 25,
        "target_raw": "25",
        "definition": "cosa humosa, a quiere decir no",
        "witness_line": "<i><b>apocyo</b> (25), motetzontia (26), tetetzontia (27), tlapachoa (28), tetlapachilhuia (29), monepacholtia (30), monemachtia (31), tenepacholtia (32), hueca (33) tlachia (34), tetlamachia (35), tlatlalia (36), tlatecpana (37)</i>. A_88r",
        "glosses": [
            (25, "cosa humosa, ca. nopocyocauh, a quiere decir no"),
            (26, "atesorar para sí. pret. oninotetzonti"),
            (27, "atesorar para otro. pret. onitetetzonti"),
            (28, "guardar su hacienda. pret. onitlapacho"),
            (29, "guardar algo para otro. pret. onitetlapachilhui"),
            (30, "tener cuenta con lo que gasta. pret. oninonepacholti"),
            (31, "guardar para cuando fuere menester. pret. oninonemachti"),
            (32, "enseñar o guardar. pret. onitenepachulti"),
            (33, "hueca, lejos, ca. noueca"),
            (34, "mirar. pret. onitlachix"),
            (35, "disponer o repartir las cosas ordenadamente. pret. onitetlamachi"),
            (36, "idem o mandar. pret. onitlatlali"),
            (37, "ordenar. pret. onitlatecpa"),
        ],
        "citation": {"folio_end": None, "folio_start": "88r", "manuscript": "A", "raw": "A_88r", "type": "folio"},
        "reason": "raw header COSA HUMOSA... (25B) and gloss 25 identify hapocyo/apocyo as the target",
    },
    "1565-sahagun-escolios:001194": {
        "target_number": 13,
        "target_raw": "13",
        "definition": "dar gritos",
        "witness_line": p160v_cluster_witness("netenhuiteco"),
        "glosses": list(zip(range(11, 18), P160V_CLUSTER_GLOSSES)),
        "citation": {"folio_end": None, "folio_start": "160v", "manuscript": "P", "raw": "P_160v", "type": "folio"},
        "reason": "raw P_160v cluster maps dar gritos/tehuitqui to netenhuiteco (13)",
    },
    "1565-sahagun-escolios:001219": {
        "target_number": 14,
        "target_raw": "14",
        "definition": "dar gritos",
        "witness_line": p160v_cluster_witness("netempapahuilo"),
        "glosses": list(zip(range(11, 18), P160V_CLUSTER_GLOSSES)),
        "citation": {"folio_end": None, "folio_start": "160v", "manuscript": "P", "raw": "P_160v", "type": "folio"},
        "reason": "raw P_160v cluster maps dar gritos/tempapahuiya to netempapahuilo (14)",
    },
    "1565-sahagun-escolios:001259": {
        "target_number": 7,
        "target_raw": "7+",
        "definition": "venir a simplicidad o a estado de inocencia",
        "witness_line": "<i>¶ Tecul (1), culli, in tecul, chicahuac (2), pipinqui (3), tzoniztac (4), cuaiztac (5), otlatziuh (6) aoc (7) quenca iyollo, <b>oteut</b>.</i>. A_91v",
        "glosses": [
            (1, "abuelo caso. nocul"),
            (2, "cosa dura ca. nochicahuacatzin"),
            (3, "cosa correosa ca. nopipincauh"),
            (4, "persona de cabellos canos ca. notzoniztacauh"),
            (5, "persona de cabeza cana ca. nocuaiztacauh"),
            (6, "hacer se inútil o infructuoso o impotente pret. onitlatziuh"),
            (7, "venir a simplicidad o a estado de inocencia"),
        ],
        "citation": {"folio_end": None, "folio_start": "91v", "manuscript": "A", "raw": "A_91v", "type": "folio"},
        "reason": "raw header gives pt. oteut for teoti (7+), so the public target highlight belongs on oteut rather than aoc",
    },
}

STALE_TARGET_CLEARS = {
    "1565-sahagun-escolios:000572": "no preserved raw packet and no public target apparatus remain for ilhuia",
    "1565-sahagun-escolios:000843": "no preserved raw packet and no public target apparatus remain for mochi",
    "1565-sahagun-escolios:000906": "no preserved raw packet and no public target apparatus remain for nanahuatzin",
    "1565-sahagun-escolios:001527": "no preserved raw packet and no public target apparatus remain for tlapaloa",
}


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def append_issue(value: object, marker: str) -> list[str]:
    if isinstance(value, list):
        out = [str(item) for item in value]
    elif value:
        out = [str(value)]
    else:
        out = []
    if marker not in out:
        out.append(marker)
    return out


def build_commentary(row: dict, override: dict) -> str:
    lemma = str(row.get("Editado") or row.get("Original") or "").strip()
    gloss_html = "".join(f"({number}) {text};<br/>" for number, text in override["glosses"])
    return (
        f"{lemma}.<br/><br/>{override['definition']}<br/><br/>"
        f"{override['witness_line']}<br/><br/>"
        f"Glosas relevantes del escolio:<br/>{gloss_html}"
    )


def apply_override(row: dict, override: dict) -> None:
    previous_commentary = str(row.get("Comentario", ""))
    commentary = build_commentary(row, override)
    for field in COMMENTARY_FIELDS:
        row[field] = commentary
    if override.get("translation"):
        row["Traducción"] = override["translation"]

    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
    row["Comentario_display_issues"] = append_issue(row.get("Comentario_display_issues"), MARKER)

    metadata = row.setdefault("Sahagun_Escolios_JSON", {})
    metadata["target_number_base"] = override["target_number"]
    metadata["target_number_raw"] = override["target_raw"]
    alignment = metadata.setdefault("target_alignment_v34_1", {})
    alignment["number_base"] = override["target_number"]
    alignment["number_raw"] = override["target_raw"]
    alignment["repair_policy"] = MARKER
    alignment["review_needed"] = False

    display = metadata.setdefault("display", {})
    display["html"] = commentary
    display["display_gloss"] = override["definition"]
    display["display_witness_line"] = override["witness_line"]
    display["citation"] = override["citation"]
    display["lemma"] = str(row.get("Editado") or row.get("Original") or "").strip()
    display["witness_count"] = 1
    display["issues"] = append_issue(display.get("issues"), MARKER)

    witness = metadata.setdefault("witness", {})
    witness["display_gloss_v28"] = override["definition"]
    witness["display_witness_line_v28"] = override["witness_line"]
    witness["citation"] = override["citation"]
    witness["v28_display_method"] = MARKER

    metadata["qa_v90_internal_coherence_exact_override"] = {
        "action": "rebuilt_public_fields_from_exact_raw_packet_override",
        "marker": MARKER,
        "target_number_base": override["target_number"],
        "target_number_raw": override["target_raw"],
        "reason": override["reason"],
        "raw_field": RAW_FIELD,
        "raw_preserved": True,
        "previous_commentary_sha1": hashlib.sha1(previous_commentary.encode("utf-8")).hexdigest(),
    }


def current_target_number(row: dict) -> object:
    metadata = row.get("Sahagun_Escolios_JSON", {})
    if isinstance(metadata, dict):
        return metadata.get("target_number_base")
    return ""


def clear_stale_target(row: dict, reason: str) -> None:
    metadata = row.setdefault("Sahagun_Escolios_JSON", {})
    previous_target = metadata.get("target_number_base")
    previous_raw = metadata.get("target_number_raw")
    metadata.pop("target_number_base", None)
    metadata.pop("target_number_raw", None)
    alignment = metadata.setdefault("target_alignment_v34_1", {})
    alignment.pop("number_base", None)
    alignment.pop("number_raw", None)
    alignment["review_needed"] = True
    alignment["stale_target_number_cleared_by"] = MARKER
    metadata["qa_v90_internal_coherence_stale_target_clear"] = {
        "action": "cleared_stale_target_number_without_raw_or_public_apparatus",
        "marker": MARKER,
        "previous_target_number_base": previous_target,
        "previous_target_number_raw": previous_raw,
        "reason": reason,
    }
    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), MARKER)
    row["Comentario_display_issues"] = append_issue(row.get("Comentario_display_issues"), MARKER)


def load_rows(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    os.replace(tmp, path)


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--proposals", type=Path, default=PROPOSALS_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    proposals: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        record_id = row.get("record_id", "")
        override = OVERRIDES.get(record_id)
        stale_clear_reason = STALE_TARGET_CLEARS.get(record_id)
        if not override and not stale_clear_reason:
            continue
        current_number = current_target_number(row)
        if override:
            counts["override_rows"] += 1
            new_commentary = build_commentary(row, override)
            needs_change = (
                any(row.get(field) != new_commentary for field in COMMENTARY_FIELDS)
                or current_number != override["target_number"]
                or (bool(override.get("translation")) and row.get("Traducción") != override["translation"])
            )
            new_target_number = str(override["target_number"])
            definition = override["definition"]
            witness_line = override["witness_line"]
            reason = override["reason"]
        else:
            counts["stale_target_clear_rows"] += 1
            needs_change = current_number not in ("", None)
            new_target_number = ""
            definition = ""
            witness_line = ""
            reason = stale_clear_reason or ""
        if not needs_change:
            continue
        proposals.append(
            {
                "record_id": record_id,
                "original": row.get("Original", ""),
                "editado": row.get("Editado", ""),
                "old_target_number": str(current_number),
                "new_target_number": new_target_number,
                "definition": definition,
                "witness_line": witness_line,
                "reason": reason,
            }
        )
        counts["proposal_rows"] += 1
        if args.apply:
            if override:
                apply_override(row, override)
            else:
                clear_stale_target(row, reason)
            counts["applied_rows"] += 1

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "old_target_number", "new_target_number", "definition", "witness_line", "reason"],
    )
    if args.apply and proposals:
        write_rows(args.data, rows)
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
