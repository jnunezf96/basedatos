#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_orthography_cluster_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"2021 Wimmer", "1992 Karttunen", "V94 Diccionario Global SNP"}
DUPLICATE_BRACKET_RE = re.compile(rf"\b([{LETTER}]+)\s+\[\1\]", re.I)
SINGLE_BRACKET_LETTER_RE = re.compile(rf"\[([{LETTER}])\]([{LETTER}])")
DOLLAR_S_RE = re.compile(rf"(?<=[{LETTER}])\$(?=[{LETTER}])")

ROW_TRANSLATION_REPLACEMENTS = {
    "1571-molina-1:024470": "reguizcar (arcaico: hacer cosquillas).",
    "1571-molina-1:025356": "reguizcar (arcaico: escarnecer o mofar).",
    "1780-bnf-361:002699": "Desconocer el beneficio recibido",
    "153-trilingue:006290": "Abarraganado varón con hembra.",
    "153-trilingue:006742": "Señas para entenderse.",
    "1571-molina-1:016703": "ensayarse a poner bien la rodela para arrodelarse.",
    "1571-molina-2:014748": "solana, o lugar para calentarse al sol.",
    "1780-bnf-361:018963": "Acostarse a la parte de alguna persona; hacerse del bando contrario; favorecer socorriendo a otro en algún peligro; ayudar a otro haciéndose de su banda; acostarse hacia, o a la parte de alguna persona",
    "1780-bnf-361:015310": "Acostado, o entortado madero o pared; cosa no derecha como asa de jarro; encorvado, por encorvarse.",
    "1780-bnf-361:025728": "Estimar, tasar o apreciar.",
    "153-trilingue:008020": "Colchón o colcedra (arcaico: colchón) de cama.",
    "1765-cortes-y-zedeno:004451": "Colchón, o colcedra (arcaico: colchón) de cama",
}


PHRASE_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\biesu\s+christo\b", re.I), "Jesucristo", "old_i_j_phrase"),
    (re.compile(r"\b[ijy]ugo\s+para\s+vñir\b", re.I), "yugo para uncir", "old_initial_v_phrase"),
    (re.compile(r"\buna\s+abe\b", re.I), "un ave", "old_b_v_phrase"),
    (re.compile(r"\bque\s+ba\s+rresonando\b", re.I), "que va resonando", "old_b_v_phrase"),
    (re.compile(r"\ba\s+las\s+mill\s+marabillas\b", re.I), "a las mil maravillas", "old_b_v_phrase"),
    (re.compile(r"\bsueño\s+bano\b", re.I), "sueño vano", "old_b_v_phrase"),
    (re.compile(r"\bhablador\s+bano\b", re.I), "hablador vano", "old_b_v_phrase"),
    (re.compile(r"\bbano,\s+el\s+acto\s+de\s+bañarse\b", re.I), "baño, el acto de bañarse", "old_b_v_phrase"),
    (re.compile(r"\ben\s+bano\b", re.I), "en vano", "old_b_v_phrase"),
    (re.compile(r"\bbautizar\s+o\s+baptizar\b", re.I), "bautizar", "old_b_v_phrase"),
    (re.compile(r"\bpublicación\s+de\s+biene\b", re.I), "publicación de bienes", "old_context_phrase"),
    (re.compile(r"\bdonde\s+biene\b", re.I), "donde viene", "old_context_phrase"),
    (re.compile(r"\bbiene\s+sonando\b", re.I), "viene sonando", "old_context_phrase"),
    (re.compile(r"\bbi[sz]ma,?\s+o\s+bidma\b", re.I), "bizma", "old_context_phrase"),
    (re.compile(r"\babollar[ao]\s+abollonar\b", re.I), "abollar o abollonar", "old_context_phrase"),
    (re.compile(r"\bavellacar\s+obaldonar\b", re.I), "avellacar o baldonar", "old_context_phrase"),
    (re.compile(r"\bechar\s+apuertas\s+operseguir\b", re.I), "echar a puertas o perseguir", "old_context_phrase"),
    (re.compile(r"\brendir\s+por\s+vomitar;\s+gomitar,\s*ó\s+vomitar;\s+bosar\s+ó\s+gomitar\.?", re.I), "rendir por vomitar.", "old_context_phrase"),
    (re.compile(r"\bgomitar,?\s+[oó]\s+lomitar\b", re.I), "vomitar", "old_context_phrase"),
    (re.compile(r"\bbosar\s+[oó]\s+(?:gomitar|vomitar)\b", re.I), "vomitar", "old_context_phrase"),
    (re.compile(r"\bgomitar\s+[oó]\s+(?:bomitar|vomitar)\b", re.I), "vomitar", "old_context_phrase"),
    (re.compile(r"\bbocezo\s+o\s+postezo\b", re.I), "bostezo", "old_context_phrase"),
    (re.compile(r"\bbarnizam\(ien\)to\b", re.I), "barnizamiento", "old_context_phrase"),
    (re.compile(r"\bablandam\(ien\)to\b", re.I), "ablandamiento", "old_context_phrase"),
    (re.compile(r"\bbarrim\(ien\)to\b", re.I), "barrimiento", "old_context_phrase"),
    (re.compile(r"\bembarnizam\(ien\)to\b", re.I), "embarnizamiento", "old_context_phrase"),
    (re.compile(r"\bbuscam\(ien\)to\b", re.I), "buscamiento", "old_context_phrase"),
    (re.compile(r"\bcontinuadam\(en\)te\b", re.I), "continuadamente", "old_context_phrase"),
    (re.compile(r"\bborraro\s+ennegrecer\b", re.I), "borrar o ennegrecer", "old_context_phrase"),
    (re.compile(r"\babocanadas\s+echar\b", re.I), "a bocanadas echar", "old_context_phrase"),
    (re.compile(r"\[em\]briagan\b", re.I), "embriagan", "old_context_phrase"),
    (re.compile(r"\[em\]bajador\b", re.I), "embajador", "old_context_phrase"),
    (re.compile(r"\besclarezero\s+resplandecer\b", re.I), "esclarecer o resplandecer", "old_context_phrase"),
    (re.compile(r"\ben\s+loquezer\b", re.I), "enloquecer", "old_context_phrase"),
    (re.compile(r"\bobrega\s+entresi\b", re.I), "o brega entre sí", "old_context_phrase"),
    (re.compile(r"\bdescala\s+brar\b", re.I), "descalabrar", "old_context_phrase"),
    (re.compile(r"\bescar\[\]uada\b", re.I), "escarbada", "old_context_phrase"),
    (re.compile(r"\bme\(n\)struada\b", re.I), "menstruada", "old_context_phrase"),
    (re.compile(r"\[s\]auze\b", re.I), "sauce", "old_context_phrase"),
    (re.compile(r"\bbehemenciao\s+porfiar\b", re.I), "vehemencia o porfiar", "old_context_phrase"),
    (re.compile(r"\bhazercimiento\s+de\s+pared\b", re.I), "hacer cimiento de pared", "old_context_phrase"),
    (re.compile(r"\bescontrahazer\b", re.I), "es contrahacer", "old_context_phrase"),
    (re.compile(r"\breziempreñada\b", re.I), "recién preñada", "old_context_phrase"),
    (re.compile(r"\bahziendose\s+de\s+su\s+vanda\b", re.I), "haciéndose de su banda", "old_context_phrase"),
    (re.compile(r"\bha\s+ziendose\s+de\s+su\s+vanda\b", re.I), "haciéndose de su banda", "old_context_phrase"),
    (re.compile(r"\bnudo\s+de\s+cana;\s+brucoula\b", re.I), "nudo de caña; brújula", "old_context_phrase"),
    (re.compile(r"\bmahizal,\s+ola\s+ortaliza\b", re.I), "maizal, o la hortaliza", "old_context_phrase"),
    (re.compile(r"\bverta\s+para\s+(?:h)?ortaliza\b", re.I), "huerta para hortaliza", "old_context_phrase"),
    (re.compile(r"\bcorrientede\s+rio\b", re.I), "corriente de río", "old_context_phrase"),
    (re.compile(r"\bredque\s+cae\b", re.I), "red que cae", "old_context_phrase"),
    (re.compile(r"\botazer\s+detener\s+el\s+relox\b", re.I), "atrasar o detener el reloj", "old_context_phrase"),
    (re.compile(r"\btomar\s+arras\s+el\s+relox\b", re.I), "tomar atrás el reloj", "old_context_phrase"),
    (re.compile(r"\bcasador\s+de\s+aves\b", re.I), "cazador de aves", "old_context_phrase"),
    (re.compile(r"\bbahohar,\s+echar\s+de\s+si\s+vaho\b", re.I), "vahar, echar de sí vaho", "old_context_phrase"),
    (re.compile(r"\bsilguiro\s+p[aá]jaro\b", re.I), "jilguero, pájaro", "old_context_phrase"),
    (re.compile(r"\bquanta\s+i\s+propriedad\b", re.I), "cuánta propiedad", "old_context_phrase"),
    (re.compile(r"\basi\s+mismo\b", re.I), "a sí mismo", "old_context_phrase"),
    (re.compile(r"\badoquieraque\b", re.I), "adondequiera que", "old_context_phrase"),
    (re.compile(r"\bpordonde\s+quiera\s+que\b", re.I), "por dondequiera que", "old_context_phrase"),
    (re.compile(r"\bbuenavolúntad\b", re.I), "buena voluntad", "old_context_phrase"),
    (re.compile(r"\bbuenopara\b", re.I), "bueno para", "old_context_phrase"),
    (re.compile(r"\bbuentiempo\b", re.I), "buen tiempo", "old_context_phrase"),
    (re.compile(r"\babregoviento\s+lluvioso\b", re.I), "ábrego, viento lluvioso", "old_context_phrase"),
    (re.compile(r"\bbannas\s+hacer,?\s*o\s+divulgaciones\b", re.I), "hacer amonestaciones o divulgaciones", "old_context_phrase"),
    (re.compile(r"\bbannas\s+hacer\b", re.I), "hacer amonestaciones", "old_context_phrase"),
    (re.compile(r"\bbalan\s+y\s+bienatauiado\b", re.I), "galán y bien ataviado", "old_context_phrase"),
    (re.compile(r"\bbux[eé]ta\s+de\s+vox\b", re.I), "bujeta de boj", "old_context_phrase"),
    (re.compile(r"\baud\(ienci\)a\b", re.I), "audiencia", "old_context_phrase"),
    (re.compile(r"\bm\(i\)embro\b", re.I), "miembro", "old_context_phrase"),
    (re.compile(r"\bp\^posición\s+de\s+abltô\b", re.I), "preposición de ablativo", "old_context_phrase"),
    (re.compile(r"\bp\^a\b", re.I), "para", "old_context_phrase"),
    (re.compile(rf"(?<![{LETTER}])q\^(?![{LETTER}])", re.I), "que", "old_context_phrase"),
    (re.compile(rf"(?<![{LETTER}])d\^(?![{LETTER}])", re.I), "de", "old_context_phrase"),
    (re.compile(r"\bp\^lado\b", re.I), "prelado", "old_context_phrase"),
    (re.compile(r"\buocal\s+letra\s+que\s+suena\s+por\s+si\b", re.I), "vocal letra que suena por sí", "old_context_phrase"),
    (re.compile(r"\babad\s+prelado\s+de\s+monges\b", re.I), "abad prelado de monjes", "old_context_phrase"),
    (re.compile(r"\bquebrantar\?canas\b", re.I), "quebrantar cañas", "old_context_phrase"),
    (re.compile(r"\bdeleic\?oso\s+lugar\b", re.I), "deleitoso lugar", "old_context_phrase"),
    (re.compile(r"\bembeodarse,?\s+embriagarse\b", re.I), "embriagarse", "old_context_phrase"),
    (re.compile(r"\bembeodamiento,?\s+beodez\b", re.I), "embriaguez", "old_context_phrase"),
    (re.compile(r"\bbuzano\s+entrar\s+en\s+el\s+agua\b", re.I), "bucear, entrar en el agua", "old_context_phrase"),
    (re.compile(r"\babahamiento\s+que\s+se\s+hecha\s+del\s+bajo\s+aliento\b", re.I), "vahamiento que se echa del vaho o aliento", "old_context_phrase"),
    (re.compile(r"\bab\[\]rochada\b", re.I), "abrochada", "old_context_phrase"),
    (re.compile(r"\ba\[\]si\b", re.I), "a sí", "old_context_phrase"),
    (re.compile(r"\bmaestro\s+\[\]\s+de\b", re.I), "maestro de", "old_context_phrase"),
    (re.compile(r"\bdesembue\[\]ta\b", re.I), "desenvuelta", "old_context_phrase"),
    (re.compile(r"\btener\[\]", re.I), "tener", "old_context_phrase"),
    (re.compile(r"\bperue\[\]tano\b", re.I), "peruétano", "old_context_phrase"),
    (re.compile(r"\bg\[\]olosinear\b", re.I), "golosinear", "old_context_phrase"),
    (re.compile(r"\bme\[\]didor\b", re.I), "medidor", "old_context_phrase"),
    (re.compile(r"\bdepos\[\]ición\b", re.I), "deposición", "old_context_phrase"),
    (re.compile(r"\bcomo\[\]", re.I), "como", "old_context_phrase"),
    (re.compile(r"\bay\[\]re\b", re.I), "aire", "old_context_phrase"),
    (re.compile(r"\baduf\[\]e\b", re.I), "adufe", "old_context_phrase"),
    (re.compile(r"\bpe\[\]sadumbre\b", re.I), "pesadumbre", "old_context_phrase"),
    (re.compile(r"\bsacrifi\[\]cio\b", re.I), "sacrificio", "old_context_phrase"),
    (re.compile(r"\bi\[\]nocencia\b", re.I), "inocencia", "old_context_phrase"),
    (re.compile(r"\[\]andar\b", re.I), "andar", "old_context_phrase"),
    (re.compile(r"\bglori\[\]ficado\b", re.I), "glorificado", "old_context_phrase"),
    (re.compile(r"\benga\[\]ñando\b", re.I), "engañando", "old_context_phrase"),
    (re.compile(r"\bacarrear\[\]", re.I), "acarrear", "old_context_phrase"),
    (re.compile(r"\bo\[\]tras\b", re.I), "otras", "old_context_phrase"),
    (re.compile(r"\bdesc\[\]ubrimiento\b", re.I), "descubrimiento", "old_context_phrase"),
    (re.compile(r"\bcono\[\]cido\b", re.I), "conocido", "old_context_phrase"),
    (re.compile(r"\baco\[\]metido\b", re.I), "acometido", "old_context_phrase"),
    (re.compile(r"\bence\[\]rarse\b", re.I), "encerrarse", "old_context_phrase"),
    (re.compile(r"\[\]cañaveral\b", re.I), "cañaveral", "old_context_phrase"),
    (re.compile(r"\balguna\s+\[\]\s+cosa\b", re.I), "alguna cosa", "old_context_phrase"),
    (re.compile(r"\bensarten\b", re.I), "en sartén", "old_context_phrase"),
    (re.compile(r"\babarisco,?\s+vos\s+antigua,?\s+que\s+significa\s+enteramente\s+del\s+todo,?\s+omnino\.?", re.I), "enteramente del todo", "old_context_phrase"),
    (re.compile(r"\babarrisco\s+llevar\s+el\s+ladrón\s+cuanto\s+había\b", re.I), "llevar el ladrón todo cuanto había", "old_context_phrase"),
    (re.compile(r"\babarrisco,?\s+o\s*sin\s+dejar\s+nada\b", re.I), "enteramente del todo, o sin dejar nada", "old_context_phrase"),
    (re.compile(r"\babarrisco,?\s+osin\s+quedar\s+nada\b", re.I), "enteramente del todo, o sin quedar nada", "old_context_phrase"),
    (re.compile(r"\babarrisco\b", re.I), "enteramente del todo", "old_context_phrase"),
    (re.compile(r"\bbaladrear,?\s+o\s+fanfarronear\b", re.I), "fanfarronear", "old_context_phrase"),
    (re.compile(r"\bbaladrear\b", re.I), "fanfarronear", "old_context_phrase"),
    (re.compile(r"\bbalandrear\s+o\s+parlar\b", re.I), "parlar", "old_context_phrase"),
    (re.compile(r"\bbulliciar\s+alborotando\b", re.I), "alborotar", "old_context_phrase"),
    (re.compile(r"\bbulliciar\s+como\s+quiera\b", re.I), "alborotar como quiera", "old_context_phrase"),
    (re.compile(r"\bembazar,?\s+y\s+maravillarse\b", re.I), "quedar pasmado y maravillarse", "old_context_phrase"),
    (re.compile(r"\bembazar\s+o\s+estar\s+atonito\b", re.I), "quedar pasmado o estar atónito", "old_context_phrase"),
    (re.compile(r"\bembazar\s+o\s+quedar\s+pasmado,?\s+o\s+hecho\s+matachin\b", re.I), "quedar pasmado, o hecho matachín", "old_context_phrase"),
    (re.compile(r"\bembazado\s+maravillado\b", re.I), "pasmado y maravillado", "old_context_phrase"),
    (re.compile(r"\bembazado,?\s+y\s+maravillado\b", re.I), "pasmado y maravillado", "old_context_phrase"),
    (re.compile(r"\bembazádo,?\s+y\s+maravillado\b", re.I), "pasmado y maravillado", "old_context_phrase"),
    (re.compile(r"\bembazado,?\s+o\s+el\s+que\s+se\s+para\b", re.I), "pasmado, o el que se para", "old_context_phrase"),
    (re.compile(r"\bembazado\s+así\b", re.I), "pasmado así", "old_context_phrase"),
    (re.compile(r"\bembazarse\b", re.I), "quedarse pasmado", "old_context_phrase"),
    (re.compile(r"\bpesquiz\s+algún\s+maleficio\b", re.I), "pesquis de algún maleficio", "old_context_phrase"),
    (re.compile(r"\bbortar\s+o\s+brosar\b", re.I), "bordar", "old_context_phrase"),
    (re.compile(r"\bbrosador\s+o\s+sastre\b", re.I), "bordador o sastre", "old_context_phrase"),
    (re.compile(r"\bbroslador\s+o\s+sastre\b", re.I), "bordador o sastre", "old_context_phrase"),
    (re.compile(r"\bbrosladura\s+de\s+ropa\b", re.I), "bordadura de ropa", "old_context_phrase"),
    (re.compile(r"\bbroslar\s+o\s+coser\b", re.I), "bordar o coser", "old_context_phrase"),
    (re.compile(r"\bbuenfagos\s+o\s+bofes\b", re.I), "bofes", "old_context_phrase"),
    (re.compile(r"\babaharre\s+tener\s+albajo\s+vapor\b", re.I), "vahar, tener al bajo vapor", "old_context_phrase"),
    (re.compile(r"\bablandeado\s+condecendiendo\b", re.I), "ablandado condescendiendo", "old_context_phrase"),
    (re.compile(r"\bbraveserse\b", re.I), "bravearse", "old_context_phrase"),
    (re.compile(r"\bomezillo\s+enemistad\s+mortal\b", re.I), "homicillo, enemistad mortal", "old_context_phrase"),
    (re.compile(r"\benricarse\b", re.I), "enriscarse", "old_context_phrase"),
    (re.compile(r"\benrisarse\b", re.I), "enriscarse", "old_context_phrase"),
    (re.compile(r"\benrrisarse\b", re.I), "enriscarse", "old_context_phrase"),
    (re.compile(r"\bsiervo\s+bazal\b", re.I), "siervo bozal", "old_context_phrase"),
    (re.compile(r"\bhazino\s+o\s+mezquino\b", re.I), "avaro o mezquino", "old_context_phrase"),
    (re.compile(r"\bbobedad\s+tal\b", re.I), "bobería", "old_context_phrase"),
    (re.compile(r"\bbobedad;\s*necedad\b", re.I), "bobería; necedad", "old_context_phrase"),
    (re.compile(r"\bbobería,?\s+o\s+bobedad\b", re.I), "bobería", "old_context_phrase"),
    (re.compile(r"\binstrumento\s+para\s+callentar,?\s+o\s+escallentar\s+algo,?\s+o\s+escallentador\b", re.I), "instrumento para calentar algo, o calentador", "old_context_phrase"),
    (re.compile(r"\bestropezar,?\s+o\s+i?tropezar\b", re.I), "tropezar", "old_context_phrase"),
    (re.compile(r"\bdistilar,?\s+o\s+destilar\b", re.I), "destilar", "old_context_phrase"),
    (re.compile(r"\bpolir,?\s+o\s+pulir\b", re.I), "pulir", "old_context_phrase"),
    (re.compile(r"\bdesenhadar,?\s+o\s+recrear\s+[aá]\s+otro\b(?!\s*\(arcaico:)", re.I), "desenhadar (arcaico: recrear) a otro", "old_context_phrase"),
    (re.compile(r"\bdesenhadarse,?\s+o\s+recrearse\s+otro\b(?!\s*\(arcaico:)", re.I), "desenhadarse (arcaico: recrearse) otro", "old_context_phrase"),
    (re.compile(r"\bdesenhadarse\b(?!\s*\(arcaico:)", re.I), "desenhadarse (arcaico: recrearse)", "old_context_phrase"),
    (re.compile(r"\bdesenhadamiento,?\s+o\s+recreo\s+de\s+otro\b(?!\s*\(arcaico:)", re.I), "desenhadamiento (arcaico: recreo de otro)", "old_context_phrase"),
    (re.compile(r"\bdesenhadamiento,?\s+o\s+recreación\s+que\s+se\s+da\s+a\s+otro\b(?!\s*\(arcaico:)", re.I), "desenhadamiento (arcaico: recreación que se da a otro)", "old_context_phrase"),
    (re.compile(r"\bdesenhadamiento,?\s+o\s+recreación\s+de\s+otro\b(?!\s*\(arcaico:)", re.I), "desenhadamiento (arcaico: recreación de otro)", "old_context_phrase"),
    (re.compile(r"\bdesenhadamiento\s+así\b(?!\s*\(arcaico:)", re.I), "desenhadamiento (arcaico: recreación) así", "old_context_phrase"),
    (re.compile(r"\bfornecer,?\s+o\s+fortalecer\b(?!\s*\(arcaico:)", re.I), "fornecer (arcaico: fortalecer)", "old_context_phrase"),
    (re.compile(r"\bfornecer,?\s+fortalecer,?\s+firmar,?\s+fortificar\b(?!\s*\(arcaico:)", re.I), "fornecer (arcaico: fortalecer), firmar, fortificar", "old_context_phrase"),
    (re.compile(r"\bayuda\s+aparir\b", re.I), "ayuda a parir", "old_context_phrase"),
    (re.compile(r"\bpensar\s+bestias,?\s+odar\s+apacer\s+alganado\b", re.I), "pensar bestias, o dar a pacer al ganado", "old_context_phrase"),
    (re.compile(r"\bmojar\s+a\s+otro\s+hechandole\s+agua;\s+mojar\s+a\s+otra\s+cosa;\s+remojar\b", re.I), "mojar a otro echándole agua; mojar otra cosa; remojar", "old_context_phrase"),
    (re.compile(r"\bembebecerse\s+en\s+algo\b(?!\s*\(arcaico:)", re.I), "embebecerse en algo (arcaico: estar absorto en algo)", "old_context_phrase"),
    (re.compile(r"\bembebecerse\s+en\s+otra\s+cosa\b(?!\s*\(arcaico:)", re.I), "embebecerse en otra cosa (arcaico: estar absorto en otra cosa)", "old_context_phrase"),
    (re.compile(r"^\s*embebecerse\.?\s*$", re.I), "embebecerse (arcaico: estar absorto)", "old_context_phrase"),
    (re.compile(r"\bembebecido\s+en\s+alguna\s+cosa\b(?!\s*\(arcaico:)", re.I), "embebecido en alguna cosa (arcaico: absorto)", "old_context_phrase"),
    (re.compile(r"\bembebecido\b(?!\s*(?:\(arcaico:|en\b))", re.I), "embebecido (arcaico: absorto)", "old_context_phrase"),
    (re.compile(r"\bembebecida\s+cosa\b(?!\s*\(arcaico:)", re.I), "embebecida cosa (arcaico: cosa absorta)", "old_context_phrase"),
    (re.compile(r"\benaguazada\s+tierra\b(?!\s*\(arcaico:)", re.I), "enaguazada tierra (arcaico: tierra anegada)", "old_context_phrase"),
    (re.compile(r"\benaguazarse\s+la\s+tierra\b(?!\s*\(arcaico:)", re.I), "enaguazarse la tierra (arcaico: anegarse la tierra)", "old_context_phrase"),
    (re.compile(r"\babochornarse\s+los\s+panes\s+o\s+enaguazarse\s+y\s+anegarse\b", re.I), "abochornarse los panes o enaguazarse y anegarse", "old_context_phrase"),
    (re.compile(r"\brosas\s+poner\s+enalguna\s+cosa\s+o\s+enrosar\s+algo\b(?!\s*\(arcaico:)", re.I), "rosas poner en alguna cosa o enrosar algo (arcaico: adornar algo con flores)", "old_context_phrase"),
    (re.compile(r"\bflores\s+poner\s+en\s+alguna\s+parte,?\s+o\s+enrosar\s+algo\b(?!\s*\(arcaico:)", re.I), "flores poner en alguna parte, o enrosar algo (arcaico: adornar algo con flores)", "old_context_phrase"),
    (re.compile(r"\bponer\s+flores\s+en\s+algún\s+altar,?\s+o\s+enrosarlo\b(?!\s*\(arcaico:)", re.I), "poner flores en algún altar, o enrosarlo (arcaico: adornarlo con flores)", "old_context_phrase"),
    (re.compile(r"\benrosar,?\s+o\s+adornar\s+algo\s+con\s+flores\b", re.I), "enrosar, o adornar algo con flores", "old_context_phrase"),
    (re.compile(r"\batapar,?\s+o\s+cubrir\s+a\s+otro\s+la\s+boca\s+con\s+la\s+manta\.\s+etc\.\s+o\s+echar\s+aziar,?\s+o\s+cohechar\s+al\s+juez\.?", re.I), "atapar, o cubrir a otro la boca con la manta. etc. o echar aziar (arcaico: sobornar), o cohechar al juez", "old_context_phrase"),
    (re.compile(r"\bechar\s+aziar,?\s+o\s+sobornar\s+a\s+otro,?\s+cubrir\s+y\s+atapar\s+a\s+otro\s+la\s+boca\s+con\s+manta,?\s+o\s+con\s+otra\s+cosa\.?", re.I), "echar aziar (arcaico: sobornar), o sobornar a otro, cubrir y atapar a otro la boca con manta, o con otra cosa", "old_context_phrase"),
    (re.compile(r"\bechar\s+aziar\b(?!\s*(?:\(arcaico:|;))", re.I), "echar aziar (arcaico: sobornar o cohechar al juez)", "old_context_phrase"),
    (re.compile(r"\bechar\s+az\s+iar;\s*sobornar;\s*cohechar\s+al\s+juez\b", re.I), "echar aziar; sobornar; cohechar al juez", "old_context_phrase"),
    (re.compile(r"\benalguna\b", re.I), "en alguna", "old_context_phrase"),
    (re.compile(r"^\s*baratar\.?\s*$", re.I), "baratar (arcaico: barajar)", "old_context_phrase"),
    (re.compile(r"\bbaratar,?\s+o\s+trafaguear,?\s+o\s+mohatrar\b(?!\s*\(arcaico:)", re.I), "baratar o trafaguear o mohatrar (arcaico: regatear o negociar)", "old_context_phrase"),
    (re.compile(r"^\s*barreñón\.?\s*$", re.I), "barreñón (arcaico: lebrillo grande de barro)", "old_context_phrase"),
    (re.compile(r"\blebrillo,?\s+o\s+barreñón\s+grande\s+de\s+barro\b", re.I), "lebrillo, o barreñón grande de barro", "old_context_phrase"),
    (re.compile(r"\bbarraco\s+o\s+verraco\b", re.I), "barraco o verraco", "old_context_phrase"),
    (re.compile(r"\by\s+también\.\s*s\.\s*iuan\.\s*conjunction\.?", re.I), "y también. s. iuan. conjunción", "old_context_phrase"),
    (re.compile(r"\biuan\s+de\s+mena\b", re.I), "Juan de Mena", "old_context_phrase"),
    (re.compile(r"\baarón\s+hierba\s+abarba\s+de\s+aarón\b", re.I), "hierba barba de Aarón", "old_context_phrase"),
    (re.compile(r"\bmozo,?\s+que\s+comienza\s+a?\s*barbar\b(?!\s*\(arcaico:)", re.I), "mozo que comienza a barbar (arcaico: tener barba)", "old_context_phrase"),
    (re.compile(r"\babarraganada\s+hembra\s+con\s+soltero\b(?!\s*\(arcaico:)", re.I), "abarraganada hembra con soltero (arcaico: mujer amancebada)", "old_context_phrase"),
    (re.compile(r"\babarraganada\s+de\s+casado\b(?!\s*\(arcaico:)", re.I), "abarraganada de casado (arcaico: amancebada con casado)", "old_context_phrase"),
    (re.compile(r"\bbarraganía\s+mujer\s+manceba\b(?!\s*\(arcaico:)", re.I), "barraganía mujer manceba (arcaico: mancebía)", "old_context_phrase"),
    (re.compile(r"\bbarraganía\s+de\s+varón\b(?!\s*\(arcaico:)", re.I), "barraganía de varón (arcaico: mancebía de varón)", "old_context_phrase"),
    (re.compile(r"\bhigo\s+temprano,\s*o\s+breba\b", re.I), "higo temprano, o breva", "old_context_phrase"),
    (re.compile(r"\bhigo\s+temprano\s+o\s+breba\b", re.I), "higo temprano o breva", "old_context_phrase"),
    (re.compile(r"^\s*abasta\s+o\s+abastanza\.?\s*$", re.I), "abasta o abastanza (arcaico: abundamiento)", "old_context_phrase"),
    (re.compile(r"^\s*aburado\.?\s*$", re.I), "aburado (arcaico: quemado)", "old_context_phrase"),
    (re.compile(r"\bdar\s+coces\s+tomarse\s+las\s+abos\b", re.I), "dar coces, tomarse las abos (arcaico: dar coces)", "old_context_phrase"),
    (re.compile(r"^\s*alicaze\s+o\s+zanja\.?\s*$", re.I), "alicaze o zanja.", "old_context_phrase"),
    (re.compile(r"\bbanda\s+atreuada\s+como\s+divisa\b", re.I), "banda atravesada como divisa", "old_context_phrase"),
    (re.compile(r"\bavituado\s+otro\s+en\s+alguna\s+cosa\b", re.I), "habituado otro en alguna cosa", "old_context_phrase"),
    (re.compile(r"^\s*bene\s+valere\s*$", re.I), "bene valere (latín: hallarse bien dispuesto)", "old_context_phrase"),
    (re.compile(r"\bboledo\s+semillado\b(?!\s*\(arcaico:)", re.I), "boledo semillado (arcaico: bledo semillado)", "old_context_phrase"),
    (re.compile(r"^\s*borregón\.?\s*$", re.I), "borregón.", "old_context_phrase"),
    (re.compile(r"\bborrachonazo\b(?!\s*\(arcaico:)", re.I), "borrachonazo (arcaico: borrachón)", "old_context_phrase"),
    (re.compile(r"^\s*bermejecerse\.?\s*$", re.I), "bermejecerse (arcaico: enrojecerse)", "old_context_phrase"),
    (re.compile(r"\bbermejecerse\s+el\s+rostro\s+de\s+enojo,?\s+etc\.?(?!\s*\(arcaico:)", re.I), "bermejecerse el rostro de enojo (arcaico: enrojecerse el rostro de enojo)", "old_context_phrase"),
    (re.compile(r"\bbermejecerse\s+el\s+rostro\s+de\s+enojo\.?(?!\s*\(arcaico:)", re.I), "bermejecerse el rostro de enojo (arcaico: enrojecerse el rostro de enojo)", "old_context_phrase"),
    (re.compile(r"\bembermejecerse\b(?!\s*\(arcaico:)", re.I), "embermejecerse (arcaico: enrojecerse)", "old_context_phrase"),
    (re.compile(r"\bembermejecido\b(?!\s*\(arcaico:)", re.I), "embermejecido (arcaico: enrojecido)", "old_context_phrase"),
    (re.compile(r"\bmenstruada\s+mujer\b", re.I), "menstruada mujer", "old_context_phrase"),
    (re.compile(r"\bbarbechazón\s+el\s+tiempo\s+de\s+el\b(?!\s*\(arcaico:)", re.I), "barbechazón, el tiempo de él (arcaico: tiempo de barbecho)", "old_context_phrase"),
    (re.compile(r"\benfiuzia\s+de\s+alguno\s+o\s+con\s+alguno\b(?!\s*\(arcaico:)", re.I), "enfiuzia de alguno o con alguno (arcaico: confianza en alguno o con alguno)", "old_context_phrase"),
    (re.compile(r"^\s*obispalía\s+casa\s+de\s+obispo\.?\s*$", re.I), "casa de obispo", "old_context_phrase"),
    (re.compile(r"^\s*per\s+abreuiationem\.\s+quiere\s+decir\.\s+quitoznequi\s+i\.\s+vultdicere\.?\s*$", re.I), "per abbreviationem, quiere decir quitoznequi, id est vult dicere", "old_context_phrase"),
    (re.compile(r"^\s*abyimo\s+agua\s+sin\s+hondo\s*$", re.I), "abismo, agua sin fondo", "old_context_phrase"),
    (re.compile(r"^\s*botorbuna\s+o\s+divieso\.?\s*$", re.I), "botorbuna o divieso.", "old_context_phrase"),
    (re.compile(r"^\s*vnun\s+fit\s*$", re.I), "unum fit (latín: se hace uno)", "old_context_phrase"),
    (re.compile(r"\babrasamento\b", re.I), "abrasamiento", "old_context_phrase"),
    (re.compile(r"\bquitamiento\s+de\s+(?:la\s+)?ley;\s*abrogatio\s+legis\b", re.I), "quitamiento de la ley; abrogatio legis", "old_context_phrase"),
    (re.compile(r"\boveja\s+grosera\s+o\s+burdalla\b(?!\s*\(arcaico:)", re.I), "oveja grosera o burdalla (arcaico: oveja burda, de lana gruesa y áspera)", "old_context_phrase"),
    (re.compile(r"\bhacer\s+ayere\s+de\s+esta\s+manera\s+a\s+otro\b", re.I), "hacer aire de esta manera a otro", "old_context_phrase"),
    (re.compile(r"\bal\s+ayere\b", re.I), "al aire", "old_context_phrase"),
    (re.compile(r"\babortear\s+por\s+algún\s+desastre\s+y\s+sin\s+voluntad\b(?!\s*\(arcaico:)", re.I), "abortear por algún desastre y sin voluntad (arcaico: abortar por algún desastre y sin voluntad)", "old_context_phrase"),
    (re.compile(r"^\s*bene\.?\s*$", re.I), "Bene (latín: bien)", "old_context_phrase"),
    (re.compile(r"\breziono\s+doliente\b", re.I), "recio no doliente", "old_context_phrase"),
    (re.compile(r"\bbardonarse\s+mujeres\b", re.I), "baldonarse las mujeres", "old_context_phrase"),
    (re.compile(r"\bbocadas\s+dar\s+arremetiendo\s+contra\s+alguno\b", re.I), "bocados dar arremetiendo contra alguno", "old_context_phrase"),
    (re.compile(r"\bbubas\s+de\s+budas\s+largas\b", re.I), "bubas de bubas largas (bubas grandes y largas)", "old_context_phrase"),
    (re.compile(r"\bllevar\s+algo\s+en\s+jazeba\b\??", re.I), "llevar algo en jaula", "old_context_phrase"),
    (re.compile(r"^\s*obaxo\?\s*$", re.I), "obrero", "old_context_phrase"),
    (re.compile(r"^\s*enoxullezerse\s*$", re.I), "enojarse", "old_context_phrase"),
    (re.compile(r"\bembismador\b", re.I), "embizmador", "old_context_phrase"),
    (re.compile(r"\bembismado\b", re.I), "embizmado", "old_context_phrase"),
    (re.compile(r"\bbosada\s+cosa\b", re.I), "cosa vomitada", "old_context_phrase"),
    (re.compile(r"\boriniento\b", re.I), "mohoso", "old_context_phrase"),
    (re.compile(r"\ber\?\?badura\b", re.I), "escarbadura", "old_context_phrase"),
    (re.compile(r"\bbuleta\s+cosa\s+de\s+arriba\s+a\s+bajo,?\s+y\s+que\s+cuelgue\b", re.I), "cosa vuelta de arriba abajo y que cuelga", "old_context_phrase"),
    (re.compile(r"\bembrar\s+algo\s+con\s+otro\b", re.I), "enviar algo con otro", "old_context_phrase"),
    (re.compile(r"\bcomplacedor\s+de\s+buzedor\s+de\s+placeria\s+a\s+otro\b", re.I), "complacedor o hacedor de placer a otro", "old_context_phrase"),
    (re.compile(r"\bbragar,?\s+como\s+almaizal\?\s+ricas\s+y\s+muy\s+labradas\b", re.I), "bragas como almaizal, ricas y muy labradas", "old_context_phrase"),
    (re.compile(r"\bpostilla\s+de\s+sarna\s+o\s+botor\b", re.I), "postilla de sarna", "old_context_phrase"),
    (re.compile(r"\bbuetagos\s+o\s+escopetina\b", re.I), "bofes o escopetina", "old_context_phrase"),
    (re.compile(r"\bbruniel\b", re.I), "bruñida cosa", "old_context_phrase"),
    (re.compile(r"\bbostana\s+cosa\b", re.I), "labrada cosa", "old_context_phrase"),
    (re.compile(r"\babajar\s+lo\s+berbio\b", re.I), "abajar lo soberbio", "old_context_phrase"),
    (re.compile(r"\bdezidos\s+suave\b", re.I), "decidor suave", "old_context_phrase"),
    (re.compile(r"\bmexias\s+en\s+hebra\s+y\s+co\s+es\s+brigido\b", re.I), "Mesías en hebreo es ungido", "old_context_phrase"),
    (re.compile(r"\bhacer\s+algo\s+behementer\b", re.I), "hacer algo vehementemente", "old_context_phrase"),
    (re.compile(r"\bbaldres\s+polleja\s+curtida\b", re.I), "baldrés, pelleja curtida", "old_context_phrase"),
    (re.compile(r"\btomarplazer\b", re.I), "tomar placer", "old_context_phrase"),
    (re.compile(r"\bpararsesuzio\b", re.I), "pararse sucio", "old_context_phrase"),
    (re.compile(r"\bhaziasi\b", re.I), "hacia sí", "old_context_phrase"),
    (re.compile(r"\bhaziati\b", re.I), "hacia ti", "old_context_phrase"),
    (re.compile(r"\botrodize\b", re.I), "otro dice", "old_context_phrase"),
    (re.compile(r"\bqualq\(uier\)a\b", re.I), "cualquiera", "old_context_phrase"),
    (re.compile(r"\ba\s+a\s+lguien\b", re.I), "a alguien", "old_context_phrase"),
    (re.compile(r"\ba\s+o\s+otro\b", re.I), "a otro", "old_context_phrase"),
    (re.compile(r"\bbarui\[\]rojo\b", re.I), "barbirrojo", "old_context_phrase"),
    (re.compile(r"\bve\[\]zindad\b", re.I), "vecindad", "old_context_phrase"),
    (re.compile(r"\bcon\$tituir\b", re.I), "constituir", "old_context_phrase"),
    (re.compile(r"\bcompa\?sion\b", re.I), "compasión", "old_context_phrase"),
    (re.compile(r"\binable\s+cosa\s+no\s+abile\b", re.I), "inhábil cosa no hábil", "old_context_phrase"),
    (re.compile(r"\ben\s+en\s+el\b", re.I), "en el", "old_context_phrase"),
    (re.compile(r"\ben\s+en\s+la\b", re.I), "en la", "old_context_phrase"),
    (re.compile(r"\ben\s+en\s+los\b", re.I), "en los", "old_context_phrase"),
    (re.compile(r"\ben\s+en\s+las\b", re.I), "en las", "old_context_phrase"),
    (re.compile(r"\bde\s+de\s+mujer\b", re.I), "de mujer", "old_context_phrase"),
    (re.compile(r"\bposesión\s+oblig\.", re.I), "posesión obligatoria", "old_context_phrase"),
    (re.compile(r"\bhazercimiento\b", re.I), "hacer cimiento", "old_context_phrase"),
    (re.compile(r"\bénhaziénda\b", re.I), "en hacienda", "old_context_phrase"),
    (re.compile(r"\bamanizquierda\b", re.I), "a mano izquierda", "old_context_phrase"),
    (re.compile(r"\bbuentratamiento\b", re.I), "buen tratamiento", "old_context_phrase"),
    (re.compile(r"\bpicobaxo\b", re.I), "pico bajo", "old_context_phrase"),
    (re.compile(r"\bpor\s+ay\b", re.I), "por ahí", "old_context_phrase"),
    (re.compile(r"\bde\s+aqui\b", re.I), "de aquí", "old_context_phrase"),
    (re.compile(r"\bdesde\s+aqui\b", re.I), "desde aquí", "old_context_phrase"),
    (re.compile(r"\bde\s+hay\b", re.I), "de ahí", "old_context_phrase"),
    (re.compile(r"\bde\s+ay\b", re.I), "de ahí", "old_context_phrase"),
    (re.compile(r"\bhasta\s+hay\b", re.I), "hasta ahí", "old_context_phrase"),
    (re.compile(r"\bhasta\s+ay\b", re.I), "hasta ahí", "old_context_phrase"),
    (re.compile(r"\bdesde\s+ay\b", re.I), "desde ahí", "old_context_phrase"),
    (re.compile(r"\bhay\s+donde\b", re.I), "ahí donde", "old_context_phrase"),
    (re.compile(r"\bay\s+donde\b", re.I), "ahí donde", "old_context_phrase"),
    (re.compile(r"\benque\s+esta\b", re.I), "en que está", "old_context_phrase"),
    (re.compile(r"\bqe\.\s+esta\b", re.I), "que está", "old_context_phrase"),
    (re.compile(r"\bdeque\s+esta\b", re.I), "de que está", "old_context_phrase"),
    (re.compile(r"\bque\s+esta\b", re.I), "que está", "old_context_phrase"),
    (re.compile(r"\bque\s+estas\b", re.I), "que estás", "old_context_phrase"),
    (re.compile(r"\bdonde\s+esta\b", re.I), "donde está", "old_context_phrase"),
    (re.compile(r"\bcuando\s+esta\b", re.I), "cuando está", "old_context_phrase"),
    (re.compile(r"\btu\s+estas\b", re.I), "tú estás", "old_context_phrase"),
    (re.compile(r"\blla\s+esta\b", re.I), "ya está", "old_context_phrase"),
    (re.compile(r"\blla\s+lo\s+esta\b", re.I), "ya lo está", "old_context_phrase"),
    (re.compile(r"\bdigno\s+deser\b", re.I), "digno de ser", "old_context_phrase"),
    (re.compile(r"\bdigna\s+deser\b", re.I), "digna de ser", "old_context_phrase"),
    (re.compile(r"\bdignas\s+deser\b", re.I), "dignas de ser", "old_context_phrase"),
    (re.compile(r"\bdignos\s+deser\b", re.I), "dignos de ser", "old_context_phrase"),
    (re.compile(r"\bcodicia\s+deser\b", re.I), "codicia de ser", "old_context_phrase"),
    (re.compile(r"\bDeseo,\s+deser\s+codiciado\b", re.I), "Deseo de ser codiciado", "old_context_phrase"),
    (re.compile(r"\bdeser\s+codiciado\b", re.I), "de ser codiciado", "old_context_phrase"),
    (re.compile(r"\bdescobrir\s+se\b", re.I), "descubrirse", "old_context_phrase"),
    (re.compile(r"\besta\s+encubierto\b", re.I), "está encubierto", "old_context_phrase"),
    (re.compile(r"\besta\s+cubierto\b", re.I), "está cubierto", "old_context_phrase"),
    (re.compile(r"\besta\s+amancebado\b", re.I), "está amancebado", "old_context_phrase"),
    (re.compile(r"\besta\s+enlasado\b", re.I), "está enlazado", "old_context_phrase"),
    (re.compile(r"\bsu\s+merced\s+encasa\b", re.I), "su merced en casa", "old_context_phrase"),
    (re.compile(r"\bdóndevoy\b", re.I), "donde voy", "old_context_phrase"),
    (re.compile(r"\bconella\b", re.I), "con ella", "old_context_phrase"),
    (re.compile(r"\bes\s+entres\s+maneras\b", re.I), "es en tres maneras", "old_context_phrase"),
    (re.compile(r"\bdividido\s+entres\s+partes\b", re.I), "dividido en tres partes", "old_context_phrase"),
]


EXPAND_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(
            r"\b("
            r"abierta|abuhado|adonde|ahuhado|algo|algo mejor|alguno|aquel|allí|"
            r"aquí|así|bien|cabe quien|cada uno|cargo|claro|como|con quien|cosa|"
            r"de veras|deque|"
            r"dónde algo|dónde aquel|dónde otro|el alba|el enfermo|el que|elque|"
            r"enfermo|enque|le|me|no|nos|otro|por donde otro|por dónde|qe\.|"
            r"que nos|que tanto|se|siempre|una cosa|ya"
            r")\s+esta\b",
            re.I,
        ),
        r"\1 está",
        "contextual_estar_accent",
    ),
    (
        re.compile(
            r"\besta\s+("
            r"a mi cargo|adornado|ahito|aliviado|alto|apegada|bien|borracho|bueno|claro|"
            r"crecido|desbastado|determinado|dividido|el|en|enduresido|"
            r"escarmenado|estendida|firme|la|limpio|lleno|madura|mejor|"
            r"muriendo|otorgando|pensando|podrida|prometid[ao]|repleto|"
            r"riendo|seco|sentado|su merced|tejida|vivo|ya estendida"
            r")\b",
            re.I,
        ),
        r"está \1",
        "contextual_estar_accent",
    ),
]


PAIRS = """
abaxamiento	abajamiento
abaxando	abajando
abaxan	abajan
aborrezer	aborrecer
accusatiuo	acusativo
aliofar	aljófar
aljofar	aljófar
aljaua	aljaba
algunasyeruas	algunas hierbas
arcabuzero	arcabucero
azedera	acedera
azederas	acederas
azeda	aceda
azedar	acedar
azedarse	acedarse
azedia	acedía
azedo	acedo
azeite	aceite
azeitero	aceitero
azeitosa	aceitosa
azemila	acémila
azequia	acequia
azepilladuras	acepilladuras
azepillar	acepillar
azeptador	aceptador
azeptar	aceptar
azero	acero
aziago	aciago
azial	acial
azucar	azúcar
abejado	avezado
abejarse	avezarse
abuehamiento	abuhamiento
baxada	bajada
baxado	bajado
baxador	bajador
baxando	bajando
baxas	bajas
baxilla	vajilla
bende	vende
bendedor	vendedor
bendezida	bendecida
bendezidas	bendecidas
bendezido	bendecido
bendezir	bendecir
bendizidor	bendecidor
beruena	verbena
bezerro	becerro
biuda	viuda
biudez	viudez
biudo	viudo
bibir	vivir
boz	voz
bozear	vocear
bozes	voces
bozina	bocina
bocarriba	boca arriba
bueltas	vueltas
cabezbaxo	cabezbajo
cabezear	cabecear
cabezera	cabecera
catorze	catorce
coza	cosa
cozer	cocer
cozes	coces
cozida	cocida
cozidas	cocidas
cozido	cocido
cozina	cocina
cozinero	cocinero
combida	convida
combidador	convidador
combidada	convidada
combidado	convidado
combidados	convidados
combidar	convidar
combidarse	convidarse
combite	convite
combites	convites
complazer	complacer
complazimiento	complacimiento
conbidar	convidar
conbidarse	convidarse
conbidada	convidada
conbidado	convidado
conbidados	convidados
conbidador	convidador
conbite	convite
conbites	convites
contradezir	contradecir
cóntradezir	contradecir
cueze	cuece
dezimada	diezmada
deziseis	dieciséis
dezisiete	diecisiete
deziocho	dieciocho
dezidor	decidor
dezmar	diezmar
dezmero	diezmero
deziséis	dieciséis
dezisiete	diecisiete
deziocho	dieciocho
doze	doce
dozena	docena
desaparecivido	desapercibido
desauziado	desahuciado
desembuelta	desenvuelta
desembuelto	desenvuelto
desemboluer	desenvolver
desemboluerse	desenvolverse
desemboluerse	desenvolverse
deserbar	desyerbar
desdezir	desdecir
desdezirse	desdecirse
desyunzir	desuncir
dizese	dícese
diziendoselos	diciéndoselos
embaxada	embajada
émbaxador	embajador
embaxador	embajador
embiad	enviad
embiada	enviada
embiadas	enviadas
embiado	enviado
embiados	enviados
embiador	enviador
embiar	enviar
embidia	envidia
embidiar	envidiar
embidiosamente	envidiosamente
embidioso	envidioso
embio	envió
embiudada	enviudada
embiudado	enviudado
embiudar	enviudar
embolber	envolver
emboltorio	envoltorio
embolver	envolver
emboluer	envolver
emboluerle	envolverle
embuelue	envuelve
embuelta	envuelta
embuelto	envuelto
enbuelto	envuelto
enboluer	envolver
enflaquezer	enflaquecer
ensoberbezerse	ensoberbecerse
ensoberuecer	ensoberbecer
ensoberuecerme	ensoberbecerme
ensoberuecerse	ensoberbecerse
ensoberuecido	ensoberbecido
ensuzia	ensucia
ensuziada	ensuciada
ensuziador	ensuciador
ensuziar	ensuciar
ensuziarse	ensuciarse
enzias	encías
enzina	encina
enzinal	encinal
eredad	heredad
eredades	heredades
eredar	heredar
eredero	heredero
erir	herir
ermana	hermana
ermano	hermano
ermanos	hermanos
escozer	escocer
escozimiento	escocimiento
esparzida	esparcida
esparzidas	esparcidas
esparzido	esparcido
esparziendo	esparciendo
esparzidor	esparcidor
esparzir	esparcir
esparzirse	esparcirse
hacezillo	hacecillo
hazecillo	hacecillo
hechizeria	hechicería
hechizero	hechicero
hechizeros	hechiceros
iarro	jarro
iabali	jabalí
iabalies	jabalíes
iacinto	jacinto
iesu	Jesu
iugo	yugo
iuramentado	juramentado
iusticia	justicia
induzir	inducir
juizio	juicio
juizios	juicios
layerua	la hierba
lanzero	lancero
lazerado	lacerado
lazeria	lacería
lebantar	levantar
lebantador	levantador
lebantamiento	levantamiento
lebantarse	levantarse
lebanto	levanto
lenzero	lencero
lleban	llevan
llebar	llevar
llebaras	llevarás
llebarrrodeando	llevar rodeando
llubia	lluvia
llubias	lluvias
luzero	lucero
luziente	luciente
luzio	lucio
luzir	lucir
luzimiento	lucimiento
maldezidor	maldecidor
maldezir	maldecir
maldiziente	maldiciente
maluada	malvada
maluado	malvado
manzilla	mancilla
manzillada	mancillada
manzillado	mancillado
manzillar	mancillar
mánzillar	mancillar
mánzillado	mancillado
manzillarse	mancillarse
melezina	medicina
nabaxa	navaja
nabaxón	navajón
narizes	narices
nazer	nacer
nuves	nubes
orimento	mohoso
ombro	hombro
ombros	hombros
ombre	hombre
ombres	hombres
onra	honra
onrable	honrable
onradamente	honradamente
onrado	honrado
onrar	honrar
onrarse	honrarse
onrrado	honrado
onrrar	honrar
onrras	honras
onrrosamente	honrosamente
onze	once
osiruienta	o sirvienta
odrezillo	odrecillo
perbertirse	pervertirse
peruersa	perversa
peruertidamente	pervertidamente
peruertiendo	pervirtiendo
peruertiendolos	pervirtiéndolos
peruertido	pervertido
peruertimiento	pervertimiento
peruertir	pervertir
peruertirlo	pervertirlo
peruertirse	pervertirse
plazer	placer
plazentera	placentera
plazentero	placentero
prelazia	prelacía
raizes	raíces
rebuelca	revuelca
rebuelco	revuelco
rebuelue	revuelve
rebuelta	revuelta
rebueltas	revueltas
rebuelto	revuelto
rebolbedor	revolvedor
rebolbador	revolvedor
rebolber	revolver
rebolbimiento	revolvimiento
reboluimiento	revolvimiento
reboluedero	revolvedero
reboluedor	revolvedor
reboluerle	revolverle
reboluerse	revolverse
rebolver	revolver
rebolverse	revolverse
rebolviendo	revolviendo
rebolviendo	revolviendo
reboluiendo	revolviendo
reboluiendolos	revolviéndolos
reboluiendos	revolviendo
rebolvedor	revolvedor
reciura	reciura
recive	recibe
recivido	recibido
recivió	recibió
recivirá	recibirá
redezilla	redecilla
reduzimiento	reducimiento
reduzir	reducir
rehazer	rehacer
reluze	reluce
reluzir	relucir
renzilla	rencilla
renzilloso	rencilloso
resplandezer	resplandecer
rezia	recia
reziamente	reciamente
reziaménte	reciamente
rezien	recién
reziente	reciente
rezientes	recientes
rezio	recio
reziura	reciura
rrebuelto	revuelto
salbar	salvar
salbados	salvados
salbo	salvo
saluado	salvado
saluados	salvados
saluador	salvador
saluaje	salvaje
saluar	salvar
saluarse	salvarse
saluanse	sálvanse
salua	salva
saluonor	salvonor
salbonor	salvonor
sauze	sauce
sauzes	sauces
senzilla	sencilla
senzillo	sencillo
serbía	servía
serbie	servir
serbil	servil
serbir	servir
seruidor	servidor
seruidores	servidores
seruir	servir
seruirme	servirme
siluestre	silvestre
siluestres	silvestres
sinzel	cincel
sirbe	sirve
sirben	sirven
sirue	sirve
siruen	sirven
siruo	sirvo
siruienta	sirvienta
satisfazer	satisfacer
satisfazerle	satisfacerle
satisfazerme	satisfacerme
satisfazerse	satisfacerse
soberuecerse	soberbecerse
suzia	sucia
suzias	sucias
suziedad	suciedad
suzio	sucio
surzidor	zurcidor
surzir	zurcir
traduzir	traducir
trasluziente	trasluciente
treze	trece
uazura	basura
vazura	basura
vazia	vacía
vaziadizo	vaciadizo
vaziar	vaciar
vaziedad	vaciedad
vazo	vaso
vezes	veces
vezindad	vecindad
vezino	vecino
vezinos	vecinos
vbre	ubre
vfano	ufano
vhuela	vihuela
vltima	última
vltimadamente	últimamente
vmbral	umbral
vmido	húmedo
vnavez	una vez
vncopo	un copo
vngido	ungido
vngir	ungir
vngirle	ungirle
vnguento	ungüento
vnguentos	ungüentos
vnguénto	ungüento
vnica	única
vnidos	unidos
vniformidad	uniformidad
vnion	unión
vnlado	un lado
vnlugar	un lugar
vnojo	un ojo
vnpoco	un poco
vnpoquillo	un poquillo
vnpoquito	un poquito
vnirse	unirse
vntar	untar
vntarse	untarse
vña	uña
vñas	uñas
vrbanidad	urbanidad
vrdir	urdir
vrdida	urdida
vrdidor	urdidor
vrdirtela	urdir tela
vrdiembre	urdiembre
vsada	usada
vsa	usa
vsando	usando
vsarse	usarse
vsase	usase
vsura	usura
vsurero	usurero
vsurpar	usurpar
vñir	unir
vozes	voces
yazer	yacer
yazija	yacija
yerba	hierba
yerbas	hierbas
yerbazal	herbazal
yerua	hierba
yeruas	hierbas
yerva	hierba
yervas	hierbas
yervazal	herbazal
zerezas	cerezas
alcanze	alcance
alguazil	alguacil
aplazible	apacible
aplaziblemente	apaciblemente
avecindado	avecindado
azer	hacer
azije	acije
bazin	bacín
blanquezino	blanquecino
boluerla	volverla
boluerlo	volverlo
boluerme	volverme
boluerseme	volvérseme
bozinglero	vocinglero
brazelete	brazalete
brazero	brasero
ceniziento	ceniciento
codornizes	codornices
conbiene	conviene
cuezen	cuecen
desdize	desdice
donzel	doncel
donzella	doncella
dozientas	doscientas
dulze	dulce
embia	envía
embian	envían
embidar	envidar
embijar	embijar
embijarse	embijarse
embite	envite
embixada	embijada
embixado	embijado
embixamiento	embijamiento
embixar	embijar
embixarse	embijarse
embuelbe	envuelve
embolbedero	envolvedero
embolbedor	envolvedor
embolbimiento	envolvimiento
emboltorios	envoltorios
emboluedero	envolvedero
emboluedor	envolvedor
emboluimiento	envolvimiento
embolverse	envolverse
enbolber	envolver
enbolver	envolver
escueze	escuece
hezes	heces
juezes	jueces
mozedad	mocedad
nuezes	nueces
pezes	peces
pobrezilla	pobrecilla
pobrezillo	pobrecillo
razimo	racimo
razimos	racimos
rebolcadero	revolcadero
rebolcar	revolcar
rebolcarse	revolcarse
reboltellado	revuelto
reboltera	revuelta
reboluera	revolviera
reboltoso	revoltoso
regozijado	regocijado
regozijarse	regocijarse
rezentar	recentar
silua	silba
siluador	silbador
siluando	silbando
siluar	silbar
siluo	silbo
tranze	trance
trebol	trébol
vrava	brava
vmor	humor
zelar	celar
brazear	bracear
clerezia	clerecía
cruzero	crucero
encruzijada	encrucijada
enluzir	enlucir
heziste	hiciste
lanzeta	lanceta
peze	pez
pesquizidor	pesquisidor
regozijada	regocijada
trasluze	trasluce
zebratana	cerbatana
zelo	celo
zemejanza	semejanza
zizania	cizaña
avezindado	avecindado
arreziar	arreciar
abellana	avellana
abergonzado	avergonzado
abentajado	aventajado
aberiguar	averiguar
abil	hábil
abilidad	habilidad
abilitar	habilitar
abilmente	hábilmente
abido	habido
abidos	habidos
abían	habían
abisado	avisado
abisar	avisar
abispa	avispa
abitado	habitado
abituado	habituado
abituar	habituar
abituarse	habituarse
abivar	avivar
abe	ave
abla	habla
ablada	hablada
ablador	hablador
ablar	hablar
ablo	hablo
abogacia	abogacía
absoluer	absolver
absorver	absorber
abreuia	abrevia
abreuiadamente	abreviadamente
abreviadura	abreviatura
adquire	adquiere
aduertencia	advertencia
aduertiendo	advirtiendo
aduertiendolo	advirtiéndolo
aduertiéndo	advirtiendo
aduertid	advertid
aduertir	advertir
aduiento	adviento
agluien	alguien
agradezer	agradecer
aguazero	aguacero
aguazeros	aguaceros
apaziguar	apaciguar
aquien	a quien
aquiense	a quien se
azeitera	aceitera
azeituno	aceituno
azepillado	acepillado
azeptada	aceptada
alrredor	alrededor
anbas	ambas
bacia	bacía
bahari	baharí
baho	vaho
baldres	baldrés
baldia	baldía
balsamo	bálsamo
baleroso	valeroso
balerosos	valerosos
baliente	valiente
barón	varón
baron	varón
varon	varón
baldon	baldón
baladron	baladrón
balor	valor
barbaro	bárbaro
baston	bastón
baso	vaso
barua	barba
baruas	barbas
baruado	barbado
baruechar	barbechar
baruero	barbero
baruiponiente	barbiponiente
baveando	babeando
bavear	babear
bavoso	baboso
bebedor	bebedor
bedija	vedija
bendimia	vendimia
bengarse	vengarse
berano	verano
berde	verde
berdes	verdes
berdad	verdad
berdadero	verdadero
berdugo	verdugo
berduras	verduras
bergüenzas	vergüenzas
bermellon	bermellón
berraco	verraco
berruga	verruga
berrugas	verrugas
berrugosa	verrugosa
berrugoso	verrugoso
bestido	vestido
bestidura	vestidura
bestir	vestir
bestirse	vestirse
betun	betún
beva	beba
beinte	veinte
bevedor	bebedor
bevedizos	bebedizos
bever	beber
bevida	bebida
bién	bien
beer	ver
bida	vida
bidrio	vidrio
biexos	viejos
biniese	viniese
bisiones	visiones
bista	vista
bituperado	vituperado
bivir	vivir
bivienda	vivienda
bizcaíno	vizcaíno
bibora	víbora
boces	voces
bofeton	bofetón
bohio	bohío
bohios	bohíos
bolador	volador
bolando	volando
bolante	volante
bolber	volver
bolberse	volverse
boltear	voltear
bolteador	volteador
boluntad	voluntad
boluntaria	voluntaria
bolverse	volverse
borron	borrón
bordon	bordón
botin	botín
boton	botón
bovo	bobo
braba	brava
braverserse	bravearse
brasos	brazos
brebe	breve
buhio	bohío
buho	búho
buelcos	vuelcos
buela	vuela
buelque	vuelque
buelvo	vuelvo
buen	buen
buén	buen
cabezeando	cabeceando
capazete	capacete
capazidad	capacidad
caxcabeles	cascabeles
ceruiz	cerviz
cozerlos	cocerlos
cozimiento	cocimiento
cónuiene	conviene
contradiziendo	contradiciendo
contradiziéndo	contradiciendo
contradiziéndole	contradiciéndole
descozida	descosida
desuirgar	desvirgar
dezirle	decirle
dezirme	decirme
dezis	decís
dizén	dicen
dulzes	dulces
debisa	divisa
ebdomada	hebdómada
ebdomadario	hebdomadario
emblanquezer	emblanquecer
embra	hembra
embrauecerlo	embravecerlo
embrabecer	embravecer
embrabecerse	embravecerse
embrabecido	embravecido
embrabecimiento	embravecimiento
embeber	embeber
embever	embeber
embevida	embebida
enbasar	envasar
enbiada	enviada
enbiado	enviado
enbiar	enviar
encoruado	encorvado
encruzijadas	encrucijadas
enflaquezido	enflaquecido
enflaquezimiento	enflaquecimiento
enmohezerse	enmohecerse
enquadernado	encuadernado
enquadernador	encuadernador
enquadernar	encuadernar
enquadra	encuadra
enriquezedor	enriquecedor
enriquezer	enriquecer
enrrejado	enrejado
enrrejar	enrejar
enrriquecer	enriquecer
enrriquecimiento	enriquecimiento
ensordezer	ensordecer
entristezer	entristecer
enzino	encino
esparzimiento	esparcimiento
esparzio	esparció
esquadra	escuadra
esquadron	escuadrón
escaruador	escarbador
escaruadientes	escarbadientes
estoruado	estorbado
fortalezerse	fortalecerse
frunzida	fruncida
frunzido	fruncido
guizada	guisada
guizado	guisado
hazersele	hacérsele
hazerles	hacerles
hazía	hacía
hizierón	hicieron
hombrezillo	hombrecillo
hozico	hocico
induze	induce
induzido	inducido
induzirlo	inducirlo
introduzir	introducir
inuierno	invierno
lauador	lavador
lazerada	lacerada
lombrizes	lombrices
maldize	maldice
maldiziendo	maldiciendo
maldiziendolo	maldiciéndolo
mezes	meses
mortezina	mortecina
mortezino	mortecino
obeja	oveja
obejas	ovejas
obejero	ovejero
obejuno	ovejuno
obedezer	obedecer
orin	orín
ormiga	hormiga
ormigas	hormigas
padezer	padecer
pauón	pavón
perdizes	perdices
pertinazia	pertinacia
pesquiza	pesquisa
pesquizar	pesquisar
pezquiza	pesquisa
pinzel	pincel
preuiene	previene
produzir	producir
quadrarme	cuadrarme
quadriles	cuadriles
razero	rasero
regozija	regocija
regozijan	regocijan
regozijen	regocijen
regozijo	regocijo
reluziente	reluciente
renouada	renovada
renzillas	rencillas
renzillosos	rencillosos
rénzilla	rencilla
rred	red
rrelumbrante	relumbrante
rrica	rica
rricamente	ricamente
rrodela	rodela
rropa	ropa
rresonando	resonando
rozillo	rollizo
satisfaze	satisface
satisfaziendo	satisfaciendo
sauzeda	sauceda
senbrado	sembrado
senzillamente	sencillamente
senzillas	sencillas
torzer	torcer
torzida	torcida
traduzida	traducida
viejezita	viejecita
zebolla	cebolla
zelos	celos
zentencia	sentencia
zepo	cepo
zerdas	cerdas
zirugia	cirugía
zirujano	cirujano
abito	hábito
abuen	a buen
abuena	a buena
abusion	abusión
acaezerme	acaecerme
acozeador	acoceador
acozeando	acoceando
acozear	acocear
aizquierdas	a izquierdas
amanezer	amanecer
ambar	ámbar
anochezer	anochecer
avecindados	avecindados
avezindamiento	avecindamiento
azemilero	acemilero
bacin	bacín
bale	vale
baporo	vapor
bapor	vapor
barvacana	barbacana
bastecer	abastecer
bautizmo	bautismo
bela	vela
bender	vender
bilingue	bilingüe
bisahuelo	bisabuelo
bobeda	bóveda
bobedad	bobería
boberia	bobería
bofetear	abofetear
bomitar	vomitar
bolatil	volátil
bolviendola	volviéndola
borzegui	borceguí
bracelete	brazalete
breton	bretón
brunir	bruñir
cóntinuada	continuada
cónseguir	conseguir
donzellas	doncellas
embotamiénto	embotamiento
enronquecimiénto	enronquecimiento
enrredado	enredado
enrredar	enredar
enrramado	enramado
enrramar	enramar
enrramarse	enramarse
ensoberbezer	ensoberbecer
esparzírse	esparcirse
escuadron	escuadrón
heruir	hervir
peruierte	pervierte
regozijar	regocijar
zaquizami	zaquizamí
abalanzandose	abalanzándose
abrego	ábrego
abstienén	abstienen
abstraido	abstraído
abúndancia	abundancia
abadia	abadía
abejon	abejón
abes	aves
aber	haber
abrebiador	abreviador
avezindados	avecindados
baptiza	bautiza
baptizar	bautizar
baptize	bautice
bara	vara
barberia	barbería
barrigon	barrigón
bastardia	bastardía
beneplacito	beneplácito
blánca	blanca
blánco	blanco
brio	brío
burlon	burlón
deseruado	desyerbado
deseruador	desyerbador
deseruada	desyerbada
embaucamiénto	embaucamiento
enrónquecido	enronquecido
enrronquecerse	enronquecerse
erisarse	erizarse
ménguada	menguada
ménguado	menguado
obedeceras	obedecerás
obedeciéndo	obedeciendo
obediénteménte	obedientemente
origén	origen
oyerón	oyeron
persiguiendolo	persiguiéndolo
quierén	quieren
abas	habas
abien	a bien
aborescente	arborescente
aborrcer	aborrecer
aborresco	aborrezco
abuado	abuhado
abahada	vahada
abahar	vahar
abahamiento	vahamiento
abrebiada	abreviada
abrebiadura	abreviatura
abrebiar	abreviar
abrebiado	abreviado
abregjo	ábrego
abrotar	brotar
abundamente	abundantemente
adezir	a decir
adondequier	adondequiera
alaguien	alguien
alanzear	alancear
alanzeado	alanceado
alanzeador	alanceador
allguien	alguien
abolorio	abolengo
artifisioso	artificioso
conjectura	conjetura
conjecturas	conjeturas
freir	freír
idem	ídem
impacibilidad	impasibilidad
mecanica	mecánica
mecanicas	mecánicas
monesterio	monasterio
official	oficial
officiales	oficiales
peruetano	peruétano
prenosticar	pronosticar
sarten	sartén
taverna	taberna
tavernas	tabernas
almazén	almacén
ambitentales	ambientales
aquirir	adquirir
asi	así
azepillador	acepillador
azuzena	azucena
baboza	babosa
bacucar	bazucar
bacija	vasija
baculo	báculo
bagamundo	vagamundo
bahar	vahear
baina	vaina
baiben	vaivén
balla	vaya
balle	valle
balza	balsa
bana	vana
banas	banas
baptizador	bautizador
baptizan	bautizan
baptizarlo	bautizarlo
baptizarse	bautizarse
baptizo	bautizo
baruo	barbo
baruacana	barbacana
baruada	barbada
barueria	barbería
baruudo	barbudo
barenar	barrenar
barnisador	barnizador
barnizam	barnizamiento
basija	vasija
benerficio	beneficio
beneficiio	beneficio
benefico	beneficio
bereda	vereda
betum	betún
beyota	bellota
bezes	veces
bidas	vidas
bilma	bizma
bilmar	bizmar
bimbres	mimbres
blándear	blandear
blándo	blando
bocarriva	bocarriba
bodeda	bóveda
bolliciar	bulliciar
bollicio	bullicio
bolza	bolsa
boracho	borracho
borbujear	burbujear
bosar	vomitar
gomitar	vomitar
lomitar	vomitar
enrriscarse	enriscarse
vacija	vasija
brabo	bravo
brebedad	brevedad
brebes	breves
brunirse	bruñirse
burbugear	burbujear
cezeoso	ceceoso
comenze	comencé
complazedor	complacedor
constuir	construir
cruzijada	crucijada
desauziar	desahuciar
desemboluedor	desenvolvedor
destuir	destruir
disfraze	disfraz
dozientos	doscientos
embachado	empachado
embarasar	embarazar
embarasarse	embarazarse
embarbasacado	embarbascado
embaruascar	embarbascar
embevecerse	embebecerse
embevecido	embebecido
enbarrar	embarrar
enborrachar	emborrachar
enborracharse	emborracharse
encoruadura	encorvadura
enflaquezerse	enflaquecerse
enretorno	en retorno
enrriquecedor	enriquecedor
enrriquesido	enriquecido
enrrollar	enrollar
enrriscado	enriscado
enrronquecido	enronquecido
enrronquecimiento	enronquecimiento
enrroscada	enroscada
enrroscarse	enroscarse
erguira	erguir a
escozimiénto	escocimiento
guizan	guisan
guizar	guisar
hoze	hoz
maziza	maciza
mazizar	macizar
melizina	medicina
miezes	mieses
monazillo	monacillo
obcceno	obsceno
oblligatoria	obligatoria
obsenas	obscenas
obaraja	o baraja
operseguir	o perseguir
pizina	piscina
rezelo	recelo
senzillez	sencillez
sinzelar	cincelar
venzer	vencer
abartimiento	abatimiento
abartirse	abatirse
abaz	habas
abeber	a beber
aberiguador	averiguador
abiendo	habiendo
abisa	avisa
ablen	hablen
abodas	a bodas
abonandola	abonándola
abriendola	abriéndola
ahuir	a huir
azirse	asirse
baruechada	barbechada
baruechado	barbechado
baruechador	barbechador
baruechan	barbechan
baruecho	barbecho
barvaro	bárbaro
basallo	vasallo
baseja	vasija
bastantemte	bastantemente
bastatemente	bastantemente
batizar	bautizar
bauptizo	bautizo
bautisma	bautismo
ballientes	valientes
beladores	veladores
bellosa	vellosa
belloso	velloso
bendicidor	bendecidor
bendto	bendito
benficio	beneficio
benificio	beneficio
benefie	beneficie
benefiiar	beneficiar
benefisios	beneficios
benerficiar	beneficiar
beniuolencia	benevolencia
berdecica	verdecica
berjuco	bejuco
beteada	veteada
betada	veteada
beudo	beodo
beuio	bebió
bevo	bebo
bianda	vianda
bieja	vieja
bienauenturada	bienaventurada
biento	viento
bilmar	bizmar
birgen	virgen
bisión	visión
bivar	vivar
biñas	viñas
bladas	blandas
blano	blanco
blanquerino	blanquecino
bobedas	bóvedas
bodeguenero	bodeguero
bolliciosa	bulliciosa
bollicioso	bullicioso
bolson	bolsón
bomito	vomito
bonica	bonita
borraro	borrar o
borregon	borregón
bosear	vocear
boslador	bordador
boslandera	labrandera
botixa	botija
boverme	moverme
brabear	bravear
brabeza	braveza
brazeñete	brazalete
breuajes	brebajes
bruesos	gruesos
buatismo	bautismo
bucando	buscando
buseando	buceando
bíbora	víbora
cavezera	cabecera
conbatida	combatida
conseguiente	consiguiente
conseguientemente	consiguientemente
contruir	construir
contruirse	construirse
coruada	corvada
coruadas	corvadas
cozedura	cocedura
cozerse	cocerse
cozio	coció
desmenuzedo	desmenuzado
desparziendo	desparciendo
desyunzidos	desuncidos
ebano	ébano
embarnizam	embarnizamiento
embaruascado	embarbascado
emborachar	emborrachar
embrabecimeinto	embravecimiento
embricar	embrocar
embrogadura	embrocadura
enbalde	en balde
enbarazado	embarazado
enbarra	embarra
enbarradura	embarradura
enbaucado	embaucado
enbaucar	embaucar
enblanquecerse	emblanquecerse
enblanquecimiento	emblanquecimiento
enbriagante	embriagante
enbriagó	embriagó
ermar	yermar
enhazer	en hacer
enhumodezer	humedecer
enlaquezimiento	enloquecimiento
enrreda	enreda
enrredador	enredador
enrredamiento	enredamiento
enrrejada	enrejada
enrriquecido	enriquecido
enrriquezedor	enriquecedor
enrriscada	enriscada
enrronquesido	enronquecido
enrronquesimiento	enronquecimiento
enrrosar	enrosar
enrrubiados	enrubiados
escazeza	escasez
escozerme	escocerme
escriuir	escribir
escurezer	oscurecer
esparze	esparce
esparzirle	esparcirle
guadarse	guardarse
guiron	girón
hazeme	hazme
hazesor	hacedor
hiruiendo	hirviendo
hyerva	hierba
hyerve	hierve
ierta	cierta
lanze	lance
lohaze	lo hace
melancolize	melancolice
nuuada	nubada
obcenos	obscenos
obececer	obedecer
obedencia	obediencia
obedercer	obedecer
obedesco	obedezco
obedesida	obedecida
obervar	observar
obfuscarse	ofuscarse
oblibar	obligar
obligandose	obligándose
obriros	obreros
oriado	criado
oriejas	orejas
orillade	orillada
ouieren	hubieren
persuadiendolo	persuadiéndolo
persuadille	persuadirle
piedrezicas	piedrecitas
reazimiento	rehazimiento
reprouada	reprobada
reprouado	reprobado
rezelar	recelar
salzera	salsera
seguirdad	seguridad
seruienta	sirvienta
siguiendole	siguiéndole
sostituir	sustituir
trezientos	trescientos
treziéntas	trescientas
tuuieres	tuvieres
vaziamente	vacíamente
vazias	vacías
verdezica	verdecica
vozear	vocear
zepa	cepa
zerrarle	cerrarle
abocanadas	a bocanadas
bahear	vahear
embarañado	enmarañado
embarañar	enmarañar
bollver	volver
boltearle	voltearle
botiller	botillero
bovear	bobear
boveria	bobería
bozador	vomitador
burlal	burlar
burlameinto	burlamiento
burlardo	burlando
burrico	borrico
buua	buba
bvche	buche
compribuir	contribuir
embarado	embarazado
embebercerse	embebecerse
embejecerse	envejecerse
embitarse	embotarse
enbarnescer	embarnecer
enbrabecido	embravecido
enrostro	en rostro
erizarsele	erizársele
gozes	goces
hazese	hácese
hazinda	hacienda
hezer	hacer
mazero	macero
mestruada	menstruada
ohazer	o hacer
oripio	o ripio
oriéntal	oriental
pajezillo	pajecillo
perdize	perdiz
quierer	querer
requiren	requieren
requirida	requerida
sequiere	se quiere
sinzelada	cincelada
yerval	yerbal
boluedor	volvedor
bolbedor	volvedor
bolvedor	volvedor
boluimiento	volvimiento
bolvimiento	volvimiento
buelbe	vuelve
begiga	vejiga
heruiente	herviente
enqualquiera	en cualquiera
abugero	agujero
abeza	cabeza
abracar	abrazar
abrajos	abrazos
abrimiénto	abrimiento
abundasamente	abundantemente
abundosamente	abundantemente
auienta	avienta
azeña	aceña
azeñero	aceñero
azedamiento	acedamiento
ballesterar	ballestear
barreñon	barreñón
barroncoso	barrancoso
baruiroxo	barbirrojo
baruinegro	barbinegro
basandillas	barandillas
bauear	babear
beficio	beneficio
begnino	benigno
bejucose	bejucos
belas	velas
belear	pelear
benda	venda
berzos	berzas
betúm	betún
beubaje	brebaje
beues	bebes
beodez	embriaguez
bibar	vivar
biborrezno	viborezno
biborreznos	viboreznos
bidma	bizma
biene	viene
billettes	billetes
biscocho	bizcocho
biuienda	vivienda
boberias	boberías
bordardo	bordado
bosador	vomitador
bosadura	vomitadura
botilla	botella
bracil	brasil
brebiada	abreviada
buelo	vuelo
destuirse	destruirse
disbribuirse	distribuirse
donezillo	donecillo
emboradura	embotadura
embejezerse	envejecerse
encruelezerse	encruelecerse
enrriquecersce	enriquecerse
ensuziamiento	ensuciamiento
enronquezerse	enronquecerse
enrónquecerse	enronquecerse
enruviados	enrubiados
enruviar	enrubiar
enruviarse	enrubiarse
enrtre	entre
enrucijada	encrucijada
esparzidamente	esparcidamente
guadería	guardería
hazemalo	hace mal
hazerchichones	hacer chichones
haziedor	hacedor
hezedor	hacedor
heruiendola	hirviéndola
injuiriador	injuriador
laguien	alguien
lguien	alguien
morzielago	murciélago
oqualquier	o cualquier
ohazerse	o hacerse
oburlado	o burlado
poluiento	polviento
quieraque	quiera que
regozijadamente	regocijadamente
salzereta	salsereta
sedize	se dice
sehazer	hacerse
soldaduiria	soldadura
sustuir	sustituir
traluzirse	traslucirse
zebratan	cerbatana
zizañia	cizaña
zinbria	cimbra
aqualquier	a cualquier
azezar	acezar
azezido	acezado
azezo	acezo
baldádo	baldado
bandújo	bandujo
bánco	banco
bánquete	banquete
bénditas	benditas
abatimieuto	abatimiento
aplazedor	aplacedor
aplazimiento	aplacimiento
aplazer	aplacer
barragan	barragán
barragania	barraganía
barer	barrer
barrrio	barrio
batioja	batihoja
azige	acije
atierze	alerce
atarreziamente	atar reciamente
atras	atrás
aguila	águila
aguilas	águilas
angel	ángel
angeles	ángeles
arbol	árbol
arboles	árboles
arronjada	arrojada
asabiendas	a sabiendas
baruar	barbar
batei	batey
balsaminacea	Balsaminaceae
bedejas	vedijas
belar	velar
bermegecerse	bermejecerse
biboreznos	viboreznos
básquekbol	básquetbol
buxéta	bujeta
bahuinia	Bauhinia
bombacaeae	Bombacaceae
borthops	Bothrops
bodeguenetra	bodegonera
bolberlo	volverlo
bolbiendola	volviéndola
bolbimiento	volvimiento
bolliciador	bulliciador
bolvedro	volvedor
borni	borní
butey	batey
buelua	vuelva
brucoula	brújula
bromeliacea	bromeliácea
calezilla	calecilla
catiuadero	cautivadero
catiuan	cautivan
cauadura	cavadura
cauello	cabello
cauellos	cabellos
carambano	carámbano
complazimento	complacimiento
comunidd	comunidad
conosida	conocida
comprehender	comprender
comprehenderlo	comprenderlo
corazon	corazón
conquien	con quien
contrahazimiento	contrahacimiento
contradezidor	contradecidor
cuernezillos	cuernecillos
descarriamiénto	descarriamiento
desemboluedura	desenvolvedura
deseruar	desyerbar
deseruadura	desyerbadura
desierua	desyerba
desieruan	desyerban
demas	demás
desparzimiento	desparcimiento
desparzimiénto	desparcimiento
dificil	difícil
dosvezes	dos veces
dragon	dragón
embermejererse	embermejecerse
embeodamento	embriaguez
embeoda	embriaga
embeodan	embriagan
embeodar	embriagar
embeodarse	embriagarse
embeodamiento	embriaguez
embiodar	embriagar
embulta	envuelta
embulto	envuelto
enbeodarse	embriagarse
enbermejecerse	embermejecerse
elada	helada
elos	ellos
embermetercer	embermejecer
famlia	familia
facil	fácil
fructales	frutales
havia	había
haviendo	habiendo
haverle	haberle
imagenes	imágenes
inutil	inútil
landrezillas	landrecillas
ladron	ladrón
leon	león
leziente	reciente
llamao	llamado
yelo	hielo
mahizal	maizal
mahizales	maizales
maiz	maíz
medula	médula
musica	música
mui	muy
nieva	nieve
obar	ovar
publicamente	públicamente
ortaliza	hortaliza
otraa	otra
parescía	parecía
pequeno	pequeño
poluoso	polvoso
porquien	por quien
pajaro	pájaro
pajaros	pájaros
poseera	poseerá
poseeran	poseerán
propriedad	propiedad
publica	pública
quanta	cuánta
raiz	raíz
raton	ratón
reconosida	reconocida
rincon	rincón
rio	río
rios	ríos
relox	reloj
carcel	cárcel
carceles	cárceles
limite	límite
limites	límites
rrelunbrante	relumbrante
relunbrante	relumbrante
rrosas	rosas
subterranea	subterránea
tardio	tardío
tambien	también
tomandolo	tomándolo
tornandolo	tornándolo
tranzadera	trenzadera
tranzado	trenzado
trempa	trampa
torquaza	torcaza
tortola	tórtola
uevo	huevo
vibora	víbora
vozedal	vocedal
vuiere	hubiere
azafran	azafrán
alcon	halcón
alquitran	alquitrán
abellacar	avellacar
abesindarse	avecindarse
abibado	avivado
abiltadamente	aviltadamente
abiltar	aviltar
ablillas	hablillas
adoquiera	adondequiera
arguménto	argumento
atodos	a todos
auctoridad	autoridad
bannas	amonestaciones
banas	amonestaciones
barrañon	barreñón
batia	batía
bausan	bausán
cafe	café
canamo	cáñamo
cantaro	cántaro
cantaros	cántaros
capitan	capitán
caracter	carácter
caratula	carátula
caratulas	carátulas
cañamo	cáñamo
cesped	césped
cespedes	céspedes
comun	común
comunmente	comúnmente
comunion	comunión
complesion	complexión
composision	composición
comprehension	comprensión
cón	con
compas	compás
compasion	compasión
confesion	confesión
conclusion	conclusión
confusion	confusión
conversion	conversión
conuersion	conversión
contraposision	contraposición
circuncision	circuncisión
decision	decisión
decimo	décimo
defension	defensión
deposision	deposición
disension	disensión
disposision	disposición
distinction	distinción
division	división
ejercito	ejército
enella	en ella
én	en
ermadura	armadura
escaruada	escarbada
expresion	expresión
escolastico	escolástico
fabula	fábula
fabulas	fábulas
fantastico	fantástico
gavilan	gavilán
genero	género
generos	géneros
guada	guarda
habito	hábito
habitos	hábitos
huego	fuego
hechar	echar
hazera	acera
imagén	imagen
impresion	impresión
intelligencia	inteligencia
introduction	introducción
introductión	introducción
monges	monjes
lagrima	lágrima
lagrimas	lágrimas
lampara	lámpara
lamparas	lámparas
lamitad	la mitad
liquido	líquido
liquidos	líquidos
halcon	halcón
ingles	inglés
jabali	jabalí
jardin	jardín
jazmin	jazmín
martir	mártir
mascara	máscara
medico	médico
medicos	médicos
murezillos	murecillos
imposision	imposición
inquisision	inquisición
jusion	jusión
lision	lesión
numero	número
numeros	números
ocasion	ocasión
occasion	ocasión
ofension	ofensión
omision	omisión
organo	órgano
organos	órganos
parpado	párpado
parpados	párpados
pildora	píldora
polvora	pólvora
poluora	pólvora
posesion	posesión
postrimeria	postrimería
pasion	pasión
pension	pensión
permision	permisión
pénsion	pensión
persuasion	persuasión
platica	plática
platicas	pláticas
practicas	prácticas
preposision	preposición
prision	prisión
prolixa	prolija
prolixo	prolijo
prolixidad	prolijidad
proposision	proposición
procesion	procesión
profesion	profesión
proposito	propósito
propositos	propósitos
provision	provisión
reprehension	reprehensión
reprehénsion	reprehensión
remision	remisión
religion	religión
rogasion	rogación
sabado	sábado
segun	según
sepaga	se paga
sermon	sermón
silaba	sílaba
silabas	sílabas
termino	término
terminos	términos
titulo	título
titulos	títulos
ultimo	último
union	unión
vision	visión
buzano	buzo
porsi	por sí
punsion	punición
quese	que se
queriendole	queriéndole
conuertimiento	convertimiento
aflición	aflicción
ahirmar	afirmar
amarañar	enmarañar
asconder	esconder
asconderse	esconderse
ascondo	escondo
augmentar	aumentar
benedizo	venedizo
callentada	calentada
callentando	calentando
callentamiento	calentamiento
callentar	calentar
callentarse	calentarse
callente	caliente
consejar	aconsejar
costreñir	constreñir
decender	descender
descendir	descender
desatapada	destapada
desatapado	destapado
desatapar	destapar
desataparse	destaparse
desatapadura	destapadura
diciplinar	disciplinar
difinir	definir
diminuir	disminuir
discerner	discernir
disfamar	difamar
disfamarse	difamarse
distilar	destilar
escallentador	calentador
escallentar	calentar
escura	oscura
escuras	oscuras
escurecer	oscurecer
escurecerse	oscurecerse
escurecimiento	oscurecimiento
escureserse	oscurecerse
escuricerse	oscurecerse
escuridad	oscuridad
escuro	oscuro
escuros	oscuros
escusar	excusar
estropezar	tropezar
enduresido	endurecido
emendar	enmendar
enhumedecer	humedecer
estendida	extendida
expremir	exprimir
haverse	haberse
itropezar	tropezar
logar	lograr
mesclar	mezclar
mutansa	mudanza
oluidada	olvidada
perfection	perfección
polir	pulir
recebir	recibir
rehazimiento	rehacimiento
sorze	sorce
surcir	zurcir
tractar	tratar
devisar	divisar
veer	ver
zenith	zenit
zerro	cerro
acara	a cara
amanera	a manera
arregasarse	arregazarse
ayuntarase	ayuntarse
cónjunctión	conjunción
destamanera	de esta manera
delque	del que
deti	de ti
desuentura	desventura
desuenturado	desventurado
enello	en ello
enellos	en ellos
enlugar	en lugar
emmarañar	enmarañar
envejeserse	envejecerse
flore	flores
alhombra	alfombra
almoada	almohada
almidon	almidón
admirandose	admirándose
añadio	añadió
atreuer	atrever
atreuerseme	atrevérseme
atreuera	atreverá
caveza	cabeza
cavellera	cabellera
cavello	cabello
cavellos	cabellos
caida	caída
cayo	cayó
colchon	colchón
cubrén	cubren
delicto	delito
diciplina	disciplina
diciplinado	disciplinado
illustre	ilustre
impropriamente	impropiamente
inaduertencia	inadvertencia
interjection	interjección
interogatiue	interrogativo
cometio	cometió
conexo	conejo
descobrir	descubrir
descobrirse	descubrirse
descubrise	descubrirse
delvando	del bando
desuergonzar	desvergonzar
desuergonzarse	desvergonzarse
deotro	de otro
enlasado	enlazado
escripto	escrito
frias	frías
hacaydo	ha caído
huyo	huyó
moyera	mollera
odelo	o de lo
oguai	o guay
parred	pared
pargamino	pergamino
parese	parece
perzona	persona
perzonas	personas
pequenas	pequeñas
pequenitos	pequeñitos
phrase	frase
preteritos	pretéritos
propriamente	propiamente
pénsar	pensar
poniendose	poniéndose
procurandolo	procurándolo
saver	saber
sele	se le
simiénte	simiente
slen	salen
sobrel	sobre el
solto	soltó
sequexa	se queja
sentenciado	sentenciado
séntenciado	sentenciado
támbien	también
estan	están
vejesuela	vejezuela
vejes	vejez
verguenzas	vergüenzas
vestimienteo	vestimiento
virhuelas	viruelas
zarna	sarna
ansi	así
bezar	besar
hermitaño	ermitaño
selezte	celeste
sonrie	sonríe
vando	bando
vanda	banda
vandero	bandero
porsu	por su
ó	o
aca	acá
alla	allá
alli	allí
aqui	aquí
aculla	acullá
desu	de su
desus	de sus
"""


REPLACEMENTS: dict[str, tuple[str, str]] = {}
for line in PAIRS.strip().splitlines():
    old, new = line.split("\t", 1)
    REPLACEMENTS[old] = (new, "old_spanish_orthography_cluster")


TOKEN_RE = re.compile(
    rf"(?<![{LETTER}])("
    + "|".join(re.escape(token) for token in sorted(REPLACEMENTS, key=len, reverse=True))
    + rf")(?![{LETTER}])",
    re.I,
)


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def restore_single_bracket_letter(match: re.Match[str]) -> str:
    bracketed = match.group(1)
    following = match.group(2)
    if bracketed.lower() == following.lower():
        return bracketed
    return bracketed + following


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source in SKIP_SOURCES:
        return text, []

    reasons: list[str] = []
    new = text

    updated = SINGLE_BRACKET_LETTER_RE.sub(restore_single_bracket_letter, new)
    if updated != new:
        new = updated
        reasons.append("single_bracket_letter")

    updated = DOLLAR_S_RE.sub("s", new)
    if updated != new:
        new = updated
        reasons.append("long_s_artifact")

    for pattern, replacement, reason in PHRASE_REPLACEMENTS:
        updated = pattern.sub(lambda match: preserve_case(match.group(0), replacement), new)
        if updated != new:
            new = updated
            reasons.append(reason)

    for pattern, replacement, reason in EXPAND_REPLACEMENTS:
        updated = pattern.sub(
            lambda match: preserve_case(match.group(0), match.expand(replacement)),
            new,
        )
        if updated != new:
            new = updated
            reasons.append(reason)

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

    new = TOKEN_RE.sub(replace_token, new)

    updated = DUPLICATE_BRACKET_RE.sub(r"\1", new)
    if updated != new:
        new = updated
        reasons.append("duplicate_bracket_gloss")

    cleaned = MULTISPACE_RE.sub(" ", new).strip()
    if cleaned != new:
        new = cleaned
        reasons.append("multispace")

    return new, sorted(set(reasons))


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            source = row.get("Fuente") or ""
            old = row.get("Traducción") or ""
            new, reasons = clean(old, source)
            row_replacement = ROW_TRANSLATION_REPLACEMENTS.get(row.get("record_id") or "")
            if row_replacement and source not in SKIP_SOURCES and old != row_replacement:
                new = row_replacement
                reasons = sorted(set(reasons + ["row_context_translation"]))
            if new != old:
                row["Traducción"] = new
                report.append(
                    {
                        "record_id": row.get("record_id"),
                        "source": source,
                        "lemma": row.get("Texto estandarizado"),
                        "reasons": reasons,
                        "old_translation": old,
                        "new_translation": new,
                    }
                )
            rows.append(row)

    if not DRY_RUN:
        tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(tmp, DATA_PATH)

        with REPORT_PATH.open("w", encoding="utf-8") as fh:
            for item in report:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH if not DRY_RUN else '(dry-run)'}")


if __name__ == "__main__":
    main()
