#!/usr/bin/env python3
from __future__ import annotations

import gzip
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "non_wimmer_old_spanish_intervocalic_u_report.jsonl"
DRY_RUN = os.environ.get("DRY_RUN") == "1"


LETTER = "A-Za-zÁÉÍÓÚÜÑáéíóúüñÇç"
MULTISPACE_RE = re.compile(r"[ \t\r\f\v]+")
SKIP_SOURCES = {"1992 Karttunen"}


PHRASE_REPLACEMENTS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\blleuarla(\s+carga)\b", re.I), r"llevar la\1", "old_intervocalic_u_phrase"),
    (re.compile(r"\boatrauesada\b", re.I), "o atravesada", "old_intervocalic_u_phrase"),
]


PAIRS = """
abeuer	a beber
abiuar	avivar
abiuir	a vivir
abiua	aviva
abouado	abobado
abreuiada	abreviada
abreuiador	abreviador
abreuiar	abreviar
aceuilado	acevilado
aceuilarse	acevilarse
adiue	adive
adiuinada	adivinada
adiuinando	adivinando
adiuinar	adivinar
adiuino	adivino
aduersatiua	adversativa
agrauiado	agraviado
agrauiar	agraviar
agrauiarse	agraviarse
agrauio	agravio
algiue	aljibe
alcauala	alcabala
alcaualero	alcabalero
aliuiada	aliviada
aliuiado	aliviado
aliuiar	aliviar
aliuio	alivio
alreues	al revés
aprouada	aprobada
aprouador	aprobador
aprouar	aprobar
aprouechar	aprovechar
aprouechado	aprovechado
aprouechamiento	aprovechamiento
aprouechara	aprovechara
aprouecho	aprovecho
atauiada	ataviada
atauiado	ataviado
atauiador	ataviador
atauiar	ataviar
atauiarse	ataviarse
atauiarse	ataviarse
atauios	atavíos
atauio	atavío
atreuida	atrevida
atreuidamente	atrevidamente
atreuimiento	atrevimiento
atreuiose	atreviose
atreuerse	atreverse
atrauesado	atravesado
atrauesador	atravesador
atrauesar	atravesar
atrauesarse	atravesarse
atrauesarseme	atravesárseme
atrauersarse	atravesarse
atrauesado	atravesado
atrauesador	atravesador
atrauesar	atravesar
atrauillados	atravillados
auacates	aguacates
auacatl	aguacate
auaricia	avaricia
auariento	avariento
auariénto	avariento
aueja	abeja
auejas	abejas
auenado	avenado
auenencia	avenencia
auenida	avenida
auenidas	avenidas
auenirse	avenirse
auentadero	aventadero
auentado	aventado
auentajada	aventajada
auentajadamente	aventajadamente
auentajado	aventajado
auentajar	aventajar
auentar	aventar
auéntar	aventar
auentarse	aventarse
auentura	aventura
aueriguado	averiguado
aueriguador	averiguador
aueriguar	averiguar
auergonzado	avergonzado
auergonzamiento	avergonzamiento
auergonzar	avergonzar
auellacar	avellacar
auellanas	avellanas
auelo	abuelo
auela	abuela
auezindado	avecindado
auezindamiento	avecindamiento
auezindarse	avecindarse
auezes	a veces
avezes	a veces
auinagrar	avinagrar
auinagrarse	avinagrarse
auisada	avisada
auisadamente	avisadamente
auisador	avisador
auisando	avisando
auisar	avisar
auisatiuo	avisativo
auiso	aviso
baua	baba
bauas	babas
bauaza	babaza
bauoso	baboso
beue	bebe
beuen	beben
beuedor	bebedor
beuer	beber
bienauenturado	bienaventurado
bienauenturados	bienaventurados
bienauenturanza	bienaventuranza
biua	viva
biue	vive
biuen	viven
biuén	viven
biuar	vivar
biuidora	vividora
biuimos	vivimos
biuir	vivir
biuora	víbora
biuoras	víboras
biuorezno	viborezno
biuoreznos	viboreznos
boueda	bóveda
bouo	bobo
braua	brava
brauas	bravas
brauear	bravear
braueza	braveza
brauo	bravo
breua	breva
breuaxe	brebaje
breuedad	brevedad
breuaje	brebaje
breuiario	breviario
buuas	bubas
buuoso	buboso
calauerna	calavera
captiuado	captivado
captiuar	captivar
cartauon	cartabón
cauada	cavada
cauado	cavado
cauador	cavador
caualga	cabalga
caualleria	caballería
caualleriza	caballeriza
cauallerizo	caballerizo
cauallero	caballero
caualleros	caballeros
cauallillo	caballillo
cauallo	caballo
cauar	cavar
cauando	cavando
caua	cava
cauaña	cabaña
cauernoso	cavernoso
cauerna	caverna
ceuar	cebar
ceuada	cebada
ceuado	cebado
ceuon	cebón
ceuo	cebo
ceuilidad	civilidad
ceuilmente	civilmente
clauar	clavar
clauazon	clavazón
clauellina	clavellina
clauo	clavo
conchauar	conchavar
cónchauar	conchavar
conualecer	convalecer
conualeciente	convaleciente
conuencido	convencido
conueniente	conveniente
conuiene	conviene
conuenir	convenir
conuenirle	convenirle
conuertido	convertido
conuertir	convertir
conuertirse	convertirse
couarde	cobarde
couardes	cobardes
couardia	cobardía
cueua	cueva
cueuas	cuevas
dadiua	dádiva
dadiuas	dádivas
dadiuoso	dadivoso
denueuo	de nuevo
desaprouechar	desaprovechar
desaprouechada	desaprovechada
desaprouechado	desaprovechado
desaprouechamiento	desaprovechamiento
desatauiar	desataviar
desatauiarse	desataviarse
desatrauesado	desatravesado
desembrauecido	desembravecido
desfauorecedor	desfavorecedor
desfauorecer	desfavorecer
desfauorecido	desfavorecido
desgouernado	desgobernado
desgouernamiento	desgobernamiento
deslauada	deslavada
deslauarse	deslavarse
desouar	desovar
despauilada	despabilada
despauilador	despabilador
despauiladura	despabiladura
despauilar	despabilar
detraues	de través
deue	debe
deuer	deber
deuanar	devanar
deuanear	devanear
deuo	debo
dezinueue	diecinueve
diffauor	disfavor
diluuio	diluvio
diuersa	diversa
diuersidad	diversidad
diuersorio	diversorio
diuertir	divertir
diuidida	dividida
diuididamente	divididamente
diuidido	dividido
diuidir	dividir
diuidirle	dividirle
diuidirse	dividirse
diuiesos	diviesos
diuisa	divisa
diuision	división
diuorcio	divorcio
diuulga	divulga
diuulgación	divulgación
diuulgada	divulgada
diuulgar	divulgar
diuulgarse	divulgarse
embouecerse	embobecerse
embrauecer	embravecer
embrauecerse	embravecerse
embrauecido	embravecido
émbrauecida	embravecida
embrauecimiento	embravecimiento
embeue	embebe
embeuer	embeber
embeuerse	embeberse
embeuida	embebida
embeuecido	embebecido
embeuiendose	embebiéndose
enbaydor	embaidor
enclauar	enclavar
endisfauor	en disfavor
enuarado	envarado
enuaramiento	envaramiento
enuararse	envararse
enuegecerse	envejecerse
enuejecer	envejecer
enuejecida	envejecida
enuilecerse	envilecerse
enuio	envío
enuuelto	envuelto
eslauon	eslabón
escauador	excavador
escauadura	excavadura
escauar	excavar
escarauajo	escarabajo
escaruadura	escarbadura
escriuania	escribanía
escriuanias	escribanías
escriuano	escribano
escriuanos	escribanos
escriue	escribe
escriuen	escriben
escreuir	escribir
escriptura	escritura
escripturas	escrituras
especulatiuo	especulativo
esquiua	esquiva
esquiuar	esquivar
estaua	estaba
estauan	estaban
estuuiere	estuviere
euangelio	evangelio
fauor	favor
fauorable	favorable
fauorablemente	favorablemente
fauorecedor	favorecedor
fauorecer	favorecer
fauorecida	favorecida
fauorecido	favorecido
garauato	garabato
garaugato	garabato
gauilan	gavilán
gouernador	gobernador
gouernalle	gobernalle
gouernar	gobernar
gouierna	gobierna
graue	grave
graues	graves
grauedad	gravedad
grauemente	gravemente
haua	haba
hauar	habar
hauas	habas
hauia	había
hauian	habían
hueuo	huevo
hueuos	huevos
jaualin	jabalí
jueues	jueves
lauada	lavada
lauadero	lavadero
lauajo	lavajo
lauajal	lavajal
lauan	lavan
lauar	lavar
lauarsela	lavársela
lauarse	lavarse
lauauan	lavaban
lauazas	lavazas
lauaduras	lavaduras
leuadura	levadura
leuantada	levantada
leuantado	levantado
leuantamiento	levantamiento
leuantando	levantando
leuantar	levantar
leuántar	levantar
leuantarse	levantarse
leuante	levante
lleuaba	llevaba
lleuaua	llevaba
lleua	lleva
lleuador	llevador
lleuado	llevado
lleuando	llevando
lleuar	llevar
lleuarla	llevarla
lleuarme	llevarme
lleue	lleve
llaue	llave
llouiznar	lloviznar
llouer	llover
llueue	llueve
lluuia	lluvia
liuiana	liviana
liuianamente	livianamente
liuianaménte	livianamente
liuiano	liviano
liuianos	livianos
marauilla	maravilla
marauillado	maravillado
marauillarse	maravillarse
marauillas	maravillas
marauillosa	maravillosa
marauillosamente	maravillosamente
marauillosas	maravillosas
marauilloso	maravilloso
matauan	mataban
mouedor	movedor
mouer	mover
mouerse	moverse
mouible	movible
mouido	movido
mouimiento	movimiento
nauaja	navaja
nauajas	navajas
nauajon	navajón
naue	nave
nauegable	navegable
nauegan	navegan
nauegante	navegante
nauegar	navegar
naues	naves
naueta	naveta
nauidad	navidad
nauio	navío
nauios	navíos
neuar	nevar
nieue	nieve
nouela	novela
nouelas	novelas
nouelero	novelero
nouembre	noviembre
nouenas	novenas
noueno	noveno
nouia	novia
nouiembre	noviembre
nouillo	novillo
nouio	novio
nouios	novios
nuue	nube
nuues	nubes
nueue	nueve
nueuo	nuevo
nueua	nueva
nueuos	nuevos
nueuas	nuevas
ochauario	ochavario
octauo	octavo
oliuas	olivas
ouar	ovar
oueja	oveja
ouejas	ovejas
ouiere	hubiere
ouillo	ovillo
pauellon	pabellón
pauesa	pavesa
paues	pavés
pauesada	pavesada
pauilo	pabilo
pauo	pavo
paua	pava
pauon	pavón
perseuerancia	perseverancia
perseuerando	perseverando
perseuerante	perseverante
perseuerar	perseverar
picauiento	picaviento
piuela	pihuela
pluuia	lluvia
preuenido	prevenido
preuenir	prevenir
priuar	privar
priuarle	privarle
prouable	probable
prouada	probada
prouado	probado
prouando	probando
prouar	probar
prouara	probara
prouecho	provecho
prouechosa	provechosa
prouechosamente	provechosamente
prouechoso	provechoso
proueer	proveer
proueerla	proveer la
proueerse	proveerse
prouincia	provincia
prouision	provisión
prouisor	provisor
prouoca	provoca
prouocada	provocada
prouocado	provocado
prouocador	provocador
prouocamiento	provocamiento
prouocandole	provocándole
prouocar	provocar
prouocarse	provocarse
prueua	prueba
rebiuir	revivir
reboluer	revolver
renouador	renovador
renouamiento	renovamiento
renouar	renovar
renouarse	renovarse
renueuo	renuevo
renueuos	renuevos
reuanada	rebanada
reuanadas	rebanadas
reuende	revende
reuelada	revelada
reuelador	revelador
reuelarse	revelarse
reuerdecer	reverdecer
reuerencia	reverencia
reuerenciado	reverenciado
reuegido	revejido
reues	revés
ruuia	rubia
saliua	saliva
sauandija	sabandija
sobreauiso	sobre aviso
soliuiar	soliviar
souadura	sobadura
souajada	sobajada
souajadura	sobajadura
souajar	sobajar
souar	sobar
suaue	suave
suaueza	suaveza
suaues	suaves
suauidad	suavidad
suauidado	suavidad
suauemente	suavemente
suauidado	suavidad
tauano	tábano
tauerna	taberna
tauernear	tabernear
tauernero	tabernero
todauia	todavía
touillo	tobillo
trauada	trabada
trauajo	trabajo
trauajar	trabajar
trauajosa	trabajosa
trauajoso	trabajoso
trauar	trabar
trauarse	trabarse
traues	través
tuuo	tuvo
abiuado	avivado
abreuiadura	abreviadura
acordaua	acordaba
actiue	active
actiuamente	activamente
acusauan	acusaban
adjectiuo	adjetivo
adornauan	adornaban
adornauán	adornaban
agrauiadamente	agraviadamente
agrauiador	agraviador
aldaua	aldaba
altiuez	altivez
altiuo	altivo
amauan	amaban
anteuenir	antevenir
antuuiamiento	antuviamiento
antuuiarse	antuviarse
aprouecha	aprovecha
aprouechad	aprovechad
aprouecharse	aprovecharse
atauia	atavía
atrauesada	atravesada
atraueso	atravesó
atrauillador	atravillador
auentador	aventador
auentajarse	aventajarse
auentajase	aventajase
auenturarse	aventurarse
auertido	advertido
auergonzador	avergonzador
aueriguada	averiguada
auiesamente	aviesamente
auisándole	avisándole
auezindados	avecindados
azauache	azabache
bauadero	babadero
bauera	babera
beuedizos	bebedizos
bienauenturadamente	bienaventuradamente
bíuora	víbora
bouear	bobear
bouerias	boberías
boueria	bobería
bouedad	bobedad
cascaueles	cascabeles
catiuar	cautivar
catiuado	cautivado
catiuador	cautivador
catiuo	cautivo
cañaueral	cañaveral
cauallete	caballete
cauan	cavan
cauanla	cavan la
ceuil	civil
ceuadero	cebadero
ciuil	civil
conchauada	conchavada
contemplatiuo	contemplativo
contauan	contaban
confusiuamente	confusivamente
criua	criba
criuar	cribar
deuanaderas	devanaderas
deuanado	devanado
deuanador	devanador
deuaneo	devaneo
deuota	devota
deuotamente	devotamente
deuoto	devoto
decauallo	de caballo
demostratiuo	demostrativo
desembrauecerse	desembravecerse
desembrauecimiento	desembravecimiento
desgouernar	desgobernar
diuide	divide
diuididas	divididas
diuieso	divieso
diuiesos	diviesos
disfauor	disfavor
dudaua	dudaba
embouecido	embobecido
embouecimiento	embobecimiento
embeuecerse	embebecerse
enclauada	enclavada
endiuersas	en diversas
engraue	en grave
enruuiada	enrubiada
enruuiados	enrubiados
enruuiar	enrubiar
enruuiarse	enrubiarse
especulatiua	especulativa
esquiuidad	esquividad
esteuado	estevado
estiuar	estivar
estiual	estival
estuuo	estuvo
excesiua	excesiva
festiuidad	festividad
figuratiuamente	figurativamente
fugitiuo	fugitivo
gauillan	gavilán
gouernado	gobernado
gouiernan	gobiernan
hallauan	hallaban
heuilla	hebilla
heuillas	hebillas
heuilleta	hebilleta
houo	bobo
imperatiuo	imperativo
improuiso	improviso
laua	lava
lauado	lavado
leuántado	levantado
lleuandolo	llevándolo
lleuo	llevo
llouerse	lloverse
lluuioso	lluvioso
maceual	macehual
maceuales	macehuales
marauedi	maravedí
matauán	mataban
motiuo	motivo
mouedura	movedura
mouida	movida
mueue	mueve
murmurauan	murmuraban
natiua	nativa
natiuidad	natividad
natiuidades	natividades
niuel	nivel
niuelar	nivelar
nouedad	novedad
nouicio	novicio
nueuamente	nuevamente
ochauada	ochavada
ochauas	ochavas
opinatiuo	opinativo
optatiuo	optativo
oua	ova
ouejuno	ovejuno
pensatiuo	pensativo
perseuerantemente	perseverantemente
perspetiua	perspectiva
preuilegiado	privilegiado
priuarlo	privarlo
priuaste	privaste
promouer	promover
prouee	provee
proueedor	proveedor
proueidamente	proveídamente
prouincial	provincial
pujauante	pujavante
purgatiua	purgativa
rauano	rábano
reuanar	rebanar
relieues	relieves
reuerencial	reverencial
reuelar	revelar
rrelumbraua	relumbraba
rrelunbraua	relumbraba
ruuio	rubio
sacrificauan	sacrificaban
sauadixa	sabandija
sauana	sábana
sauañon	sabañón
seuo	sebo
seuoso	seboso
soliuio	solivio
soliuiadura	soliviadura
substantiuo	sustantivo
tauernas	tabernas
tauernera	tabernera
touaja	toalla
trauando	trabando
trauazon	trabazón
uua	uva
vengatiuo	vengativo
vetatiuo	vetativo
visauelo	bisabuelo
viue	vive
viuir	vivir
vntouillo	tobillo
vocatiuo	vocativo
abouamiento	abobamiento
accusatiuo	acusativo
adeuinándo	adivinando
aljaua	aljaba
aouar	aovar
atauán	ataban
auiesa	aviesa
auenir	avenir
buscaua	buscaba
carcaua	cárcava
eleuarse	elevarse
enseuada	ensebada
entreuenir	entrevenir
oliua	oliva
oneuar	o nevar
oreuénder	o revender
perseuerándo	perseverando
prouena	provena
prouocarme	provocarme
riua	riba
toua	toba
despechugadaaue	despechugada ave
uiuir	vivir
veuo	huevo
"""


REPLACEMENTS: dict[str, tuple[str, str]] = {}
for line in PAIRS.strip().splitlines():
    old, new = line.split("\t", 1)
    REPLACEMENTS[old] = (new, "old_intervocalic_u")


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


def clean(value: str, source: str) -> tuple[str, list[str]]:
    text = value or ""
    if source == "2021 Wimmer" or source in SKIP_SOURCES:
        return text, []

    reasons: list[str] = []
    new = text

    for pattern, replacement, reason in PHRASE_REPLACEMENTS:
        replaced = pattern.sub(replacement, new)
        if replaced != new:
            new = replaced
            reasons.append(reason)

    def replace_token(match: re.Match[str]) -> str:
        replacement, reason = REPLACEMENTS[match.group(0).lower()]
        reasons.append(reason)
        return preserve_case(match.group(0), replacement)

    new = TOKEN_RE.sub(replace_token, new)

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
            if source and source != "2021 Wimmer":
                old = row.get("Traducción") or ""
                new, reasons = clean(old, source)
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
