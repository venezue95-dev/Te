#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyrogram import Client, filters
from pyrogram.types import Message, InlineQueryResultArticle
from pyrogram.enums import ParseMode
from pyrogram.errors import RPCError
from MoodleClient import MoodleClient
from JDatabase import JsonDatabase
import zipfile
import os
import infos
import datetime
import time
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import requests
import urllib.parse
import asyncio

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
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def sizeof_fmt(num, suffix='B'):
    """Formatea bytes a unidades legibles (compatible con pyobigram)"""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

# ==============================
# FUNCIONES DE PROGRESO
# ==============================

def downloadFile(downloader, filename, currentBits, totalBits, speed, time_elapsed, args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread and thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename, totalBits, currentBits, speed, time_elapsed, tid=thread.id if thread else '')
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex:
        print(str(ex))
    pass

def uploadFile(filename, currentBits, totalBits, speed, time_elapsed, args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        uploadingInfo = infos.createUploading(filename, totalBits, currentBits, speed, time_elapsed, originalfile)
        bot.editMessageText(message, uploadingInfo)
    except Exception as ex:
        print(str(ex))
    pass

# ==============================
# FUNCIONES PRINCIPALES
# ==============================

def processUploadFiles(filename, filesize, files, message, bot, thread=None, jdb=None):
    try:
        bot.editMessageText(message, '🤜 Preparando Para Subir ☁...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(message.from_user.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
        
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files) > 1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    resp = None
                    iter_count = 0
                    tokenize = user_info['tokenize'] != 0
                    while resp is None:
                        if user_info['uploadtype'] == 'evidence':
                            fileid, resp = client.upload_file(f, evidence, fileid, progressfunc=uploadFile,
                                                              args=(bot, message, originalfile, thread), tokenize=tokenize)
                            draftlist.append(resp)
                        if user_info['uploadtype'] == 'draft':
                            fileid, resp = client.upload_file_draft(f, progressfunc=uploadFile,
                                                                    args=(bot, message, originalfile, thread),
                                                                    tokenize=tokenize)
                            draftlist.append(resp)
                        if user_info['uploadtype'] == 'blog':
                            fileid, resp = client.upload_file_blog(f, progressfunc=uploadFile,
                                                                   args=(bot, message, originalfile, thread),
                                                                   tokenize=tokenize)
                            draftlist.append(resp)
                        if user_info['uploadtype'] == 'calendario':
                            fileid, resp = client.upload_file_calendar(f, progressfunc=uploadFile,
                                                                       args=(bot, message, originalfile, thread),
                                                                       tokenize=tokenize)
                            draftlist.append(resp)
                        iter_count += 1
                        if iter_count >= 10:
                            break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:
                        pass
                return draftlist
            else:
                bot.editMessageText(message, '❌ Error En La Pagina ❌')
        elif cloudtype == 'cloud':
            tokenize = user_info['tokenize'] != 0
            bot.editMessageText(message, '🤜 Subiendo ☁ Espere Mientras... 😄')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user, passw, host, proxy=proxy)
            loged = client.login()
            if loged:
                originalfile = ''
                if len(files) > 1:
                    originalfile = filename
                filesdata = []
                for f in files:
                    data = client.upload_file(f, path=remotepath, progressfunc=uploadFile,
                                              args=(bot, message, originalfile, thread), tokenize=tokenize)
                    filesdata.append(data)
                    os.unlink(f)
                return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message, f'❌ Error ❌\n{str(ex)}')
        return None

def processFile(message, bot, file_path, thread=None, jdb=None):
    file_size = get_file_size(file_path)
    getUser = jdb.get_user(message.from_user.username)
    
    # Obtener el límite del usuario
    user_limit_mb = float(getUser['zips'])
    max_file_size = int(1024 * 1024 * user_limit_mb)
    
    if max_file_size <= 0:
        max_file_size = 1 * 1024 * 1024
    
    file_upload_count = 0
    client = None
    findex = 0
    
    # Comprimir si el archivo supera el límite
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file_path, file_size, max_file_size)
        bot.editMessageText(message, compresingInfo)
        zipname = str(file_path).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname, max_file_size)
        zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file_path)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file_path, file_size, mult_file.files, message, bot, jdb=jdb)
        try:
            os.unlink(file_path)
        except:
            pass
        file_upload_count = len(mult_file.files)
    else:
        client = processUploadFiles(file_path, file_size, [file_path], message, bot, jdb=jdb)
        file_upload_count = 1
    
    bot.editMessageText(message, '🤜 Preparando Archivo 📄...')
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidences = client.getEvidences()
                    evidname = str(file_path).split('.')[0]
                    for ev in evidences:
                        if ev['name'] == evidname:
                            files = ev['files']
                            break
                        if len(ev.get('files', [])) > 0:
                            findex += 1
                    client.logout()
                except:
                    pass
            if getUser['uploadtype'] in ['draft', 'blog', 'calendario']:
                for draft in client:
                    files.append({'name': draft.get('file', 'desconocido'), 'directurl': draft.get('url', '')})
        else:
            for data in client:
                files.append({'name': data.get('name', 'desconocido'), 'directurl': data.get('url', '')})
        
        bot.deleteMessage(message.chat.id, message.id)
        finishInfo = infos.createFinishUploading(file_path, file_size, max_file_size, file_upload_count, file_upload_count, findex)
        filesInfo = infos.createFileMsg(file_path, files)
        bot.sendMessage(message.chat.id, finishInfo + '\n' + filesInfo, parse_mode='html')
        
        if len(files) > 0:
            txtname = str(file_path).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname, files, message, bot)

def ddl(message, bot, url, file_name='', thread=None, jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url, progressfunc=downloadFile, args=(bot, message, thread))
    if not downloader.stoping:
        if file:
            processFile(message, bot, file, jdb=jdb)
        else:
            megadl(message, bot, url, file_name, thread, jdb=jdb)

def megadl(message, bot, megaurl, file_name='', thread=None, jdb=None):
    try:
        import megacli.mega as mega
        import megacli.megafolder as megaf
        megadl = mega.Mega({'verbose': True})
        megadl.login()
        try:
            info = megadl.get_public_url_info(megaurl)
            file_name = info['name']
            megadl.download_url(megaurl, dest_path=None, dest_filename=file_name, progressfunc=downloadFile,
                                args=(bot, message, thread))
            if not megadl.stoping:
                processFile(message, bot, file_name, jdb=jdb)
        except:
            files = megaf.get_files_from_folder(megaurl)
            for f in files:
                file_name = f['name']
                megadl._download_file(f['handle'], f['key'], dest_path=None, dest_filename=file_name, is_public=False,
                                      progressfunc=downloadFile, args=(bot, message, thread), f_data=f['data'])
                if not megadl.stoping:
                    processFile(message, bot, file_name, jdb=jdb)
    except:
        pass

def sendTxt(name, files, message, bot):
    txt = open(name, 'w')
    for i, f in enumerate(files):
        url = f['directurl']
        txt.write(url)
        if i < len(files) - 1:
            txt.write('\n\n')
    txt.close()
    bot.sendFile(message.chat.id, name)
    os.unlink(name)

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
# CLASE PARA SIMULAR THREAD
# ==============================

class ThreadSimulator:
    def __init__(self, id):
        self.id = id
        self._store = {}
    
    def store(self, key, value):
        self._store[key] = value
    
    def getStore(self, key):
        return self._store.get(key)

class BotSimulator:
    def __init__(self):
        self.threads = {}
        self.this_thread = None
    
    def create_thread(self):
        import random
        tid = str(random.randint(100000, 999999))
        self.threads[tid] = ThreadSimulator(tid)
        self.this_thread = self.threads[tid]
        return self.threads[tid]
    
    def sendMessage(self, chat_id, text, parse_mode=None):
        # Simula enviar mensaje
        print(f"[Mensaje para {chat_id}]: {text}")
        return MockMessage(chat_id, text)
    
    def editMessageText(self, message, text, parse_mode=None):
        print(f"[Editando mensaje]: {text}")
        if message:
            message.text = text
    
    def deleteMessage(self, chat_id, message_id):
        print(f"[Eliminando mensaje {message_id} en {chat_id}]")
    
    def sendFile(self, chat_id, file_path):
        print(f"[Enviando archivo {file_path} a {chat_id}]")

class MockMessage:
    def __init__(self, chat_id, text):
        self.chat = type('obj', (object,), {'id': chat_id})
        self.id = 123456
        self.text = text

# ==============================
# MANEJO DE MENSAJES CON PYROGRAM
# ==============================

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message()
async def handle_message(client: Client, message: Message):
    try:
        username = message.from_user.username
        chat_id = message.chat.id
        
        # Simular bot para compatibilidad
        bot = BotSimulator()
        thread = bot.create_thread()
        
        # Inicializar base de datos
        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()
        
        user_info = jdb.get_user(username)
        
        # Validar acceso
        has_access = False
        if username == TL_ADMIN_USER or user_info:
            has_access = True
            if user_info is None:
                if username == TL_ADMIN_USER:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        
        if not has_access:
            await client.send_message(chat_id, '❌ No tienes acceso a este bot')
            return
        
        # ==============================
        # MANEJO DE ARCHIVOS CON PYROGRAM
        # ==============================
        
        # Documento
        if message.document:
            try:
                document = message.document
                file_name = document.file_name or f"documento_{int(time.time())}"
                file_size = document.file_size
                
                msg = await client.send_message(chat_id, f'📥 Recibido archivo: {file_name} ({format_file_size(file_size)})')
                
                # Descargar con Pyrogram
                downloaded_file = await client.download_media(message.document)
                
                if not downloaded_file:
                    await client.send_message(chat_id, '❌ Error al descargar el archivo')
                    return
                
                # Procesar
                processFile(msg, bot, downloaded_file, thread=thread, jdb=jdb)
                
                # Limpiar
                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass
                
                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar el archivo: {str(e)}')
                return
        
        # Foto
        if message.photo:
            try:
                timestamp = int(time.time())
                img_name = f"imagen_{timestamp}.jpg"
                
                msg = await client.send_message(chat_id, f'📥 Recibida imagen: {img_name}')
                
                downloaded_file = await client.download_media(message.photo[-1], file_name=img_name)
                
                if not downloaded_file:
                    await client.send_message(chat_id, '❌ Error al descargar la imagen')
                    return
                
                processFile(msg, bot, downloaded_file, thread=thread, jdb=jdb)
                
                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass
                
                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar la imagen: {str(e)}')
                return
        
        # Video
        if message.video:
            try:
                video = message.video
                file_name = video.file_name or f"video_{int(time.time())}.mp4"
                
                msg = await client.send_message(chat_id, f'📥 Recibido video: {file_name}')
                
                downloaded_file = await client.download_media(message.video, file_name=file_name)
                
                if not downloaded_file:
                    await client.send_message(chat_id, '❌ Error al descargar el video')
                    return
                
                processFile(msg, bot, downloaded_file, thread=thread, jdb=jdb)
                
                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass
                
                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar el video: {str(e)}')
                return
        
        # Audio
        if message.audio:
            try:
                audio = message.audio
                file_name = audio.file_name or f"audio_{int(time.time())}.mp3"
                
                msg = await client.send_message(chat_id, f'📥 Recibido audio: {file_name}')
                
                downloaded_file = await client.download_media(message.audio, file_name=file_name)
                
                if not downloaded_file:
                    await client.send_message(chat_id, '❌ Error al descargar el audio')
                    return
                
                processFile(msg, bot, downloaded_file, thread=thread, jdb=jdb)
                
                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass
                
                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar el audio: {str(e)}')
                return
        
        # ==============================
        # MANEJO DE TEXTO (COMANDOS)
        # ==============================
        
        msgText = message.text or ''
        
        # Comandos de admin
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = msgText.split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    await client.send_message(chat_id, f'😃 Genial @{user} ahora tiene acceso al bot 👍')
                except:
                    await client.send_message(chat_id, '❌ Error en el comando /adduser username')
            else:
                await client.send_message(chat_id, '❌ No Tiene Permiso')
            return
        
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = msgText.split(' ')[1]
                    if user == username:
                        await client.send_message(chat_id, '❌ No Se Puede Banear Usted')
                        return
                    jdb.remove(user)
                    jdb.save()
                    await client.send_message(chat_id, f'🦶 Fuera @{user} Baneado ❌')
                except:
                    await client.send_message(chat_id, '❌ Error en el comando /banuser username')
            else:
                await client.send_message(chat_id, '❌ No Tiene Permiso')
            return
        
        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                await client.send_message(chat_id, 'Base De Datos 👇')
                await client.send_document(chat_id, 'database.jdb')
            else:
                await client.send_message(chat_id, '❌ No Tiene Permiso')
            return
        
        # Comandos de usuario
        if '/tutorial' in msgText:
            tuto = open('tuto.txt', 'r') if os.path.exists('tuto.txt') else None
            if tuto:
                await client.send_message(chat_id, tuto.read())
                tuto.close()
            else:
                await client.send_message(chat_id, '📖 Tutorial no disponible')
            return
        
        if '/myuser' in msgText:
            if user_info:
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            return
        
        # Comando /zips
        if '/zips' in msgText:
            try:
                size_str = msgText.split(' ')[1]
                size = float(size_str)
                
                if size < 0.1:
                    await client.send_message(chat_id, '❌ El límite mínimo es 0.1 MB')
                    return
                if size > 1024:
                    await client.send_message(chat_id, '❌ El límite máximo es 1024 MB (1 GB)')
                    return
                
                user_info['zips'] = int(size) if size.is_integer() else size
                jdb.save_data_user(username, user_info)
                jdb.save()
                
                size_bytes = int(size * 1024 * 1024)
                await client.send_message(chat_id, f'😃 Genial, los zips serán de {format_file_size(size_bytes)} las partes 👍')
            except ValueError:
                await client.send_message(chat_id, '❌ Error: Debes enviar un número (ej: /zips 0.9 o /zips 2)')
            except:
                await client.send_message(chat_id, '❌ Error en el comando /zips size')
            return
        
        # Comando /account
        if '/account' in msgText:
            try:
                account = msgText.split(' ', 2)[1].split(',')
                user = account[0]
                passw = account[1]
                user_info['moodle_user'] = user
                user_info['moodle_password'] = passw
                jdb.save_data_user(username, user_info)
                jdb.save()
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌ Error en el comando /account usuario,contraseña')
            return
        
        # Comando /host
        if '/host' in msgText:
            try:
                host = msgText.split(' ', 2)[1]
                user_info['moodle_host'] = host
                jdb.save_data_user(username, user_info)
                jdb.save()
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌ Error en el comando /host moodlehost')
            return
        
        # Comando /repoid
        if '/repoid' in msgText:
            try:
                repoid = int(msgText.split(' ', 2)[1])
                user_info['moodle_repo_id'] = repoid
                jdb.save_data_user(username, user_info)
                jdb.save()
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌ Error en el comando /repoid id')
            return
        
        # Comando /uptype
        if '/uptype' in msgText:
            try:
                upload_type = msgText.split(' ', 2)[1]
                user_info['uploadtype'] = upload_type
                jdb.save_data_user(username, user_info)
                jdb.save()
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌ Error en el comando /uptype (evidence, draft, blog, calendario)')
            return
        
        # Comando /proxy
        if '/proxy' in msgText:
            try:
                proxy = msgText.split(' ', 2)[1]
                user_info['proxy'] = proxy
                jdb.save_data_user(username, user_info)
                jdb.save()
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            except:
                user_info['proxy'] = ''
                jdb.save_data_user(username, user_info)
                jdb.save()
                statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
            return
        
        # Comando /start
        if '/start' in msgText:
            start_msg = (
                '🤖 Bot: TGUploaderPro v7.0\n'
                '👨‍💻 Desarrollador: @obisoftdevel\n'
                '🔗 API: https://github.com/ObisoftDev/tguploaderpro\n\n'
                '📌 Uso: Envía enlaces de descarga o archivos para procesar\n'
                '⚙️ Configura antes de empezar, usa /tutorial'
            )
            await client.send_message(chat_id, start_msg)
            return
        
        # Comando /files (solo Moodle)
        if '/files' == msgText and user_info.get('cloudtype') == 'moodle':
            proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
            moodle_client = MoodleClient(
                user_info['moodle_user'],
                user_info['moodle_password'],
                user_info['moodle_host'],
                user_info['moodle_repo_id'],
                proxy=proxy
            )
            if moodle_client.login():
                files = moodle_client.getEvidences()
                filesInfo = infos.createFilesMsg(files)
                await client.send_message(chat_id, filesInfo)
                moodle_client.logout()
            else:
                await client.send_message(chat_id, f'❌ Error: {moodle_client.path}')
            return
        
        # Comando /txt_
        if '/txt_' in msgText and user_info.get('cloudtype') == 'moodle':
            try:
                findex = int(msgText.split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
                moodle_client = MoodleClient(
                    user_info['moodle_user'],
                    user_info['moodle_password'],
                    user_info['moodle_host'],
                    user_info['moodle_repo_id'],
                    proxy=proxy
                )
                if moodle_client.login():
                    evidences = moodle_client.getEvidences()
                    evindex = evidences[findex]
                    txtname = evindex['name'] + '.txt'
                    sendTxt(txtname, evindex['files'], message, bot)
                    moodle_client.logout()
                    await client.send_message(chat_id, '📄 TXT aquí 👇')
                else:
                    await client.send_message(chat_id, f'❌ Error: {moodle_client.path}')
            except:
                await client.send_message(chat_id, '❌ Error en el comando /txt_ índice')
            return
        
        # Comando /del_
        if '/del_' in msgText and user_info.get('cloudtype') == 'moodle':
            try:
                findex = int(msgText.split('_')[1])
                proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
                moodle_client = MoodleClient(
                    user_info['moodle_user'],
                    user_info['moodle_password'],
                    user_info['moodle_host'],
                    user_info['moodle_repo_id'],
                    proxy=proxy
                )
                if moodle_client.login():
                    evfile = moodle_client.getEvidences()[findex]
                    moodle_client.deleteEvidence(evfile)
                    moodle_client.logout()
                    await client.send_message(chat_id, '🗑️ Archivo Borrado')
                else:
                    await client.send_message(chat_id, f'❌ Error: {moodle_client.path}')
            except:
                await client.send_message(chat_id, '❌ Error en el comando /del_ índice')
            return
        
        # Comando /delall
        if '/delall' in msgText and user_info.get('cloudtype') == 'moodle':
            proxy = ProxyCloud.parse(user_info['proxy']) if user_info.get('proxy') else None
            moodle_client = MoodleClient(
                user_info['moodle_user'],
                user_info['moodle_password'],
                user_info['moodle_host'],
                user_info['moodle_repo_id'],
                proxy=proxy
            )
            if moodle_client.login():
                evfiles = moodle_client.getEvidences()
                for item in evfiles:
                    try:
                        moodle_client.deleteEvidence(item)
                    except:
                        pass
                moodle_client.logout()
                await client.send_message(chat_id, '🗑️ Archivos Borrados')
            else:
                await client.send_message(chat_id, f'❌ Error: {moodle_client.path}')
            return
        
        # Enlaces HTTP
        if 'http' in msgText:
            url = msgText
            msg = await client.send_message(chat_id, '🕰️ Procesando...')
            ddl(msg, bot, url, thread=thread, jdb=jdb)
            return
        
        # Mensaje no reconocido
        if msgText:
            await client.send_message(chat_id, '😵 No se pudo procesar el mensaje')
        
    except Exception as e:
        print(f"Error en handler: {str(e)}")
        try:
            await client.send_message(chat_id, f'❌ Error: {str(e)}')
        except:
            pass

# ==============================
# MAIN
# ==============================

def main():
    print("🤖 Iniciando bot con Pyrogram...")
    print(f"📊 API ID: {API_ID}")
    print(f"👑 Admin: {TL_ADMIN_USER}")
    app.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
        main()
