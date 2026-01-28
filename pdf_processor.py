# pdf_processor.py - VERSION CORREGIDA PARA ROTACIÓN

# ... (mantener imports y funciones de log igual) ...

def crear_folio_pdf(page_width, page_height, folio_text, font, font_size, 
                    offset_cm, corner, orientation, rotation=0) -> BytesIO:
    """Crea un PDF en memoria ajustando las coordenadas según la rotación de la página."""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    can.setFont(font, font_size)

    margin = offset_cm * cm

    # --- Lógica de Compensación de Rotación ---
    # Si la página está rotada 180°, invertimos las posiciones lógicas
    temp_corner = corner
    if rotation == 180:
        if "bottom" in corner: temp_corner = temp_corner.replace("bottom", "top")
        elif "top" in corner: temp_corner = temp_corner.replace("top", "bottom")
        
        if "right" in corner: temp_corner = temp_corner.replace("right", "left")
        elif "left" in corner: temp_corner = temp_corner.replace("left", "right")

    # --- Cálculo de Posición ---
    if "right" in temp_corner:
        x_position = page_width - margin
        align_func = can.drawRightString
    else: 
        x_position = margin 
        align_func = can.drawString
    
    if "bottom" in temp_corner:
        y_position = margin 
    else: 
        y_position = page_height - margin - font_size 
    
    # --- Aplicación de Orientación ---
    if orientation == "vertical":
        can.translate(x_position, y_position)
        # Si la página está a 180°, el texto también debe girar 180° extra para no salir de cabeza
        can.rotate(90 if rotation == 0 else 270)
        can.drawString(0, 0, folio_text)
    else: 
        # Si la página está a 180°, giramos el texto sobre su eje para que se lea derecho
        if rotation == 180:
            can.saveState()
            can.translate(x_position, y_position)
            can.rotate(180)
            can.drawString(0, 0, folio_text)
            can.restoreState()
        else:
            align_func(x_position, y_position, folio_text)
            
    can.save()
    packet.seek(0)
    return packet


def agregar_folios_web(input_path, output_path, font="Courier-Bold", font_size=16, 
                       start_number=1, offset_cm=1, 
                       corner="bottom-right", orientation="horizontal",
                       start_page=1, end_page=None, 
                       preview_mode=False) -> bool:
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        if reader.is_encrypted:
            log_error("PDF cifrado detectado", details=input_path)
            return False

        total_pages_in_file = len(reader.pages)
        start_index = max(0, int(start_page) - 1) 
        
        if end_page is None or end_page == "" or int(end_page) == 0:
            end_index = total_pages_in_file
        else:
            end_index = min(total_pages_in_file, int(end_page))
        
        # Procesar páginas anteriores
        if not preview_mode:
            for i in range(start_index):
                writer.add_page(reader.pages[i]) 

        # Foliar rango
        folio_actual = start_number
        for i in range(start_index, end_index):
            page = reader.pages[i]
            folio_text = f"{folio_actual:04}" 

            # LEER ROTACIÓN REAL DE LA PÁGINA
            rotation = page.get('/Rotate', 0)
            
            # Dimensiones
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            # Crear overlay pasando la rotación
            overlay_buffer = crear_folio_pdf(
                page_width, page_height, folio_text, font, font_size, 
                offset_cm, corner, orientation, rotation
            )
            
            overlay_reader = PdfReader(overlay_buffer)
            page.merge_page(overlay_reader.pages[0]) 
            
            writer.add_page(page)
            folio_actual += 1

        # Añadir páginas restantes si no es preview
        if not preview_mode and end_index < total_pages_in_file:
            for i in range(end_index, total_pages_in_file):
                writer.add_page(reader.pages[i])

        with open(output_path, "wb") as f:
            writer.write(f)
        
        if not preview_mode:
            log_success(start_number, (end_index - start_index), corner)

        return True

    except Exception as e:
        log_error("Fallo al procesar PDF", details=str(e))
        return False