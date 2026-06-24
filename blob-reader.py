import os
import datetime
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

# Cargar variables de entorno
load_dotenv()

def get_client():
    """
    Obtiene el cliente de Blob Service usando diferentes métodos de autenticación.
    Prioridad: 1. Connection String, 2. Account Key, 3. SAS Token
    """
    # Método 1: Connection String
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if connection_string:
        try:
            return BlobServiceClient.from_connection_string(connection_string)
        except Exception as e:
            print(f"Error con connection string: {e}")
    
    # Método 2: Account Name y Account Key
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    if account_name and account_key:
        try:
            account_url = f"https://{account_name}.blob.core.windows.net"
            return BlobServiceClient(account_url=account_url, credential=account_key)
        except Exception as e:
            print(f"Error con account key: {e}")
    
    # Método 3: SAS Token
    sas_token = os.getenv("AZURE_STORAGE_SAS_TOKEN")
    if account_name and sas_token:
        try:
            account_url = f"https://{account_name}.blob.core.windows.net"
            # Si el SAS token no empieza con ?, lo añadimos
            if not sas_token.startswith('?'):
                sas_token = '?' + sas_token
            return BlobServiceClient(account_url=account_url, credential=sas_token)
        except Exception as e:
            print(f"Error con SAS token: {e}")
    
    # Método 4: Managed Identity (para entornos de Azure)
    try:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
        account_url = f"https://{account_name}.blob.core.windows.net"
        return BlobServiceClient(account_url=account_url, credential=credential)
    except ImportError:
        print("azure-identity no está instalado. Instala con: pip install azure-identity")
    except Exception as e:
        print(f"Error con Managed Identity: {e}")
    
    raise ValueError("No se pudo autenticar con Azure Blob Storage. Verifica tus credenciales.")

def listar_archivos(container_name=""):
    """
    Lista todos los archivos en un contenedor de Azure Blob Storage
    y guarda la lista en un archivo de texto.
    
    Args:
        container_name (str): Nombre del contenedor a listar
    """
    if not container_name:
        container_name = os.getenv("AZURE_STORAGE_CONTAINER", "default-container")
        print(f"Usando contenedor por defecto: {container_name}")
    
    try:
        # Obtener cliente
        blob_service_client = get_client()
        
        # Obtener cliente del contenedor
        container_client = blob_service_client.get_container_client(container_name)
        
        # Verificar si el contenedor existe
        if not container_client.exists():
            raise ResourceNotFoundError(f"El contenedor '{container_name}' no existe.")
        
        # Listar blobs
        print(f"Listando archivos en el contenedor: {container_name}...")
        blob_list = container_client.list_blobs()
        
        # Contadores
        total_blobs = 0
        total_size = 0
        
        # Preparar datos
        blobs_data = []
        for blob in blob_list:
            total_blobs += 1
            total_size += blob.size if blob.size else 0
            
            # Formatear tamaño
            size_str = ""
            if blob.size:
                if blob.size < 1024:
                    size_str = f"{blob.size} B"
                elif blob.size < 1024 * 1024:
                    size_str = f"{blob.size / 1024:.2f} KB"
                elif blob.size < 1024 * 1024 * 1024:
                    size_str = f"{blob.size / (1024 * 1024):.2f} MB"
                else:
                    size_str = f"{blob.size / (1024 * 1024 * 1024):.2f} GB"
            
            # Formatear fecha
            date_str = ""
            if blob.last_modified:
                date_str = blob.last_modified.strftime("%Y-%m-%d %H:%M:%S")
            
            blobs_data.append({
                'name': blob.name,
                'size': size_str,
                'size_bytes': blob.size,
                'last_modified': date_str,
                'blob_type': blob.blob_type if hasattr(blob, 'blob_type') else 'Unknown',
                'content_type': blob.content_settings.content_type if hasattr(blob, 'content_settings') else 'Unknown'
            })
        
        # Ordenar por nombre (opcional)
        blobs_data.sort(key=lambda x: x['name'].lower())
        
        # Generar archivo de salida
        output_file = f"lista_blobs_{container_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Encabezado
            f.write("=" * 80 + "\n")
            f.write(f"LISTADO DE ARCHIVOS EN AZURE BLOB STORAGE\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Contenedor: {container_name}\n")
            f.write(f"Cuenta de almacenamiento: {blob_service_client.account_name}\n")
            f.write(f"Fecha de generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total de archivos: {total_blobs}\n")
            f.write(f"Tamaño total: {total_size / (1024*1024):.2f} MB\n")
            f.write("-" * 80 + "\n\n")
            
            # Lista detallada
            f.write("LISTA DETALLADA:\n")
            f.write("-" * 80 + "\n")
            
            for i, blob_data in enumerate(blobs_data, 1):
                f.write(f"{i:4d}. {blob_data['name']}\n")
                f.write(f"     Tamaño: {blob_data['size']}\n")
                f.write(f"     Última modificación: {blob_data['last_modified']}\n")
                f.write(f"     Tipo: {blob_data['blob_type']}\n")
                f.write(f"     Content-Type: {blob_data['content_type']}\n")
                f.write("\n")
        
        print(f"\n✅ Se ha generado el archivo: {output_file}")
        print(f"📊 Resumen:")
        print(f"   - Total de archivos: {total_blobs}")
        print(f"   - Tamaño total: {total_size / (1024*1024):.2f} MB")
        
        # También mostrar en consola los primeros 10 archivos
        print(f"\n📁 Primeros 10 archivos:")
        for i, blob_data in enumerate(blobs_data[:10], 1):
            print(f"   {i:2d}. {blob_data['name']} ({blob_data['size']})")
        
        if total_blobs > 10:
            print(f"   ... y {total_blobs - 10} más")
        
        return {
            'output_file': output_file,
            'total_blobs': total_blobs,
            'total_size': total_size,
            'container_name': container_name
        }
        
    except ResourceNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Verifica que el contenedor exista y tengas permisos de lectura.")
    except HttpResponseError as e:
        print(f"❌ Error de Azure: {e.message}")
        print(f"   Código de error: {e.error_code}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def listar_contenedores():
    """
    Lista todos los contenedores disponibles en la cuenta de almacenamiento.
    """
    try:
        blob_service_client = get_client()
        
        print("📦 Contenedores disponibles:")
        print("-" * 50)
        
        containers = blob_service_client.list_containers()
        container_list = []
        
        for container in containers:
            container_list.append(container.name)
            print(f"  • {container.name}")
            
            # Obtener propiedades del contenedor
            container_client = blob_service_client.get_container_client(container.name)
            properties = container_client.get_container_properties()
            
            # Mostrar información adicional si está disponible
            if hasattr(properties, 'last_modified'):
                print(f"    Última modificación: {properties.last_modified}")
            print()
        
        return container_list
        
    except Exception as e:
        print(f"❌ Error al listar contenedores: {e}")
        return []

# Script principal
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