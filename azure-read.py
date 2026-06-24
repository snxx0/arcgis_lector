from azure.storage.blob import BlobServiceClient
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
import datetime, os

load_dotenv()

tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")
account_name = os.getenv("AZURE_READ_ACCOUNT_NAME")
container_name = os.getenv("AZURE_READ_CONTAINER", "media")

def get_client():
    credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    blob_service_url = f"https://{account_name}.blob.core.windows.net/"
    return BlobServiceClient(account_url=blob_service_url, credential=credential)


def existe_archivo(blob_name, container=""):
    client = get_client()
    if container == "":
        container = container_name
    blob_client = client.get_blob_client(container=container, blob=blob_name)
    return blob_client.exists()


def copiar_archivo(blob_name, nuevo_blob_name, container=""):
    client = get_client()
    if container == "":
        container = container_name
    source_blob = client.get_blob_client(container=container_name, blob=blob_name)
    destination_blob = client.get_blob_client(container=container_name, blob=nuevo_blob_name)
    source_blob_url = source_blob.url
    try:
        copy_operation = destination_blob.start_copy_from_url(source_blob_url)
        copy_status = destination_blob.get_blob_properties().copy.status
        if copy_status == 'success':
            return True
        else:
            return False
    except Exception as e:
        return False


def upload_file(file, blob_name, container=""):
    client = get_client()
    if container == "":
        container = container_name
    blob_client = client.get_blob_client(container=container, blob=blob_name)
    if blob_client.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        partes = os.path.splitext(blob_name)
        nuevo_blob_name = partes[0] + "_" + timestamp + partes[1]
        if not copiar_archivo(blob_name, nuevo_blob_name):
            return None
    try:
        blob_client.upload_blob(file, overwrite=True)
    except Exception as e:
        return None
    resultado = blob_client.url.split(container + "/")
    return resultado[1]


def descargar_archivo(blob_name, container=""):
    client = get_client()
    if container == "":
        container = container_name
    blob_client = client.get_blob_client(container=container, blob=blob_name)
    try:
        stream = blob_client.download_blob()
        return stream.readall()
    except Exception as e:
        return None

def listar_archivos(container=""):
    blob_service_client = get_client()
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs()
    output_file = "lista_blobs.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Listado de archivos en el contenedor: {container_name}\n")
        f.write(f"Generado el: {datetime.datetime.now()}\n\n")
        for blob in blob_list:
            f.write(f"{blob.name}\n")
            # Si quieres más información del blob, puedes incluirla:
            # f.write(f"Nombre: {blob.name} - Tamaño: {blob.size} bytes - Última modificación: {blob.last_modified}\n")
    print(f"Se ha generado el archivo {output_file} con la lista de blobs.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Listar archivos de Azure Blob Storage')
    parser.add_argument('--container', '-c', type=str, help='Nombre del contenedor')
    parser.add_argument('--list-containers', '-l', action='store_true', help='Listar todos los contenedores')
    
    args = parser.parse_args()
    
    # Configurar logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    if args.list_containers:
        listar_contenedores()
    else:
        # Si no se especifica contenedor, listar todos primero
        if not args.container:
            print("⚠️  No se especificó un contenedor.")
            containers = listar_contenedores()
            
            if containers:
                respuesta = input("\n¿Deseas listar archivos de algún contenedor? (s/n): ")
                if respuesta.lower() == 's':
                    container_name = input("Ingresa el nombre del contenedor: ")
                    listar_archivos(container_name)
            else:
                print("No se encontraron contenedores.")
        else:
            listar_archivos(args.container)