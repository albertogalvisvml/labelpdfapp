from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import time
import traceback
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import mm
from io import BytesIO
import uuid


def generate_pdf(base_dir, custom_text, name_image, image_type):
    """
    Genera una imagen personalizada con texto sobrepuesto dentro de un área rectangular.
    Con bordes mejorados para un acabado más redondeado.
    
    Args:
        base_dir (str): Directorio base de la aplicación
        custom_text (str): Texto personalizado a escribir en la imagen
        name_image (str): Nombre base de la imagen a modificar
    
    Returns:
        dict: Información sobre la imagen generada o error
    """
    try:
        PUBLIC_DIR = os.path.join(base_dir, "public")
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        # Verificar ruta de la imagen base
        image_base_path = os.path.join(base_dir, "asset", f"{name_image}.png")
        if not os.path.exists(image_base_path):
            print(f"ERROR: La imagen base no existe en: {image_base_path}")
            return {"error": f"Imagen base no encontrada en {image_base_path}"}
        
        print(f"Intentando abrir imagen desde: {image_base_path}")
        # Abre la imagen preservando transparencia
        image_base = Image.open(image_base_path).convert("RGBA")
        print(f"Imagen abierta correctamente, tamaño: {image_base.size}, modo: {image_base.mode}")
        
        # Crear un nuevo canvas transparente del mismo tamaño pero con resolución 2x para mejor calidad
        scale_factor = 2
        high_res_size = (image_base.size[0] * scale_factor, image_base.size[1] * scale_factor)
        txt_layer = Image.new("RGBA", high_res_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Verificar ruta de la fuente
        font_path = os.path.join("fonts", "Coke-Regular.otf")
        if not os.path.exists(font_path):
            print(f"ERROR: El archivo de fuente no existe en: {font_path}")
            print(f"Intentando ruta absoluta...")
            font_path = os.path.join(base_dir, "fonts", "Coke-Regular.otf")
            if not os.path.exists(font_path):
                print(f"ERROR: El archivo de fuente tampoco existe en: {font_path}")
                print(f"Usando fuente por defecto")
                font = ImageFont.load_default()
            else:
                # Usaremos un tamaño inicial escalado para la alta resolución
                initial_font_size = 90 * scale_factor
                font = ImageFont.truetype(font_path, initial_font_size)
        else:
            initial_font_size = 90 * scale_factor
            font = ImageFont.truetype(font_path, initial_font_size)
        
        # Definir los cuatro puntos que forman el área rectangular (escalados para alta resolución Botella)
        # area_points = [(153 * scale_factor, 184 * scale_factor), 
        #                (594 * scale_factor, 184 * scale_factor), 
        #                (153 * scale_factor, 303 * scale_factor), 
        #                (594 * scale_factor, 303 * scale_factor)]
        
        # Definir los cuatro puntos que forman el área rectangular (escalados para alta resolución latas)

        if image_type == "400":
            # ETIQUETA 400 ML
            area_points = [(233 * scale_factor, 119 * scale_factor),
                        (832 * scale_factor, 119 * scale_factor),
                        (233 * scale_factor, 218 * scale_factor),
                        (832 * scale_factor, 218 * scale_factor)]
        else:
            # ETIQUETA 500 ML (por defecto)
            area_points = [(235 * scale_factor, 150 * scale_factor),
                        (623 * scale_factor, 150 * scale_factor),
                        (235 * scale_factor, 297 * scale_factor),
                        (623 * scale_factor, 297 * scale_factor)]      
        
        # Obtener las dimensiones del área rectangular
        min_x = min(point[0] for point in area_points)
        max_x = max(point[0] for point in area_points)
        min_y = min(point[1] for point in area_points)
        max_y = max(point[1] for point in area_points)
        
        # Calcular ancho y alto del área
        rect_width = max_x - min_x
        rect_height = max_y - min_y
        
        print(f"Área rectangular: x1={min_x}, y1={min_y}, ancho={rect_width}, alto={rect_height}")
        
        # Calcular el tamaño de fuente óptimo para el texto en alta resolución
        max_font_size = calculate_optimal_font_size(
            draw, custom_text, 
            rect_width * 0.95,       # 95% del ancho disponible
            rect_height * 0.9 + (10 * scale_factor),  # 90% del alto disponible + 10px adicionales (escalados)
            font_path, 
            initial_font_size
        )
        
        # Incrementamos el tamaño de la fuente en 15% para que sea más grande de lo calculado
        max_font_size = int(max_font_size * 1.15)
        
        font = ImageFont.truetype(font_path, max_font_size) if os.path.exists(font_path) else ImageFont.load_default()
        print(f"Tamaño de fuente óptimo calculado: {max_font_size}")
        
        # Calcular dimensiones del texto con la fuente óptima
        text_bbox = draw.textbbox((0, 0), custom_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Punto central del área rectangular
        center_x = min_x + (rect_width // 2)
        # Ajustamos el centro vertical un poco hacia arriba para compensar los 10px extras
        center_y = min_y + (rect_height // 2) - (5 * scale_factor)
        
        # Calcular posición para centrar el texto en el área
        x_position = center_x - (text_width // 2)
        y_position = center_y - (text_height // 2)
        
        print(f"Posición del texto: x={x_position}, y={y_position}, ancho={text_width}, alto={text_height}")
        
        # Configuración de colores (con canal alfa completo original)
        # color_borde = (231, 235, 236, 255)  # Blanco para el borde (totalmente opaco)
        # color_texto = (237, 26, 59, 0)    # Rojo para el texto (totalmente opaco)
        
        # Configuración de colores (con canal alfa completo zero)
        color_borde = (231, 235, 236, 255)  # Blanco para el borde (totalmente opaco)
        color_texto = (10, 10, 10, 255)    # Rojo para el texto (totalmente opaco)
        
        # Configuración de colores (con canal alfa completo diet)
        # color_borde = (237, 26, 59, 255)  # Blanco para el borde (totalmente opaco)
        # color_texto = (231, 235, 236, 0)    # Rojo para el texto (totalmente opaco)
        
        # Grosor del borde
        borde_grosor = 8 * scale_factor
        
        # MÉTODO MEJORADO: Usamos múltiples pasadas con distancias variadas para crear un borde más suave
        
        # Primera pasada: Borde exterior más grueso
        for angle in range(0, 360, 10):  # Incrementos de 10 grados para un borde circular
            radian = math.radians(angle)
            offset_x = int(math.cos(radian) * borde_grosor)
            offset_y = int(math.sin(radian) * borde_grosor)
            draw.text((x_position + offset_x, y_position + offset_y), 
                    custom_text, 
                    fill=color_borde, 
                    font=font)
        
        # Segunda pasada: Borde intermedio
        for angle in range(0, 360, 15):  # Incrementos de 15 grados
            radian = math.radians(angle)
            offset_x = int(math.cos(radian) * (borde_grosor * 0.7))
            offset_y = int(math.sin(radian) * (borde_grosor * 0.7))
            draw.text((x_position + offset_x, y_position + offset_y), 
                    custom_text, 
                    fill=color_borde, 
                    font=font)
        
        # Tercera pasada: Borde interior más fino
        for angle in range(0, 360, 20):  # Incrementos de 20 grados
            radian = math.radians(angle)
            offset_x = int(math.cos(radian) * (borde_grosor * 0.4))
            offset_y = int(math.sin(radian) * (borde_grosor * 0.4))
            draw.text((x_position + offset_x, y_position + offset_y), 
                    custom_text, 
                    fill=color_borde, 
                    font=font)
        
        # Dibujar el texto principal en rojo
        draw.text((x_position, y_position), custom_text, fill=color_texto, font=font)
        print(f"Texto '{custom_text}' dibujado con borde mejorado")
        
        # Aplicar un ligero desenfoque gaussiano para suavizar los bordes
        txt_layer = txt_layer.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Redimensionar de vuelta al tamaño original
        txt_layer = txt_layer.resize(image_base.size, Image.LANCZOS)
        
        # Combinar la capa de texto con la imagen original
        imagen_final = Image.alpha_composite(image_base, txt_layer)
        print("Capas combinadas exitosamente")
        
        # Crear carpeta output si no existe
        # output_dir = os.path.join(base_dir, "output") #botellas
        output_dir = os.path.join(base_dir, "output_can") #latas
        if not os.path.exists(output_dir):
            print(f"Creando carpeta de salida: {output_dir}")
            os.makedirs(output_dir)
        
        # Generar nombre con formato personalizado
        output_filename = f"{custom_text}+{name_image}.png"
        output_path = os.path.join(output_dir, output_filename)
        print(f"Intentando guardar imagen en: {output_path}")
        
        try:
            # Guardar como PNG para mantener transparencia
            imagen_final.save(output_path, format="PNG")

            pdf_filename = f"{custom_text}_{name_image}_{uuid.uuid4().hex[:6]}.pdf"
            pdf_path = os.path.join(PUBLIC_DIR, pdf_filename)

            # Configuración de resolución (300 DPI)
            DPI = 300
            PIXELS_PER_POINT = DPI / 72  # 72 puntos por pulgada es la base de PDF

            # Convertir dimensiones de píxeles a puntos para 300 DPI
            img_width_pt = imagen_final.width / PIXELS_PER_POINT
            img_height_pt = imagen_final.height / PIXELS_PER_POINT

            # Crear PDF con tamaño personalizado basado en la imagen
            custom_page_size = (img_width_pt, img_height_pt)
            c = canvas.Canvas(pdf_path, pagesize=custom_page_size)
            
            # Dibujar la imagen a tamaño completo con alta resolución
            c.drawImage(
                output_path,
                x=0,
                y=0,
                width=img_width_pt,
                height=img_height_pt,
                preserveAspectRatio=True,
                mask='auto'
            )
            
            # Configurar metadatos para impresión profesional
            c.setTitle(f"Etiqueta {custom_text}")
            c.setAuthor("Sistema de Generación de Etiquetas")
            c.setSubject(f"Etiqueta personalizada {name_image}")
            
            # Asegurar calidad de impresión
            c.setPageCompression(0)  # 0 = sin compresión para máxima calidad
            c.save()

            # Opcional: Verificar tamaño físico resultante
            width_inches = imagen_final.width / DPI
            height_inches = imagen_final.height / DPI
            print(f"Tamaño físico del PDF: {width_inches:.2f} x {height_inches:.2f} pulgadas")

            #image.save(output_path.replace(".png", ".pdf"), "PDF", resolution=100.0)
            print(f"Imagen guardada exitosamente como PNG")
        except Exception as e:
            print(f"Error al guardar la imagen: {e}")
            traceback.print_exc()
            return {"error": f"No se pudo guardar la imagen: {str(e)}"}
        
        if os.path.exists(output_path):
            print(f"Verificado: El archivo existe en {output_path}")
            file_size = os.path.getsize(output_path)
            print(f"Tamaño del archivo: {file_size} bytes")
        else:
            print(f"ERROR: El archivo no existe después de guardarlo")
            return {"error": "La imagen no se creó correctamente"}
        
        print(f"Procesamiento completado con éxito")
        
        # Extraer solo el nombre del archivo sin la ruta
        file_name = os.path.basename(output_filename)
        
        return {
            "success": True,
            "image_path": output_path,
            "pdf_path": pdf_path,
            "pdf_url": f"/public/{pdf_filename}",
            "filename": pdf_filename
        }
        
    except Exception as e:
        print(f"Error general en la función: {e}")
        traceback.print_exc()
        return {"error": str(e)}

def calculate_optimal_font_size(draw, text, max_width, max_height, font_path, start_size=100, min_size=8):
    """
    Calcula el tamaño de fuente óptimo para que el texto quepa en dimensiones máximas dadas
    
    Args:
        draw: Objeto ImageDraw
        text: Texto a dibujar
        max_width: Ancho máximo disponible
        max_height: Alto máximo disponible
        font_path: Ruta a la fuente
        start_size: Tamaño inicial para probar
        min_size: Tamaño mínimo aceptable
        
    Returns:
        int: Tamaño de fuente óptimo
    """
    size = start_size
    font = ImageFont.truetype(font_path, size) if os.path.exists(font_path) else ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    while (text_width > max_width or text_height > max_height) and size > min_size:
        size -= 2
        font = ImageFont.truetype(font_path, size) if os.path.exists(font_path) else ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    
    return size
