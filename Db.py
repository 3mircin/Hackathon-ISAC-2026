import os
import json
import sqlite3
import math

DB_NAME = "hackathon.db"
DATA_DIR = "data/eventos_ordenados"

def inicializar_base_datos():
    # Borramos la base de datos anterior para empezar limpios con la estructura completa
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("Base de datos anterior eliminada. Creando la estructura avanzada y pulida...")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabla de Partidos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partidos (
            id_partido TEXT PRIMARY KEY,
            rival TEXT,
            fecha TEXT,
            estadio TEXT,
            competencia TEXT
        )
    """)
    
    # 2. Tabla de Eventos Generales (Incluye acciones defensivas, pases, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id_evento TEXT PRIMARY KEY,
            id_partido TEXT,
            event_index INTEGER,
            periodo INTEGER,
            timestamp TEXT,
            duracion REAL,
            minuto INTEGER,
            segundo INTEGER,
            equipo TEXT,
            equipo_id TEXT,
            tipo_evento TEXT,
            subtipo_evento TEXT,
            jugador TEXT,
            jugador_id TEXT,
            x_inicio REAL,
            y_inicio REAL,
            x_fin REAL,
            y_fin REAL,
            bajo_presion INTEGER, -- 1 si fue bajo presión, 0 si no
            possession_id INTEGER,
            possession_team TEXT,
            patron_juego TEXT,
            resultado TEXT,
            related_events TEXT,
            FOREIGN KEY(id_partido) REFERENCES partidos(id_partido)
        )
    """)
    
    # 3. Tabla Analítica de Remates y Ocasiones (xG y efectividad)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS remates (
            id_remate TEXT PRIMARY KEY,
            id_partido TEXT,
            equipo TEXT,
            jugador TEXT,
            minuto INTEGER,
            segundo INTEGER,
            tipo_gol_o_remate TEXT, -- 'Gol', 'Guardado', 'Bloqueado', 'Desviado', 'Poste', etc.
            xg REAL,
            carril_creacion TEXT,
            tecnica TEXT, -- 'De cabeza', 'Con el pie', etc.
            cuerpo_parte TEXT,
            possession_id INTEGER,
            key_pass_id TEXT,
            FOREIGN KEY(id_partido) REFERENCES partidos(id_partido)
        )
    """)

    # 4. Tabla de Estructuras Defensivas / Formaciones Tácticas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS formaciones_tacticas (
            id_cambio TEXT PRIMARY KEY,
            id_partido TEXT,
            equipo TEXT,
            minuto INTEGER,
            segundo INTEGER,
            formacion TEXT, -- Ej. 4-2-3-1, 4-3-3
            alineacion_json TEXT
        )
    """)

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS posesiones (
            id_partido TEXT NOT NULL,
            possession_id INTEGER NOT NULL,
            possession_team TEXT,
            periodo INTEGER,
            inicio_event_index INTEGER,
            fin_event_index INTEGER,
            inicio_segundo REAL,
            fin_segundo REAL,
            duracion REAL,
            eventos INTEGER,
            pases INTEGER,
            conducciones INTEGER,
            tiros INTEGER,
            recuperacion_alta INTEGER DEFAULT 0,
            PRIMARY KEY (id_partido, possession_id)
        );

        CREATE TABLE IF NOT EXISTS pases (
            id_evento TEXT PRIMARY KEY,
            id_partido TEXT NOT NULL,
            possession_id INTEGER,
            equipo TEXT,
            jugador TEXT,
            receptor TEXT,
            resultado TEXT,
            x_inicio REAL,
            y_inicio REAL,
            x_fin REAL,
            y_fin REAL,
            longitud REAL,
            angulo REAL,
            progresivo INTEGER DEFAULT 0,
            shot_assist INTEGER DEFAULT 0,
            goal_assist INTEGER DEFAULT 0,
            assisted_shot_id TEXT,
            pase_clave INTEGER DEFAULT 0,
            cross INTEGER DEFAULT 0,
            cut_back INTEGER DEFAULT 0,
            through_ball INTEGER DEFAULT 0,
            switch_pass INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS acciones_defensivas (
            id_evento TEXT PRIMARY KEY,
            id_partido TEXT NOT NULL,
            equipo TEXT,
            jugador TEXT,
            tipo_accion TEXT,
            resultado TEXT,
            x REAL,
            y REAL,
            zona TEXT,
            exitosa INTEGER,
            counterpress INTEGER DEFAULT 0,
            penalty_box INTEGER DEFAULT 0,
            defensive_third INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS asistencias (
            id_pase TEXT PRIMARY KEY,
            id_tiro TEXT NOT NULL,
            id_partido TEXT NOT NULL,
            equipo TEXT,
            jugador_pasador TEXT,
            jugador_rematador TEXT,
            xg_remate REAL,
            xag REAL,
            shot_assist INTEGER,
            goal_assist INTEGER
        );

        CREATE TABLE IF NOT EXISTS jugadores_partido (
            id_partido TEXT NOT NULL,
            jugador_id TEXT NOT NULL,
            jugador TEXT,
            equipo TEXT,
            posicion TEXT,
            posicion_id INTEGER,
            minuto_entrada REAL,
            minuto_salida REAL,
            titular INTEGER,
            PRIMARY KEY (id_partido, jugador_id, minuto_entrada)
        );

        CREATE TABLE IF NOT EXISTS disciplina_sustituciones (
            id_evento TEXT PRIMARY KEY,
            id_partido TEXT NOT NULL,
            minuto INTEGER,
            segundo INTEGER,
            equipo TEXT,
            jugador TEXT,
            tipo TEXT,
            jugador_reemplazo TEXT,
            tarjeta TEXT,
            razon TEXT
        );

        CREATE TABLE IF NOT EXISTS estado_partido (
            id_partido TEXT NOT NULL,
            event_index INTEGER NOT NULL,
            minuto REAL,
            equipo TEXT,
            marcador_equipo INTEGER,
            marcador_rival INTEGER,
            diferencia_goles INTEGER,
            estado TEXT,
            jugadores_activos INTEGER,
            rival_jugadores_activos INTEGER,
            PRIMARY KEY (id_partido, event_index, equipo)
        );

        CREATE TABLE IF NOT EXISTS transiciones (
            id_partido TEXT NOT NULL,
            id_recuperacion TEXT NOT NULL,
            equipo TEXT,
            zona_recuperacion TEXT,
            possession_id INTEGER,
            segundos_hasta_tiro REAL,
            eventos_hasta_tiro INTEGER,
            pases_hasta_tiro INTEGER,
            xg_generado REAL DEFAULT 0,
            hubo_tiro INTEGER DEFAULT 0,
            hubo_gol INTEGER DEFAULT 0,
            PRIMARY KEY (id_partido, id_recuperacion)
        );

        CREATE TABLE IF NOT EXISTS data_quality (
            id_partido TEXT NOT NULL,
            regla TEXT NOT NULL,
            registros INTEGER NOT NULL,
            severidad TEXT NOT NULL,
            PRIMARY KEY (id_partido, regla)
        );

        CREATE TABLE IF NOT EXISTS features_jugador_ventana (
            id_partido TEXT NOT NULL,
            equipo TEXT NOT NULL,
            jugador_id TEXT,
            jugador TEXT NOT NULL,
            periodo INTEGER,
            ventana_minuto INTEGER,
            minutos_activos REAL,
            pases INTEGER DEFAULT 0,
            pases_progresivos INTEGER DEFAULT 0,
            conducciones INTEGER DEFAULT 0,
            xa REAL DEFAULT 0,
            xg REAL DEFAULT 0,
            presiones INTEGER DEFAULT 0,
            recuperaciones INTEGER DEFAULT 0,
            perdidas INTEGER DEFAULT 0,
            duelos_ganados INTEGER DEFAULT 0,
            estado_partido TEXT,
            PRIMARY KEY (
                id_partido, equipo, jugador, periodo, ventana_minuto
            )
        );

        CREATE INDEX IF NOT EXISTS idx_eventos_possession
            ON eventos(id_partido, possession_id, event_index);
        CREATE INDEX IF NOT EXISTS idx_eventos_tiempo
            ON eventos(id_partido, periodo, minuto, segundo);
        CREATE INDEX IF NOT EXISTS idx_pases_progresivos
            ON pases(id_partido, equipo, progresivo);
        CREATE INDEX IF NOT EXISTS idx_transiciones_partido
            ON transiciones(id_partido, equipo, hubo_tiro);
        CREATE INDEX IF NOT EXISTS idx_features_jugador
            ON features_jugador_ventana(id_partido, jugador, ventana_minuto);
    """)
    
    conn.commit()
    conn.close()
    print("Estructura avanzada de la base de datos creada con éxito.")

def nombre(valor):
    return valor.get("name") if isinstance(valor, dict) else valor

def tiempo_evento(ev):
    timestamp = ev.get("timestamp")
    if timestamp:
        partes = timestamp.split(":")
        if len(partes) == 3:
            horas, minutos, segundos = partes
            tiempo_periodo = (
                int(horas) * 3600
                + int(minutos) * 60
                + float(segundos)
            )
        else:
            tiempo_periodo = float(partes[-1])
        return (ev.get("period", 1) - 1) * 45 * 60 + tiempo_periodo
    return (ev.get("period", 1) - 1) * 45 * 60 + ev.get("minute", 0) * 60 + ev.get("second", 0)

def zona_campo(x, y):
    if x is None or y is None:
        return None
    if x >= 102 and 18 <= y <= 62:
        return "PENALTY_BOX"
    if x < 40:
        return "DEFENSIVE_THIRD"
    if x < 80:
        return "MIDDLE_THIRD"
    return "ATTACKING_THIRD"

def distancia_porteria(x, y):
    return math.hypot(120 - x, 40 - y)

def pase_progresivo(x1, y1, x2, y2, outcome):
    if None in (x1, y1, x2, y2) or outcome not in (None, "Complete"):
        return 0
    avance = x2 - x1
    reduccion = distancia_porteria(x1, y1) - distancia_porteria(x2, y2)
    return int(avance >= 10 or reduccion >= 15)

def determinar_carril(y):
    """
    En la cancha de StatsBomb (ancho de 0 a 80 metros):
    - Carril izquierdo: y de 0 a 26.6
    - Carril central: y de 26.6 a 53.3
    - Carril derecho: y de 53.3 a 80
    """
    if y is None:
        return "CENTRO"
    if y < 26.6:
        return "IZQUIERDA"
    elif y <= 53.3:
        return "CENTRO"
    else:
        return "DERECHA"

def es_recuperacion(ev):
    return ev.get("type", {}).get("name") in {
        "Ball Recovery", "Interception", "Tackle", "Duel",
        "Dispossessed", "Error"
    }

def actualizar_analitica_partido(cursor, id_partido, eventos):
    ordenados = sorted(eventos, key=lambda ev: ev.get("index", 0))
    equipos = [
        ev.get("team", {}).get("name")
        for ev in ordenados
        if ev.get("team", {}).get("name")
    ]
    equipos = list(dict.fromkeys(equipos))
    if len(equipos) < 2:
        return

    marcador = {equipo: 0 for equipo in equipos}
    tarjetas_rojas = {equipo: set() for equipo in equipos}
    ultimos_estados = {}

    for ev in ordenados:
        equipo = ev.get("team", {}).get("name")
        if not equipo:
            continue
        tipo = ev.get("type", {}).get("name")
        jugador = ev.get("player", {}).get("name")
        indice = ev.get("index", 0)

        if tipo == "Shot" and nombre(ev.get("shot", {}).get("outcome")) == "Goal":
            marcador[equipo] = marcador.get(equipo, 0) + 1

        tarjeta = nombre(ev.get("bad_behaviour", {}).get("card"))
        if tipo == "Bad Behaviour" and tarjeta in {"Red Card", "Second Yellow"}:
            tarjetas_rojas.setdefault(equipo, set()).add(jugador)

        rival = next((nombre_equipo for nombre_equipo in equipos if nombre_equipo != equipo), None)
        propios_activos = max(0, 11 - len(tarjetas_rojas.get(equipo, set())))
        rivales_activos = max(0, 11 - len(tarjetas_rojas.get(rival, set())))
        diferencia = marcador[equipo] - marcador.get(rival, 0)
        estado = "ganando" if diferencia > 0 else "perdiendo" if diferencia < 0 else "empatando"
        tiempo = tiempo_evento(ev)

        cursor.execute("""
            INSERT OR REPLACE INTO estado_partido (
                id_partido, event_index, minuto, equipo, marcador_equipo,
                marcador_rival, diferencia_goles, estado,
                jugadores_activos, rival_jugadores_activos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_partido, indice, tiempo, equipo, marcador[equipo],
            marcador.get(rival, 0), diferencia, estado,
            propios_activos, rivales_activos
        ))
        ultimos_estados[(equipo, indice)] = estado

    for recuperacion in ordenados:
        if not es_recuperacion(recuperacion):
            continue
        equipo = recuperacion.get("team", {}).get("name")
        if not equipo or recuperacion.get("location") is None:
            continue

        indice = recuperacion.get("index", 0)
        tiempo_inicio = tiempo_evento(recuperacion)
        possession_id = recuperacion.get("possession")
        candidatos = [
            ev for ev in ordenados
            if ev.get("index", 0) > indice
            and ev.get("team", {}).get("name") == equipo
            and ev.get("type", {}).get("name") == "Shot"
            and (
                possession_id is None
                or ev.get("possession") == possession_id
            )
            and 0 <= tiempo_evento(ev) - tiempo_inicio <= 20
        ]
        tiro = candidatos[0] if candidatos else None
        siguientes = [
            ev for ev in ordenados
            if ev.get("index", 0) > indice
            and (
                possession_id is None
                or ev.get("possession") == possession_id
            )
            and 0 <= tiempo_evento(ev) - tiempo_inicio <= 20
        ]
        x, y = recuperacion["location"][:2]
        if tiro:
            tramo = [
                ev for ev in siguientes
                if ev.get("index", 0) <= tiro.get("index", 0)
            ]
            xg = tiro.get("shot", {}).get("statsbomb_xg", 0.0) or 0.0
            outcome = nombre(tiro.get("shot", {}).get("outcome"))
        else:
            tramo, xg, outcome = [], 0.0, None

        cursor.execute("""
            INSERT OR REPLACE INTO transiciones (
                id_partido, id_recuperacion, equipo, zona_recuperacion,
                possession_id, segundos_hasta_tiro, eventos_hasta_tiro,
                pases_hasta_tiro, xg_generado, hubo_tiro, hubo_gol
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id_partido, recuperacion.get("id"), equipo, zona_campo(x, y),
            possession_id,
            tiempo_evento(tiro) - tiempo_inicio if tiro else None,
            len(tramo),
            sum(ev.get("type", {}).get("name") == "Pass" for ev in tramo),
            xg, int(tiro is not None), int(outcome == "Goal")
        ))

    reglas = {
        "eventos_sin_indice": sum(ev.get("index") is None for ev in ordenados),
        "eventos_sin_equipo": sum(
            ev.get("team", {}).get("name") is None for ev in ordenados
        ),
        "eventos_sin_possession": sum(
            ev.get("possession") is None for ev in ordenados
        ),
        "tiros_sin_xg": sum(
            ev.get("type", {}).get("name") == "Shot"
            and ev.get("shot", {}).get("statsbomb_xg") is None
            for ev in ordenados
        ),
    }
    for regla, cantidad in reglas.items():
        severidad = "alta" if cantidad > 0 and regla in {
            "eventos_sin_indice", "eventos_sin_equipo"
        } else "media" if cantidad > 0 else "ok"
        cursor.execute("""
            INSERT OR REPLACE INTO data_quality (
                id_partido, regla, registros, severidad
            ) VALUES (?, ?, ?, ?)
        """, (id_partido, regla, cantidad, severidad))

    cursor.execute("""
        INSERT OR REPLACE INTO features_jugador_ventana (
            id_partido, equipo, jugador_id, jugador, periodo,
            ventana_minuto, minutos_activos, pases, pases_progresivos,
            conducciones, xa, xg, presiones, recuperaciones, perdidas,
            duelos_ganados, estado_partido
        )
        SELECT
            e.id_partido, e.equipo, e.jugador_id, e.jugador, e.periodo,
            (e.minuto / 5) * 5,
            5.0,
            SUM(e.tipo_evento = 'Pass'),
            SUM(e.tipo_evento = 'Pass' AND p.progresivo = 1),
            SUM(e.tipo_evento = 'Carry'),
            COALESCE(SUM(a.xag), 0),
            COALESCE(SUM(
                CASE WHEN e.tipo_evento = 'Shot' THEN r.xg ELSE 0 END
            ), 0),
            SUM(e.tipo_evento = 'Pressure'),
            SUM(e.tipo_evento IN ('Ball Recovery', 'Interception')),
            SUM(e.tipo_evento IN ('Dispossessed', 'Error')),
            SUM(
                e.tipo_evento = 'Duel'
                AND e.resultado IN ('Won', 'Success', 'Successful')
            ),
            MAX(s.estado)
        FROM eventos e
        LEFT JOIN pases p ON p.id_evento = e.id_evento
        LEFT JOIN asistencias a ON a.id_pase = p.id_evento
        LEFT JOIN remates r ON r.id_remate = e.id_evento
        LEFT JOIN estado_partido s
          ON s.id_partido = e.id_partido
         AND s.event_index = e.event_index
         AND s.equipo = e.equipo
        WHERE e.id_partido = ?
          AND e.jugador IS NOT NULL
        GROUP BY e.id_partido, e.equipo, e.jugador_id, e.jugador,
                 e.periodo, (e.minuto / 5) * 5
    """, (id_partido,))

def crear_vistas_analiticas(cursor):
    cursor.executescript("""
        CREATE VIEW IF NOT EXISTS vw_posesiones_analiticas AS
        SELECT p.*,
               CASE WHEN p.tiros > 0 THEN 1 ELSE 0 END AS termina_en_tiro
        FROM posesiones p;

        CREATE VIEW IF NOT EXISTS vw_transiciones AS
        SELECT t.*,
               CASE
                   WHEN t.zona_recuperacion = 'ATTACKING_THIRD'
                   THEN 1 ELSE 0
               END AS recuperacion_alta
        FROM transiciones t;

        CREATE VIEW IF NOT EXISTS vw_jugador_partido AS
        SELECT id_partido, equipo, jugador_id, jugador,
               SUM(pases) AS pases,
               SUM(pases_progresivos) AS pases_progresivos,
               SUM(conducciones) AS conducciones,
               SUM(xa) AS xa,
               SUM(xg) AS xg,
               SUM(presiones) AS presiones,
               SUM(recuperaciones) AS recuperaciones,
               SUM(perdidas) AS perdidas,
               SUM(duelos_ganados) AS duelos_ganados
        FROM features_jugador_ventana
        GROUP BY id_partido, equipo, jugador_id, jugador;
    """)

def procesar_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if not os.path.exists(DATA_DIR):
        print(f"No se encontró la carpeta {DATA_DIR}")
        return

    archivos = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    print(f"Procesando {len(archivos)} partidos con el nuevo modelo de datos completo...")

    for archivo in archivos:
        path = os.path.join(DATA_DIR, archivo)
        id_partido = archivo.replace(".json", "")
        
        with open(path, "r", encoding="utf-8") as f:
            try:
                eventos = json.load(f)
            except Exception as e:
                continue
                
        # Insertar partido base
        rival = id_partido.split("_")[-2] if "_" in id_partido else "Desconocido"
        cursor.execute("INSERT OR IGNORE INTO partidos (id_partido, rival) VALUES (?, ?)", 
                       (id_partido, rival))

        for ev in eventos:
            ev_id = ev.get("id")
            event_index = ev.get("index")
            periodo = ev.get("period")
            timestamp = ev.get("timestamp")
            duracion = ev.get("duration")
            minuto = ev.get("minute")
            segundo = ev.get("second")
            
            equipo_dict = ev.get("team", {})
            equipo = equipo_dict.get("name")
            equipo_id = equipo_dict.get("id")
            
            tipo_dict = ev.get("type", {})
            tipo = tipo_dict.get("name")
            
            jugador_dict = ev.get("player", {})
            jugador = jugador_dict.get("name")
            jugador_id = jugador_dict.get("id")
            
            bajo_presion = 1 if ev.get("under_pressure") else 0
            possession_id = ev.get("possession")
            possession_team = nombre(ev.get("possession_team"))
            patron_juego = nombre(ev.get("play_pattern"))
            resultado = None
            related_events = json.dumps(ev.get("related_events", []))
            
            # Coordenadas de inicio
            loc = ev.get("location", [None, None])
            x_ini, y_ini = loc[0], loc[1]
            
            # Coordenadas finales (pase, tiro, carry, etc.)
            x_fin, y_fin = None, None
            subtipo = None

            if "pass" in ev:
                pass_info = ev.get("pass", {})
                end_loc = pass_info.get("end_location", [None, None])
                x_fin, y_fin = end_loc[0], end_loc[1]
                subtipo = pass_info.get("height", {}).get("name")
                resultado = nombre(pass_info.get("outcome"))
            elif "shot" in ev:
                shot_info = ev.get("shot", {})
                end_loc = shot_info.get("end_location", [None, None])
                x_fin, y_fin = end_loc[0], end_loc[1]
                subtipo = shot_info.get("type", {}).get("name")
                resultado = nombre(shot_info.get("outcome"))
            elif "carry" in ev:
                carry_info = ev.get("carry", {})
                end_loc = carry_info.get("end_location", [None, None])
                x_fin, y_fin = end_loc[0], end_loc[1]

            # 1. Insertar en eventos generales (ofensiva, defensa, presiones, recuperaciones)
            cursor.execute("""
                INSERT OR IGNORE INTO eventos (
                    id_evento, id_partido, event_index, periodo, timestamp, duracion,
                    minuto, segundo, equipo, equipo_id, tipo_evento, subtipo_evento,
                    jugador, jugador_id, x_inicio, y_inicio, x_fin, y_fin,
                    bajo_presion, possession_id, possession_team, patron_juego,
                    resultado, related_events
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ev_id, id_partido, event_index, periodo, timestamp, duracion,
                  minuto, segundo, equipo, equipo_id, tipo, subtipo, jugador,
                  jugador_id, x_ini, y_ini, x_fin, y_fin, bajo_presion,
                  possession_id, possession_team, patron_juego, resultado, related_events))

            if tipo == "Pass":
                pass_info = ev.get("pass", {})
                receptor = nombre(pass_info.get("recipient"))
                outcome = nombre(pass_info.get("outcome"))
                longitud = pass_info.get("length")
                angulo = pass_info.get("angle")
                asistido = pass_info.get("assisted_shot_id")
                shot_assist = int(bool(asistido))
                goal_assist = int(bool(pass_info.get("goal_assist")))
                progresivo = pase_progresivo(
                    x_ini, y_ini, x_fin, y_fin, outcome
                )
                cursor.execute("""
                    INSERT OR IGNORE INTO pases (
                        id_evento, id_partido, possession_id, equipo, jugador,
                        receptor, resultado, x_inicio, y_inicio, x_fin, y_fin,
                        longitud, angulo, progresivo, shot_assist, goal_assist,
                        assisted_shot_id, pase_clave, cross, cut_back,
                        through_ball, switch_pass
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ev_id, id_partido, possession_id, equipo, jugador, receptor,
                    outcome, x_ini, y_ini, x_fin, y_fin, longitud, angulo,
                    progresivo, shot_assist, goal_assist, asistido, shot_assist,
                    int(bool(pass_info.get("cross"))),
                    int(bool(pass_info.get("cut_back"))),
                    int(bool(pass_info.get("through_ball"))),
                    int(bool(pass_info.get("switch")))
                ))

            tipos_defensivos = {
                "Pressure", "Block", "Interception", "Clearance",
                "Tackle", "Duel", "Ball Recovery", "Dispossessed", "Error"
            }
            if tipo in tipos_defensivos:
                detalle = ev.get(tipo.lower().replace(" ", "_"), {})
                resultado_def = nombre(detalle.get("outcome"))
                zona = zona_campo(x_ini, y_ini)
                cursor.execute("""
                    INSERT OR IGNORE INTO acciones_defensivas (
                        id_evento, id_partido, equipo, jugador, tipo_accion,
                        resultado, x, y, zona, exitosa, counterpress,
                        penalty_box, defensive_third
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ev_id, id_partido, equipo, jugador, tipo, resultado_def,
                    x_ini, y_ini, zona,
                    int(resultado_def in {"Won", "Success", "Successful"}),
                    int(bool(ev.get("counterpress"))),
                    int(zona == "PENALTY_BOX"),
                    int(zona == "DEFENSIVE_THIRD")
                ))

            # 2. Procesamiento específico de Remates / Ocasiones de Gol (incluye xG)
            if tipo == "Shot":
                shot_data = ev.get("shot", {})
                outcome = shot_data.get("outcome", {}).get("name")
                xg = shot_data.get("statsbomb_xg", 0.0)
                tecnica = shot_data.get("technique", {}).get("name")
                cuerpo = shot_data.get("body_part", {}).get("name")
                carril = determinar_carril(y_ini)
                key_pass_id = shot_data.get("key_pass_id")
                
                cursor.execute("""
                    INSERT OR IGNORE INTO remates (
                        id_remate, id_partido, equipo, jugador, minuto, segundo,
                        tipo_gol_o_remate, xg, carril_creacion, tecnica, cuerpo_parte,
                        possession_id, key_pass_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ev_id, id_partido, equipo, jugador, minuto, segundo, outcome,
                      xg, carril, tecnica, cuerpo, possession_id, key_pass_id))

            # 3. Captura de Formaciones Tácticas o cambios de estructura
            if tipo == "Tactical Shift" or tipo == "Starting XI":
                tactical_data = ev.get("tactics", {})
                formacion = tactical_data.get("formation")
                if formacion:
                    cursor.execute("""
                        INSERT OR IGNORE INTO formaciones_tacticas (
                            id_cambio, id_partido, equipo, minuto, segundo, formacion,
                            alineacion_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (ev_id, id_partido, equipo, minuto, segundo, str(formacion),
                          json.dumps(tactical_data.get("lineup", []))))

                    for jugador_tactico in tactical_data.get("lineup", []):
                        jugador_info = jugador_tactico.get("player", {})
                        posicion = jugador_tactico.get("position", {})
                        cursor.execute("""
                            INSERT OR IGNORE INTO jugadores_partido (
                                id_partido, jugador_id, jugador, equipo, posicion,
                                posicion_id, minuto_entrada, minuto_salida, titular
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            id_partido, jugador_info.get("id"),
                            jugador_info.get("name"), equipo,
                            posicion.get("name"), posicion.get("id"),
                            tiempo_evento(ev), None, int(tipo == "Starting XI")
                        ))

            if tipo == "Substitution":
                sub = ev.get("substitution", {})
                cursor.execute("""
                    INSERT OR IGNORE INTO disciplina_sustituciones (
                        id_evento, id_partido, minuto, segundo, equipo,
                        jugador, tipo, jugador_reemplazo, tarjeta, razon
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ev_id, id_partido, minuto, segundo, equipo, jugador,
                    tipo, nombre(sub.get("replacement")), None,
                    nombre(sub.get("outcome"))
                ))

            if tipo == "Bad Behaviour":
                    bad = ev.get("bad_behaviour", {})
                    cursor.execute("""
                        INSERT OR IGNORE INTO disciplina_sustituciones (
                            id_evento, id_partido, minuto, segundo, equipo,
                            jugador, tipo, jugador_reemplazo, tarjeta, razon
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ev_id, id_partido, minuto, segundo, equipo, jugador,
                        tipo, None, nombre(bad.get("card")), None
                    ))

        posesiones = {}
        for ev in eventos:
            pid = ev.get("possession")
            if pid is None:
                    continue
            t = tiempo_evento(ev)
            tipo_ev = ev.get("type", {}).get("name")
            loc_ev = ev.get("location") or [None, None]
            recuperacion_alta = int(
                    tipo_ev in {
                        "Ball Recovery", "Interception", "Tackle",
                        "Duel", "Dispossessed", "Error"
                    }
                    and loc_ev[0] is not None
                    and loc_ev[0] >= 80
            )
            p = posesiones.setdefault(pid, {
                    "team": nombre(ev.get("possession_team")),
                    "period": ev.get("period"),
                    "first_index": ev.get("index"),
                    "last_index": ev.get("index"),
                    "start": t,
                    "end": t,
                    "events": 0,
                    "passes": 0,
                    "carries": 0,
                    "shots": 0,
                    "high_turnover": 0,
            })
            p["first_index"] = min(p["first_index"], ev.get("index", p["first_index"]))
            p["last_index"] = max(p["last_index"], ev.get("index", p["last_index"]))
            p["start"] = min(p["start"], t)
            p["end"] = max(p["end"], t)
            p["events"] += 1
            p["passes"] += int(tipo_ev == "Pass")
            p["carries"] += int(tipo_ev == "Carry")
            p["shots"] += int(tipo_ev == "Shot")
            p["high_turnover"] = max(p["high_turnover"], recuperacion_alta)

        for pid, p in posesiones.items():
            cursor.execute("""
                    INSERT OR REPLACE INTO posesiones (
                        id_partido, possession_id, possession_team, periodo,
                        inicio_event_index, fin_event_index, inicio_segundo,
                        fin_segundo, duracion, eventos, pases, conducciones, tiros,
                        recuperacion_alta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                    id_partido, pid, p["team"], p["period"], p["first_index"],
                    p["last_index"], p["start"], p["end"], p["end"] - p["start"],
                    p["events"], p["passes"], p["carries"], p["shots"],
                    p["high_turnover"]
            ))

        tiros = {
            ev.get("id"): ev for ev in eventos
            if ev.get("type", {}).get("name") == "Shot"
        }
        for ev in eventos:
            if ev.get("type", {}).get("name") != "Pass":
                    continue
            pase = ev.get("pass", {})
            shot_id = pase.get("assisted_shot_id")
            if not shot_id or shot_id not in tiros:
                    continue
            tiro = tiros[shot_id]
            cursor.execute("""
                    INSERT OR IGNORE INTO asistencias (
                        id_pase, id_tiro, id_partido, equipo, jugador_pasador,
                        jugador_rematador, xg_remate, xag, shot_assist, goal_assist
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                    ev.get("id"), shot_id, id_partido,
                    ev.get("team", {}).get("name"),
                    ev.get("player", {}).get("name"),
                    tiro.get("player", {}).get("name"),
                    tiro.get("shot", {}).get("statsbomb_xg", 0.0),
                    tiro.get("shot", {}).get("statsbomb_xg", 0.0),
                    1, int(bool(pase.get("goal_assist")))
            ))

        actualizar_analitica_partido(cursor, id_partido, eventos)

    crear_vistas_analiticas(cursor)

    conn.commit()
    conn.close()
    print("¡Base de datos completamente reconstruida, optimizada y poblada con éxito (`hackathon.db`)!")

if __name__ == "__main__":
    inicializar_base_datos()
    procesar_datos()