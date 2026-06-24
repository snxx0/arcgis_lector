import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import getpass
import sys

def test_smtp_connection():
    """
    Prueba la conexión SMTP con Outlook.office.com
    """
    print("=" * 50)
    print("TEST DE CONEXIÓN SMTP - OUTLOOK/OFFICE 365")
    print("=" * 50)
    
    # Configuración del servidor
    smtp_server = "smtp.office365.com"
    port = 587  # Puerto recomendado para STARTTLS
    
    # Solicitar credenciales de forma segura
    print("\n📧 Ingresa tus credenciales de Microsoft 365:")
    username = input("Correo electrónico (ej: usuario@dominio.com): ").strip()
    password = getpass.getpass("Contraseña (no se mostrará): ")
    
    # Opción: usar contraseña de aplicación si tienes MFA
    print("\n⚠️  ¿Tienes verificación en dos pasos (MFA) habilitada?")
    print("   Si es así, usa una 'Contraseña de aplicación'")
    print("   Generarla en: https://account.microsoft.com/security")
    print("-" * 50)
    
    # Correo de prueba
    recipient = input("\n📨 Correo destinatario (para prueba de envío, opcional): ").strip()
    
    if not recipient:
        print("\n⚠️  Sin destinatario - Solo probaré conexión/autenticación")
        test_only_connection = True
    else:
        test_only_connection = False
    
    try:
        # Crear conexión SMTP
        print(f"\n🔗 Conectando a {smtp_server}:{port}...")
        
        # Método 1: Usando starttls() explícito (recomendado)
        server = smtplib.SMTP(smtp_server, port, timeout=30)
        
        # Iniciar conexión
        server.ehlo()
        
        # Iniciar cifrado TLS
        print("🔒 Iniciando cifrado TLS...")
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        
        print("✅ Conexión establecida y cifrada")
        
        # Autenticación
        print(f"🔑 Autenticando como {username}...")
        server.login(username, password)
        print("✅ Autenticación exitosa")
        
        if not test_only_connection and recipient:
            # Enviar correo de prueba
            print(f"\n📤 Enviando correo de prueba a {recipient}...")
            
            # Crear mensaje
            message = MIMEMultipart("alternative")
            message["Subject"] = "📧 Prueba SMTP desde Python"
            message["From"] = username
            message["To"] = recipient
            
            # Contenido del correo
            text = f"""Hola,

Este es un correo de prueba enviado mediante Python SMTP.
Servidor: {smtp_server}:{port}
Usuario: {username}

✅ Si recibes este correo, la configuración SMTP es correcta.

Saludos,
Script de prueba Python
"""
            
            html = f"""<html>
  <body>
    <h2>✅ Prueba SMTP Exitosa</h2>
    <p>Este es un correo de prueba enviado mediante Python SMTP.</p>
    <ul>
      <li><strong>Servidor:</strong> {smtp_server}:{port}</li>
      <li><strong>Usuario:</strong> {username}</li>
    </ul>
    <p>Si recibes este correo, la configuración SMTP es correcta.</p>
    <hr>
    <p><em>Script de prueba Python</em></p>
  </body>
</html>"""
            
            # Adjuntar partes
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Enviar correo
            server.sendmail(username, recipient, message.as_string())
            print("✅ Correo enviado exitosamente")
        
        # Obtener información del servidor
        print("\n📊 Información del servidor:")
        try:
            # Algunos servidores soportan HELP
            help_response = server.help()
            print(f"  Respuesta HELP: {help_response[:100]}...")
        except:
            pass
        
        # Mostrar límites conocidos
        print("\n📋 Límites conocidos de Microsoft 365:")
        print("  • 10,000 destinatarios por día (plan E1/E3)")
        print("  • 30 mensajes por minuto")
        print("  • 10 MB límite por mensaje")
        
        # Cerrar conexión
        server.quit()
        print("\n🔌 Conexión cerrada correctamente")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Error de autenticación: {e}")
        print("\nPosibles soluciones:")
        print("  1. Verifica tu usuario y contraseña")
        print("  2. Si tienes MFA, usa una 'Contraseña de aplicación'")
        print("  3. Asegúrate de que la cuenta no esté bloqueada")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ Error de conexión al servidor: {e}")
        print("\nPosibles soluciones:")
        print("  1. Verifica tu conexión a internet")
        print("  2. El firewall podría bloquear el puerto 587")
        print("  3. Prueba con un puerto alternativo (25 o 465)")
        return False
        
    except smtplib.SMTPServerDisconnected as e:
        print(f"\n❌ Servidor desconectado: {e}")
        print("  1. El servidor podría haber cerrado la conexión")
        print("  2. Verifica los tiempos de espera")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ Error SMTP general: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {type(e).__name__}: {e}")
        return False

def test_multiple_ports():
    """
    Prueba conexión en diferentes puertos
    """
    print("\n" + "=" * 50)
    print("PRUEBA DE PUERTOS ALTERNATIVOS")
    print("=" * 50)
    
    smtp_server = "smtp.office365.com"
    ports_to_test = [587, 25, 465]
    
    for port in ports_to_test:
        print(f"\n🔍 Probando puerto {port}...")
        try:
            if port == 465:
                # Puerto 465 generalmente usa SSL desde el inicio
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(smtp_server, port, timeout=10, context=context)
                print(f"  ✅ Puerto {port} accesible (SSL)")
            else:
                server = smtplib.SMTP(smtp_server, port, timeout=10)
                if port == 587:
                    server.starttls(context=ssl.create_default_context())
                print(f"  ✅ Puerto {port} accesible")
            server.quit()
        except Exception as e:
            print(f"  ❌ Puerto {port} falló: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("TESTER SMTP PARA MICROSOFT 365 / OUTLOOK.OFFICE.COM")
    print("=" * 50)
    
    # Opciones
    print("\nOpciones:")
    print("  1. Probar conexión y enviar correo")
    print("  2. Solo probar conexión/autenticación")
    print("  3. Probar puertos alternativos")
    print("  4. Todas las pruebas")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    if choice == "1":
        test_smtp_connection()
    elif choice == "2":
        # Forzar solo prueba de conexión
        original_input = input
        input = lambda prompt: "test@example.com" if "destinatario" in prompt else original_input(prompt)
        test_smtp_connection()
    elif choice == "3":
        test_multiple_ports()
    elif choice == "4":
        test_smtp_connection()
        test_multiple_ports()
    else:
        print("Opción no válida")
    
    print("\n" + "=" * 50)
    print("PRUEBA COMPLETADA")
    print("=" * 50)