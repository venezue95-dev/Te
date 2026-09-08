from pyobigram.utils import sizeof_fmt, nice_time
import datetime
import time
import os
import urllib.parse

def text_progres(index, max_val):
    """
    Crea una barra de progreso visual con 20 caracteres
    """
    try:
        if max_val < 1:
            max_val += 1
        porcent = (index / max_val) * 100
        porcent = round(porcent)
        
        make_text = '\n['
        for i in range(1, 21):
            if porcent >= i * 5:
                make_text += '█'
            else:
                make_text += '░'
        make_text += ']\n'
        return make_text
    except Exception:
        return ''

def porcent(index, max_val):
    """
    Calcula el porcentaje de progreso
    """
    try:
        if max_val <= 0:
            return 0
        porcent = (index / max_val) * 100
        return round(porcent)
    except Exception:
        return 0

def format_time(seconds):
    """
    Formatea el tiempo en formato HH:MM:SS
    """
    try:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    except:
        return "00:00"

def create_downloading(filename, total_bits, current_bits, speed, time_elapsed, tid=''):
    """
    Crea el mensaje de progreso de descarga
    """
    msg = "📥 Descargando Archivo...\n\n"
    msg += f"➤ Archivo: {filename}\n"
    msg += text_progres(current_bits, total_bits)
    msg += f"➤ Porcentaje: {porcent(current_bits, total_bits)}%\n\n"
    msg += f"➤ Total: {sizeof_fmt(total_bits)}\n\n"
    msg += f"➤ Descargado: {sizeof_fmt(current_bits)}\n\n"
    msg += f"➤ Velocidad: {sizeof_fmt(speed)}/s\n\n"
    msg += f"➤ Tiempo de Descarga: {format_time(time_elapsed)}\n\n"
    
    if tid:
        msg += f"/cancel_{tid}"
    
    return msg

def create_uploading(filename, total_bits, current_bits, speed, time_elapsed, original_name=''):
    """
    Crea el mensaje de progreso de subida
    """
    # 📌 CORREGIDO: Usar total_bits correctamente
    # Si es una parte comprimida, mostrar el nombre original
    if original_name and ('.7z.' in filename or '.zip.' in filename or '.part' in filename):
        part_num = filename.split('.')[-1]
        if part_num.isdigit():
            display_name = f"{original_name} (Parte {part_num})"
        else:
            display_name = f"{original_name} (Parte {filename.split('.')[-2]})"
    elif original_name:
        display_name = original_name
    else:
        display_name = filename
    
    # 📌 CORREGIDO: Usar total_bits como tamaño de la parte
    total_size = sizeof_fmt(total_bits)
    current_size = sizeof_fmt(current_bits)
    speed_formatted = f"{sizeof_fmt(speed)}/s"
    
    msg = "☁️ Subiendo a la Nube...\n\n"
    msg += f"📄 Nombre: {display_name}\n"
    
    # Si es una parte comprimida, mostrar información adicional
    if original_name and ('.7z.' in filename or '.zip.' in filename):
        part_name = filename
        msg += f"📦 Parte: {part_name}\n"
    
    msg += text_progres(current_bits, total_bits)
    msg += f"📊 Progreso: {porcent(current_bits, total_bits)}%\n\n"
    msg += f"📦 Tamaño Total: {total_size}\n\n"
    msg += f"⬆️ Subido: {current_size}\n\n"
    msg += f"⚡ Velocidad: {speed_formatted}\n\n"
    msg += f"⏱️ Tiempo: {format_time(time_elapsed)}\n"
    
    return msg

def create_compresing(filename, filesize, splitsize):
    """
    Crea el mensaje de compresión
    """
    parts_count = int(filesize / splitsize) + (1 if filesize % splitsize > 0 else 0)
    
    msg = "🗜️ Comprimiendo Archivo...\n\n"
    msg += f"📄 Nombre: {filename}\n"
    msg += f"📦 Tamaño Total: {sizeof_fmt(filesize)}\n"
    msg += f"📂 Tamaño por Parte: {sizeof_fmt(splitsize)}\n"
    msg += f"🔢 Cantidad de Partes: {parts_count}\n\n"
    msg += "⏳ Por favor espera mientras se comprime el archivo..."
    
    return msg

def create_finish_uploading(filename, filesize, split_size, current, count, findex):
    """
    Crea el mensaje de finalización de subida
    """
    msg = "✅ Proceso Finalizado Exitosamente!\n\n"
    msg += f"📄 Nombre: {filename}\n"
    msg += f"📦 Tamaño Total: {sizeof_fmt(filesize)}\n"
    
    if count > 1:
        msg += f"📂 Tamaño por Parte: {sizeof_fmt(split_size)}\n"
        msg += f"📤 Partes Subidas: {current} de {count}\n\n"
    else:
        msg += "📤 Subida Directa: 1 de 1\n\n"
    
    msg += "🗑️ Para eliminar esta evidencia usa:\n"
    msg += f"/del_{findex}"
    
    return msg

def create_file_msg(filename, files):
    """
    Crea el mensaje con los enlaces de los archivos subidos
    """
    if not files:
        return ""
    
    msg = "<b>🔗 Enlaces de Descarga</b>\n\n"
    for i, f in enumerate(files, 1):
        try:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            name = f.get('name', f'Archivo {i}')
            # Limitar nombre para no saturar
            display_name = name[:50] + "..." if len(name) > 50 else name
            msg += f"<b>{i}.</b> <a href='{url}'>🔗 {display_name}</a>\n"
        except Exception:
            msg += f"<b>{i}.</b> <a href='{f.get('directurl', '#')}'>🔗 Enlace</a>\n"
    
    return msg

def create_files_msg(evfiles):
    """
    Crea el mensaje con la lista de evidencias del usuario
    """
    if not evfiles:
        return "📭 No tienes evidencias disponibles"
    
    msg = f"📑 Tus Evidencias ({len(evfiles)})\n\n"
    
    for i, f in enumerate(evfiles):
        try:
            # Obtener extensión del primer archivo
            if f.get('files') and len(f['files']) > 0:
                filename = f['files'][0].get('name', '')
                ext = os.path.splitext(filename)[1]
                display_name = f['name'] + ext
            else:
                display_name = f['name']
            
            # Limitar nombre
            if len(display_name) > 35:
                display_name = display_name[:35] + "..."
            
            # Contar archivos
            file_count = len(f.get('files', []))
            
            msg += f"<b>{i}.</b> 📄 {display_name}\n"
            msg += f"   📁 {file_count} archivo(s)\n"
            msg += f"   📋 /txt_{i}  |  🗑️ /del_{i}\n\n"
        except Exception:
            msg += f"<b>{i}.</b> 📄 {f.get('name', 'Sin nombre')}\n\n"
    
    return msg

def create_stat(username, userdata, isadmin):
    """
    Crea el mensaje con la configuración del usuario
    """
    from pyobigram.utils import sizeof_fmt
    
    msg = "⚙️ Configuración de Usuario\n\n"
    msg += f"👤 Usuario: @{username}\n"
    msg += f"📧 Moodle User: {userdata.get('moodle_user', 'No configurado')}\n"
    msg += f"🔑 Password: {'*' * len(str(userdata.get('moodle_password', '')))}\n"
    msg += f"🌐 Host: {userdata.get('moodle_host', 'No configurado')}\n"
    
    if userdata.get('cloudtype') == 'moodle':
        msg += f"🏷️ Repo ID: {userdata.get('moodle_repo_id', 'No configurado')}\n"
    
    msg += f"☁️ Cloud Type: {userdata.get('cloudtype', 'No configurado')}\n"
    msg += f"📤 Upload Type: {userdata.get('uploadtype', 'No configurado')}\n"
    
    if userdata.get('cloudtype') == 'cloud':
        msg += f"📂 Directorio: /{userdata.get('dir', 'No configurado')}\n"
    
    zips_mb = userdata.get('zips', 0)
    msg += f"📦 Tamaño de Partes: {sizeof_fmt(zips_mb * 1024 * 1024)}\n\n"
    
    msg += f"👑 Admin: {'✅ Sí' if isadmin else '❌ No'}\n"
    msg += f"🔌 Proxy: {'✅ Activado' if userdata.get('proxy') else '❌ Desactivado'}\n"
    msg += f"🔮 Tokenize: {'✅ Activado' if userdata.get('tokenize', 0) != 0 else '❌ Desactivado'}\n\n"
    
    msg += "📌 Para cambiar la configuración de Moodle:\n"
    msg += "🤜 /account usuario,contraseña 👀"
    
    return msg

# ==============================
# FUNCIONES LEGACY (Compatibilidad con código existente)
# ==============================

def createDownloading(filename, totalBits, currentBits, speed, time_elapsed, tid=''):
    """Versión legacy de create_downloading"""
    return create_downloading(filename, totalBits, currentBits, speed, time_elapsed, tid)

def createUploading(filename, totalBits, currentBits, speed, time_elapsed, originalname=''):
    """Versión legacy de create_uploading"""
    return create_uploading(filename, totalBits, currentBits, speed, time_elapsed, originalname)

def createCompresing(filename, filesize, splitsize):
    """Versión legacy de create_compresing"""
    return create_compresing(filename, filesize, splitsize)

def createFinishUploading(filename, filesize, split_size, current, count, findex):
    """Versión legacy de create_finish_uploading"""
    return create_finish_uploading(filename, filesize, split_size, current, count, findex)

def createFileMsg(filename, files):
    """Versión legacy de create_file_msg"""
    return create_file_msg(filename, files)

def createFilesMsg(evfiles):
    """Versión legacy de create_files_msg"""
    return create_files_msg(evfiles)

def createStat(username, userdata, isadmin):
    """Versión legacy de create_stat"""
    return create_stat(username, userdata, isadmin)
