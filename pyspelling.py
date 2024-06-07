#!/usr/bin/env python3

"""
pyspelling
Used: Python 3, Yandex spellservice.
based on script by proft @ http://proft.me
with my fix
"""

import sys
import dbus
import requests
from subprocess import Popen, PIPE
from PyQt5.Qt import QApplication, QClipboard

ICON_OK = 'emblem-ok-symbolic'
ICON_ERROR = 'emblem-important'
NOTIFY_TIMEOUT_OK = 2000
NOTIFY_TIMEOUT_ERROR = 10000


def set_clipboard(text):
    xsel_proc = Popen(['xsel', '-bi'], stdin=PIPE)
    xsel_proc.communicate(bytes(text, 'utf-8'))


def get_clipboard():
    app = QApplication(sys.argv)
    clipboard = app.clipboard()
    if clipboard.supportsSelection():
        result = str(clipboard.text(QClipboard.Selection))
    else:
        print('Clipboard Selection is not supported')
        # xsel костыль, удалить?
        try:
            xsel_proc = Popen(['xsel1', '-o'], stdout=PIPE, stderr=PIPE)
        except Exception as error:
            result = str(error)
            send_notify_message(ICON_ERROR, 'Ошибка!', result)
            raise SystemExit(error)
        else:
            stdout, stderr = xsel_proc.communicate()
            result = stdout.decode('utf-8')
    return result


def send_notify_message(icon, title, message, time=NOTIFY_TIMEOUT_OK):
    item = "org.freedesktop.Notifications"
    path = "/org/freedesktop/Notifications"
    interface = "org.freedesktop.Notifications"
    app_name = "pySpellCheck"
    id_num_to_replace = 0
    actions_list = ''
    hint = ''
    bus = dbus.SessionBus()
    notif = bus.get_object(item, path)
    notify = dbus.Interface(notif, interface)
    notify.Notify(app_name, id_num_to_replace, icon, title, message, actions_list, hint, time)
    return


cheked_text = get_clipboard()
#print(cheked_text)
#cheked_text = 'вквоз ашипка ышо одна ошипка'
if cheked_text:
    params = {'text': cheked_text}
    try:
        req = requests.get('http://speller.yandex.net/services/spellservice.json/checkText', params=params)
        connection_result = req.status_code
    except requests.exceptions.RequestException as request_error:
        connection_result = request_error
        exit(1)
    if connection_result == 200:
        if len(req.json()) > 0:
            firs_result = True
            wrong_words = []
            for out in req.json():
                curline = out['word'] + ':'
                for string in out['s']:
                    curline += ' ' + string
                    if firs_result:
                        firs_result = False
                        set_clipboard(string)
                if not len(out['s']):
                    curline += ' подходящее слово не найдено'
                wrong_words.append(curline)
            outtext = '\n'.join(wrong_words)
            send_notify_message(ICON_ERROR, cheked_text, outtext, NOTIFY_TIMEOUT_ERROR)
        else:
            send_notify_message(ICON_OK, 'Ошибок не найдено', cheked_text)
    else:
        send_notify_message(ICON_ERROR, 'Ошибка подключения!', str(connection_result))
else:
    send_notify_message(ICON_ERROR, 'Выделите текст!', 'Не найден текст в буфере обмена')
