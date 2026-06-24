from datetime import datetime
import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    # sys.argv[0] es el nombre del script
    # sys.argv[1] es el primer parámetro, etc.
    
    if len(sys.argv) < 2:
        print("Uso: python script.py <parámetro>")
        sys.exit(1)
    
    parametro = sys.argv[1]
    cedula = str(parametro)
    
    url = "https://www.arcgis.com/sharing/rest/oauth2/token"
    data = {
        "client_id": os.getenv("ARCGIS_CLIENT_ID"),
        "client_secret": os.getenv("ARCGIS_CLIENT_SECRET"),
        "grant_type": "client_credentials"
    }

    response = requests.post(url, data=data)
    token_info = response.json()
    rows = {"capa1":[], "capa2":[]}
    # busqueda en predios_pol por cedula
    url_base = "https://services5.arcgis.com/glfMbWySNTqABUGO/ArcGIS/rest/services/"

    # url_capa1 = url_base + "Predios_Pol_AC/FeatureServer/0/query?where=Cedula=" + cedula + "&outFields=*&f=json&token=" + token_info['access_token']
    url_capa1 = url_base + "Lote_levantamiento_/FeatureServer/0/query?where=Cedula=" + cedula + "&outFields=*&f=json&token=" + token_info['access_token']
    response = requests.post(url_capa1, data=data)
    arc_info = response.json()
    features = arc_info.get('features', [])    
    for feature in features:
        attributes = feature.get('attributes', {})
        if attributes:
            rows["capa1"].append(attributes)

    # url_capa2 = url_base + "Predios_Pol_Validacion_AC/FeatureServer/0/query?where=Cedula=" + cedula + "&outFields=*&f=json&token=" + token_info['access_token']
    url_capa2 = url_base + "Lote_levantamiento_QC_/FeatureServer/0/query?where=Cedula=" + cedula + "&outFields=*&f=json&token=" + token_info['access_token']
    response = requests.post(url_capa2, data=data)
    arc_info = response.json()
    features = arc_info.get('features', [])    
    for feature in features:
        attributes = feature.get('attributes', {})
        if attributes:
            rows["capa2"].append(attributes)
    
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")  # Formato: AAAAMMDD_HHMMSS
    nombre_archivo = f"{cedula}_{fecha_hora}.json"
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"creado {nombre_archivo}")

if __name__ == "__main__":
    main()