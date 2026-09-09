#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError
import os
import time
import zipfile
import requests
import urllib.parse
import asyncio
import datetime
import random
import string

# ==============================
# IMPORTACIONES DE TUS MÓDULOS
# ==============================

# Nota: Asegúrate de que estos módulos existan en tu sistema
try:
    from MoodleClient import MoodleClient
except ImportError:
    print("⚠️ MoodleClient no encontrado, usando simulación")
    MoodleClient = None

try:
    from JDatabase import JsonDatabase
except ImportError:
    print("⚠️ JDatabase no encontrado, usando simulación")
    JsonDatabase = None

try:
    from pydownloader.downloader import Downloader
except ImportError:
    print("⚠️ pydownloader no encontrado, usando simulación")
    Downloader = None

try:
    from ProxyCloud import ProxyCloud
    import ProxyCloud
except ImportError:
    print("⚠️ ProxyCloud no encontrado, usando simulación")
    ProxyCloud = None

try:
    import infos
except ImportError:
    print("⚠️ infos no encontrado, usando simulación")
    infos = None

try:
    import NexCloudClient
except ImportError:
    print("⚠️ NexCloudClient no encontrado, usando simulación")
    NexCloudClient = None

try:
    import S5Crypto
except ImportError:
    print("⚠️ S5Crypto no encontrado, usando simulación")
    S5Crypto = None

# ==============================
# CONFIGURACIÓN
# ==============================

# 📌 CONFIGURACIÓN DE PYROGRAM
API_ID = 20534584
API_HASH = "6d5b13261d2c92a9a00afc1fd613b9df"
BOT_TOKEN = "8867154518:AAEiUWIj5DGF182MNxGtx-f29jKG3lw_nVA"

# 📌 ADMINISTRADOR
TL_ADMIN_USER = "Eliel_21"

# 📌 LÍMITES DIARIOS (0 = sin límite)
DAILY_LIMIT_BYTES = 100 * 1024 * 1024 * 1024  # 100 GB

# ==============================
# FUNCIONES AUXILIARES
# ==============================

def format_file_size(size_bytes):
    """Formatea bytes a KB, MB o GB automáticamente"""
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

def get_file_size(path):
    """Obtiene el tamaño de un archivo en bytes"""
    try:
        return os.path.getsize(path)
    except:
        return 0

def createID():
    """Crea un ID único"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def sizeof_fmt(num, suffix='B'):
    """Formatea bytes a unidades legibles (compatible con pyobigram)"""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

# ==============================
# SISTEMA DE ESTADÍSTICAS EN MEMORIA
# ==============================

class MemoryStats:
    def __init__(self):
        self.reset_stats()
    
    def reset_stats(self):
        self.stats = {
            'total_uploads': 0,
            'total_deletes': 0,
            'total_size_uploaded': 0
        }
        self.user_stats = {}
        self.upload_logs = []
        self.delete_logs = []
    
    def check_and_update_daily_reset(self, username):
        current_date = datetime.datetime.now().strftime("%d/%m/%y")
        if username in self.user_stats:
            if self.user_stats[username].get('last_date') != current_date:
                self.user_stats[username]['daily_size'] = 0
                self.user_stats[username]['last_date'] = current_date
        else:
            self.user_stats[username] = {
                'uploads': 0,
                'deletes': 0,
                'total_size': 0,
                'daily_size': 0,
                'last_date': current_date,
                'last_activity': datetime.datetime.now().strftime("%d/%m/%y %I:%M %p")
            }
    
    def log_upload(self, username, filename, file_size, moodle_host):
        try:
            file_size = int(file_size)
        except:
            file_size = 0
        
        self.check_and_update_daily_reset(username)
        
        self.stats['total_uploads'] += 1
        self.stats['total_size_uploaded'] += file_size
        
        self.user_stats[username]['uploads'] += 1
        self.user_stats[username]['total_size'] += file_size
        self.user_stats[username]['daily_size'] += file_size
        self.user_stats[username]['last_activity'] = datetime.datetime.now().strftime("%d/%m/%y %I:%M %p")
        
        log_entry = {
            'timestamp': datetime.datetime.now().strftime("%d/%m/%y %I:%M %p"),
            'username': username,
            'filename': filename,
            'file_size_bytes': file_size,
            'file_size_formatted': format_file_size(file_size),
            'moodle_host': moodle_host
        }
        self.upload_logs.append(log_entry)
        
        if len(self.upload_logs) > 300:
            self.upload_logs.pop(0)
        
        return True
    
    def get_user_stats(self, username):
        self.check_and_update_daily_reset(username)
        if username in self.user_stats:
            return self.user_stats[username]
        return None
    
    def get_all_stats(self):
        return self.stats

memory_stats = MemoryStats()

# ==============================
# FUNCIONES DE PROGRESO
# ==============================

def download_progress(current, total, args):
    """Función de progreso para descargas"""
    try:
        bot = args.get('bot')
        message = args.get('message')
        thread = args.get('thread')
        filename = args.get('filename', 'Archivo')
        
        if thread and thread.get('stop'):
            return
        
        # Calcular porcentaje
        percent = (current / total) * 100 if total > 0 else 0
        
        # Crear barra de progreso
        bar_length = 20
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Crear mensaje
        progress_msg = (
            f"📥 Descargando: {filename}\n\n"
            f"[{bar}]\n"
            f"📊 Progreso: {percent:.1f}%\n\n"
            f"📦 Total: {format_file_size(total)}\n"
            f"📥 Descargado: {format_file_size(current)}\n"
        )
        
        # Editar mensaje
        try:
            if message:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    text=progress_msg
                )
        except:
            pass
            
    except Exception as e:
        print(f"Error en download_progress: {e}")

def upload_progress(current, total, args):
    """Función de progreso para subidas"""
    try:
        bot = args.get('bot')
        message = args.get('message')
        thread = args.get('thread')
        filename = args.get('filename', 'Archivo')
        originalname = args.get('originalname', '')
        
        if thread and thread.get('stop'):
            return
        
        # Calcular porcentaje
        percent = (current / total) * 100 if total > 0 else 0
        
        # Crear barra de progreso
        bar_length = 20
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Crear mensaje
        display_name = originalname if originalname else filename
        
        progress_msg = (
            f"☁️ Subiendo a la Nube...\n\n"
            f"📄 Nombre: {display_name}\n"
            f"[{bar}]\n"
            f"📊 Progreso: {percent:.1f}%\n\n"
            f"📦 Total: {format_file_size(total)}\n"
            f"⬆️ Subido: {format_file_size(current)}\n"
        )
        
        # Editar mensaje
        try:
            if message:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    text=progress_msg
                )
        except:
            pass
            
    except Exception as e:
        print(f"Error en upload_progress: {e}")

# ==============================
# PROCESAMIENTO DE ARCHIVOS
# ==============================

def process_upload_files(filename, filesize, files, message, client, jdb=None):
    """Procesa la subida de archivos a Moodle"""
    try:
        # Obtener información del usuario
        username = message.from_user.username
        user_info = jdb.get_user(username) if jdb else None
        
        if not user_info:
            return None
        
        cloudtype = user_info.get('cloudtype', 'moodle')
        proxy = user_info.get('proxy', '')
        
        # Parsear proxy si existe
        proxy_parsed = None
        if proxy and ProxyCloud:
            try:
                proxy_parsed = ProxyCloud.parse(proxy)
            except:
                pass
        
        if cloudtype == 'moodle' and MoodleClient:
            # Crear cliente Moodle
            client_moodle = MoodleClient(
                user_info.get('moodle_user', ''),
                user_info.get('moodle_password', ''),
                user_info.get('moodle_host', ''),
                user_info.get('moodle_repo_id', 1),
                proxy=proxy_parsed
            )
            
            # Intentar login
            if not client_moodle.login():
                return "LOGIN_FAILED"
            
            evidence = None
            
            # Si es tipo evidence, buscar o crear evidencia
            if user_info.get('uploadtype') == 'evidence':
                evidences = client_moodle.getEvidences()
                evidname = str(filename).split('.')[0]
                for evid in evidences:
                    if evid['name'] == evidname:
                        evidence = evid
                        break
                if evidence is None:
                    evidence = client_moodle.createEvidence(evidname)
            
            originalfile = ''
            if len(files) > 1:
                originalfile = filename
            
            draftlist = []
            tokenize = user_info.get('tokenize', 0) != 0
            
            for f in files:
                resp = None
                iter_count = 0
                
                while resp is None:
                    # Subir según el tipo
                    if user_info.get('uploadtype') == 'evidence':
                        fileid, resp = client_moodle.upload_file(
                            f, evidence, None,
                            progressfunc=upload_progress,
                            args={'bot': client, 'message': message, 'filename': f, 'originalname': originalfile},
                            tokenize=tokenize
                        )
                        draftlist.append(resp)
                    elif user_info.get('uploadtype') == 'draft':
                        fileid, resp = client_moodle.upload_file_draft(
                            f,
                            progressfunc=upload_progress,
                            args={'bot': client, 'message': message, 'filename': f, 'originalname': originalfile},
                            tokenize=tokenize
                        )
                        draftlist.append(resp)
                    elif user_info.get('uploadtype') == 'blog':
                        fileid, resp = client_moodle.upload_file_blog(
                            f,
                            progressfunc=upload_progress,
                            args={'bot': client, 'message': message, 'filename': f, 'originalname': originalfile},
                            tokenize=tokenize
                        )
                        draftlist.append(resp)
                    elif user_info.get('uploadtype') == 'calendario':
                        fileid, resp = client_moodle.upload_file_calendar(
                            f,
                            progressfunc=upload_progress,
                            args={'bot': client, 'message': message, 'filename': f, 'originalname': originalfile},
                            tokenize=tokenize
                        )
                        draftlist.append(resp)
                    
                    iter_count += 1
                    if iter_count >= 10:
                        break
                
                # Eliminar archivo temporal
                try:
                    os.unlink(f)
                except:
                    pass
            
            # Guardar evidencia si es necesario
            if user_info.get('uploadtype') == 'evidence':
                try:
                    client_moodle.saveEvidence(evidence)
                except:
                    pass
            
            return draftlist
        
        elif cloudtype == 'cloud' and NexCloudClient:
            # Subir a NextCloud
            tokenize = user_info.get('tokenize', 0) != 0
            
            host = user_info.get('moodle_host', '')
            user = user_info.get('moodle_user', '')
            passw = user_info.get('moodle_password', '')
            remotepath = user_info.get('dir', '/')
            
            client_cloud = NexCloudClient.NexCloudClient(user, passw, host, proxy=proxy_parsed)
            
            if not client_cloud.login():
                return "LOGIN_FAILED"
            
            originalfile = ''
            if len(files) > 1:
                originalfile = filename
            
            filesdata = []
            for f in files:
                data = client_cloud.upload_file(
                    f, path=remotepath,
                    progressfunc=upload_progress,
                    args={'bot': client, 'message': message, 'filename': f, 'originalname': originalfile},
                    tokenize=tokenize
                )
                filesdata.append(data)
                try:
                    os.unlink(f)
                except:
                    pass
            
            return filesdata
        
        return None
        
    except Exception as e:
        print(f"Error en process_upload_files: {e}")
        return None

def process_file(message, client, file_path):
    """Procesa un archivo descargado"""
    try:
        # Obtener información del usuario
        username = message.from_user.username
        jdb = JsonDatabase('database') if JsonDatabase else None
        
        if jdb:
            jdb.check_create()
            jdb.load()
            user_info = jdb.get_user(username)
        else:
            user_info = None
        
        # Obtener tamaño del archivo
        file_size = get_file_size(file_path)
        filename = os.path.basename(file_path)
        
        # Obtener límite del usuario
        if user_info:
            user_limit_mb = float(user_info.get('zips', 1))
            max_file_size = int(1024 * 1024 * user_limit_mb)
        else:
            max_file_size = 1024 * 1024  # 1 MB por defecto
        
        if max_file_size <= 0:
            max_file_size = 1024 * 1024
        
        file_upload_count = 0
        result_files = None
        findex = 0
        
        # Verificar si necesita compresión
        if file_size > max_file_size:
            # Enviar mensaje de compresión
            compress_msg = (
                f"🗜️ Comprimiendo Archivo...\n\n"
                f"📄 Nombre: {filename}\n"
                f"📦 Tamaño Total: {format_file_size(file_size)}\n"
                f"📂 Tamaño por Parte: {format_file_size(max_file_size)}\n"
                f"🔢 Cantidad de Partes: {int(file_size / max_file_size) + 1}\n\n"
                f"⏳ Por favor espera..."
            )
            
            try:
                client.send_message(message.chat.id, compress_msg)
            except:
                pass
            
            # Crear archivos comprimidos
            zipname = str(file_path).split('.')[0] + createID()
            mult_file = zipfile.MultiFile(zipname, max_file_size)
            zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
            zip.write(file_path)
            zip.close()
            mult_file.close()
            
            # Subir archivos comprimidos
            result_files = process_upload_files(
                file_path, file_size, mult_file.files,
                message, client, jdb
            )
            
            # Limpiar archivo original
            try:
                os.unlink(file_path)
            except:
                pass
            
            file_upload_count = len(mult_file.files)
        else:
            # Subida directa
            result_files = process_upload_files(
                file_path, file_size, [file_path],
                message, client, jdb
            )
            file_upload_count = 1
        
        # Procesar resultado
        files = []
        if result_files and result_files != "LOGIN_FAILED":
            # Obtener enlaces de los archivos subidos
            if user_info and user_info.get('cloudtype') == 'moodle':
                if user_info.get('uploadtype') in ['draft', 'blog', 'calendario']:
                    for draft in result_files:
                        files.append({
                            'name': draft.get('file', 'desconocido'),
                            'directurl': draft.get('url', '')
                        })
                elif user_info.get('uploadtype') == 'evidence':
                    # Obtener evidencias
                    proxy = user_info.get('proxy', '')
                    proxy_parsed = None
                    if proxy and ProxyCloud:
                        try:
                            proxy_parsed = ProxyCloud.parse(proxy)
                        except:
                            pass
                    
                    if MoodleClient:
                        client_moodle = MoodleClient(
                            user_info.get('moodle_user', ''),
                            user_info.get('moodle_password', ''),
                            user_info.get('moodle_host', ''),
                            user_info.get('moodle_repo_id', 1),
                            proxy=proxy_parsed
                        )
                        
                        if client_moodle.login():
                            evidences = client_moodle.getEvidences()
                            evidname = str(file_path).split('.')[0]
                            for ev in evidences:
                                if ev['name'] == evidname:
                                    files = ev.get('files', [])
                                    break
                            client_moodle.logout()
            else:
                for data in result_files:
                    files.append({
                        'name': data.get('name', 'desconocido'),
                        'directurl': data.get('url', '')
                    })
            
            # Registrar estadísticas
            if jdb and user_info:
                memory_stats.log_upload(
                    username=username,
                    filename=filename,
                    file_size=file_size,
                    moodle_host=user_info.get('moodle_host', '')
                )
            
            # Crear mensaje de finalización
            finish_msg = (
                f"✅ Proceso Finalizado Exitosamente!\n\n"
                f"📄 Nombre: {filename}\n"
                f"📦 Tamaño Total: {format_file_size(file_size)}\n"
            )
            
            if file_upload_count > 1:
                finish_msg += f"📂 Tamaño por Parte: {format_file_size(max_file_size)}\n"
                finish_msg += f"📤 Partes Subidas: {file_upload_count}\n\n"
            else:
                finish_msg += f"📤 Subida Directa: 1 de 1\n\n"
            
            # Agregar enlaces
            if files:
                finish_msg += "🔗 Enlaces de Descarga:\n\n"
                for i, f in enumerate(files, 1):
                    url = f.get('directurl', '#')
                    name = f.get('name', f'Archivo {i}')
                    finish_msg += f"{i}. {name}\n   {url}\n\n"
            
            # Enviar mensaje final
            client.send_message(message.chat.id, finish_msg)
            
            # Enviar archivo TXT con enlaces
            if len(files) > 0:
                txtname = filename.split('.')[0] + '.txt'
                txt = open(txtname, 'w')
                for i, f in enumerate(files):
                    txt.write(f.get('directurl', ''))
                    if i < len(files) - 1:
                        txt.write('\n\n')
                txt.close()
                
                try:
                    client.send_document(message.chat.id, txtname)
                except:
                    pass
                
                try:
                    os.unlink(txtname)
                except:
                    pass
            
            return True
            
        elif result_files == "LOGIN_FAILED":
            client.send_message(
                message.chat.id,
                "❌ Error de autenticación en Moodle\n"
                "⚠️ Verifica tus credenciales o el estado del servidor."
            )
            return False
        
        return False
        
    except Exception as e:
        print(f"Error en process_file: {e}")
        try:
            client.send_message(
                message.chat.id,
                f"❌ Error al procesar el archivo: {str(e)}"
            )
        except:
            pass
        return False

def download_file(message, client, url, jdb=None):
    """Descarga un archivo desde una URL"""
    try:
        # Enviar mensaje de inicio
        start_msg = client.send_message(
            message.chat.id,
            f"🔗 Descargando archivo desde: {url}\n⏳ Esto puede tomar un momento..."
        )
        
        # Crear downloader
        if Downloader:
            downloader = Downloader()
            filename = url.split('/')[-1] or 'archivo'
            
            # Descargar archivo
            file_path = downloader.download_url(
                url,
                progressfunc=download_progress,
                args={'bot': client, 'message': start_msg, 'filename': filename}
            )
            
            if file_path:
                # Procesar archivo descargado
                client.send_message(
                    message.chat.id,
                    f"✅ Archivo descargado: {filename}\n📦 Tamaño: {format_file_size(get_file_size(file_path))}"
                )
                
                # Procesar el archivo
                return process_file(message, client, file_path)
            else:
                client.send_message(message.chat.id, "❌ Error al descargar el archivo")
                return False
        else:
            client.send_message(message.chat.id, "❌ Módulo de descarga no disponible")
            return False
            
    except Exception as e:
        print(f"Error en download_file: {e}")
        try:
            client.send_message(message.chat.id, f"❌ Error al descargar: {str(e)}")
        except:
            pass
        return False

# ==============================
# HANDLERS DE MENSAJES CON PYROGRAM
# ==============================

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    """Maneja documentos enviados al bot"""
    try:
        document = message.document
        file_name = document.file_name or f"documento_{int(time.time())}"
        file_size = document.file_size
        
        # Verificar acceso del usuario
        username = message.from_user.username
        if username != TL_ADMIN_USER:
            # Verificar si está en la base de datos
            jdb = JsonDatabase('database') if JsonDatabase else None
            if jdb:
                jdb.check_create()
                jdb.load()
                if not jdb.get_user(username):
                    await client.send_message(
                        message.chat.id,
                        "❌ No tienes acceso a este bot. Contacta al administrador."
                    )
                    return
            else:
                await client.send_message(
                    message.chat.id,
                    "⚠️ Sistema de usuarios no disponible"
                )
                return
        
        # Verificar límite diario
        if username != TL_ADMIN_USER and DAILY_LIMIT_BYTES > 0:
            user_stats = memory_stats.get_user_stats(username)
            current_daily = user_stats.get('daily_size', 0) if user_stats else 0
            
            if current_daily + file_size > DAILY_LIMIT_BYTES:
                await client.send_message(
                    message.chat.id,
                    f"🚫 Límite diario excedido\n"
                    f"📊 Usado hoy: {format_file_size(current_daily)}\n"
                    f"📦 Límite: {format_file_size(DAILY_LIMIT_BYTES)}\n\n"
                    f"El archivo pesa {format_file_size(file_size)} y excedería tu límite."
                )
                return
        
        # Enviar mensaje de procesando
        await client.send_message(
            message.chat.id,
            f"📥 Recibido archivo: {file_name} ({format_file_size(file_size)})\n⏳ Procesando..."
        )
        
        # ✅ CORRECTO: Descargar con Pyrogram
        downloaded_file = await client.download_media(
            message.document,
            file_name=file_name
        )
        
        if not downloaded_file:
            await client.send_message(message.chat.id, "❌ Error al descargar el archivo")
            return
        
        # Procesar archivo (síncrono pero ejecutado en un hilo separado)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_file, message, client, downloaded_file)
            result = future.result()
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(downloaded_file):
                os.unlink(downloaded_file)
        except:
            pass
        
        if result:
            await client.send_message(message.chat.id, "✅ Procesamiento completado")
        else:
            await client.send_message(message.chat.id, "❌ Error en el procesamiento")
        
    except Exception as e:
        print(f"Error en handle_document: {e}")
        await client.send_message(message.chat.id, f"❌ Error al procesar el documento: {str(e)}")

@app.on_message(filters.photo)
async def handle_photo(client: Client, message: Message):
    """Maneja fotos enviadas al bot"""
    try:
        # Obtener la foto de mayor calidad
        photo = message.photo[-1]
        timestamp = int(time.time())
        img_name = f"imagen_{timestamp}.jpg"
        
        # Verificar acceso
        username = message.from_user.username
        if username != TL_ADMIN_USER:
            jdb = JsonDatabase('database') if JsonDatabase else None
            if jdb:
                jdb.check_create()
                jdb.load()
                if not jdb.get_user(username):
                    await client.send_message(
                        message.chat.id,
                        "❌ No tienes acceso a este bot"
                    )
                    return
        
        # Enviar mensaje de procesando
        await client.send_message(
            message.chat.id,
            f"📥 Recibida imagen: {img_name}\n⏳ Procesando..."
        )
        
        # ✅ CORRECTO: Descargar con Pyrogram
        downloaded_file = await client.download_media(
            message.photo[-1],
            file_name=img_name
        )
        
        if not downloaded_file:
            await client.send_message(message.chat.id, "❌ Error al descargar la imagen")
            return
        
        # Procesar imagen
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_file, message, client, downloaded_file)
            result = future.result()
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(downloaded_file):
                os.unlink(downloaded_file)
        except:
            pass
        
        if result:
            await client.send_message(message.chat.id, "✅ Imagen procesada correctamente")
        else:
            await client.send_message(message.chat.id, "❌ Error en el procesamiento")
        
    except Exception as e:
        print(f"Error en handle_photo: {e}")
        await client.send_message(message.chat.id, f"❌ Error al procesar la imagen: {str(e)}")

@app.on_message(filters.video)
async def handle_video(client: Client, message: Message):
    """Maneja videos enviados al bot"""
    try:
        video = message.video
        file_name = video.file_name or f"video_{int(time.time())}.mp4"
        
        # Verificar acceso
        username = message.from_user.username
        if username != TL_ADMIN_USER:
            jdb = JsonDatabase('database') if JsonDatabase else None
            if jdb:
                jdb.check_create()
                jdb.load()
                if not jdb.get_user(username):
                    await client.send_message(
                        message.chat.id,
                        "❌ No tienes acceso a este bot"
                    )
                    return
        
        # Enviar mensaje de procesando
        await client.send_message(
            message.chat.id,
            f"📥 Recibido video: {file_name}\n⏳ Procesando..."
        )
        
        # ✅ CORRECTO: Descargar con Pyrogram
        downloaded_file = await client.download_media(
            message.video,
            file_name=file_name
        )
        
        if not downloaded_file:
            await client.send_message(message.chat.id, "❌ Error al descargar el video")
            return
        
        # Procesar video
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_file, message, client, downloaded_file)
            result = future.result()
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(downloaded_file):
                os.unlink(downloaded_file)
        except:
            pass
        
        if result:
            await client.send_message(message.chat.id, "✅ Video procesado correctamente")
        else:
            await client.send_message(message.chat.id, "❌ Error en el procesamiento")
        
    except Exception as e:
        print(f"Error en handle_video: {e}")
        await client.send_message(message.chat.id, f"❌ Error al procesar el video: {str(e)}")

@app.on_message(filters.audio)
async def handle_audio(client: Client, message: Message):
    """Maneja audios enviados al bot"""
    try:
        audio = message.audio
        file_name = audio.file_name or f"audio_{int(time.time())}.mp3"
        
        # Verificar acceso
        username = message.from_user.username
        if username != TL_ADMIN_USER:
            jdb = JsonDatabase('database') if JsonDatabase else None
            if jdb:
                jdb.check_create()
                jdb.load()
                if not jdb.get_user(username):
                    await client.send_message(
                        message.chat.id,
                        "❌ No tienes acceso a este bot"
                    )
                    return
        
        # Enviar mensaje de procesando
        await client.send_message(
            message.chat.id,
            f"📥 Recibido audio: {file_name}\n⏳ Procesando..."
        )
        
        # ✅ CORRECTO: Descargar con Pyrogram
        downloaded_file = await client.download_media(
            message.audio,
            file_name=file_name
        )
        
        if not downloaded_file:
            await client.send_message(message.chat.id, "❌ Error al descargar el audio")
            return
        
        # Procesar audio
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(process_file, message, client, downloaded_file)
            result = future.result()
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(downloaded_file):
                os.unlink(downloaded_file)
        except:
            pass
        
        if result:
            await client.send_message(message.chat.id, "✅ Audio procesado correctamente")
        else:
            await client.send_message(message.chat.id, "❌ Error en el procesamiento")
        
    except Exception as e:
        print(f"Error en handle_audio: {e}")
        await client.send_message(message.chat.id, f"❌ Error al procesar el audio: {str(e)}")

@app.on_message(filters.text & filters.command(["start", "help"]))
async def handle_commands(client: Client, message: Message):
    """Maneja comandos /start y /help"""
    username = message.from_user.username or "Usuario"
    
    start_msg = (
        f"🤖 ¡Hola @{username}!\n\n"
        "📌 **Bot para subir archivos a Moodle/Cloud**\n\n"
        "**¿Qué puedo hacer?**\n"
        "📤 Envíame un **archivo**, **foto**, **video** o **audio**\n"
        "🔗 También puedo procesar **enlaces de descarga**\n"
        "🗜️ Los archivos grandes se comprimen automáticamente\n\n"
        "**Configuración:**\n"
        "/account usuario,contraseña - Configurar cuenta Moodle\n"
        "/host https://moodle.com - Configurar host\n"
        "/repoid 1 - Configurar ID del repositorio\n"
        "/zips 1 - Tamaño de partes en MB\n"
        "/uptype evidence - Tipo de subida (evidence/draft/blog/calendario)\n\n"
        "**Comandos de usuario:**\n"
        "/myuser - Ver tu configuración\n"
        "/files - Ver tus evidencias (Moodle)\n"
        "/txt_X - Obtener TXT de evidencia X\n"
        "/del_X - Eliminar evidencia X\n"
        "/delall - Eliminar todas tus evidencias\n\n"
        "👑 **Admin:** /adduser, /banuser, /getdb"
    )
    
    await client.send_message(message.chat.id, start_msg)

@app.on_message(filters.text & filters.regex(r'http[s]?://'))
async def handle_links(client: Client, message: Message):
    """Maneja enlaces HTTP"""
    try:
        url = message.text
        
        # Verificar acceso
        username = message.from_user.username
        if username != TL_ADMIN_USER:
            jdb = JsonDatabase('database') if JsonDatabase else None
            if jdb:
                jdb.check_create()
                jdb.load()
                if not jdb.get_user(username):
                    await client.send_message(
                        message.chat.id,
                        "❌ No tienes acceso a este bot"
                    )
                    return
        
        # Procesar enlace
        await client.send_message(
            message.chat.id,
            f"🔗 Procesando enlace: {url}\n⏳ Esto puede tomar un momento..."
        )
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(download_file, message, client, url)
            result = future.result()
        
        if result:
            await client.send_message(message.chat.id, "✅ Enlace procesado correctamente")
        else:
            await client.send_message(message.chat.id, "❌ Error al procesar el enlace")
        
    except Exception as e:
        print(f"Error en handle_links: {e}")
        await client.send_message(message.chat.id, f"❌ Error al procesar el enlace: {str(e)}")

# ==============================
# MAIN
# ==============================

def main():
    print("🤖 Iniciando bot con Pyrogram...")
    print(f"📊 API ID: {API_ID}")
    print(f"👑 Admin: {TL_ADMIN_USER}")
    print("✅ Esperando mensajes...")
    print("📌 Envía archivos, fotos, videos o enlaces para procesarlos")
    app.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
        main()
