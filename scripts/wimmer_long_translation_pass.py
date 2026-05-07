#!/usr/bin/env python3
import gzip
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data.jsonl.gz"
REPORT_PATH = ROOT / "scripts" / "wimmer_long_translation_report.jsonl"


FIXES = {
    "2021-wimmer:000007": "v.t. tla-., adelgazar una cosa; batir metal. / v.refl. en sentido pasivo, adelgazarse o ser enrollado sobre una piedra. / v.t. tē-., dar forma a una persona al crearla.",
    "2021-wimmer:000473": "v.bitrans. tētla-., ocultar algo a alguien; quemar algo para alguien. / v.bitrans. motē-., honorífico: esconder a alguien; matar a alguien. / v.bitrans. motla-., esconder u ocultar algo; hacer fuego para calentarse.",
    "2021-wimmer:001333": "v.bitrans. tētla-., hacer oír algo a alguien; informar o invitar a alguien. / v.bitrans. motla-., entender cosas; honorífico de caqui, oír, escuchar.",
    "2021-wimmer:003097": "v.i., alcanzar, llegar. / v.t. tla-., alcanzar o capturar algo. / v.t. tē-., capturar a alguien, hacerlo prisionero. / v.refl., alcanzar la madurez.",
    "2021-wimmer:003193": "v.t. tē-., seguir o perseguir a alguien. / v.t. tla-., seguir o cruzar un camino o zona; sembrar o rellenar algo. / v.refl. mo-., fingir ser. / v.t. tē-/tla-., enterrar a alguien o algo. / pasivo, ser sembrado o enterrado.",
    "2021-wimmer:003415": "v.refl., ser pobre, sufrir, ser atormentado o tener penas. / v.t. tē-., afligir, maltratar o atormentar a alguien. / v.t. tla-., necesitar algo. / v.impers., sentir dolor, lamentarse.",
    "2021-wimmer:003716": "v.bitrans. motla-., hacer prosperar algo. / v.refl., ser sacrificado. / v.bitrans. tētla-., dedicar algo a alguien. / v.t. tē-., dedicar un día a una deidad; sacrificar u ofrendar por un muerto; poner al sol; honrar el signo natal.",
    "2021-wimmer:005103": "v.refl. m-., ser perfecto, consumado. / con negación, no ser del todo perfecto. / v.i., ser perfecto o llegar a un lugar.",
    "2021-wimmer:005589": "v.t. tē-., separar, dispersar, dividir, desunir o destruir a un pueblo. / v.t. tla-., compartir, dividir, fragmentar o cavar algo. / v.refl. con significado pasivo, ser repartido. / metáfora: examinar la vida de alguien.",
    "2021-wimmer:006132": "v.t. tla-., enfriar, apagar, refrescar o calmar algo; calmar la fiebre; apagar el fuego de un templo. / v.t. tē-., aliviar, ayudar, consolar o calmar a alguien.",
    "2021-wimmer:006486": "v.t. tla-., adornar algo con flores; agregar flores al cacao. / v.t. tē-., alabar, exaltar a alguien. / v.refl., florecer; dejar buen recuerdo.",
    "2021-wimmer:008882": "v.t. tla-., preparar, adornar, disponer, ordenar, sazonar o terminar algo. / v.t. tē-., preparar, adornar u honrar a alguien; abandonar a alguien para siempre. / v.refl., prepararse o adornarse. / v.refl. en sentido pasivo, estar preparado.",
    "2021-wimmer:009032": "v.i., reunirse, estar juntos; comenzar el juego; brotar constantemente; estar erecto y emitir semen; celebrar fiestas juntas. / impers., abundar todo lo necesario para la vida.",
    "2021-wimmer:009145": "v.t. tē-., unir o reunir a la gente. / v.t. tla-., amasar, amontonar, recoger, colocar, establecer o conceder algo. / v.refl., reunirse; estar sentado con seguridad. / v.bitrans. motla-., examinarse, examinar la conciencia. / expresión: determinarse a algo.",
    "2021-wimmer:009870": "Topónimo mítico: lugar celeste adonde van niños muertos durante la lactancia para mamar del árbol de leche antes de volver a la tierra.",
    "2021-wimmer:009905": "v.bitrans. tētla-., poner trampas, dañar o traicionar a alguien; preparar algo para alguien; adornar a alguien. / v.bitrans. motla-., atraer sobre sí mismo; preparar algo. / v.bitrans. motē-., encargar a alguien una función. / v.t. tē-., preparar o adornar a alguien.",
    "2021-wimmer:013585": "v.t. tē-., golpear a alguien con un palo. / v.t. tla-., talar un bosque; partir madera; cavar la tierra o romper terrones con azada o palo.",
    "2021-wimmer:015484": "v.i., irse, partir o huir. / v.t. tē-/tla-., levantar a alguien o algo acostado; separar piedra; componer, improvisar, cantar o entonar. / v.refl., irse, huir, despertarse; pasivo, ser cantado. / v.bitrans. motē-., hacer que alguien se vaya.",
    "2021-wimmer:016216": "v.t. tla-., ofrecer, colocar o depositar algo. / v.t. tē-., ordenar a personas. / v.refl., colocarse, extenderse, presentarse, quedarse quieto o estar de pie. / v.refl. con significado pasivo, ser depositado.",
    "2021-wimmer:016297": "v.t. tē-., fortalecer, endurecer o criar a alguien. / v.t. tla-., hacer crecer, endurecer o criar algo. / v.refl., crecer en edad. / v.i., crecer.",
    "2021-wimmer:019550": "v.t. tē-., conocer a alguien. / v.t. tla-., conocer, probar o experimentar algo. / v.refl., conocerse a sí mismo; ser prudente o sabio. / v.refl. con significado pasivo, ser probado. / v.recipr., reconocerse mutuamente como parientes.",
    "2021-wimmer:020181": "v.t. tē-., hacer sonrojar a alguien. / v.refl., volver la cabeza con asco o ira. / v.t. tla-., destruir, aplanar o dejar caer algo desde una superficie. / metáfora: adquirir mala reputación.",
    "2021-wimmer:021361": "v.bitrans. tētla-., distribuir, compartir o dar algo a varias personas; administrar algo con prefijos indefinidos. / v.bitrans. motla-., compartir algo recíprocamente.",
    "2021-wimmer:021404": "v.t. tla-., taladrar, agujerear, perforar; girar el palo de fuego; encender ritualmente fuego; inaugurar un edificio religioso; garantizar responsabilidad. / v.refl. con significado pasivo, estar girando; ser inaugurado. / v.t. tē-., moldear a alguien. / v.refl., presentarse.",
    "2021-wimmer:021510": "v.t. tla-., ofrecer, colocar o depositar algo. / v.t. tē-., ordenar a personas. / v.refl., colocarse, extenderse, presentarse, quedarse quieto o estar de pie. / v.refl. con significado pasivo, ser depositado.",
    "2021-wimmer:022083": "v.t. tē-., tirar o derribar a alguien al suelo. / v.t. tla-., tirar algo al suelo. / v.i., empujar hacia atrás, alejar o dejar a un lado; arrojarse encima. / v.refl., tirarse al suelo.",
    "2021-wimmer:024535": "v.bitrans. tētla-., hacer que alguien encuentre algo o a alguien. / v.bitrans. motē-., encontrarse con alguien, pelear o discutir. / v.refl., casarse; v.t. tē-., casar a otro. / v.t. tla-., igualar, ajustar o comparar una cosa con otra. / v.impers., casarse colectivamente.",
    "2021-wimmer:025050": "v.t. tla-., torcer, doblar, torturar algo; comerciar. / v.refl., bajar, hablando del sol; ondular o cambiar de rumbo, hablando de agua o río.",
    "2021-wimmer:028601": "v.refl. o v.recipr., separarse, desatarse. / v.t. tla-., separar, despegar, diluir o cambiar algo. / v.bitrans. tētla-., disolver o diluir algo para alguien. / v.bitrans. motla-., vender, trocar algo. / v.t. tē-., desviar a alguien o tomar su lugar.",
    "2021-wimmer:028636": "v.t. tla-., cambiar, permutar o trocar; derretir o diluir algo. / v.t. tē-., sustituir a una persona por otra. / v.refl. con significado pasivo, ser reemplazado. / v.refl., aburrirse, cansarse de esperar o desconfiar.",
    "2021-wimmer:028807": "v.t. tē-., hacer la cama de alguien, servirlo. / v.t. tla-., cargar una bestia; fundar el discurso en una autoridad. / v.bitrans. motē-., hacer de alguien su lecho. / v.bitrans. motla-., hacer una capa, cama o nido; usar algo como fondo.",
    "2021-wimmer:029261": "v.i., envolver tamales en hojas. / v.t. tla-., forjar, inventar, fingir o mentir a sabiendas; pretender; dar forma a algo; envolver tamales; ocultar. / v.t. tē-., crear o modelar a alguien. / v.refl., reunirse; cerrarse, hablando de labios o boca.",
    "2021-wimmer:029268": "v.t. tla-., fundir; tocar un instrumento de viento; declarar guerra; hacer sonar caracolas. / v.refl. en sentido pasivo, hacerse sonar. / v.impers., sonar trompetas. / v.t. tē-., entrenar a alguien. / v.refl., encenderse, brillar.",
    "2021-wimmer:029274": "v.inanim., volverse o estar delgado. / v.t. tē-., hacer adelgazar a alguien. / v.t. tla-., adelgazar o encoger algo. / v.impers., adelgazar; hablar, cantar o gritar con voz clara.",
    "2021-wimmer:030080": "v.t. tla-., enderezar, levantar, poner derecho, colocar o contar algo. / v.t. tē-., colocar a alguien. / v.refl., presentarse, llegar, crecer, aparecer o levantarse, hablando del viento. / v.bitrans. motla-., establecer mutuamente.",
    "2021-wimmer:030771": "v.t. tla-., sacar, extraer, quitar, limpiar; hacer crecer; reproducir la imagen de algo. / v.t. tē-., asemejarse a alguien. / v.refl., liberarse; transformarse, tomar forma o disfrazarse. / v.refl., honorífico de quiza, salir.",
    "2021-wimmer:033051": "v.refl., hablar o entrometerse donde no corresponde. / v.t. tla-., afilar una cuchilla; poner flecos; decorar con borde. / v.t. tē-., dar labios o boca a alguien.",
    "2021-wimmer:033739": "v.t. tē-., apedrear o herir a alguien. / v.t. tla-., golpear, someter o conquistar algo con piedra. / pasivo, ser apedreado.",
    "2021-wimmer:033910": "v.inanim., caer o esparcirse en el suelo. / v.t. tla-., esparcir algo en el suelo. / v.t. tē-., hacer caer a la gente. / v.refl., esparcirse por el suelo; apresurarse; proponerse conquistar.",
    "2021-wimmer:036407": "v.refl. mo-., ponerse sandalias o zapatos. / v.bitrans. motla-., ponerse algo. / v.bitrans. motē-., ponerse las sandalias de alguien. / v.t. tē-., calzar a alguien.",
    "2021-wimmer:036582": "v.t. tla-., aplicar barniz blanco o tiza a algo. / pasivo, ser barnizado de blanco. / v.t. tē-., cubrir a alguien con tiza o barniz blanco. / v.refl., ponerse barniz blanco.",
    "2021-wimmer:036953": "v.t. tla-., introducir, encerrar algo; cobrar tributo. / v.t. tē-., traer, encerrar, recibir o dar bienvenida a alguien. / v.refl., contratarse; honorífico: entrar, introducirse.",
    "2021-wimmer:037161": "v.t. tē-., engendrar, dar a luz o dar forma humana a alguien. / v.impers., tratar humanamente a otro. / v.t. tla-., generar, engendrar, criar o dar forma a algo.",
    "2021-wimmer:037704": "v.t. tla-., introducir, encerrar algo; cobrar tributo. / v.t. tē-., traer, encerrar, recibir o dar bienvenida a alguien. / v.refl., contratarse; honorífico: entrar, introducirse.",
    "2021-wimmer:038643": "v.t. tē-., encerrar a alguien en su casa; dar casa por cárcel; despedir a un súbdito o servidor. / v.refl., establecer el propio hogar. / pasivo, ser arrasado, desterrado, confinado o reducido a pueblo.",
    "2021-wimmer:000514": "v.t. tē-., orar, adular, encantar, fascinar, seducir o atraer a alguien. / v.t. tla-., acariciar o adular algo. / metáfora: recomendarse a alguien.",
    "2021-wimmer:000648": "v.t. tē-., absolver o perdonar a alguien; perdonar pecados. / v.refl., entregarse y obtener remisión de pecados por contrición o confesión.",
    "2021-wimmer:000768": "v.t. tla-., colocar o arreglar cosas; componer canciones o escritos. / v.refl. en sentido pasivo, ser depositado. / v.t. tē-., retener a alguien. / v.refl., sentarse o detenerse en varios lugares.",
    "2021-wimmer:000773": "v.refl., desnudarse. / v.bitrans. motla-., ponerse algo. / v.bitrans. tētla-., despojar a alguien de su ropa; dar reglas u órdenes a alguien. / v.t. tla-., parchear, corregir, añadir, anotar o insertar algo.",
    "2021-wimmer:000852": "recipr. tito-., lanzarse hechizos unos a otros. / v.t. tla-., parchar, remendar o añadir algo. / v.t. tē-., hacer ofrendas a divinidades.",
    "2021-wimmer:000955": "v.t. tla-., teñir o colorear algo de varios colores.",
    "2021-wimmer:001272": "v.t. tla-., oír, escuchar. / v.refl., estar satisfecho. / v.refl. con significado pasivo, ser escuchado u oído.",
    "2021-wimmer:001306": "v.bitrans. tētla-., hacer oír un ruido; hacer que alguien escuche algo; informar o notificar a alguien. / v.bitrans. motla-., honorífico de caqui, escuchar.",
    "2021-wimmer:001612": "v.t. tla-., llevar; responsabilizarse, gobernar. / v.t. tē-., llevar o transportar a alguien. / v.refl., transportarse; permanecer intacto. / v.refl. en sentido pasivo, ser transportado.",
    "2021-wimmer:001753": "v.i., tener pereza, ser perezoso. / v.inanim., estar devastado o abandonado, hablando del suelo; marchitarse, hablando de flores. / v.t. tla-., retractarse, cambiar de opinión, abandonar o desdeñar algo.",
    "2021-wimmer:001822": "v.t. tla-., descuidar hacer una cosa; ser descuidado o indiferente.",
    "2021-wimmer:002546": "v.t. tla-., tirar algo; hacer pasar un periodo de tiempo. / v.t. tē-., tirar a alguien. / v.refl. en sentido pasivo, ser derrotado.",
    "2021-wimmer:002583": "v.t. tē-., agradecer, recompensar o pagar a alguien por un servicio. / v.t. tla-., estimar, apreciar o agradecer algo. / v.refl., ser agradecido.",
    "2021-wimmer:002784": "v.refl., recaer, volver a enfermar; dar a luz. / v.t. tla-., desatar, desarmar o relajar algo.",
    "2021-wimmer:002877": "v.i., avivar el fuego, remover brasas, barrer o limpiar el hogar u horno.",
    "2021-wimmer:008698": "v.t. tē-., punzar, pinchar o sangrar a alguien. / v.t. tla-., pinchar o perforar algo. / v.refl., sangrar. / v.refl. con significado pasivo, ser perforado. / partícula.",
    "2021-wimmer:011581": "v.t. tē-., lastimar a alguien. / v.t. tla-., tener envidia. / v.refl., enfermarse o estar enfermo. / v.recipr. mo-., lastimarse mutuamente.",
    "2021-wimmer:012859": "v.refl., vendar o ceñir la cabeza. / v.t. tē-., vendar o atar la cabeza de alguien. / metáfora: recibir confirmación.",
    "2021-wimmer:012956": "Bueno; de tamaño mediano; breve. / plural: los buenos.",
    "2021-wimmer:016405": "v.i., envejecer; demorarse o detenerse por mucho tiempo. / v.t. tla-., retener o aplazar algo, no devolverlo a tiempo o descuidarlo. / v.t. tē-., retener a alguien mucho tiempo; durar mucho en relación con alguien.",
    "2021-wimmer:018553": "v.t. tē-., unir, atar a alguien. / v.t. tla-., atar algo. / v.refl., ceñirse, abrocharse el cinturón; en sentido pasivo, ser atado. / v.bitrans. motla-., ceñirse con algo. / pasivo, ser amarrado.",
    "2021-wimmer:018918": "v.t. tla-., llevar; responsabilizarse, gobernar. / v.t. tē-., llevar o transportar a alguien. / v.refl., transportarse; permanecer intacto. / v.refl. en sentido pasivo, ser transportado.",
    "2021-wimmer:019677": "v.inanim., darse la vuelta, mezclarse, hablar de varias cosas. / v.impers. tla-., mezclarse o enredarse las cosas.",
    "2021-wimmer:020496": "He aquí; aquí está; toma esto.",
    "2021-wimmer:020860": "v.bitrans. tētla-., dar algo a alguien. / v.bitrans. motla-., darse o atribuirse algo; tomar; darse algo recíprocamente. / v.bitrans. motē-., entregarse a alguien. / indicador del vetativo.",
    "2021-wimmer:020861": "v.bitrans. tētla-., dar algo a alguien. / v.bitrans. motla-., darse o atribuirse algo; tomar; darse algo recíprocamente. / v.bitrans. motē-., entregarse a alguien. / indicador del vetativo.",
    "2021-wimmer:021405": "v.bitrans. tētla-., llevar algo sobre los hombros para alguien. / v.bitrans. motla-., honorífico: llevar sobre los hombros.",
    "2021-wimmer:029756": "v.i., hincharse; tener el cuerpo hinchado. / v.t. tla-., hinchar o inflar algo. / v.t. tē-., inflar a alguien. / v.refl., estar despierto, respirar.",
    "2021-wimmer:030846": "v.inanim., dar un golpe; celebrarse, hablando de fiesta; tener efecto, hablando de alucinógeno. / v.i., salir, levantarse, pasar; descender de alguien; encarnar a alguien.",
    "2021-wimmer:041469": "v.i. + locativo., gobernar. / v.t. tla-., tapar u ocultar algo. / v.t. tē-., tapar o cubrir a alguien. / v.refl., cubrirse.",
    "2021-wimmer:006954": "v.t. tla-., cortar tela o papel. / v.t. tē-., hacer una incisión en alguien. / v.refl. en sentido pasivo, estar inciso. / v.inanim., reventar, abrirse, florecer. / metáfora: alcanzar la madurez; encenderse, brillar.",
    "2021-wimmer:010447": "v.refl., hacerse un escudo o usar algo como protección. / v.bitrans. motē-., hacer de alguien un escudo. / v.bitrans. motla-., hacer un escudo de algo. / v.t. tē-., hacer o dar un escudo a alguien.",
    "2021-wimmer:010612": "v.t. tla-., hacer saltar o explotar algo; dejar escapar una palabra sin querer; ganar en una venta. / v.refl., dejar escapar una palabra sin darse cuenta.",
    "2021-wimmer:018051": "v.bitrans. tētla-., seguir los pasos de alguien. / v.t. tē-., seguir a alguien por la pista. / v.t. tla-., corregir un escrito, investigar, repetir una lección, rehacer una cuenta o recuperar lo propio. / v.refl., examinar la conciencia.",
    "2021-wimmer:018900": "v.t. tē-., hacer sudar a alguien. / v.refl., sudar, transpirar; atraer humedad, hablando de piedras o granos. / metáfora: expresar perturbación grave de sensualidad o pasiones.",
    "2021-wimmer:018901": "v.t. tē-., hacer sudar a alguien. / v.refl., sudar, transpirar; atraer humedad, hablando de piedras o granos. / metáfora: expresar perturbación grave de sensualidad o pasiones.",
    "2021-wimmer:019262": "v.t. tla-., poseer o cuidar una sola cosa. / v.refl., ocuparse sólo de lo propio. / v.bitrans., ocuparse exclusivamente de algo.",
    "2021-wimmer:019826": "v.t. tē-., dañar la cara de alguien. / v.t. tla-., borrar o tachar algo, especialmente escritura. / v.refl. en sentido pasivo, destruirse o desaparecer, hablando de un pueblo o ciudad.",
    "2021-wimmer:020115": "v.t. tla-., ir por camino tortuoso o atajo. / v.refl., tener la cara pintada de rojo.",
    "2021-wimmer:021413": "v.t. tē-., cargar o llevar a alguien; responsabilizarse de alguien. / v.refl., cargar a la espalda; gobernarse. / v.bitrans. tētla-., cargar algo en la espalda de alguien. / v.bitrans. motē-/motla-., llevar a alguien o algo en la espalda.",
    "2021-wimmer:022426": "v.t. tē-., poner a alguien una máscara de hojas de agave. / v.refl., ponerse una máscara de hojas de agave.",
    "2021-wimmer:023028": "v.refl., morir. / v.i., volverse mate, hablando de cerámica.",
    "2021-wimmer:024327": "v.t. tla-., formar la piedra angular; poner tacones a sandalias. / v.refl., ser estimado, tener honra, crédito o poder. / pasivo, ser escuchado o bien visto.",
    "2021-wimmer:027956": "Ornitología: alas. / aletas. / hoja, follaje. / metáfora: pueblo. / plural: alas en sentido metafórico.",
    "2021-wimmer:028287": "v.t. tē-., servir, favorecer, apoyar o ayudar a alguien. / v.refl., cuidarse, ayudarse a sí mismo. / v.bitrans. tētla-., ofrecer algo a alguien.",
    "2021-wimmer:028467": "Que tiene mariposas. / adorno con diseño de mariposas.",
    "2021-wimmer:030329": "v.refl., arrojarse o caer al agua. / impers., ahogarse. / v.t. tē-., tirar a alguien al agua. / v.t. tla-., tirar algo al agua. / metáfora: cometer un gran error; condenar, corregir o destruir por mal gobierno.",
    "2021-wimmer:030561": "v.impers., ser la primera vez que acaece algo.",
    "2021-wimmer:030619": "v.t. tē-., acompañar o seguir a alguien hasta su casa o posada. / v.t. tla-., completar, suplir o añadir lo que falta; hacer que algo llegue o quepa en su lugar.",
    "2021-wimmer:032781": "v.t. tē-., hacer famoso, votar por alguien, designarlo, descubrir culpables, llamar, prohibir o despedir a alguien. / v.t. tla-., prometer, exponer, indicar, fijar, estimar o apreciar algo. / v.refl., ser nombrado, mencionado, pronunciado o proclamado.",
    "2021-wimmer:035092": "v.t. tla-., dejar o abandonar algo. / v.t. tē-., dejar personas en distintos lugares; superar a otros. / v.recipr., separarse, hablando de cónyuges; superarse mutuamente. / v.refl., tranquilizarse, descansar o dejar de hacer algo.",
    "2021-wimmer:037602": "v.i., entrar en las casas.",
    "2021-wimmer:039920": "v.t. tē-., construir o proporcionar una casa a alguien. / v.refl., construir una casa o nido. / v.bitrans. motla-., tomar algo como casa. / v.bitrans. motē-., tomar posesión de la casa de alguien. / impers., construir casa.",
    "2021-wimmer:040430": "Deshierbe, acción de arrancar malas hierbas.",
    "2021-wimmer:040688": "v.i., regañar y mostrar los dientes, dicho del perro; enseñar los dientes.",
    "2021-wimmer:000583": "Tos fuerte.",
    "2021-wimmer:000584": "Tos fuerte.",
    "2021-wimmer:004562": "v.refl., peinarse. / v.t. tē-., peinar a alguien.",
    "2021-wimmer:004631": "v.t. tla-., chupar por el trasero.",
    "2021-wimmer:006376": "Árbol en flor.",
    "2021-wimmer:010866": "Mentonera de cristal.",
    "2021-wimmer:011555": "v.i., haber dormido bien.",
    "2021-wimmer:015590": "v.i., estar afligido o angustiado. / v.t. tē-., ahogar a alguien.",
    "2021-wimmer:015934": "Estornudo.",
    "2021-wimmer:016145": "v.i., entrar.",
    "2021-wimmer:016966": "Que está cubierto de hojas grandes y colgantes, hablando de un árbol.",
    "2021-wimmer:018694": "Y si nadie, o si está ausente.",
    "2021-wimmer:020017": "v.i., estar cubierto o lleno de polvo.",
    "2021-wimmer:021591": "Nombre del dedo medio; tercer dedo desde el pulgar.",
    "2021-wimmer:022278": "Correa para transportar cargas; mecapal. / honorífico: siervo o portero.",
    "2021-wimmer:022875": "El que apoya o favorece. / el que vuelve la cara enfadado.",
    "2021-wimmer:025031": "Momento de retorno.",
    "2021-wimmer:025990": "v.impers., inclinarse profunda y humildemente.",
    "2021-wimmer:027030": "Sacerdote encargado del culto de una diosa.",
    "2021-wimmer:029402": "Ahumado, ennegrecido; color de una cosa ahumada.",
    "2021-wimmer:031536": "v.t. tla-., contar o enumerar una cosa en orden o por rango.",
    "2021-wimmer:032558": "Concha. / color entre morado y naranja.",
    "2021-wimmer:034386": "v.t. tla-., cortar algo con hacha. / v.refl. en sentido pasivo, cortarse con hacha.",
    "2021-wimmer:035382": "Plumas de cuervo.",
    "2021-wimmer:035870": "Chinche grande.",
    "2021-wimmer:036398": "Mamífero carnívoro centroamericano, parecido a la comadreja, nocturno y arbóreo.",
    "2021-wimmer:037288": "Persona que escoge algo único y sin par.",
    "2021-wimmer:038371": "Probado, acreditado.",
    "2021-wimmer:039163": "Espacio de tiempo muy pequeño.",
    "2021-wimmer:040262": "Templo dedicado al dios del pulque.",
    "2021-wimmer:001837": "Ofrenda de brotes jóvenes.",
    "2021-wimmer:002846": "Especie de pan horneado sobre cenizas. / ornamento militar. / nombre personal.",
    "2021-wimmer:004800": "Niño enfermo por la mala leche que chupa. / nombre de un adorno.",
    "2021-wimmer:007954": "v.i., morir al eyacular.",
    "2021-wimmer:008379": "v.i., morir al eyacular.",
    "2021-wimmer:014388": "v.t. tē-., amenazar, intimidar o violentar a alguien. / v.t. tla-., blandir o agitar una lanza u otro objeto.",
    "2021-wimmer:014932": "Estera cubierta con piel de oso.",
    "2021-wimmer:026713": "Acto de ponerse flores.",
    "2021-wimmer:027099": "Alfombra de piel de jaguar.",
    "2021-wimmer:027247": "Tallado en madera de pino.",
    "2021-wimmer:027868": "Carnero, cordero. / constelación de Aries.",
    "2021-wimmer:028470": "Nombre personal femenino.",
    "2021-wimmer:033452": "Nombre de una festividad donde bailan los dioses.",
    "2021-wimmer:042224": "Que tiene cuerpo. / de pecho ancho. / que tiene tronco. / corpulento.",
    "2021-wimmer:037649": "Nombre de un adorno.",
}


def main() -> None:
    rows = []
    report = []

    with gzip.open(DATA_PATH, "rt", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            record_id = row.get("record_id", "")
            old = row.get("Traducción (es)")
            new = FIXES.get(record_id)
            if row.get("Fuente") == "2021 Wimmer" and new and old != new:
                row["Traducción (es)"] = new
                report.append(
                    {
                        "record_id": record_id,
                        "lemma": row.get("Texto estandarizado"),
                        "old_translation_es": old,
                        "new_translation_es": new,
                    }
                )
            rows.append(row)

    tmp = DATA_PATH.with_suffix(DATA_PATH.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    os.replace(tmp, DATA_PATH)

    with REPORT_PATH.open("w", encoding="utf-8") as fh:
        for item in report:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"changed_rows={len(report)}")
    print(f"report={REPORT_PATH}")


if __name__ == "__main__":
    main()
