/// <summary>
/// EL GUION DEL JUEGO: todos los textos de la historia en un solo lugar.
/// Si quieres cambiar un diálogo, cámbialo aquí (no hay que tocar la lógica).
/// N = narración (pantalla negra), D = diálogo (quién, texto), Nota = hoja de papel.
/// Versión 1.5: historia de SIETE (la Máquina 7), la estrella nueva y la charola de galletas.
/// Borrador aprobado: documentacion/md/en_progreso/FASE_01_historia_guion.md
/// </summary>
public static class Guion
{
    public const string Titulo = "TURNO DE NOCHE\nEN EL TALLER";

    /// <summary>Cambia "Tilo" por el nombre del elfo elegido en el menú (y "el elfo" por "la elfa" si es Nieves).</summary>
    public static string Personalizar(string texto)
    {
        if (string.IsNullOrEmpty(texto)) return texto;
        var d = VarianteElfo.Actual;
        if (d.esElfa) texto = texto.Replace("el elfo del turno de noche", "la elfa del turno de noche");
        return texto.Replace("Tilo", d.nombre);
    }
    public const string Subtitulo = "una Navidad diferente";

    // ------------------------------------------------------------------ INTRO
    public static readonly Linea[] Intro =
    {
        Linea.N("<size=34><color=#9fb4ff>Polo Norte</color></size>\n24 de diciembre · 11:47 p.m."),
        Linea.N("Todos los elfos se fueron a dormir temprano.\nMañana es el gran día."),
        Linea.N("Todos...\nmenos <color=#ffd166>Tilo</color>, el elfo del turno de noche."),
        Linea.N("Su tarea era sencilla:\ncuidar el <color=#7dffa1>Gran Árbol</color> hasta que Santa regresara de su último vuelo de prueba.\n\nY una sola regla en el tablero: <color=#ff9a8a>NO tocar la Máquina 7</color>."),
        Linea.N("Tilo fue a la bodega por su chocolate caliente..."),
    };

    /// <summary>Texto grande de la cinemática del chispazo (sin Tilo).</summary>
    public const string Zaap = "¡ZAAAP!";

    public static readonly Linea[] IntroTaller =
    {
        Linea.D("Tilo", "¿...?"),
        Linea.D("Tilo", "¿¡EL ÁRBOL!? ¿Quién tumbó el Gran Árbol?"),
        Linea.D("Tilo", "Piezas por todos lados... y huellas. Huellas pequeñitas... <i>de madera</i>."),
        Linea.D("Tilo", "Y esto dorado en el piso... ¿un pedazo de la estrella? ¡No, no, no! ¡La rompieron!"),
        Linea.D("Tilo", "Sin estrella, Santa no encuentra el camino en esta tormenta."),
        Linea.D("Tilo", "La única que sabe hacer estrellas es la Máquina 7. La descompuesta. ...Genial."),
        Linea.D("Tilo", "Primero armo el árbol. Luego veo qué hago con esa máquina."),
    };

    // ------------------------------------------------------------------ AL TERMINAR CADA ETAPA
    // índice = etapa terminada (0 Maceta, 1 Ramas, 2 Esferas, 3 Guirnalda, 4 Curar a Siete, 5 Fabricar la estrella)
    public static readonly string[] NombreMision =
        { "La Maceta", "Las Ramas", "Las Esferas", "La Guirnalda de Luces", "Curar a Siete", "La Estrella Nueva" };

    public static readonly Linea[][] FinEtapa =
    {
        new[] { // 1 · Maceta: primera descarga (tutorial)
            Linea.D("Tilo", "¡Listo! Ya tenemos dónde plantar el árbol."),
            Linea.N("<size=40>bzzz...   BZZZZT...   ¡ZAP!</size>"),
            Linea.D("Tilo", "¿¡Qué fue eso!? Venía de la Máquina 7..."),
            Linea.D("Siete", "♪ bip... bup... ♪"),
            Linea.D("Tilo", "...¿Me está pidiendo perdón?"),
        },
        new[] { // 2 · Ramas
            Linea.D("Tilo", "Las ramas otra vez en su lugar. El taller vuelve a oler a pino."),
            Linea.D("Tilo", "Pero cada vez que el árbol brilla un poquito más... ellos se ponen más nerviosos."),
        },
        new[] { // 3 · Esferas
            Linea.D("Tilo", "Seis esferas, seis lucecitas."),
            Linea.D("Tilo", "¿Vieron la llave que tienen en la espalda? Cuando la máquina chispea, gira rapidísimo."),
            Linea.D("Tilo", "¡Es ella! La Máquina 7 les está dando cuerda... pero no lo hace a propósito."),
            Linea.D("Tilo", "Está enferma."),
        },
        new[] { // 4 · Guirnalda
            Linea.D("Tilo", "¡La guirnalda funciona! Gracias, amigo reno."),
            Linea.D("Tilo", "Ahora sí: hay que curar a esa máquina."),
            Linea.D("Tilo", "En el cuarto de máquinas, atrás de ella, debe decir qué le falta."),
        },
        new[] { // 5 · Curar a Siete (la melodía y el "de nada" salen al curarla: Guion.SieteCurada)
            Linea.D("Tilo", "Oye, Siete... ¿me ayudas con algo? Necesito una estrella nueva."),
            Linea.D("Siete", "♪ bup! ♪"),
            Linea.D("Tilo", "La rota la subieron hasta lo alto de la repisa del oeste. Unas cajas me ayudarían a subir."),
        },
        new[] { // 6 · Fabricar la estrella
            Linea.D("Tilo", "¡Una estrella nueva! Brilla todavía más que la de antes."),
            Linea.D("Siete", "♪ bup! ♪"),
            Linea.D("Tilo", "Gracias, Siete. Ahora... ¡al árbol!"),
        },
    };

    /// <summary>Al instalar la última refacción (en cualquier momento de la noche): la melodía de gracias de Siete.</summary>
    public static readonly Linea[] SieteCurada =
    {
        Linea.D("Tilo", "¡Funciona! ...¿Eso es una canción?"),
        Linea.D("Siete", "♪ bip-bip-bup ♪"),
        Linea.D("Tilo", "De nada, Siete."),
    };

    /// <summary>Lo que dice Tilo justo antes de jalar la palanca (etapa 6).</summary>
    public static readonly Linea[] JalarPalanca =
    {
        Linea.D("Tilo", "Aquí va la estrella rota... y ahora, ¡la palanca!"),
    };

    // ------------------------------------------------------------------ CASCANUECES
    /// <summary>Lo que dice Tilo cuando ve despertar a un cascanueces (por orden de despertar).</summary>
    public static readonly Linea[][] Despertar =
    {
        new[] { Linea.D("Tilo", "Ese cascanueces... ¿me acaba de MIRAR? Y la llave de su espalda... está girando."),
                Linea.D("Tilo", "Mejor que no me vea cargando piezas. Si me atrapa, seguro las vuelve a esconder.") },
        new[] { Linea.D("Tilo", "¡Otro más! Y este tiene cara de pocos amigos.") },
        new[] { Linea.D("Tilo", "El Capitán... el más grande de todos. Y ahora está cuidando el establo.") },
    };

    public static readonly string[] ConsejoDespertar =
    {
        "Consejo: si un cascanueces te ve, sus ojos brillan en rojo. ¡Corre con [Shift]!",
        "Consejo: junta nieve en una cubeta o un montón y lánzala con [F] para aturdirlos.",
        "Consejo: los cascanueces te OYEN si corres cerca de ellos. Camina despacio a sus espaldas.",
    };

    /// <summary>Gritos de los cascanueces (globito sobre la cabeza + voz). Creen que son los guardias del taller.</summary>
    public static readonly string[] GritoSospecha = { "¿Tac?", "¿Quién anda ahí?" };
    public static readonly string[] GritoVer      = { "¡Alto! ¡Intruso en el taller!", "¡Proteger la caja!", "¡Uno, dos! ¡Uno, dos!" };
    public static readonly string[] GritoAtrapar  = { "¡Prisionero!", "¡A la caja!" };
    public static readonly string[] GritoAturdido = { "¡Me quedé sin cuerda...!", "Brrr... ¿dónde estoy?" };
    public static readonly string[] GritoPerder   = { "Mmm... falsa alarma.", "¡Volver a sus puestos!" };
    public static readonly string[] GritoDescarga = { "¡MÁS CUERDA! ¡MÁS CUERDA!" };

    // ------------------------------------------------------------------ DESCARGAS DE SIETE
    public const string ConsejoDescarga =
        "Consejo: cada descarga de la Máquina 7 les da más cuerda a los cascanueces. Si llega a 10... ¡sobrecarga!";

    /// <summary>Aviso corto de cada descarga (n = número de descarga, 1..10).</summary>
    public static string AvisoDescarga(int n)
    {
        if (n >= 9) return "¡Una descarga más y Siete se sobrecarga! (" + n + "/10)";
        if (n >= 8) return "Siete está muy mal... (" + n + "/10). ¡Cúrala pronto!";
        return "¡ZAP! La Máquina 7 dio una descarga (" + n + "/10)";
    }

    /// <summary>Descarga 10 en Fácil/Medio: solo un susto.</summary>
    public const string AvisoSobrecargaSusto = "¡SOBRECARGA! Se fueron las luces y todos los cascanueces están en alerta...";
    public static readonly Linea[] SobrecargaSusto =
    {
        Linea.D("Tilo", "¡Aguanta, Siete! Ya voy."),
    };

    // ------------------------------------------------------------------ GALLETAS Y CHAROLA
    /// <summary>Las 10 galletas de la charola, en orden: cada forma lleva una letra de NOCHEBUENA.</summary>
    public const string PalabraGalletas = "NOCHEBUENA";
    public static readonly string[] FormaGalleta =
        { "estrella", "campana", "arbolito", "muñeco de nieve", "bastón", "copo", "calcetín", "regalo", "reno", "corazón" };

    public static string AvisoGalleta(int indice, int encontradas, int total)
    {
        return "¡Galleta con forma de " + FormaGalleta[indice] + "! Tiene una \"" + PalabraGalletas[indice]
             + "\" de betún (" + encontradas + "/" + total + ")";
    }

    public static readonly Linea[] PrimeraGalleta =
    {
        Linea.D("Tilo", "¿Una galleta de jengibre... con una letra? Debe ser de la charola de Santa."),
    };

    public const string AvisoEncajo = "¡Encajó!";

    public static readonly Linea[] CharolaCompleta =
    {
        Linea.D("Tilo", "¡NOCHEBUENA! ...Pero, ¿quién las horneó?"),
        Linea.D("???", "¡Fui yo!"),
        Linea.D("Jengibre", "Perdón por esconderme... nadie en el taller me conocía. ¡Gracias por salvar mis galletas!"),
        Linea.D("Jengibre", "Toma, para el camino: ¡te van a dar energía de sobra!"),
    };
    /// <summary>Si ya juegas con Jengibre, él mismo reconoce su receta.</summary>
    public static readonly Linea[] CharolaCompletaJengibre =
    {
        Linea.D("Jengibre", "¡NOCHEBUENA! ¡Mi charola completa otra vez!"),
        Linea.D("Jengibre", "Santa se va a poner feliz... y yo ya tengo energía de sobra."),
    };
    public const string PoderGalleta =
        "Desbloqueaste a Jengibre · Poder de galleta: corres más rápido y tus bolas de nieve aturden el doble.";
    public const string PoderGalletaYaDesbloqueado =
        "Poder de galleta: corres más rápido y tus bolas de nieve aturden el doble.";

    // ------------------------------------------------------------------ PISTAS DE LAS ETAPAS NUEVAS
    public const string PistaCurarSiete = "Busca el engrane, el resorte y el fusible. Instálalos en el cuarto de máquinas.";
    public const string PistaFabricarEstrella = "Baja la estrella rota de la repisa oeste, llévala a Siete y jala la palanca.";
    public const string PistaPonerEstrella = "¡Pon la estrella nueva en lo alto del Gran Árbol!";

    // ------------------------------------------------------------------ FINAL
    public static readonly Linea[] FinalArbol =
    {
        Linea.D("Tilo", "¡Lo logré! ¡El Gran Árbol está completo!"),
    };
    public static readonly Linea[] FinalCascanueces =
    {
        Linea.N("La luz del Gran Árbol viajó por los cables del techo hasta la Máquina 7..."),
        Linea.D("Siete", "♪ bip-bip-BUUUP ♪"),
        Linea.N("...y Siete dio su última descarga de la noche:\nuna descarga buena, <color=#ffd166>dorada y tibia</color>."),
        Linea.N("Las llaves de cuerda se detuvieron. Los ojos rojos se apagaron..."),
        Linea.N("...y se volvieron <color=#7fc8ff>azules</color>, como los pintan los elfos:\nlos ojos de un juguete bueno."),
    };
    public static readonly Linea[] FinalSanta =
    {
        Linea.D("Santa", "¡Jo, jo, jo! ¡Vi tu estrella desde las nubes, Tilo!"),
        Linea.D("Santa", "Sin ella me habría perdido en esta tormenta."),
        Linea.D("Santa", "...¿Y por qué la Máquina 7 brilla tan bonito?"),
        Linea.D("Tilo", "Es una larga historia, Santa. Se llama Siete... y ya está mejor."),
        Linea.D("Santa", "¿Siete? ¡Mi vieja Siete! La primera máquina que armé..."),
        Linea.D("Santa", "Ya me contarás todo con un chocolate caliente. Por hoy... <color=#ffd166>¡Feliz Navidad, Tilo!</color>"),
    };

    /// <summary>En la 1.5 Siete siempre está curada al final (es obligatorio); se deja la firma por compatibilidad.</summary>
    public static Linea[] LineasFinalSanta(bool maquinaReparada) { return FinalSanta; }

    /// <summary>FINAL ESPECIAL: solo si completaste la charola de galletas.</summary>
    public static readonly Linea[] FinalGalletas =
    {
        Linea.D("Santa", "Un momento... <i>*olfatea*</i> ...¿eso que huelo es JENGIBRE?"),
        Linea.D("Tilo", "Es su charola, Santa. Los cascanueces la tiraron, pero encontré las diez."),
        Linea.D("Santa", "N... O... C... H... E... ¡<color=#ffd166>NOCHEBUENA</color>! ¿Y quién las horneó?"),
        Linea.D("Jengibre", "¡Yo, Santa!"),
        Linea.D("Santa", "¡Mis favoritas! <i>¡Ñam!</i> ...<i>¡Ñam, ñam!</i> ...¡JO, JO, JO!"),
        Linea.D("Santa", "Jengibre, desde hoy <color=#ffd166>tienes lugar en el taller</color>. Y en el turno de noche, si Tilo te deja."),
    };
    /// <summary>Final especial cuando el elfo elegido ES Jengibre.</summary>
    public static readonly Linea[] FinalGalletasJengibre =
    {
        Linea.D("Santa", "Un momento... <i>*olfatea*</i> ...¿eso que huelo es JENGIBRE?"),
        Linea.D("Jengibre", "¡Mi charola, Santa! Los cascanueces la tiraron, pero encontré las diez."),
        Linea.D("Santa", "N... O... C... H... E... ¡<color=#ffd166>NOCHEBUENA</color>! <i>¡Ñam!</i> ...<i>¡Ñam, ñam!</i> ...¡JO, JO, JO!"),
        Linea.D("Santa", "El mejor elfo del turno de noche... y el mejor repostero del Polo Norte."),
    };

    public static readonly Linea[] Epilogo =
    {
        Linea.N("Esa mañana, los niños del mundo recibieron sus regalos a tiempo."),
        Linea.N("Y en una repisa del taller, tres cascanueces chiquitos, juntitos,\nmiraban la puerta con sus ojos <color=#7fc8ff>azules</color>."),
        Linea.N("<size=34>Pero... ¿alguien vio dónde quedaron sus llaves de cuerda?</size>"),
    };

    // ------------------------------------------------------------------ DERROTAS
    /// <summary>Amaneció sin estrella; cambia si Siete ya estaba curada.</summary>
    public static Linea[] LineasDerrota(bool sieteCurada) { return sieteCurada ? DerrotaSieteCurada : Derrota; }

    public static readonly Linea[] Derrota =
    {
        Linea.N("Los primeros rayos del sol entraron por las ventanas del taller..."),
        Linea.N("Santa llegó, pero el árbol seguía sin estrella...\ny la Máquina 7 seguía chispeando."),
        Linea.N("<size=34>Tal vez... si lo intentas otra vez, Tilo.</size>"),
    };
    public static readonly Linea[] DerrotaSieteCurada =
    {
        Linea.N("Los primeros rayos del sol entraron por las ventanas del taller..."),
        Linea.N("Santa llegó, pero el árbol seguía sin estrella...\ny Siete tarareaba solita, esperando."),
        Linea.N("<size=34>Tal vez... si lo intentas otra vez, Tilo.</size>"),
    };

    public static readonly Linea[] DerrotaAtrapado =
    {
        Linea.N("Los cascanueces rodearon a Tilo y lo encerraron en una caja de juguetes..."),
        Linea.N("Al amanecer, Santa encontró el tapete vacío\ny una caja que decía \"NO ABRIR\" desde adentro."),
        Linea.N("<size=34>Tal vez... si lo intentas otra vez, Tilo.</size>"),
    };

    /// <summary>Descarga 10 sin curar a Siete (solo Difícil / Imposible).</summary>
    public static readonly Linea[] DerrotaSobrecarga =
    {
        Linea.N("Siete dio la descarga más grande de su vida.\n<size=44>¡KA-BZZZOOOM!</size>"),
        Linea.N("Los osos, los trenes, los soldaditos... hasta la escoba:\ntodos los juguetes del taller abrieron los ojos al mismo tiempo."),
        Linea.N("Al amanecer, Santa encontró el taller lleno de juguetes marchando...\ny a Tilo escondido arriba de la chimenea."),
        Linea.N("<size=34>Tal vez... si lo intentas otra vez, Tilo.</size>"),
    };

    // ------------------------------------------------------------------ LETREROS NUEVOS (cuarto de máquinas y charola)
    public const string TituloPlanoSiete = "Plano de la Máquina 7";
    public const string PlanoSiete =
        "<b>MÁQUINA No. 7 — \"Siete\"</b>\nDiseño: S. Claus. Mi primera máquina.\n\n" +
        "• Pinta ojos con cariño. Da cuerda justa: 3 vueltas.\n" +
        "• Si se enferma: 1 engrane, 1 resorte, 1 fusible.\n" +
        "• Hace estrellas: dale la vieja y jala la palanca grande.\n" +
        "• Le gusta que le digan gracias.\n\n" +
        "<i>(al margen, con otra letra: \"Cuídenla. — S.\")</i>";
    public const string ComentarioPlanoSiete = "Siete... ¿así se llama?";

    public const string TituloRecetaGalletas = "Receta de galletas";
    public const string RecetaGalletas =
        "<b>Galletas NOCHEBUENA</b> — receta de Jengibre\n\n" +
        "10 formas, una letra de betún cada una.\n" +
        "Se acomodan en la charola de Santa: cada forma tiene su hueco.\n\n" +
        "<i>(No se vale comérselas antes. Ya sé quién fue el año pasado.)</i>";
    public const string ComentarioRecetaGalletas = "¿Jengibre? No conozco a ningún elfo con ese nombre...";

    // ------------------------------------------------------------------ CRÉDITOS Y CONTROLES
    public const string Creditos =
        "<size=64><color=#ffd166>TURNO DE NOCHE EN EL TALLER</color></size>\n\n" +
        "Mini Game Jam · \"Una Navidad diferente\"\n\n" +
        "<color=#9fb4ff>Un juego de</color>\n<size=44>Cristian Amauri Gonzaga Castañeda</size>\n\n" +
        "<color=#9fb4ff>Diseño, modelos 3D y programación</color>\nhecho con Unity 6 (URP) y Blender\n\n" +
        "<color=#9fb4ff>Personajes</color>\nTilo, Nieves y Chispa, los elfos del turno de noche\nSiete, la Máquina 7\nSargento Nuez · Cabo Bellota · Capitán Cáscara\nlos renos del establo · Santa\ny un elfo de galleta muy tímido\n\n" +
        "¡Gracias por jugar!\n\n<size=30>{OTRA_VEZ}</size>";

    /// <summary>Último renglón de los créditos según el control (teclado o pantalla táctil).</summary>
    public static string OtraVez { get { return Tactil.Activo ? "Toca la pantalla para jugar otra vez" : "[R] jugar otra vez"; } }

    public const string Controles =
        "<b><color=#ffd166>Controles</color></b>\n" +
        "[WASD] caminar · [Shift] correr <color=#ff9a8a>(¡hace ruido!)</color> · [Espacio] saltar · [Mouse] cámara · [Rueda] zoom\n" +
        "[E] recoger / colocar / juntar nieve · [Q] soltar · [F] o [Clic] lanzar bola de nieve · [Esc] pausa\n" +
        "<size=22><color=#9fe0ff>Difícil/Imposible: recarga la linterna junto a la chimenea o un farol · refúgiate de las ventiscas · rodea las cajas sorpresa</color></size>";

    public const string ControlesTactiles =
        "<b><color=#ffd166>Controles</color></b>\n" +
        "Joystick (izquierda) caminar · empújalo a fondo para correr <color=#ff9a8a>(¡hace ruido!)</color> · arrastra a la derecha: cámara · pellizca: zoom\n" +
        "[E] recoger / colocar / juntar nieve · [Q] soltar · [Bola] lanzar · [Saltar] · [II] pausa\n" +
        "<size=22><color=#9fe0ff>Difícil/Imposible: recarga la linterna junto a la chimenea o un farol · refúgiate de las ventiscas · rodea las cajas sorpresa</color></size>";
}
