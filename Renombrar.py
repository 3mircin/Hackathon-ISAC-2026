import os
import requests
import json
import unicodedata
from dotenv import load_dotenv

load_dotenv()
AUTH = (os.getenv('STATSBOMB_USER'), os.getenv('STATSBOMB_PASS'))
BASE_URL = "https://data.statsbomb.com/api/v6"

LIGA_MX_ID = 73
TEMPORADAS_IDS = [108, 235, 281, 317, 318, 351]
DT_OBJETIVO = "André Soares Jardine"

def limpiar_nombre(texto):
    return texto.replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")

def normalizar_texto(texto):
    texto = texto or ""
    return "".join(
        caracter for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    ).casefold().strip()

def dirige_objetivo(partido):
    objetivo = normalizar_texto(DT_OBJETIVO)
    managers = (
        partido.get("home_team", {}).get("managers") or []
    ) + (
        partido.get("away_team", {}).get("managers") or []
    )
    return any(
        normalizar_texto(manager.get("name")) == objetivo
        for manager in managers
    )

def renombrar_archivos_existentes():
    os.makedirs("data/eventos_ordenados", exist_ok=True)
    
    # Mapear match_id con su nombre amigable consultando la API de partidos (sin descargar eventos pesados)
    print(" Mapeando IDs con nombres de partidos...")
    mapa_partidos = {}
    
    for season_id in TEMPORADAS_IDS:
        url_partidos = f"{BASE_URL}/competitions/{LIGA_MX_ID}/seasons/{season_id}/matches"
        res = requests.get(url_partidos, auth=AUTH)
        if res.status_code == 200:
            for partido in res.json():
                if dirige_objetivo(partido):
                    m_id = partido["match_id"]
                    local = limpiar_nombre(partido['home_team']['home_team_name'])
                    visita = limpiar_nombre(partido['away_team']['away_team_name'])
                    fecha = partido['match_date']
                    mapa_partidos[m_id] = f"{local}_vs_{visita}_{fecha}.json"

    # Revisar los archivos que ya descargaste en la carpeta 'data/eventos'
    carpeta_origen = "data/eventos"
    if not os.path.exists(carpeta_origen):
        print(" No se encontró la carpeta data/eventos. Asegúrate de que tus archivos estén ahí.")
        return

    archivos = os.listdir(carpeta_origen)
    movidos = 0

    for archivo in archivos:
        if archivo.endswith(".json"):
            match_id_str = archivo.replace(".json", "")
            try:
                match_id = int(match_id_str)
            except ValueError:
                continue
                
            if match_id in mapa_partidos:
                nombre_amigable = mapa_partidos[match_id]
                origen = os.path.join(carpeta_origen, archivo)
                destino = os.path.join("data/eventos_ordenados", nombre_amigable)
                
                # Copiar o renombrar el archivo a la nueva carpeta limpia
                with open(origen, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(destino, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                    
                print(f"✨ Renombrado: {archivo} ➡️ {nombre_amigable}")
                movidos += 1

    print(f"\n✅ ¡Listo! Se ordenaron y renombraron {movidos} archivos en la carpeta `data/eventos_ordenados`.")

if __name__ == "__main__":
    renombrar_archivos_existentes()