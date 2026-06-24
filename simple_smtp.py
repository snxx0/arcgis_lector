import os
import smtplib
import ssl
from dotenv import load_dotenv

load_dotenv()

def simple_smtp_test():
    """Prueba básica de conexión SMTP"""

    # Configuración
    smtp_server = "smtp.office365.com"
    port = 587
    username = os.getenv("SMTP_USERNAME")  # Definido en .env
    password = os.getenv("SMTP_PASSWORD")  # Definido en .env
    
    try:
        # Conectar al servidor
        print(f"Conectando a {smtp_server}:{port}...")
        server = smtplib.SMTP(smtp_server, port)
        
        # Iniciar TLS
        server.starttls(context=ssl.create_default_context())
        print("TLS iniciado correctamente")
        
        # Autenticar
        server.login(username, password)
        print("✅ Autenticación exitosa!")
        
        # Obtener información
        print(f"\nInformación del servidor:")
        print(f"  Servidor: {smtp_server}")
        print(f"  Puerto: {port}")
        print(f"  Usuario: {username}")
        
        # Cerrar conexión
        server.quit()
        print("\nConexión cerrada correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"Detalle: {e}")
        return False

# Ejecutar prueba
if __name__ == "__main__":
    simple_smtp_test()