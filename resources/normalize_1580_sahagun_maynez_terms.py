#!/usr/bin/env python3
"""Normalize safe visible Nahuatl term spelling in 1580 Sahagun/Maynez.

This is a source-specific continuation of the sentence-source plan. It keeps
the original public commentary in a raw-preserved field before changing display
commentary. The automatic rewrites are deliberately narrow and limited to
bolded Nahuatl term/example spans. Other old-spelling patterns are written to
review TSV for source-specific decisions.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


DATA_PATH = Path("data/data.jsonl.gz")
PROPOSALS_PATH = Path("resources/sahagun_maynez_term_normalization_proposals.tsv")
REVIEW_PATH = Path("resources/sahagun_maynez_term_normalization_review.tsv")
SUMMARY_PATH = Path("resources/sahagun_maynez_term_normalization_summary.json")
SOURCE = "1580 Sahagún/Máynez"
RAW_FIELD = "Comentario_raw_1580_sahagun_maynez"
CEDILLA_MARKER = "visible_bold_nahuatl_cedilla_to_z_2026_06_29"
QU_MARKER = "visible_bold_nahuatl_qu_before_ao_to_cu_2026_06_29"
EDITADO_ALIGNED_MARKER = "visible_bold_nahuatl_editado_aligned_oldspell_2026_06_29"
SPAN_EDITADO_ALIGNED_MARKER = "visible_bold_nahuatl_span_editado_aligned_oldspell_2026_06_29"
SOURCE_TERM_MAP_MARKER = "visible_bold_nahuatl_1580_source_term_map_2026_06_29"
VISIBLE_SOURCE_TERM_MAP_MARKER = "visible_nahuatl_1580_source_term_map_2026_06_29"
DUPLICATE_VARIANT_MARKER = "visible_bold_nahuatl_1580_duplicate_variant_collapse_2026_06_29"
SOURCE_LEXICON_ALIGNED_MARKER = "visible_bold_nahuatl_1580_source_lexicon_aligned_oldspell_2026_06_29"
TRAILING_SPLIT_BOLD_MARKER = "visible_bold_nahuatl_1580_trailing_split_bold_repair_2026_06_29"

COMMENTARY_FIELDS = ["Comentario", "Comentario (es)", "Comentario_wimmer_plus_html"]

BOLD_RE = re.compile(r"(<b\b[^>]*>)(.*?)(</b>)", re.I | re.S)
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
TAG_RE = re.compile(r"<[^>]+>")
BR_RE = re.compile(r"<br\s*/?>", re.I)
TOKEN_CHARS = "A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôÇç\\[\\]"
WORD_RE = re.compile(rf"[{TOKEN_CHARS}]+")
PAREN_VARIANT_LIST_RE = re.compile(r"^\s*(?:\([^()]+\)\s*){2,}$")
QU_BEFORE_AO_RE = re.compile(r"[Qq][Uu](?=[aAoOāĀōŌáÁóÓâÂôÔ])")
OLD_SPELL_SIGNAL_RE = re.compile(
    r"j|ç|q\[|[äëïöüÿâêîô]|(?<![A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô])h[aeioáéíóāēīōâêîô]|"
    r"\bqu[aoāōáóâô]|[aeiouāēīōáéíóúâêîô]v[aeiouāēīōáéíóúâêîô]|\b[vV][aeiouāēīōáéíóúâêîô]",
    re.I,
)
DIACRITIC_TRANS = str.maketrans(
    "ÁÉÍÓÚÜÑáéíóúüñĀĒĪŌāēīōÂÊÎÔâêîôÇç",
    "AEIOUUNaeiouunAEIOaeioAEIOaeioCc",
)
SPANISH_TOKEN_DENY = {
    "vez",
    "veces",
    "vergantines",
    "veinte",
    "nueve",
    "hicieron",
    "hacer",
    "hacen",
    "hizo",
    "vieron",
    "vinieron",
    "viene",
    "vienen",
    "verdadero",
    "vuelta",
}
NAHUATL_TOKEN_HINTS = (
    "tl",
    "tz",
    "hu",
    "auh",
    "quauh",
    "cuauh",
    "tzin",
    "xoch",
    "teo",
    "atl",
    "yotl",
    "pohu",
    "mict",
    "tepec",
    "tlan",
    "quetz",
    "coatl",
    "chih",
    "ch",
    "calli",
    "cu",
    "cui",
    "qui",
    "tocht",
    "cuitl",
    "olli",
    "yollo",
    "ix",
    "qua",
)

RECORD_TERM_REPLACEMENTS: dict[str, dict[str, str]] = {
    "1580-sahagun-maynez:000019": {"capulquauitl": "capolcuahuitl"},
    "1580-sahagun-maynez:000206": {"iquechquauhio": "iquechcuahyo"},
    "1580-sahagun-maynez:000381": {"xoquauhtli": "xocuahuitl"},
    "1580-sahagun-maynez:000401": {"xoxocololujvila": "xoxocoyololhuihuila"},
    "1580-sahagun-maynez:000416": {"yiaqualli": "yacualli"},
    "1580-sahagun-maynez:000434": {"yiequachtli": "yecuachtli"},
    "1580-sahagun-maynez:000459": {"yolloxuchiquavjtl": "yolloxochicuahuitl"},
    "1580-sahagun-maynez:000527": {"ycue": "icue"},
    "1580-sahagun-maynez:000528": {"ycue": "icue"},
    "1580-sahagun-maynez:000762": {"yyesuchitl": "yiexochitl"},
    "1580-sahagun-maynez:000993": {"ytzotecon": "itzontecon"},
    "1580-sahagun-maynez:001019": {"yteupan": "iteopan"},
    "1580-sahagun-maynez:001176": {"macuilcipactli yteupan": "macuilcipactli iteopan", "yteupan": "iteopan"},
    "1580-sahagun-maynez:001177": {"macuilmalinal yteupan": "macuilmalinal iteopan", "yteupan": "iteopan"},
    "1580-sahagun-maynez:001346": {"nappa tecutli yteupan": "nappatecuhtli iteopan"},
    "1580-sahagun-maynez:000489": {"zaquanpanjtl": "zacuampanitl"},
    "1580-sahagun-maynez:000562": {"chichioalquauitl": "chichihualcuahuitl"},
    "1580-sahagun-maynez:000597": {"chicunavj": "chiucnahui"},
    "1580-sahagun-maynez:000614": {"chilnequatulli": "chilnecuatolli"},
    "1580-sahagun-maynez:000639": {"chiqujvites": "chiquihuitl"},
    "1580-sahagun-maynez:000737": {"haacxoatic": "ahaxotic"},
    "1580-sahagun-maynez:000766": {"cozcaquauhxihujt": "cozcacuauhxihuitl"},
    "1580-sahagun-maynez:000772": {"aoacaquauitl": "ahuacacuahuitl"},
    "1580-sahagun-maynez:000841": {"quatimalla": "cuauhtemallan", "quautemala": "cuauhtemallan"},
    "1580-sahagun-maynez:000091": {"tlamjavalli": "tlamiyahualli"},
    "1580-sahagun-maynez:000421": {"yautachcavan": "yaotachcahuan"},
    "1580-sahagun-maynez:000455": {"yiollocoquavitl": "yollococuahuitl"},
    "1580-sahagun-maynez:000774": {"quachichil": "cuachichitl"},
    "1580-sahagun-maynez:000812": {"quauacalco": "cuauhcalco"},
    "1580-sahagun-maynez:000908": {"hecachichinquj": "ehecachichinqui"},
    "1580-sahagun-maynez:000909": {"hecacoa": "ehecacoa", "hecacoatl": "ehecacoatl"},
    "1580-sahagun-maynez:000910": {"hecauitzili": "ehecahuiztilli"},
    "1580-sahagun-maynez:000911": {"hecatempatiltzin": "ehecatempatitzin"},
    "1580-sahagun-maynez:000912": {"hecatl": "ehecatl"},
    "1580-sahagun-maynez:000913": {"hecatl": "ehecatl"},
    "1580-sahagun-maynez:000914": {"hecatototl": "ehecatototl"},
    "1580-sahagun-maynez:000948": {"hauauhtzin": "huahuauhtzin"},
    "1580-sahagun-maynez:000962": {
        "oauhqujltamalqualiztli": "huauhquiltamalcualiztli",
        "ouauhqujltamalqualiztli": "huauhquiltamalcualiztli",
    },
    "1580-sahagun-maynez:000964": {"hoauhtli": "huauhtli"},
    "1580-sahagun-maynez:000973": {"vevetes": "huehuetl"},
    "1580-sahagun-maynez:001026": {"vitzitzimjchi": "huitzitzilmichi"},
    "1580-sahagun-maynez:001027": {"vitzitzilocosuchitl": "huitzitzilocoxochitl"},
    "1580-sahagun-maynez:001031": {
        "uitznaoa": "huitznahuac",
        "uitznaoac": "huitznahuac",
        "vitznaoac": "huitznahuac",
        "uitnaoac": "huitznahuac",
    },
    "1580-sahagun-maynez:001044": {"vitzteculsuchitl": "huitztecolxochitl"},
    "1580-sahagun-maynez:001007": {"viloc": "huiloc"},
    "1580-sahagun-maynez:001056": {"amacapulquauitl": "amacapolcuahuitl"},
    "1580-sahagun-maynez:001067": {"ychpuchtiachcauh": "ichpochtiachcauh"},
    "1580-sahagun-maynez:001076": {"ycpales": "icpales"},
    "1580-sahagun-maynez:001088": {"yhujtitemuc": "ihuitl temoc"},
    "1580-sahagun-maynez:001115": {
        "ytzcujnpatli": "itzcuimpatli",
        "itzcujnpatli": "itzcuimpatli",
    },
    "1580-sahagun-maynez:001116": {
        "itzcujn quanj": "itzcuincuani",
        "itzcujn quani": "itzcuincuani",
        "izcujn": "itzcuin",
        "quanj": "cuani",
    },
    "1580-sahagun-maynez:001120": {"ytzmjqlitl": "itzmiquilitl"},
    "1580-sahagun-maynez:001138": {"yxnestlacujlolli": "ixnextlacuilolli"},
    "1580-sahagun-maynez:001140": {"yxocujllooaliztli": "ixocuillohualiztli"},
    "1580-sahagun-maynez:001144": {
        "yzqujxochitl": "ixquixochitl",
        "izqujxuchitl": "ixquixochitl",
    },
    "1580-sahagun-maynez:001149": {"yxyayaoal": "ixyayahual"},
    "1580-sahagun-maynez:001150": {"ycacayo": "iyacayo"},
    "1580-sahagun-maynez:001152": {"yzoatlan": "izhuatlan"},
    "1580-sahagun-maynez:001166": {"yztlacamjscoa tlaylocatl": "iztacamixcoatlailotlacac"},
    "1580-sahagun-maynez:001132": {"ytzonquaujtl": "itztoncuahuitl"},
    "1580-sahagun-maynez:001136": {"campavee": "campahue"},
    "1580-sahagun-maynez:001296": {"mjzquj quavitl": "mizquicuahuitl"},
    "1580-sahagun-maynez:001264": {"mjchvauhtli": "michyauhtli"},
    "1580-sahagun-maynez:001636": {"qujnvevechoa": "quinhuehuechihua"},
    "1580-sahagun-maynez:001727": {"tequaloia": "tecualoyan"},
    "1580-sahagun-maynez:001819": {"teuqualo": "teocualo"},
    "1580-sahagun-maynez:001820": {"teuquaque": "teocuaque"},
    "1580-sahagun-maynez:001821": {"teuquauhquetzaliztli": "teocuauhquetzaliztli"},
    "1580-sahagun-maynez:001822": {"teuquauhxochitl": "teocuauhxochitl"},
    "1580-sahagun-maynez:001825": {"yxqua": "ixcua"},
    "1580-sahagun-maynez:001831": {"teuvauhqujlitl": "teohuauhquilitl"},
    "1580-sahagun-maynez:001832": {"teuvaxin": "teohuaxin"},
    "1580-sahagun-maynez:001907": {"tepupuxaquaujque": "tepopoxacuahuique"},
    "1580-sahagun-maynez:001939": {
        "cacaoaquavitl": "cacahuacuahuitl",
        "cacaoquavitl": "cacahuacuahuitl",
    },
    "1580-sahagun-maynez:002034": {"tlaamaviques": "tlaamahuique"},
    "1580-sahagun-maynez:001440": {"vllac": "olac"},
    "1580-sahagun-maynez:002042": {"tlancavilotl": "tlacahuilotl"},
    "1580-sahagun-maynez:002043": {"tlacaloazquavitl": "tlacalhuazcuahuitl"},
    "1580-sahagun-maynez:002107": {"tlacujlolquavitl": "tlacuilocuahuitl"},
    "1580-sahagun-maynez:002103": {"tlaquauac": "tlacuac"},
    "1580-sahagun-maynez:002104": {"tlaquatzin": "tlacuatzin"},
    "1580-sahagun-maynez:002105": {"itlaquaian": "itlacuayan"},
    "1580-sahagun-maynez:002140": {"tlachiquatli": "tlalchicuatli"},
    "1580-sahagun-maynez:002170": {"ypap": "ipapa"},
    "1580-sahagun-maynez:002189": {"yzqujsuchitl": "izquixochitl"},
    "1580-sahagun-maynez:002180": {"tlanquacemjlhujme": "tlancuacemilhuitime"},
    "1580-sahagun-maynez:002198": {"campavee": "campahue"},
    "1580-sahagun-maynez:002201": {
        "tlappanecatl hecatl": "tlappanecatl ecatzin",
        "hecatl": "ecatzin",
    },
    "1580-sahagun-maynez:000371": {"coioacâ": "coyoacan"},
    "1580-sahagun-maynez:001459": {
        "âtlacatl": "ātlacatl",
        "cetlâcatl": "cētlācatl",
        "tlâcatl": "tlācatl",
    },
    "1580-sahagun-maynez:002056": {
        "âtlacatl": "ātlacatl",
        "cetlâcatl": "cētlācatl",
        "tlâcatl": "tlācatl",
        "umetlâcatl": "umetlācatl",
    },
    "1580-sahagun-maynez:002092": {"tlaxôtlan": "tlaxotlan"},
}

REVIEWED_J_I_RECORD_TERM_REPLACEMENTS: dict[str, dict[str, str]] = {
    "1580-sahagun-maynez:000027": {
        "tlatlauje": "tlatlauhqui",
        "tezcatlipuca": "tezcatlipoca",
    },
    "1580-sahagun-maynez:000100": {"tochmjtl": "tochomitl"},
    "1580-sahagun-maynez:000107": {"tucujchtlamatzoalli": "tocuichtamaltzohualli"},
    "1580-sahagun-maynez:000188": {"totomjchi": "totomichin"},
    "1580-sahagun-maynez:000231": {"tzayanaqujlitl": "tzayanalquilitl"},
    "1580-sahagun-maynez:000241": {"tziuequjlitl": "tzihuinquilitl"},
    "1580-sahagun-maynez:000253": {"tzitzimjtles": "tzitzimime"},
    "1580-sahagun-maynez:000258": {
        "tzooacalli": "tzoacalli",
        "tlayoalonj": "tlayohualoni",
    },
    "1580-sahagun-maynez:000264": {"tzonpachqujlitl": "tzompachquilitl"},
    "1580-sahagun-maynez:000299": {"xicara": "jícara", "xicaras": "jícaras"},
    "1580-sahagun-maynez:000352": {
        "sochmjlco": "xochimilco",
        "xochmjlco": "xochimilco",
        "xuchmjlco": "xochimilco",
    },
    "1580-sahagun-maynez:000353": {"xuchmjtl": "xochimitl"},
    "1580-sahagun-maynez:000382": {"xucujchtamaltzoalli": "xocuichtamaltzohualli"},
    "1580-sahagun-maynez:000460": {"yolloxochiqujtl": "yolloxochiquilitl"},
    "1580-sahagun-maynez:000518": {
        "chachiujtes": "chalchihuites",
        "chalchiujtes": "chalchihuites",
    },
    "1580-sahagun-maynez:000603": {"chicunamjctla": "chiucnamictlan"},
    "1580-sahagun-maynez:000639": {"chiqujujtes": "chiquihuites"},
    "1580-sahagun-maynez:000645": {"acujtlacpalli": "acuitlapalli"},
    "1580-sahagun-maynez:000785": {"acacujatl": "acacueyatl"},
    "1580-sahagun-maynez:000822": {
        "cuauheloqujltic": "cuauheloquilitic",
        "cuauheloqujlitic": "cuauheloquilitic",
    },
    "1580-sahagun-maynez:000863": {"cuaujtzqujlitl": "cuauhhuitzquilitl"},
    "1580-sahagun-maynez:000875": {"cujtlachtli": "cuetlachtli"},
    "1580-sahagun-maynez:000883": {"cujatl": "cueyatl"},
    "1580-sahagun-maynez:000890": {"cujtla axcatl": "cuitlaazcatl"},
    "1580-sahagun-maynez:000902": {"cujtlazaoli": "cuitlazayolli"},
    "1580-sahagun-maynez:000963": {
        "oauhqujltamales": "huauhquiltamales",
        "oauhqujtamalli": "huauhquiltamalli",
    },
    "1580-sahagun-maynez:001118": {"itzcujn": "itzcuin"},
    "1580-sahagun-maynez:001179": {"macujl": "macuil", "ocelutl": "ocelotl"},
    "1580-sahagun-maynez:001180": {"macujl": "macuil", "uctli": "octli"},
    "1580-sahagun-maynez:001256": {"mjchi": "michin"},
    "1580-sahagun-maynez:001257": {"mjchpictli": "michpictli"},
    "1580-sahagun-maynez:001260": {"mjchtlacectli": "michtlacecetli"},
    "1580-sahagun-maynez:001297": {"mjzqujqujlitl": "mizquiquilitl"},
    "1580-sahagun-maynez:001298": {
        "mjzquite": "mizquite",
        "mjzqujtes": "mizquites",
    },
    "1580-sahagun-maynez:001310": {
        "moqujuixtzin": "moquihuixtzin",
        "moqujuix": "moquihuixtli",
    },
    "1580-sahagun-maynez:001357": {"necujlictli": "necuiloctli"},
    "1580-sahagun-maynez:001359": {"necutlatotonjlli": "neuctlatotonilli"},
    "1580-sahagun-maynez:001373": {"netecujtotilo": "netecuitotilo"},
    "1580-sahagun-maynez:001384": {"nextecujli": "nextecuilin"},
    "1580-sahagun-maynez:001416": {"ocelomjchi": "ocelomichin"},
    "1580-sahagun-maynez:001479": {"atlacujoaia": "atlacuihuayan"},
    "1580-sahagun-maynez:001597": {"quetzalhujtzili": "quetzalhuitztli"},
    "1580-sahagun-maynez:001628": {
        "qujmjchin": "quimichin",
        "qujmjchti": "quimichti",
    },
    "1580-sahagun-maynez:001740": {"tecutlacozauhquj": "teuctlacozauhqui"},
    "1580-sahagun-maynez:001750": {"teuetzqujti": "tehuitzquiti"},
    "1580-sahagun-maynez:001805": {
        "aioxochqujlitl": "ayoxochiquilitl",
        "ayoxochqujltic": "ayoxochiquilitic",
    },
    "1580-sahagun-maynez:001810": {"mjchi": "michin"},
    "1580-sahagun-maynez:001814": {"teucalhujacan": "teocalhuican"},
    "1580-sahagun-maynez:001917": {
        "tequjsqtl": "tequixquitl",
        "tequisqujtl": "tequixquitl",
        "tequjxqujte": "tequixquite",
    },
    "1580-sahagun-maynez:001956": {"tetzauhqujmjchtin": "tetzauhquimichtin"},
    "1580-sahagun-maynez:002145": {"calqujmichti": "calquimichtin"},
    "1580-sahagun-maynez:002161": {"tlaltecujn": "tlaltetecuin"},
    "1580-sahagun-maynez:002172": {"tlamacaztequjoaque": "tlamacaztequiyohuaque"},
    "1580-sahagun-maynez:000085": {"calquj": "calqui"},
    "1580-sahagun-maynez:000311": {"jilotes": "xilotes"},
    "1580-sahagun-maynez:000384": {"xoujles": "xohuiles"},
    "1580-sahagun-maynez:000422": {"iautequjoaque": "yaotequihuaque"},
    "1580-sahagun-maynez:000432": {"yautequjua": "yaotequihua"},
    "1580-sahagun-maynez:000480": {
        "zacapan qujxoa": "zacapan quixhua",
        "qujxoa": "quixhua",
    },
    "1580-sahagun-maynez:000705": {
        "coalxoxouhquj": "coaxoxoqui",
        "coatl xoxouhquj": "coatl xoxoqui",
        "coaxoxouhquj": "coaxoxoqui",
        "xoxouhquj": "xoxoqui",
    },
    "1580-sahagun-maynez:000923": {
        "eeloqujltic": "eeloquilitic",
        "eheloqujltic": "eheloquilitic",
    },
    "1580-sahagun-maynez:001248": {"mjiaoatamalli": "miahuatamalli"},
    "1580-sahagun-maynez:001283": {"mjqujz": "miquiz"},
    "1580-sahagun-maynez:001292": {"mjiaoatamalli": "miyahuatamalli"},
    "1580-sahagun-maynez:001300": {
        "mociaoquezque": "mocihuaquetzque",
        "mocioaquezque": "mocihuaquetzque",
        "mocioaquezquj": "mocihuaquetzque",
    },
    "1580-sahagun-maynez:001582": {"quequexquj": "quequexqui"},
    "1580-sahagun-maynez:001694": {"tecoanjme": "tecohuanime"},
    "1580-sahagun-maynez:001773": {"tenjsio": "tenizyo"},
    "1580-sahagun-maynez:001783": {"temjlo": "temilo"},
    "1580-sahagun-maynez:001801": {"tenjsio": "tenizyo"},
    "1580-sahagun-maynez:001814": {"teucalujacan": "teocalhuican"},
    "1580-sahagun-maynez:001842": {"teunenemj": "teonenemi"},
    "1580-sahagun-maynez:001912": {"tequjoa": "tequihua"},
    "1580-sahagun-maynez:001914": {"tequjoaque": "tequihuaque"},
    "1580-sahagun-maynez:001919": {"tequjzqujyac": "tequixquiyac"},
    "1580-sahagun-maynez:001985": {"teiaoalouanj": "teyahualohuani"},
    "1580-sahagun-maynez:002014": {"tianqujz": "tianquiz"},
    "1580-sahagun-maynez:002027": {"tizaapanquj": "tizapanqui"},
    "1580-sahagun-maynez:001279": {"mjl tomate": "mil tomate"},
    "1580-sahagun-maynez:001451": {"omacoxonj": "omacoxoni"},
    "1580-sahagun-maynez:001487": {
        "otomjes": "otomies",
        "otomjn": "otomin",
    },
    "1580-sahagun-maynez:001519": {"petaqujllas": "petaquillas"},
    "1580-sahagun-maynez:001660": {"tamjme": "tamime"},
    "1580-sahagun-maynez:001882": {"tepeaqujlla": "tepeaquilla"},
    "1580-sahagun-maynez:001976": {"texinjto": "texinito"},
}

for record_id, replacements in REVIEWED_J_I_RECORD_TERM_REPLACEMENTS.items():
    RECORD_TERM_REPLACEMENTS.setdefault(record_id, {}).update(replacements)

RECORD_TRAILING_SPLIT_BOLD_REPLACEMENTS: dict[str, dict[tuple[str, str], str]] = {
    "1580-sahagun-maynez:000517": {("chalcacujcat", "l"): "chalcacuicatl"},
    "1580-sahagun-maynez:000745": {("cototzauqujxiujt", "l"): "cototzauhqui xihuitl"},
    "1580-sahagun-maynez:000893": {("cujtlacochtotot", "l"): "cuitlacochtototl"},
    "1580-sahagun-maynez:001391": {("aqujmchi", "n"): "aquimichin"},
}

REVIEW_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "q_bracket",
        re.compile(r"\b\w*q\[[^\]]+\]\w*", re.I),
        "review bracketed q expansion",
    ),
    (
        "qu_before_a_o",
        re.compile(r"\bqu[aoāōáóâô][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô\[\]]*", re.I),
        "review qu before a/o, usually cu in normalized Nahuatl",
    ),
    (
        "v_likely_u",
        re.compile(
            r"\b[vV][aeiouāēīōáéíóúâêîô]\w*|"
            r"\w*[aeiouāēīōáéíóúâêîô][vV][aeiouāēīōáéíóúâêîô]\w*|"
            r"\bq[vV]\w*"
        ),
        "review v/u historical spelling",
    ),
    (
        "initial_h_before_aeio",
        re.compile(
            r"(?<![A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô])h[aeioáéíóāēīōâêîô]"
            r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô\[\]]*",
            re.I,
        ),
        "review initial h before a/e/i/o",
    ),
    (
        "circumflex",
        re.compile(r"\b[\wâêîôÂÊÎÔ]*[âêîôÂÊÎÔ][\wâêîôÂÊÎÔ]*\b"),
        "review circumflex source convention",
    ),
    (
        "diaeresis",
        re.compile(r"\b[\wäëïöüÄËÏÖÜÿŸ]*[äëïöüÄËÏÖÜÿŸ][\wäëïöüÄËÏÖÜÿŸ]*\b"),
        "review diaeresis source convention",
    ),
    (
        "initial_y_before_consonant",
        re.compile(r"\by[bcdfghjklmnpqrstvwxyzç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîôç]*", re.I),
        "review old initial y used for i before consonant",
    ),
    (
        "j_i",
        re.compile(r"\b\w*j\w*", re.I),
        "review j used as old-spelling i",
    ),
]


def clean_html(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = BR_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_context(value: str, token: str, width: int = 120) -> str:
    text = clean_html(value)
    index = text.lower().find(token.lower())
    if index < 0:
        return text[: width * 2].strip()
    left = max(0, index - width)
    right = min(len(text), index + len(token) + width)
    return text[left:right].strip()


def append_marker(value: object, marker: str) -> str:
    parts = [part for part in str(value or "").split(";") if part]
    if marker not in parts:
        parts.append(marker)
    return ";".join(parts)


def token_key(token: str) -> str:
    return token.translate(DIACRITIC_TRANS).lower().replace("[", "").replace("]", "")


def editado_alignment_key(value: str) -> str:
    key = token_key(clean_html(value))
    key = re.sub(r"qu(?=[ao])", "cu", key)
    key = key.replace("j", "i").replace("y", "i")
    key = key.replace("v", "u")
    key = key.replace("h", "")
    return re.sub(r"[^a-z]", "", key)


def editado_loose_alignment_key(value: str) -> str:
    key = editado_alignment_key(value)
    key = re.sub(r"i{2,}", "i", key)
    key = re.sub(r"([bcdfghjklmnpqrstvwxyz])\1+", r"\1", key)
    return key


def source_variant_alignment_key(value: str) -> str:
    key = editado_alignment_key(value)
    key = key.replace("z", "x").replace("s", "x")
    key = key.replace("u", "o").replace("q", "c")
    key = re.sub(r"i{2,}", "i", key)
    key = re.sub(r"([bcdfghjklmnpqrstvwxyz])\1+", r"\1", key)
    return key


def looks_nahuatl_token(token: str) -> bool:
    key = token_key(token)
    if len(key) < 3 or key in {item.translate(DIACRITIC_TRANS).lower() for item in SPANISH_TOKEN_DENY}:
        return False
    return any(hint in key for hint in NAHUATL_TOKEN_HINTS)


def normalize_cedilla_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            new = old.replace("ç", "z").replace("Ç", "Z")
            if old != new:
                changes.append((old, new))
            return new

        return re.sub(
            r"[A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô]*[Çç][A-Za-zÁÉÍÓÚáéíóúĀĒĪŌāēīōÂÊÎÔâêîô]*",
            repl,
            piece,
        )

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_cedilla(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_cedilla_in_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def qu_to_cu(token: str) -> str:
    def repl(match: re.Match[str]) -> str:
        old = match.group(0)
        if old == "QU":
            return "CU"
        if old == "Qu":
            return "Cu"
        return "cu"

    return QU_BEFORE_AO_RE.sub(repl, token)


def normalize_qu_before_ao_in_text(value: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            if "v" in old.lower() or not QU_BEFORE_AO_RE.search(old) or not looks_nahuatl_token(old):
                return old
            new = qu_to_cu(old)
            if old != new:
                changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_qu_before_ao(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_qu_before_ao_in_text(match.group(2))
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def apply_case_pattern(old: str, new: str) -> str:
    if old.isupper():
        return new.upper()
    if old[:1].isupper():
        return new[:1].upper() + new[1:]
    return new


def editado_display(row: dict) -> str:
    return clean_html(row.get("Editado", "")).strip().rstrip("*").strip()


def source_term_pattern(replacements: dict[str, str]) -> re.Pattern[str] | None:
    if not replacements:
        return None
    alternatives = sorted((re.escape(term) for term in replacements), key=len, reverse=True)
    return re.compile(rf"(?<![{TOKEN_CHARS}])({'|'.join(alternatives)})(?![{TOKEN_CHARS}])", re.I)


def normalize_known_source_terms_in_text(
    value: str, replacements: dict[str, str]
) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    pattern = source_term_pattern(replacements)
    if not pattern:
        return value, changes

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(1)
            replacement = replacements.get(old.lower())
            if not replacement:
                return old
            new = apply_case_pattern(old, replacement)
            if old != new:
                changes.append((old, new))
            return new

        return pattern.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_known_source_terms(value: object, row: dict) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    replacements = RECORD_TERM_REPLACEMENTS.get(str(row.get("record_id", "")), {})
    all_changes: list[tuple[str, str]] = []
    if not replacements:
        return text, all_changes

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_known_source_terms_in_text(match.group(2), replacements)
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_trailing_split_bold_terms(value: object, row: dict) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    replacements = RECORD_TRAILING_SPLIT_BOLD_REPLACEMENTS.get(str(row.get("record_id", "")), {})
    changes: list[tuple[str, str]] = []
    if not replacements:
        return text, changes

    new_text = text
    for (stem, trailing), replacement in replacements.items():
        pattern = re.compile(
            rf"(?<![{TOKEN_CHARS}])({re.escape(stem)})(</b>)(\s*){re.escape(trailing)}(?![{TOKEN_CHARS}])",
            re.I,
        )

        def repl(match: re.Match[str]) -> str:
            old = f"{match.group(1)}{match.group(3)}{trailing}"
            new = apply_case_pattern(match.group(1), replacement)
            changes.append((old, new))
            return f"{new}{match.group(2)}"

        new_text = pattern.sub(repl, new_text)
    return new_text, changes


def collapse_duplicate_parenthetical_variants(inner: str) -> str:
    if not PAREN_VARIANT_LIST_RE.fullmatch(inner):
        return inner
    variants = re.findall(r"\(([^()]+)\)", inner)
    kept: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        key = re.sub(r"\s+", " ", variant).strip().casefold()
        if key in seen:
            continue
        seen.add(key)
        kept.append(variant.strip())
    if len(kept) == len(variants):
        return inner
    return " ".join(f"({variant})" for variant in kept)


def normalize_bold_duplicate_parenthetical_variants(value: object) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        old_inner = match.group(2)
        new_inner = collapse_duplicate_parenthetical_variants(old_inner)
        if new_inner != old_inner:
            all_changes.append((old_inner, new_inner))
        return f"{match.group(1)}{new_inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def editado_candidate_map(row: dict) -> dict[str, str]:
    editado = clean_html(row.get("Editado", ""))
    if not editado:
        return {}
    tokens = WORD_RE.findall(editado)
    candidates: list[str] = []
    if len(tokens) > 1:
        candidates.append(" ".join(tokens))
    candidates.extend(tokens)

    out: dict[str, str] = {}
    for candidate in candidates:
        for key in (editado_alignment_key(candidate), editado_loose_alignment_key(candidate)):
            if len(key) >= 3 and key not in out:
                out[key] = candidate
    return out


def source_variant_candidates_from_editado(value: object) -> list[str]:
    editado = clean_html(value).strip().rstrip("*").strip()
    if not editado:
        return []
    tokens = WORD_RE.findall(editado)
    candidates: list[str] = []
    if len(tokens) > 1:
        candidates.append(" ".join(tokens))
    candidates.extend(tokens)
    return candidates


def unique_source_variant_map(candidates: list[str]) -> dict[str, str]:
    by_key: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        key = source_variant_alignment_key(candidate)
        if len(key) >= 3 and candidate not in by_key[key]:
            by_key[key].append(candidate)
    return {key: values[0] for key, values in by_key.items() if len({value.casefold() for value in values}) == 1}


def source_lexicon_candidate_map(rows: list[dict]) -> dict[str, str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        for candidate in source_variant_candidates_from_editado(row.get("Editado", "")):
            candidate_key = candidate.casefold()
            if candidate_key in seen:
                continue
            seen.add(candidate_key)
            candidates.append(candidate)
    return unique_source_variant_map(candidates)


def row_source_variant_candidate_map(row: dict) -> dict[str, str]:
    return unique_source_variant_map(source_variant_candidates_from_editado(row.get("Editado", "")))


def normalize_editado_aligned_in_text(value: str, candidates: dict[str, str]) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    if not candidates:
        return value, changes

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            key = editado_alignment_key(old)
            candidate = candidates.get(key) or candidates.get(editado_loose_alignment_key(old))
            if not candidate:
                return old
            new = apply_case_pattern(old, candidate)
            if token_key(old) == token_key(new):
                return old
            changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_editado_aligned(value: object, row: dict) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []
    candidates = editado_candidate_map(row)

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_editado_aligned_in_text(match.group(2), candidates)
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def normalize_source_lexicon_aligned_in_text(
    value: str, row_candidates: dict[str, str], source_candidates: dict[str, str]
) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def replace_piece(piece: str) -> str:
        def repl(match: re.Match[str]) -> str:
            old = match.group(0)
            if not OLD_SPELL_SIGNAL_RE.search(old) or not looks_nahuatl_token(old):
                return old
            key = source_variant_alignment_key(old)
            candidate = row_candidates.get(key) or source_candidates.get(key)
            if not candidate:
                return old
            new = apply_case_pattern(old, candidate)
            if token_key(old) == token_key(new):
                return old
            changes.append((old, new))
            return new

        return WORD_RE.sub(repl, piece)

    parts = TAG_SPLIT_RE.split(value)
    normalized = "".join(part if TAG_RE.fullmatch(part or "") else replace_piece(part) for part in parts)
    return normalized, changes


def normalize_bold_source_lexicon_aligned(
    value: object, row: dict, source_candidates: dict[str, str]
) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    all_changes: list[tuple[str, str]] = []
    row_candidates = row_source_variant_candidate_map(row)

    def repl(match: re.Match[str]) -> str:
        inner, changes = normalize_source_lexicon_aligned_in_text(match.group(2), row_candidates, source_candidates)
        all_changes.extend(changes)
        return f"{match.group(1)}{inner}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def split_single_bold_span(inner: str) -> tuple[str, str, str] | None:
    if TAG_RE.search(inner):
        return None
    leading = re.match(r"^\s*", inner).group(0)
    trailing = re.search(r"\s*$", inner).group(0)
    core = inner[len(leading) : len(inner) - len(trailing)]
    prefix = leading
    suffix = trailing

    if core.startswith("(") or core.endswith(")"):
        if not (core.startswith("(") and core.endswith(")") and core.count("(") == 1 and core.count(")") == 1):
            return None
        prefix += "("
        suffix = ")" + suffix
        core = core[1:-1].strip()

    trailing_marks = ""
    while core and core[-1] in ".,:;":
        trailing_marks = core[-1] + trailing_marks
        core = core[:-1].strip()
    suffix = trailing_marks + suffix
    if not core:
        return None
    return prefix, core, suffix


def normalize_bold_span_editado_aligned(value: object, row: dict) -> tuple[str, list[tuple[str, str]]]:
    text = str(value or "")
    target = editado_display(row)
    target_key = editado_alignment_key(target)
    if len(target_key) < 4:
        return text, []
    all_changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        parsed = split_single_bold_span(match.group(2))
        if not parsed:
            return match.group(0)
        prefix, core, suffix = parsed
        if not OLD_SPELL_SIGNAL_RE.search(core):
            return match.group(0)
        if editado_alignment_key(core) != target_key:
            return match.group(0)
        new_core = apply_case_pattern(core, target)
        if core == new_core:
            return match.group(0)
        all_changes.append((core, new_core))
        return f"{match.group(1)}{prefix}{new_core}{suffix}{match.group(3)}"

    return BOLD_RE.sub(repl, text), all_changes


def bold_texts(value: object) -> list[str]:
    return [clean_html(match.group(2)) for match in BOLD_RE.finditer(str(value or ""))]


def review_candidates(row: dict) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for field in COMMENTARY_FIELDS:
        value = row.get(field, "")
        if not isinstance(value, str) or not value:
            continue
        for bold in bold_texts(value):
            for kind, pattern, note in REVIEW_PATTERNS:
                for match in pattern.finditer(bold):
                    token = match.group(0)
                    if "ç" in token or "Ç" in token:
                        continue
                    if not looks_nahuatl_token(token):
                        continue
                    key = (field, kind, token)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(
                        {
                            "record_id": row.get("record_id", ""),
                            "original": row.get("Original", ""),
                            "editado": row.get("Editado", ""),
                            "field": field,
                            "candidate_kind": kind,
                            "token": token,
                            "note": note,
                            "bold_text": bold,
                            "context": token_context(value, token),
                        }
                    )
    return out


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
    parser.add_argument("--review", type=Path, default=REVIEW_PATH)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    args = parser.parse_args()

    rows = load_rows(args.data)
    source_candidates = source_lexicon_candidate_map(rows)
    proposals: list[dict[str, str]] = []
    review: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for row in rows:
        if row.get("Fuente") != SOURCE:
            continue
        counts["source_rows"] += 1
        if args.apply and RAW_FIELD not in row:
            row[RAW_FIELD] = row.get("Comentario", "")
            counts["raw_preserved_rows"] += 1
        row_changes: list[tuple[str, str, str, str]] = []

        for field in COMMENTARY_FIELDS:
            value = row.get(field, "")
            if not isinstance(value, str) or not value:
                continue
            new_value, visible_source_term_changes = normalize_known_source_terms_in_text(
                value, RECORD_TERM_REPLACEMENTS.get(str(row.get("record_id", "")), {})
            )
            new_value, source_term_changes = normalize_bold_known_source_terms(new_value, row)
            new_value, trailing_split_changes = normalize_trailing_split_bold_terms(new_value, row)
            new_value, cedilla_changes = normalize_bold_cedilla(new_value)
            new_value, qu_changes = normalize_bold_qu_before_ao(new_value)
            new_value, span_editado_aligned_changes = normalize_bold_span_editado_aligned(new_value, row)
            new_value, editado_aligned_changes = normalize_bold_editado_aligned(new_value, row)
            new_value, source_lexicon_aligned_changes = normalize_bold_source_lexicon_aligned(
                new_value, row, source_candidates
            )
            new_value, duplicate_variant_changes = normalize_bold_duplicate_parenthetical_variants(new_value)
            if new_value == value:
                continue
            for old, new in visible_source_term_changes:
                row_changes.append((field, VISIBLE_SOURCE_TERM_MAP_MARKER, old, new))
            for old, new in source_term_changes:
                row_changes.append((field, SOURCE_TERM_MAP_MARKER, old, new))
            for old, new in trailing_split_changes:
                row_changes.append((field, TRAILING_SPLIT_BOLD_MARKER, old, new))
            for old, new in cedilla_changes:
                row_changes.append((field, CEDILLA_MARKER, old, new))
            for old, new in qu_changes:
                row_changes.append((field, QU_MARKER, old, new))
            for old, new in span_editado_aligned_changes:
                row_changes.append((field, SPAN_EDITADO_ALIGNED_MARKER, old, new))
            for old, new in editado_aligned_changes:
                row_changes.append((field, EDITADO_ALIGNED_MARKER, old, new))
            for old, new in source_lexicon_aligned_changes:
                row_changes.append((field, SOURCE_LEXICON_ALIGNED_MARKER, old, new))
            for old, new in duplicate_variant_changes:
                row_changes.append((field, DUPLICATE_VARIANT_MARKER, old, new))
            if args.apply:
                row[field] = new_value

        if row_changes:
            counts["proposal_rows"] += 1
            counts["proposal_changes"] += len(row_changes)
            counts["proposal_changes_source_term_map"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
            )
            counts["proposal_changes_visible_source_term_map"] += sum(
                1 for _, marker, _, _ in row_changes if marker == VISIBLE_SOURCE_TERM_MAP_MARKER
            )
            counts["proposal_changes_trailing_split_bold"] += sum(
                1 for _, marker, _, _ in row_changes if marker == TRAILING_SPLIT_BOLD_MARKER
            )
            counts["proposal_changes_cedilla"] += sum(1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER)
            counts["proposal_changes_qu_before_ao"] += sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER)
            counts["proposal_changes_editado_aligned"] += sum(
                1 for _, marker, _, _ in row_changes if marker == EDITADO_ALIGNED_MARKER
            )
            counts["proposal_changes_span_editado_aligned"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SPAN_EDITADO_ALIGNED_MARKER
            )
            counts["proposal_changes_source_lexicon_aligned"] += sum(
                1 for _, marker, _, _ in row_changes if marker == SOURCE_LEXICON_ALIGNED_MARKER
            )
            counts["proposal_changes_duplicate_variant_collapse"] += sum(
                1 for _, marker, _, _ in row_changes if marker == DUPLICATE_VARIANT_MARKER
            )
            old_tokens = []
            new_tokens = []
            change_markers = []
            for field, marker, old, new in row_changes:
                old_tokens.append(f"{field}:{old}")
                new_tokens.append(f"{field}:{new}")
                if marker not in change_markers:
                    change_markers.append(marker)
            proposals.append(
                {
                    "record_id": row.get("record_id", ""),
                    "original": row.get("Original", ""),
                    "editado": row.get("Editado", ""),
                    "markers": ";".join(change_markers),
                    "old_tokens": " | ".join(old_tokens),
                    "new_tokens": " | ".join(new_tokens),
                    "context": token_context(row.get("Comentario", ""), row_changes[0][2]),
                }
            )
            if args.apply:
                for marker in change_markers:
                    row["Comentario_normalizado_version"] = append_marker(row.get("Comentario_normalizado_version"), marker)
                    row["Comentario_display_issues"] = append_marker(row.get("Comentario_display_issues"), marker)
                qa = row.get("Sentence_Source_JSON") if isinstance(row.get("Sentence_Source_JSON"), dict) else {}
                if any(marker == SOURCE_TERM_MAP_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_source_term_map": {
                            "action": "normalized_known_source_old_spellings_to_editado_or_source_variant_forms",
                            "marker": SOURCE_TERM_MAP_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SOURCE_TERM_MAP_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == VISIBLE_SOURCE_TERM_MAP_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_visible_source_term_map": {
                            "action": "normalized_known_source_old_spellings_to_reviewed_forms_in_visible_commentary",
                            "marker": VISIBLE_SOURCE_TERM_MAP_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == VISIBLE_SOURCE_TERM_MAP_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == TRAILING_SPLIT_BOLD_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_trailing_split_bold_repair": {
                            "action": "merged_bold_old_spelling_stem_with_trailing_split_letter",
                            "marker": TRAILING_SPLIT_BOLD_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == TRAILING_SPLIT_BOLD_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == CEDILLA_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_cedilla_to_z": {
                            "action": "normalized_cedilla_to_z_inside_bold_nahuatl_terms",
                            "marker": CEDILLA_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == CEDILLA_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == QU_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_qu_before_ao_to_cu": {
                            "action": "normalized_qu_before_a_o_to_cu_inside_bold_nahuatl_terms",
                            "marker": QU_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(1 for _, marker, _, _ in row_changes if marker == QU_MARKER),
                            "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                        },
                    }
                if any(marker == EDITADO_ALIGNED_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_editado_aligned_oldspell": {
                            "action": "normalized_bold_old_spelling_to_matching_editado_form",
                            "marker": EDITADO_ALIGNED_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == EDITADO_ALIGNED_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(str(row.get(RAW_FIELD, "")).encode("utf-8")).hexdigest(),
                        },
                    }
                if any(marker == SPAN_EDITADO_ALIGNED_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_span_editado_aligned_oldspell": {
                            "action": "normalized_whole_bold_old_spelling_span_to_matching_editado_form",
                            "marker": SPAN_EDITADO_ALIGNED_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SPAN_EDITADO_ALIGNED_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == SOURCE_LEXICON_ALIGNED_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_source_lexicon_aligned_oldspell": {
                            "action": "normalized_bold_old_spelling_to_unique_same_source_editado_or_term_form",
                            "marker": SOURCE_LEXICON_ALIGNED_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == SOURCE_LEXICON_ALIGNED_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                if any(marker == DUPLICATE_VARIANT_MARKER for _, marker, _, _ in row_changes):
                    qa = {
                        **qa,
                        "qa_1580_sahagun_maynez_duplicate_variant_collapse": {
                            "action": "collapsed_duplicate_parenthetical_variants_inside_bold_term_headers",
                            "marker": DUPLICATE_VARIANT_MARKER,
                            "raw_field": RAW_FIELD,
                            "raw_preserved": True,
                            "changed_token_count": sum(
                                1 for _, marker, _, _ in row_changes if marker == DUPLICATE_VARIANT_MARKER
                            ),
                            "previous_commentary_sha1": hashlib.sha1(
                                str(row.get(RAW_FIELD, "")).encode("utf-8")
                            ).hexdigest(),
                        },
                    }
                row["Sentence_Source_JSON"] = qa

        review.extend(review_candidates(row))

    write_tsv(
        args.proposals,
        proposals,
        ["record_id", "original", "editado", "markers", "old_tokens", "new_tokens", "context"],
    )
    write_tsv(
        args.review,
        review,
        ["record_id", "original", "editado", "field", "candidate_kind", "token", "note", "bold_text", "context"],
    )
    args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.apply and proposals:
        write_rows(args.data, rows)
        counts["applied_rows"] = len(proposals)
        args.summary.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"summary {dict(counts)}")
    print(f"proposals {args.proposals}")
    print(f"review {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
