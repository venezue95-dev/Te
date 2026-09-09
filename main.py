from pyrogram import Client, filters
from pyrogram.types import Message
from pyobigram.utils import sizeof_fmt, get_file_size, createID, nice_time
from MoodleClient import MoodleClient
from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto

# ==============================
# CONFIGURACIÓN DE PYROGRAM
# ==============================

# 📌 OBTENER DESDE https://my.telegram.org/apps
API_ID = 20534584  # ⚠️ REEMPLAZA CON TU API ID
API_HASH = "6d5b13261d2c92a9a00afc1fd613b9df"  # ⚠️ REEMPLAZA CON TU API HASH

# TOKEN DEL BOT (de @BotFather)
BOT_TOKEN = "8867154518:AAEiUWIj5DGF182MNxGtx-f29jKG3lw_nVA"

# ADMINISTRADOR
TL_ADMIN_USER = "Eliel_21"

# ==============================
# FUNCIONES AUXILIARES
# ==============================

def downloadFile(downloader, filename, currentBits, totalBits, speed, time, args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename, totalBits, currentBits, speed, time, tid=thread.id)
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex:
        print(str(ex))
    pass

def uploadFile(filename, currentBits, totalBits, speed, time, args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename, totalBits, currentBits, speed, time, originalfile)
        bot.editMessageText(message, downloadingInfo)
    except Exception as ex:
        print(str(ex))
    pass

def processUploadFiles(filename, filesize, files, update, bot, message, thread=None, jdb=None):
    try:
        bot.editMessageText(message, '🤜Preparando Para Subir☁...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.from_user.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
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
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize'] != 0:
                        tokenize = True
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
                        iter += 1
                        if iter >= 10:
                            break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:
                        pass
                return draftlist
            else:
                bot.editMessageText(message, '❌Error En La Pagina❌')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize'] != 0:
                tokenize = True
            bot.editMessageText(message, '🤜Subiendo ☁ Espere Mientras... 😄')
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
        bot.editMessageText(message, '❌Error❌\n' + str(ex))
        return None

def processFile(update, bot, message, file, thread=None, jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.from_user.username)

    # Obtener el límite del usuario (zips en MB, puede ser float)
    user_limit_mb = float(getUser['zips'])
    max_file_size = int(1024 * 1024 * user_limit_mb)

    # Solo forzar 1MB si el límite es 0 o negativo
    if max_file_size <= 0:
        max_file_size = 1 * 1024 * 1024

    file_upload_count = 0
    client = None
    findex = 0

    # COMPRIMIR SIEMPRE que el archivo supere el límite del usuario
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file, file_size, max_file_size)
        bot.editMessageText(message, compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname, max_file_size)
        zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file, file_size, mult_file.files, update, bot, message, jdb=jdb)
        try:
            os.unlink(file)
        except:
            pass
        file_upload_count = len(mult_file.files)
    else:
        # Subida directa sin comprimir
        client = processUploadFiles(file, file_size, [file], update, bot, message, jdb=jdb)
        file_upload_count = 1

    bot.editMessageText(message, '🤜Preparando Archivo📄...')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                            files = ev['files']
                            break
                        if len(ev['files']) > 0:
                            findex += 1
                    client.logout()
                except:
                    pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype'] == 'calendario':
                for draft in client:
                    files.append({'name': draft['file'], 'directurl': draft['url']})
        else:
            for data in client:
                files.append({'name': data['name'], 'directurl': data['url']})
        bot.deleteMessage(message.chat.id, message.id)
        finishInfo = infos.createFinishUploading(file, file_size, max_file_size, file_upload_count, file_upload_count,
                                                 findex)
        filesInfo = infos.createFileMsg(file, files)
        bot.sendMessage(message.chat.id, finishInfo + '\n' + filesInfo, parse_mode='html')
        if len(files) > 0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname, files, update, bot)

def ddl(update, bot, message, url, file_name='', thread=None, jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url, progressfunc=downloadFile, args=(bot, message, thread))
    if not downloader.stoping:
        if file:
            processFile(update, bot, message, file, jdb=jdb)
        else:
            megadl(update, bot, message, url, file_name, thread, jdb=jdb)

def megadl(update, bot, message, megaurl, file_name='', thread=None, jdb=None):
    megadl = megacli.mega.Mega({'verbose': True})
    megadl.login()
    try:
        info = megadl.get_public_url_info(megaurl)
        file_name = info['name']
        megadl.download_url(megaurl, dest_path=None, dest_filename=file_name, progressfunc=downloadFile,
                            args=(bot, message, thread))
        if not megadl.stoping:
            processFile(update, bot, message, file_name, thread=thread)
    except:
        files = megaf.get_files_from_folder(megaurl)
        for f in files:
            file_name = f['name']
            megadl._download_file(f['handle'], f['key'], dest_path=None, dest_filename=file_name, is_public=False,
                                  progressfunc=downloadFile, args=(bot, message, thread), f_data=f['data'])
            if not megadl.stoping:
                processFile(update, bot, message, file_name, thread=thread)
        pass
    pass

def sendTxt(name, files, update, bot):
    txt = open(name, 'w')
    fi = 0
    for f in files:
        separator = ''
        if fi < len(files) - 1:
            separator += '\n'
        txt.write(f['directurl'] + separator)
        fi += 1
    txt.close()
    bot.sendFile(update.chat.id, name)
    os.unlink(name)

# ==============================
# 📌 MANEJO DE MENSAJES CON PYROGRAM
# ==============================

async def on_message(client: Client, update: Message):
    try:
        username = update.from_user.username
        chat_id = update.chat.id

        # Inicializar base de datos
        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        # Validar si es admin o usuario registrado
        if username == TL_ADMIN_USER or TL_ADMIN_USER == '*' or user_info:
            if user_info is None:
                if username == TL_ADMIN_USER:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            return

        # ==============================
        # 📌 MANEJO DE ARCHIVOS CON PYROGRAM
        # ==============================

        # Verificar si el mensaje contiene un documento
        if update.document:
            try:
                document = update.document
                file_name = document.file_name
                file_size = document.file_size

                # Mensaje de procesando
                message = await client.send_message(chat_id,
                                                    f'📥 Recibido archivo: {file_name} ({infos.format_file_size(file_size)})')

                # 📌 Descargar con Pyrogram
                downloaded_file = await client.download_media(update.document)

                # Procesar el archivo descargado
                processFile(update, client, message, downloaded_file, jdb=jdb)

                # Limpiar archivo temporal
                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass

                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar el archivo: {str(e)}')
                return

        # Verificar si el mensaje contiene una foto
        if update.photo:
            try:
                # Generar nombre para la imagen
                timestamp = int(time.time())
                img_name = f"imagen_{timestamp}.jpg"

                # Mensaje de procesando
                message = await client.send_message(chat_id, f'📥 Recibida imagen: {img_name}')

                # 📌 Descargar con Pyrogram
                downloaded_file = await client.download_media(update.photo[-1], file_name=img_name)

                # Procesar la imagen
                processFile(update, client, message, downloaded_file, jdb=jdb)

                # Limpiar archivo temporal
                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass

                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar la imagen: {str(e)}')
                return

        # Verificar si el mensaje contiene un video
        if update.video:
            try:
                video = update.video
                file_name = video.file_name or f"video_{int(time.time())}.mp4"

                message = await client.send_message(chat_id, f'📥 Recibido video: {file_name}')

                # 📌 Descargar con Pyrogram
                downloaded_file = await client.download_media(update.video, file_name=file_name)

                processFile(update, client, message, downloaded_file, jdb=jdb)

                try:
                    if os.path.exists(downloaded_file):
                        os.unlink(downloaded_file)
                except:
                    pass

                return
            except Exception as e:
                await client.send_message(chat_id, f'❌ Error al procesar el video: {str(e)}')
                return

        # Verificar si el mensaje contiene un audio
        if update.audio:
            try:
                audio = update.audio
                file_name = audio.file_name or f"audio_{int(time.time())}.mp3"

                message = await client.send_message(chat_id, f'📥 Recibido audio: {file_name}')

                # 📌 Descargar con Pyrogram
                downloaded_file = await client.download_media(update.audio, file_name=file_name)

                processFile(update, client, message, downloaded_file, jdb=jdb)

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
        # FIN MANEJO DE ARCHIVOS
        # ==============================

        msgText = update.text or ''

        # Comandos de admin
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '😃Genial @' + user + ' ahora tiene acceso al bot👍'
                    await client.send_message(chat_id, msg)
                except:
                    await client.send_message(chat_id, '❌Error en el comando /adduser username❌')
            else:
                await client.send_message(chat_id, '❌No Tiene Permiso❌')
            return

        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        await client.send_message(chat_id, '❌No Se Puede Banear Usted❌')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '🦶Fuera @' + user + ' Baneado❌'
                    await client.send_message(chat_id, msg)
                except:
                    await client.send_message(chat_id, '❌Error en el comando /banuser username❌')
            else:
                await client.send_message(chat_id, '❌No Tiene Permiso❌')
            return

        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                await client.send_message(chat_id, 'Base De Datos👇')
                await client.send_document(chat_id, 'database.jdb')
            else:
                await client.send_message(chat_id, '❌No Tiene Permiso❌')
            return

        # Comandos de usuario
        if '/tutorial' in msgText:
            tuto = open('tuto.txt', 'r')
            await client.send_message(chat_id, tuto.read())
            tuto.close()
            return

        if '/myuser' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                await client.send_message(chat_id, statInfo)
                return

        # Comando /zips modificado para aceptar decimales
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                    size_str = str(msgText).split(' ')[1]
                    size = float(size_str)

                    if size < 0.1:
                        await client.send_message(chat_id, '❌ El limite minimo es 0.1 MB')
                        return
                    if size > 1024:
                        await client.send_message(chat_id, '❌ El limite maximo es 1024 MB (1 GB)')
                        return

                    if size.is_integer():
                        getUser['zips'] = int(size)
                    else:
                        getUser['zips'] = size

                    jdb.save_data_user(username, getUser)
                    jdb.save()

                    size_bytes = int(size * 1024 * 1024)
                    msg = f'😃 Genial, los zips seran de {infos.format_file_size(size_bytes)} las partes 👍'
                    await client.send_message(chat_id, msg)
                except ValueError:
                    await client.send_message(chat_id, '❌ Error: Debes enviar un numero (ej: /zips 0.9 o /zips 2)')
                except:
                    await client.send_message(chat_id, '❌ Error en el comando /zips size')
            return

        if '/account' in msgText:
            try:
                account = str(msgText).split(' ', 2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /account user,password❌')
            return

        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ', 2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /host moodlehost❌')
            return

        if '/repoid' in msgText:
            try:
                cmd = str(msgText).split(' ', 2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /repo id❌')
            return

        if '/tokenize_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 1
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /tokenize state❌')
            return

        if '/tokenize_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 0
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /tokenize state❌')
            return

        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ', 2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /cloud (moodle or cloud)❌')
            return

        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ', 2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /uptype (typo de subida (evidence,draft,blog))❌')
            return

        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ', 2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            return

        if '/dir' in msgText:
            try:
                cmd = str(msgText).split(' ', 2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['dir'] = repoid + '/'
                    jdb.save_data_user(username, getUser)
                    jdb.save()
                    statInfo = infos.createStat(username, getUser, jdb.is_admin(username))
                    await client.send_message(chat_id, statInfo)
            except:
                await client.send_message(chat_id, '❌Error en el comando /dir folder❌')
            return

        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_', 2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop', True)
                time.sleep(3)
                bot.editMessageText(msg, '❌Tarea Cancelada❌')
            except Exception as ex:
                print(str(ex))
            return

        # Procesar mensajes
        if '/start' in msgText:
            start_msg = 'Bot          : TGUploaderPro v7.0 Fixed\n'
            start_msg += 'Desarrollador: @obisoftdevel\n'
            start_msg += 'Api          : https://github.com/ObisoftDev/tguploaderpro\n'
            start_msg += 'Uso          :Envia Enlaces De Descarga y Archivos Para Procesar (Configure Antes De Empezar , Vea El /tutorial)\n'
            await client.send_message(chat_id, start_msg)

        elif '/files' == msgText and user_info['cloudtype'] == 'moodle':
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'], proxy=proxy)
            loged = client.login()
            if loged:
                files = client.getEvidences()
                filesInfo = infos.createFilesMsg(files)
                await client.send_message(chat_id, filesInfo)
                client.logout()
            else:
                await client.send_message(chat_id, '❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: ' + client.path)

        elif '/txt_' in msgText and user_info['cloudtype'] == 'moodle':
            findex = str(msgText).split('_')[1]
            findex = int(findex)
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'], proxy=proxy)
            loged = client.login()
            if loged:
                evidences = client.getEvidences()
                evindex = evidences[findex]
                txtname = evindex['name'] + '.txt'
                sendTxt(txtname, evindex['files'], update, client)
                client.logout()
                await client.send_message(chat_id, 'TxT Aqui👇')
            else:
                await client.send_message(chat_id, '❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: ' + client.path)

        elif '/del_' in msgText and user_info['cloudtype'] == 'moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                await client.send_message(chat_id, 'Archivo Borrado 🦶')
            else:
                await client.send_message(chat_id, '❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: ' + client.path)

        elif '/delall' in msgText and user_info['cloudtype'] == 'moodle':
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            if loged:
                evfiles = client.getEvidences()
                for item in evfiles:
                    client.deleteEvidence(item)
                client.logout()
                await client.send_message(chat_id, 'Archivo Borrado 🦶')
            else:
                await client.send_message(chat_id, '❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: ' + client.path)

        elif 'http' in msgText:
            url = msgText
            ddl(update, client, message, url, file_name='', jdb=jdb)

        else:
            await client.send_message(chat_id, '😵No se pudo procesar😵')

    except Exception as ex:
        print(str(ex))

# ==============================
# MAIN
# ==============================

def main():
    # Crear cliente Pyrogram
    app = Client(
        "my_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )

    # Registrar el handler de mensajes
    @app.on_message()
    async def handler(client, message):
        await on_message(client, message)

    # Iniciar el bot
    app.run()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        main()
