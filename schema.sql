CREATE TABLE acciones_defensivas (
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
CREATE TABLE asistencias (
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
CREATE TABLE data_quality (
            id_partido TEXT NOT NULL,
            regla TEXT NOT NULL,
            registros INTEGER NOT NULL,
            severidad TEXT NOT NULL,
            PRIMARY KEY (id_partido, regla)
        );
CREATE TABLE disciplina_sustituciones (
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
CREATE TABLE estado_partido (
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
CREATE TABLE eventos (
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
        );
CREATE TABLE features_jugador_ventana (
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
CREATE TABLE formaciones_tacticas (
            id_cambio TEXT PRIMARY KEY,
            id_partido TEXT,
            equipo TEXT,
            minuto INTEGER,
            segundo INTEGER,
            formacion TEXT, -- Ej. 4-2-3-1, 4-3-3
            alineacion_json TEXT
        );
CREATE TABLE jugadores_partido (
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
CREATE TABLE partidos (
            id_partido TEXT PRIMARY KEY,
            rival TEXT,
            fecha TEXT,
            estadio TEXT,
            competencia TEXT
        );
CREATE TABLE pases (
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
CREATE TABLE posesiones (
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
CREATE TABLE remates (
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
        );
CREATE TABLE transiciones (
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
CREATE INDEX idx_eventos_possession
            ON eventos(id_partido, possession_id, event_index);
CREATE INDEX idx_eventos_tiempo
            ON eventos(id_partido, periodo, minuto, segundo);
CREATE INDEX idx_pases_progresivos
            ON pases(id_partido, equipo, progresivo);
CREATE INDEX idx_transiciones_partido
            ON transiciones(id_partido, equipo, hubo_tiro);
CREATE INDEX idx_features_jugador
            ON features_jugador_ventana(id_partido, jugador, ventana_minuto);
CREATE VIEW vw_posesiones_analiticas AS
        SELECT p.*,
               CASE WHEN p.tiros > 0 THEN 1 ELSE 0 END AS termina_en_tiro
        FROM posesiones p;
CREATE VIEW vw_transiciones AS
        SELECT t.*,
               CASE
                   WHEN t.zona_recuperacion = 'ATTACKING_THIRD'
                   THEN 1 ELSE 0
               END AS recuperacion_alta
        FROM transiciones t;
CREATE VIEW vw_jugador_partido AS
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
