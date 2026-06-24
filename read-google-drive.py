from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential
import datetime
import os
import io
import time
import random
import string
from dotenv import load_dotenv

load_dotenv()

# google-api-python-client==2.187.0
# google-auth-httplib2==0.2.1
# google-auth-oauthlib==1.2.3
# azure-common==1.1.28
# azure-identity==1.19.0
# azure-storage-blob==12.24.0

# === CONFIG ===
SERVICE_ACCOUNT_FILE = os.getenv("GDRIVE_SERVICE_ACCOUNT_FILE", "driveread-478714-8c043125ed61.json")
# FOLDER_ID = "1e4dvDJ0mp97e5_2idSLGHOVl97734S6X"
FOLDER_ID = "1FHeWZkRHpPt8OkJkR_6dWNJXLJijVfe9"

# === AUTH ===
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("drive", "v3", credentials=creds)

tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

account_name = os.getenv("GDRIVE_AZURE_ACCOUNT_NAME", "stpnis")
container_name = os.getenv("GDRIVE_AZURE_CONTAINER", "testdsci")


def list_files_in_folder(folder_id):
    """Listar archivos (incluyendo subcarpetas) dentro de una carpeta."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        pageToken=None,
        pageSize=1000, 
    ).execute()

    return results.get("files", [])


def download_pdf(file_id, filename):
    """Descargar un archivo PDF por ID."""
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Descargando {filename}: {int(status.progress() * 100)}%")


def listar_carpetas_recursivo(folder_id, indent=0):
    """Lista carpetas dentro de una carpeta de forma recursiva."""
    
    query = (
        f"'{folder_id}' in parents and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )

    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    carpetas = results.get("files", [])

    for carpeta in carpetas:
        print("  " * indent + f"- {carpeta['name']}  (ID: {carpeta['id']})")
        
        # Llamada recursiva para subcarpetas
        listar_carpetas_recursivo(carpeta["id"], indent + 1)


def get_client():
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    blob_service_url = f"https://{account_name}.blob.core.windows.net/"
    return BlobServiceClient(account_url=blob_service_url, credential=credential)


def upload_file(file, blob_name):
    client = get_client()
    blob_client = client.get_blob_client(container=container_name, blob=blob_name)
    try:
        blob_client.upload_blob(file, overwrite=True)
    except Exception as e:
        print("Error uploading file:", e)
        return ""
    resultado = blob_client.url.split(container_name + "/")
    return resultado[1]


def transfer_pdf_to_azure(file_id, blob_name):
    """
    Descarga un PDF desde Google Drive (en memoria) y lo sube al Azure Blob Storage.
    No se generan archivos temporales.
    """

    # === 1. DESCARGAR DESDE GOOGLE DRIVE A MEMORIA ===
    request = service.files().get_media(fileId=file_id)
    pdf_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(pdf_buffer, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        # print(f"Descargando desde GDrive: {int(status.progress() * 100)}%")

    # Muy importante: rebobinar el buffer antes de subirlo
    pdf_buffer.seek(0)

    # === 2. SUBIR AL AZURE BLOB STORAGE ===
    client = get_client()
    blob_client = client.get_blob_client(container=container_name, blob=blob_name)

    try:
        blob_client.upload_blob(pdf_buffer, overwrite=True)
        # print("Archivo subido correctamente a Azure.")
    except Exception as e:
        print("Error al subir archivo:", e)
        return ""

    resultado = blob_client.url.split(container_name + "/")
    return resultado[1]


def genera_unique_id():
    # timestamp en milisegundos → base 36
    ts_ms = int(time.time() * 1000)
    timestamp = base36(ts_ms)

    # random → 6 caracteres base 36
    rnd = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

    return f"{timestamp}{rnd}"


def base36(num):
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""

    while num > 0:
        num, r = divmod(num, 36)
        result = chars[r] + result

    return result or "0"


def listar_archivos_hoy():
    blob_service_client = get_client()
    container_client = blob_service_client.get_container_client(container_name)

    hoy = datetime.datetime.utcnow().date()

    # list_blobs usa Paginación interna → eficiente
    blobs = container_client.list_blobs(name_starts_with="documentos/plan_inversion/")

    for blob in blobs:
        if blob.last_modified.date() == hoy:
            yield blob.name, blob.last_modified


def listar_archivos_pdfs(prefix):
    blob_service_client = get_client()
    container_client = blob_service_client.get_container_client(container_name)

    pdfs = []
    # list_blobs realiza paginación automáticamente
    for blob in container_client.list_blobs(name_starts_with=prefix):
        if blob.name.lower().endswith(".pdf"):
            # pdfs.append(blob)
            segmentos = blob.name.split("/")
            filename = segmentos[-1]
            partes = filename.rsplit("_", 1)
            if len(partes) > 1:
                pdfs.append(f"{partes[0]}.pdf")  # Recupera el # de cedula.

    return pdfs


def mover_archivos_desde_txt(ruta_txt):
    blob_service_client = get_client()
    container_client = blob_service_client.get_container_client(container_name)

    with open(ruta_txt, "r", encoding="utf-8") as f:
        archivos = [line.strip() for line in f if line.strip()]

    for archivo in archivos:
        origen = f"documentos/plan_inversion/{archivo}"
        destino = f"documentos/ficha/{archivo}"

        print(f"Moviendo: {origen} → {destino}")

        # 1️⃣ Copiar blob
        blob_origen = container_client.get_blob_client(origen)
        blob_destino = container_client.get_blob_client(destino)

        if not blob_origen.exists():
            print(f"❌ Archivo no existe en origen: {origen}")
            continue

        # Obtener URL del blob origen
        url_origen = blob_origen.url

        # Iniciar copia
        blob_destino.start_copy_from_url(url_origen)

        # 2️⃣ Borrar blob original
        blob_origen.delete_blob()

        print(f"✔ Movido correctamente: {archivo}")

    print("Proceso terminado.")



# === MAIN ===
carpetas_plan = [
    "1e4dvDJ0mp97e5_2idSLGHOVl97734S6X",
    "1FfiC4BizwLQELQZcaOzSPDBEr9kAVXE8",
    "1JMcmV2yp8l_V-bn1XYHUbFMa0fiKGFrQ",
    "1m4iXrEI_JYSCSSJtZ_ujNsfDA2Gl3EBN",
    "1o_zqtK4r1yfk-HvKbJDhAHCSVgskCGEn",
    "1NJ3jeZuqEZ4yaQZ90gSdpcYLBmuN6k6m",
]
carpetas_ficha = [
    "1MGDbslDKlIyeIoJaknWVdiilxCKwbqdJ",
    "1QigH4qsH8eJ1ZwlpTT_vIsjkMgC0jAmK",
    "136yta2R_E-aND3a1XsXZ5g_0vtHeYI9z",
    "1wu-DFPu7VN2fToOq2GvCiUgkDpTWCBj9",
    "1yJg5j3dmvzUFom3NmNHzkkUVHL41aBUb",
    "1fmqoitKL5aETVGiQNzXcsXkD9afM8jOM",
]

prefix = "narino_roberto_payan/"
existentes = listar_archivos_pdfs(prefix)
print(f"Archivos existentes en Azure bajo el prefijo '{prefix}': {len(existentes)}")
print(existentes)

# mover_archivos_desde_txt("fichas_subidas.txt")

# prefix = "documentos/plan_inversion/"
# prefix = "documentos/ficha/"
# existentes = listar_archivos_pdfs(prefix)
# subidos = []

# for carpeta in carpetas_ficha:
#     print(f"carpeta: {carpeta}")
#     files = list_files_in_folder(carpeta)
#     for f in files:
#         if f["name"] in existentes:
#             print(f"existente: {f['name']}")
#             continue
#         if f["mimeType"] == "application/pdf":
#             name, ext = os.path.splitext(f['name'])
#             filename = f"{name}_{genera_unique_id()}{ext}"
#             transfer_pdf_to_azure(f["id"], f"documentos/plan_inversion/{filename}")
#             subidos.append(filename)
#             print(f"subido: {filename}")
# with open("fichas_subidas.txt", "w", encoding="utf-8") as f:
#     for item in subidos:
#         f.write(f"{item}\n")
# print("Archivo generado: x")

# excluir = ['1004605359','1193587588','2471209','27520351','59673195','87949118','1003930325','1004603444','1004603445','1004603485','1004603578','1004603842','1004605638','1004605675','1004605719','1004605736','1004605749','1004605838','1004605883','1004605939','1004605968','1004606103','1004606748','1004611058','1004614778','1087187750','1087811368','12830933','12908216','13055897','13057135','41934714','51812608','5361557','59663204','59671324','59673407','59673416','59673443','59677280','59682669','59687900','66745135','66995389','67008991','87943352','87946645','87948552','87949833','87949867','98120001','98430979','1004606972','1004609804','1004611919','1004620822','1004637055','1004639771','1004640561','1004641198','1004712652','1010012528','1010070955','5364667','5364670','59662881','59671455','59674675','59677337','59677457','59678840','59678986','59686262','59688782','87940362','87941128','87948031','87949763','87970033','98429033']
# listar_carpetas_recursivo(FOLDER_ID)

# files = list_files_in_folder("1MGDbslDKlIyeIoJaknWVdiilxCKwbqdJ")
# for f in files:
#     print(f"- {f['name']}  ({f['mimeType']})")

# for nombre, fecha in listar_archivos_hoy():
#     print(nombre, fecha)

# for carpeta_id in carpetas:
#     print(f"Contenido de la carpeta ID: {carpeta_id}")
#     files = list_files_in_folder(carpeta_id)
#     for f in files:
        
#         # print(f"- {f['name']}  ({f['mimeType']})")
#         if f["mimeType"] == "application/pdf":
#             name, ext = os.path.splitext(f['name'])
#             if name in excluir:
#                 print(f"  >> Archivo excluido: {f['name']}")
#                 continue
#             filename = f"{name}_{genera_unique_id()}{ext}"
#             transfer_pdf_to_azure(f["id"], f"documentos/plan_inversion/{filename}")
# files = list_files_in_folder(FOLDER_ID)

# print("Archivos encontrados:")
# for f in files:
#     print(f"- {f['name']}  ({f['mimeType']})")

    # # Si es PDF → descargar
    # if f["mimeType"] == "application/pdf":
    #     download_pdf(f["id"], f["name"])

    # Si es una carpeta → mostrar ID para procesar recursivamente
    # if f["mimeType"] == "application/vnd.google-apps.folder":
    #     print(f"  >> Subcarpeta: {f['id']}")

# - ASOPORCA  (application/vnd.google-apps.folder)
# - RESCATE LAS VARAS  (application/vnd.google-apps.folder)
# - RIO ROSARIO  (application/vnd.google-apps.folder)
# - MEJICANO  (application/vnd.google-apps.folder)
# - CHAGUI  (application/vnd.google-apps.folder)
# - IMBILPI  (application/vnd.google-apps.folder)

## ficha
# 1MGDbslDKlIyeIoJaknWVdiilxCKwbqdJ
# 1QigH4qsH8eJ1ZwlpTT_vIsjkMgC0jAmK
# 136yta2R_E-aND3a1XsXZ5g_0vtHeYI9z     # mejicano
# 1wu-DFPu7VN2fToOq2GvCiUgkDpTWCBj9
# 1yJg5j3dmvzUFom3NmNHzkkUVHL41aBUb
# 1fmqoitKL5aETVGiQNzXcsXkD9afM8jOM

## plan
# 1e4dvDJ0mp97e5_2idSLGHOVl97734S6X ASOPORCA
# 1FfiC4BizwLQELQZcaOzSPDBEr9kAVXE8 RESCATE LAS VARAS
# 1JMcmV2yp8l_V-bn1XYHUbFMa0fiKGFrQ RIO ROSARIO
# 1m4iXrEI_JYSCSSJtZ_ujNsfDA2Gl3EBN MEJICANO
# 1o_zqtK4r1yfk-HvKbJDhAHCSVgskCGEn CHAGUI
# 1NJ3jeZuqEZ4yaQZ90gSdpcYLBmuN6k6m IMBILPI