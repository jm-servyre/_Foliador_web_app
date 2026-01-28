import os
import uuid
import time
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, send_file, redirect, url_for, flash

# Intentar importar la librería de procesamiento de PDF
try:
    from pdf_processor import agregar_folios_web
    PDF_PROCESSOR_AVAILABLE = True
except ImportError as e:
    print(f"Error al importar pdf_processor: {e}")
    PDF_PROCESSOR_AVAILABLE = False

# Intentar importar la librería de vista previa
try:
    from pdf2image import convert_from_bytes
    PDF_PREVIEW_AVAILABLE = True
except ImportError as e:
    print(f"Vista previa deshabilitada (Falta Poppler).")
    PDF_PREVIEW_AVAILABLE = False

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())
# Límite de carga: 2GB (para red local), pero Render tiene sus propios límites físicos
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024 

# Configuración de Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp_files')

# Crear carpeta temporal al inicio
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

def cleanup_temp_files(hours_old=1):
    """Limpia archivos viejos para no llenar el disco del servidor."""
    now = time.time()
    cutoff = now - (hours_old * 3600)
    if os.path.exists(TEMP_FOLDER):
        for filename in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, filename)
            try:
                if os.path.isfile(file_path) and os.stat(file_path).st_mtime < cutoff:
                    os.remove(file_path)
            except Exception as e:
                print(f"Error limpiando {filename}: {e}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('pdf_file')
        if not file or file.filename == '':
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(url_for('upload_file'))

        try:
            # Generar nombres únicos
            file_id = str(uuid.uuid4())
            safe_name = secure_filename(file.filename)
            temp_input = os.path.join(TEMP_FOLDER, f'{file_id}_in.pdf')
            temp_output = os.path.join(TEMP_FOLDER, f'{file_id}_out.pdf')

            # OPTIMIZACIÓN: Guardar archivo por fragmentos (Chunks) para ahorrar RAM
            with open(temp_input, 'wb') as f:
                while True:
                    chunk = file.read(8192) # 8KB por fragmento
                    if not chunk:
                        break
                    f.write(chunk)

            # Recoger parámetros del formulario
            start_num = int(request.form.get('start_number', 1))
            start_pg = int(request.form.get('start_page', 1) or 1)
            end_pg_raw = request.form.get('end_page')
            end_pg = int(end_pg_raw) if end_pg_raw and end_pg_raw.isdigit() else None
            
            # Procesar el foliado
            success = agregar_folios_web(
                input_path=temp_input,
                output_path=temp_output,
                font="Courier-Bold",
                font_size=int(request.form.get('font_size', 16)),
                start_number=start_num,
                offset_cm=float(request.form.get('offset', 1.0)),
                corner=request.form.get('corner', 'bottom-right'),
                orientation=request.form.get('orientation', 'horizontal'),
                start_page=start_pg,
                end_page=end_pg,
                preview_mode=False
            )

            if success and os.path.exists(temp_output):
                # Preparar descarga
                download_name = f"Foliado_{safe_name}"
                return send_file(
                    temp_output,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=download_name
                )
            else:
                flash('Error al procesar el documento.', 'error')
                
        except Exception as e:
            flash(f'Ocurrió un error: {str(e)}', 'error')
            
        return redirect(url_for('upload_file'))

    return render_template('index.html', 
                         pdf_processor_available=PDF_PROCESSOR_AVAILABLE,
                         pdf_preview_available=PDF_PREVIEW_AVAILABLE)

@app.route('/preview', methods=['POST'])
def preview_file():
    if not PDF_PREVIEW_AVAILABLE:
        return "Vista previa deshabilitada.", 501
    
    file = request.files.get('pdf_file')
    if not file: return "Error", 400

    # SEGURIDAD: No generar vista previa si el archivo es > 30MB en la nube
    # Esto evita que Render reinicie el servidor por falta de RAM.
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > 30:
        return "Archivo muy pesado para vista previa en la nube. Use la versión local.", 413

    try:
        file_id = str(uuid.uuid4())
        temp_in = os.path.join(TEMP_FOLDER, f'prev_in_{file_id}.pdf')
        temp_out = os.path.join(TEMP_FOLDER, f'prev_out_{file_id}.pdf')
        
        file.save(temp_in)

        # Foliar solo la página de inicio para la vista previa
        start_pg = int(request.form.get('start_page_prev', 1) or 1)
        agregar_folios_web(
            input_path=temp_in,
            output_path=temp_out,
            font="Courier-Bold",
            font_size=int(request.form.get('font_size_prev', 16)),
            start_number=int(request.form.get('start_number_prev', 1)),
            offset_cm=float(request.form.get('offset_prev', 1.0)),
            corner=request.form.get('corner_prev', 'bottom-right'),
            orientation=request.form.get('orientation_prev', 'horizontal'),
            start_page=start_pg,
            end_page=start_pg,
            preview_mode=True
        )
        
        with open(temp_out, 'rb') as f:
            # Convertir a imagen (proceso costoso en RAM)
            img_data = convert_from_bytes(f.read(), first_page=1, last_page=1, fmt='png', dpi=72)
        
        img_io = io.BytesIO()
        img_data[0].save(img_io, format='PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
            
    except Exception as e:
        return f"Error en vista previa: {str(e)}", 500

if __name__ == '__main__':
    # Limpiar archivos al arrancar
    cleanup_temp_files(hours_old=1)
    # Host 0.0.0.0 es vital para acceso LAN
    app.run(host='0.0.0.0', port=5000, debug=False)