from pyobigram.utils import sizeof_fmt, nice_time
import datetime
import time
import os
import urllib.parse

def format_file_size(size_bytes):
    """Formatea bytes a KB, MB o GB automaticamente"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    
    val = size_bytes / 1024.0
    if val < 1024:
        formatted = f"{val:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return f"{formatted} KB"
    
    val /= 1024.0
    if val < 1024:
        formatted = f"{val:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return f"{formatted} MB"
    
    val /= 1024.0
    if val < 1024:
        formatted = f"{val:.1f}"
        if formatted.endswith('.0'):
            formatted = formatted[:-2]
        return f"{formatted} GB"
    
    val /= 1024.0
    formatted = f"{val:.1f}"
    if formatted.endswith('.0'):
        formatted = formatted[:-2]
    return f"{formatted} TB"

def text_progres(index, max_val):
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
    try:
        if max_val <= 0:
            return 0
        porcent = (index / max_val) * 100
        return round(porcent)
    except Exception:
        return 0

def format_time(seconds):
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

def createDownloading(filename, totalBits, currentBits, speed, time_elapsed, tid=''):
    msg = "📥 Descargando Archivo...\n\n"
    msg += f"➤ Archivo: {filename}\n"
    msg += text_progres(currentBits, totalBits)
    msg += f"➤ Porcentaje: {porcent(currentBits, totalBits)}%\n\n"
    msg += f"➤ Total: {sizeof_fmt(totalBits)}\n\n"
    msg += f"➤ Descargado: {sizeof_fmt(currentBits)}\n\n"
    msg += f"➤ Velocidad: {sizeof_fmt(speed)}/s\n\n"
    msg += f"➤ Tiempo de Descarga: {format_time(time_elapsed)}\n\n"
    
    if tid:
        msg += f"/cancel_{tid}"
    
    return msg

def createUploading(filename, totalBits, currentBits, speed, time_elapsed, original_name=''):
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
    
    msg = "☁️ Subiendo a la Nube...\n\n"
    msg += f"📄 Nombre: {display_name}\n"
    
    # Si es una parte comprimida, mostrar informacion adicional
    if original_name and ('.7z.' in filename or '.zip.' in filename):
        part_name = filename
        msg += f"📦 Parte: {part_name}\n"
    
    msg += text_progres(currentBits, totalBits)
    msg += f"📊 Progreso: {porcent(currentBits, totalBits)}%\n\n"
    msg += f"📦 Tamaño Total: {sizeof_fmt(totalBits)}\n\n"
    msg += f"⬆️ Subido: {sizeof_fmt(currentBits)}\n\n"
    msg += f"⚡ Velocidad: {sizeof_fmt(speed)}/s\n\n"
    msg += f"⏱️ Tiempo: {format_time(time_elapsed)}\n"
    
    return msg

def createCompresing(filename, filesize, splitsize):
    parts_count = int(filesize / splitsize) + (1 if filesize % splitsize > 0 else 0)
    
    msg = "🗜️ Comprimiendo Archivo...\n\n"
    msg += f"📄 Nombre: {filename}\n"
    msg += f"📦 Tamaño Total: {sizeof_fmt(filesize)}\n"
    msg += f"📂 Tamaño por Parte: {sizeof_fmt(splitsize)}\n"
    msg += f"🔢 Cantidad de Partes: {parts_count}\n\n"
    msg += "⏳ Por favor espera mientras se comprime el archivo..."
    
    return msg

def createFinishUploading(filename, filesize, split_size, current, count, findex):
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

def createFileMsg(filename, files):
    if not files:
        return ""
    
    msg = "🔗 Enlaces de Descarga\n\n"
    for i, f in enumerate(files, 1):
        try:
            url = urllib.parse.unquote(f['directurl'], encoding='utf-8', errors='replace')
            name = f.get('name', f'Archivo {i}')
            display_name = name[:50] + "..." if len(name) > 50 else name
            msg += f"{i}. 🔗 {display_name}\n"
            msg += f"   {url}\n\n"
        except Exception:
            msg += f"{i}. 🔗 Enlace\n"
            msg += f"   {f.get('directurl', '#')}\n\n"
    
    return msg

def createFilesMsg(evfiles):
    if not evfiles:
        return "📭 No tienes evidencias disponibles"
    
    msg = f"📑 Tus Evidencias ({len(evfiles)})\n\n"
    
    for i, f in enumerate(evfiles):
        try:
            if f.get('files') and len(f['files']) > 0:
                filename = f['files'][0].get('name', '')
                ext = os.path.splitext(filename)[1]
                display_name = f['name'] + ext
            else:
                display_name = f['name']
            
            if len(display_name) > 35:
                display_name = display_name[:35] + "..."
            
            file_count = len(f.get('files', []))
            
            msg += f"{i}. 📄 {display_name}\n"
            msg += f"   📁 {file_count} archivo(s)\n"
            msg += f"   📋 /txt_{i}  |  🗑️ /del_{i}\n\n"
        except Exception:
            msg += f"{i}. 📄 {f.get('name', 'Sin nombre')}\n\n"
    
    return msg

def createStat(username, userdata, isadmin):
    msg = "⚙️ Configuracion de Usuario\n\n"
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
    msg += f"📦 Tamaño de Partes: {format_file_size(int(zips_mb * 1024 * 1024))}\n\n"
    
    msg += f"👑 Admin: {'✅ Si' if isadmin else '❌ No'}\n"
    msg += f"🔌 Proxy: {'✅ Activado' if userdata.get('proxy') else '❌ Desactivado'}\n"
    msg += f"🔮 Tokenize: {'✅ Activado' if userdata.get('tokenize', 0) != 0 else '❌ Desactivado'}\n\n"
    
    msg += "📌 Para cambiar la configuracion de Moodle:\n"
    msg += "🤜 /account usuario,contraseña"
    
    return msg
