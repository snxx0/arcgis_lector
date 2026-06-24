from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io

def agregar_imagen_moderno(pdf_entrada, pdf_salida, ruta_imagen):
    """
    Versión más moderna usando pypdf en lugar de PyPDF2
    """
    # Leer PDF original
    reader = PdfReader(pdf_entrada)
    writer = PdfWriter()
    
    # Obtener dimensiones de la página
    pagina_ref = reader.pages[0]
    ancho_pagina = float(pagina_ref.mediabox.width)
    alto_pagina = float(pagina_ref.mediabox.height)
    
    # Crear superposición para página 3
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(ancho_pagina, alto_pagina))
    
    # Calcular posición (3/4 desde el inicio)
    pos_y = alto_pagina * 0.58
    pos_x = (ancho_pagina - 100) / 2  # Centrado horizontal
    
    # Agregar imagen (asumiendo 100x50 puntos en el PDF)
    can.drawImage(ruta_imagen, pos_x, pos_y, width=100, height=50)
    can.save()
    
    packet.seek(0)
    overlay = PdfReader(packet)
    
    # Combinar páginas
    for i, page in enumerate(reader.pages):
        if i == 3:  # Página 4
            page.merge_page(overlay.pages[0])
        writer.add_page(page)
    
    # Guardar resultado
    with open(pdf_salida, 'wb') as f:
        writer.write(f)

# Uso
agregar_imagen_moderno("5428248.pdf", "modificado_5428248_2.pdf", "img_catatumbo Editado/5428248.jpeg")