/// <summary>
/// EL GUION DEL JUEGO: todos los textos de la historia en un solo lugar.
/// Si quieres cambiar un diálogo, cámbialo aquí (no hay que tocar la lógica).
/// N = narración (pantalla negra), D = diálogo (quién, texto), Nota = hoja de papel.
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
        Linea.N("Su única tarea era sencilla:\ncuidar el <color=#7dffa1>Gran Árbol</color> del taller\nhasta que Santa regresara de su último vuelo de prueba."),
        Linea.N("Pero cuando Tilo volvió de la bodega\ncon su chocolate caliente..."),
    };

    public static readonly Linea[] IntroTaller =
    {
        Linea.D("Tilo", "¿...?"),
        Linea.D("Tilo", "¿¡EL ÁRBOL!? ¿Dónde está el Gran Árbol?"),
        Linea.D("Tilo", "Está todo desarmado... hay piezas regadas por todo el taller."),
        Linea.D("Tilo", "Y huellas. Huellas pequeñitas... <i>de madera</i>."),
        Linea.D("Tilo", "Si Santa regresa y no ve la estrella encendida, no encontrará el camino a casa en esta tormenta.\nTengo que armarlo antes del amanecer."),
    };

    // ------------------------------------------------------------------ AL TERMINAR CADA ETAPA
    // índice = etapa terminada (0 Maceta, 1 Ramas, 2 Esferas, 3 Guirnalda)
    public static readonly string[] NombreMision = { "La Maceta", "Las Ramas", "Las Esferas", "La Guirnalda de Luces" };

    public static readonly Linea[][] FinEtapa =
    {
        new[] {
            Linea.D("Tilo", "¡Listo! Ya tenemos dónde plantar el árbol."),
            Linea.N("<size=40>crac...   crac...   crac...</size>"),
            Linea.D("Tilo", "¿Qué fue eso? Venía de las repisas..."),
        },
        new[] {
            Linea.D("Tilo", "Las ramas otra vez en su lugar. El taller vuelve a oler a pino."),
            Linea.D("Tilo", "Pero cada vez que el árbol brilla un poquito más... ellos se ponen más nerviosos."),
        },
        new[] {
            Linea.D("Tilo", "Seis esferas, seis lucecitas."),
            Linea.D("Tilo", "¿Oyes eso? La Máquina 7 está chispeando más fuerte que nunca..."),
            Linea.D("Tilo", "Fue ella. ¡La máquina descompuesta los despertó!"),
        },
        new[] {
            Linea.D("Tilo", "¡La guirnalda funciona! Gracias, amigo reno."),
            Linea.D("Tilo", "Solo falta la estrella... y está en lo más alto de la repisa del oeste."),
            Linea.D("Tilo", "Unas cajas me ayudarían a subir."),
        },
    };

    /// <summary>Lo que dice Tilo cuando ve despertar a un cascanueces (por orden de despertar).</summary>
    public static readonly Linea[][] Despertar =
    {
        new[] { Linea.D("Tilo", "Ese cascanueces... ¿me acaba de MIRAR?"),
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

    // ------------------------------------------------------------------ FINAL
    public static readonly Linea[] FinalArbol =
    {
        Linea.D("Tilo", "¡Lo logré! ¡El Gran Árbol está completo!"),
    };
    public static readonly Linea[] FinalCascanueces =
    {
        Linea.N("La luz del Gran Árbol llenó cada rincón del taller."),
        Linea.N("Los cascanueces se detuvieron a media zancada...\ny volvieron a ser lo que siempre debieron ser:\n<color=#ffd166>juguetes</color>."),
    };
    public static readonly Linea[] FinalSanta =
    {
        Linea.D("Santa", "¡Jo, jo, jo! ¡Vi tu estrella desde las nubes, Tilo!"),
        Linea.D("Santa", "Sin ella me habría perdido en esta tormenta."),
        Linea.D("Santa", "...¿Y por qué hay cascanueces tirados por todo el taller?"),
        Linea.D("Tilo", "Es... una larga historia, Santa."),
        Linea.D("Santa", "Ya me la contarás con un chocolate caliente. Mañana arreglamos la Máquina 7."),
        Linea.D("Santa", "Por hoy... <color=#ffd166>¡Feliz Navidad, Tilo!</color>"),
    };
    public static readonly Linea[] Derrota =
    {
        Linea.N("Los primeros rayos del sol entraron por las ventanas del taller..."),
        Linea.N("Santa llegó por el árbol, pero solo encontró el tapete vacío\ny tres cascanueces muy, muy quietos."),
        Linea.N("<size=34>Tal vez... si lo intentas otra vez, Tilo.</size>"),
    };

    public static readonly Linea[] DerrotaAtrapado =
    {
        Linea.N("Los cascanueces rodearon a Tilo y lo encerraron en una caja de juguetes..."),
        Linea.N("Al amanecer, Santa encontró el tapete vacío\ny una caja que decía \"NO ABRIR\" desde adentro."),
        Linea.N("<size=34>Tal vez... si lo intentas otra vez, Tilo.</size>"),
    };

    /// <summary>FinalSanta, pero si reparaste la Máquina 7 Santa lo nota.</summary>
    public static Linea[] LineasFinalSanta(bool maquinaReparada)
    {
        var l = (Linea[])FinalSanta.Clone();
        if (maquinaReparada)
            for (int i = 0; i < l.Length; i++)
                if (l[i].texto.Contains("Máquina 7"))
                    l[i] = Linea.D("Santa", "Ya me la contarás con un chocolate caliente. ¡Y hasta arreglaste la Máquina 7! Ese ruido no dejaba dormir a nadie.");
        return l;
    }

    /// <summary>FINAL ESPECIAL: solo si juntaste las 10 galletas de jengibre.</summary>
    public static readonly Linea[] FinalGalletas =
    {
        Linea.D("Santa", "Un momento... <i>*olfatea*</i> ...¿eso que huelo es JENGIBRE?"),
        Linea.D("Tilo", "¡Las encontré todas, Santa! Diez galletas escondidas por todo el pueblo."),
        Linea.D("Santa", "¡Mis favoritas! <i>¡Ñam!</i> ...<i>¡Ñam, ñam!</i> ...¡JO, JO, JO!"),
        Linea.D("Santa", "Con esta energía reparto los regalos del mundo entero antes del desayuno."),
        Linea.D("Santa", "Y dile a ese elfo de galleta que se esconde en la repisa... que <color=#ffd166>ya tiene lugar en el taller</color>."),
    };

    public static readonly Linea[] Epilogo =
    {
        Linea.N("Esa mañana, los niños del mundo recibieron sus regalos a tiempo."),
        Linea.N("Y en una repisa del taller, tres cascanueces de madera\nmiraban fijamente hacia la puerta..."),
        Linea.N("<size=34>...como esperando la próxima Nochebuena.</size>"),
    };

    public const string Creditos =
        "<size=64><color=#ffd166>TURNO DE NOCHE EN EL TALLER</color></size>\n\n" +
        "Mini Game Jam · \"Una Navidad diferente\"\n\n" +
        "<color=#9fb4ff>Un juego de</color>\n<size=44>Cristian Amauri Gonzaga Castañeda</size>\n\n" +
        "<color=#9fb4ff>Diseño, modelos 3D y programación</color>\nhecho con Unity 6 (URP) y Blender\n\n" +
        "<color=#9fb4ff>Personajes</color>\nTilo, Nieves y Chispa, los elfos del turno de noche\nSargento Nuez · Cabo Bellota · Capitán Cáscara\nlos renos del establo · Santa\n\n" +
        "¡Gracias por jugar!\n\n<size=30>[R] jugar otra vez</size>";

    public const string Controles =
        "<b><color=#ffd166>Controles</color></b>\n" +
        "[WASD] caminar · [Shift] correr <color=#ff9a8a>(¡hace ruido!)</color> · [Espacio] saltar · [Mouse] cámara · [Rueda] zoom\n" +
        "[E] recoger / colocar / juntar nieve · [Q] soltar · [F] o [Clic] lanzar bola de nieve · [Esc] pausa\n" +
        "<size=22><color=#9fe0ff>Difícil/Imposible: recarga la linterna junto a la chimenea o un farol · refúgiate de las ventiscas · rodea las cajas sorpresa</color></size>";
}
