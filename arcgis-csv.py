# (probablemente Web Mercator Auxiliary Sphere, EPSG:3857)
import csv
from datetime import datetime
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def main():
    # sys.argv[0] es el nombre del script
    # sys.argv[1] es el primer parámetro, etc.
    
    lenArgs = len(sys.argv)
    if lenArgs < 2:
        print("Uso: python arcgis-csv.py <clausula_where> <capa> <offset>")
        sys.exit(1)

    clausula = sys.argv[1]
    capa = '1'
    offset = '0'
    if lenArgs > 2:
        arg_capa = sys.argv[2]
        if arg_capa is None:
            capa = '1'
        else:
            capa = '2' if arg_capa == '2' else '1'
        if lenArgs > 3:
            arg_offset = sys.argv[3]
            if arg_offset is None:
                offset = '0'
            else:
                offset = '0' if arg_offset=='0' else arg_offset

    url_token = "https://www.arcgis.com/sharing/rest/oauth2/token"
    data = {
        "client_id": os.getenv("ARCGIS_CLIENT_ID"),
        "client_secret": os.getenv("ARCGIS_CLIENT_SECRET"),
        "grant_type": "client_credentials"
    }
    # capa 1
    base_capa1 = "https://services5.arcgis.com/glfMbWySNTqABUGO/ArcGIS/rest/services/Lote_levantamiento_/FeatureServer/0/query"
    # capa 2
    base_capa2 = "https://services5.arcgis.com/glfMbWySNTqABUGO/ArcGIS/rest/services/Lote_levantamiento_QC_/FeatureServer/0/query"

    response = requests.post(url_token, data=data)
    token_info = response.json()

    base_capa = base_capa1 if capa == '1' else base_capa2
    features = []
    offset = 0
    page_size = 2000  # límite típico en ArcGIS

    for ind in range(0, 20):  # límite arbitrario alto para evitar bucles infinitos
        url = f"{base_capa}?where={clausula}&outFields=*&resultOffset={offset}&f=json&token=" + token_info['access_token']

        # Hacer la petición POST
        response = requests.post(url, data={})
        arc_info = response.json()

        features_page = arc_info.get("features", [])
        features.extend(features_page)
        offset += page_size  # avanzar a la siguiente página
        if len(features_page) < page_size:
            break  # ya no hay más datos

    print(f"Cargados: {len(features)} registros...")

    rows = []
    for feature in features:
        attributes = feature.get('attributes', {})
        row = {
            'OBJECTID': attributes.get('OBJECTID', ''),
            'Validado': attributes.get('Validado', ''),
            'Validacion_Coca': attributes.get('Validacion_Coca', ''),
            'VALIDACION_COCA_SIG': attributes.get('VALIDACION_COCA_SIG', ''),
            'EditDate': attributes.get('EditDate', ''),
            'Area_Lote': attributes.get('Area_Lote', ''),
            'Coca_Observada': attributes.get('Coca_Observada', ''),
            'NMG_Residente': attributes.get('NMG_Residente', ''),
            'Cedula': attributes.get('Cedula', ''),
            'Telefono': attributes.get('Telefono', ''),
            'Departamento': attributes.get('Departamento', ''),
            'NMG_Municipio': attributes.get('NMG_Municipio', ''),
            'NMG_Vereda': attributes.get('NMG_Vereda', ''),
            'Fase': attributes.get('Fase', ''),
            'NMG_Predio': attributes.get('NMG_Predio', ''),
            'ID_Predio': attributes.get('ID_Predio', ''),
            'Fecha_Levantamiento': attributes.get('Fecha_Levantamiento', ''),
            'Encuestador': attributes.get('Encuestador', ''),
            'Telefono_Encuestador': attributes.get('Telefono_Encuestador', ''),   
            'Edad_Cultivo': attributes.get('Edad_Cultivo', ''),
            'Intercalado': attributes.get('Intercalado', ''),
            'Metodo_de_Captura': attributes.get('Metodo_de_Captura', ''),
            'Altitud': attributes.get('Altitud', ''),
            'Observaciones': attributes.get('Observaciones', ''),
            'NMG_Vereda_Geografica': attributes.get('NMG_Vereda_Geografica', ''),
            # 'Poligono_WKT': attributes.get('Poligono_WKT', ''),
            'MUNICIPIO_GEOGRAFICO': attributes.get('MUNICIPIO_GEOGRAFICO', ''),
            'NUCLEO_VEREDAL_GEOGRAFICO': attributes.get('NUCLEO_VEREDAL_GEOGRAFICO', ''),
            'COD_VERE': attributes.get('COD_VERE', ''),
            'VEREDA_GEOGRAFICA': attributes.get('VEREDA_GEOGRAFICA', ''),
            'COORDENADA_MUNICIPIO': attributes.get('COORDENADA_MUNICIPIO', ''),
            'COORDENADA_ZONA_URBANA': attributes.get('COORDENADA_ZONA_URBANA', ''),
            'NUCLEO_FORESTAL': attributes.get('NUCLEO_FORESTAL', ''),
            'RESERVA_CAMPESINA_LEGALIZADA': attributes.get('RESERVA_CAMPESINA_LEGALIZADA', ''),
            'RESERVA_CAMPESINA_SOLICITADA': attributes.get('RESERVA_CAMPESINA_SOLICITADA', ''),
            'RESGUARDO_INDIGENA_LEGALIZADO': attributes.get('RESGUARDO_INDIGENA_LEGALIZADO', ''),
            'RESGUARDO_INDIGENA_SOLICITADO': attributes.get('RESGUARDO_INDIGENA_SOLICITADO', ''),
            'CONSEJO_COMUNITARIO_LEGALIZADO': attributes.get('CONSEJO_COMUNITARIO_LEGALIZADO', ''),
            'CONSEJO_COMUNITARIO_SOLICITADO': attributes.get('CONSEJO_COMUNITARIO_SOLICITADO', ''),
            'RUNAP': attributes.get('RUNAP', ''),
            'LEY_2DA': attributes.get('LEY_2DA', ''),
            'SIIMA_DICIEMBRE_2024': attributes.get('SIIMA_DICIEMBRE_2024', ''),
            'PROYECTO_PRODUCTIVO_PNIS': attributes.get('PROYECTO_PRODUCTIVO_PNIS', ''),
            'LOTE_COCA_PNIS': attributes.get('LOTE_COCA_PNIS', ''),
            'SIIMA_AGOSTO_2023': attributes.get('SIIMA_AGOSTO_2023', ''),
            'SIIMA_ABRIL_2025': attributes.get('SIIMA_ABRIL_2025', ''),
            'SIIMA_AGOSTO_2025': attributes.get('SIIMA_AGOSTO_2025', ''),
            'SIIMA_DICIEMBRE_2025': attributes.get('SIIMA_DICIEMBRE_2025', ''),
            'SIMCI_DICIEMBRE_2024': attributes.get('SIMCI_DICIEMBRE_2024', ''),
            'COCA_OBSERVADA': attributes.get('Coca_Observada', ''),
            'GlobalID': attributes.get('GlobalID', ''),
            'Shape__Area': attributes.get('Shape__Area', ''),
            'Shape__Length': attributes.get('Shape__Length', '')
        }
        rows.append(row)

    # 3. Guardar en un archivo CSV
    if rows:
        print(f"leidos {len(rows)} registros")
        fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")  # Formato: AAAAMMDD_HHMMSS
        nombre_archivo = f"salida_{fecha_hora}.csv"
        csv_columns = rows[0].keys()  # Usar las claves del primer registro como columnas
        with open(nombre_archivo, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_columns)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Archivo CSV generado: {nombre_archivo}")
    else:
        print("No se encontraron datos para procesar.")


if __name__ == "__main__":
    main()