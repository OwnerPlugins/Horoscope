#!/usr/bin/python
# -*- coding: utf-8 -*-

# ======================================================================
# Horoscope Plugin
#
# written by Lululla
#
# ***************************************
#        coded by Lululla              *
#  update     12/01/2025               *
#       Graphics by Oktus              *
# ***************************************
# ATTENTION PLEASE...
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
# You must not remove the credits at
# all and you must make the modified
# code open to everyone. by Lululla
# ======================================================================

# Python standard libraries
import html
from re import search, findall, DOTALL
import unicodedata
from datetime import datetime
from os import path as os_path
from sys import version_info

# Enigma2 core
from enigma import (
    RT_HALIGN_LEFT,
    RT_HALIGN_RIGHT,
    RT_VALIGN_CENTER,
    eListboxPythonMultiContent,
    eTimer,
    gFont,
    loadPNG,
)

# Enigma2 Components
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.Pixmap import Pixmap

# Enigma2 Screens
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

# Enigma2 Plugins
from Plugins.Plugin import PluginDescriptor

# Enigma2 Tools
from Tools.Directories import SCOPE_CURRENT_SKIN, fileExists, resolveFilename

# Twisted
from twisted.web.client import getPage

# Local imports
from . import (
    _,
    __version__,
    HALIGN,
    add_skin_font,
    checkGZIP,
    isDreambox,
    isFHD,
    isHD,
    isWQHD,
    plugin_path
)
from .NewOeSk import ctrlSkin

# Import our new utils
try:
    from . import hUtils
except ImportError:
    # Create minimal hUtils if import fails
    import sys
    sys.path.insert(0, plugin_path)
    import hUtils

PY3 = version_info[0] == 3
if PY3:
    unicode = str

name_plug = _('Global Horoscope')
title_plug = _('Horoscope v.%s') % __version__
base_url = 'https://horoscopeservices.com/horoscopes'
INFO_RI = _("""%(title)s

Author: Lululla

Graphics: Oktus

Rss Feeds Horoscope: %(url)s
""") % {
    "title": title_plug,
    "url": base_url
}


today = datetime.now()
formatted_date = today.strftime("%B %d, %Y")


def removeAccents(content):
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError:
            content = content.decode('latin-1')

    content = unicodedata.normalize('NFKD', content)
    content = ''.join(c for c in content if not unicodedata.combining(c))
    return content


selectsign = [
    _("ARIES"), _("TAURUS"), _("GEMINI"), _("CANCER"),
    _("LEO"), _("VIRGO"), _("LIBRA"), _("SCORPIO"),
    _("SAGITTARIUS"), _("CAPRICORN"), _("AQUARIUS"), _("PISCES"),
]


country_codes = {
    "Arabic": "sa",
    "Azerbaijani": "az",
    "Brazilian": "br",
    "Bulgarian": "bg",
    "Chinese": "cn",
    "Czech": "cz",
    "Danish": "da",
    "Dutch": "nl",
    "English": "gb",
    "Finish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hebrew": "he",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Italian": "it",
    "Japanese": "jp",
    "Korean": "ko",
    "Malay": "ml",
    "Norwegian": "no",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Spanish": "es",
    "Swedish": "sv",
    "Thai": "th",
    "Turkish": "tr",
    "Vietnamese": "vi",
}


class apList(MenuList):
    def __init__(self, list):
        MenuList.__init__(self, list, True, eListboxPythonMultiContent)

        if isWQHD() or isFHD():
            self.l.setItemHeight(100)
            textfont = 42
            print("[Horoscope] Setting font 'lsat' size " + str(textfont))
            self.l.setFont(0, gFont("lsat", textfont))
        else:
            self.l.setItemHeight(100)
            textfont = 32
            print("[Horoscope] Setting font 'lsat' size " + str(textfont))
            self.l.setFont(0, gFont("lsat", textfont))


def apListEntry(name, idx):
    res = [name]

    default_icon = os_path.join(
        resolveFilename(
            SCOPE_CURRENT_SKIN,
            "countries/missing.png"))

    country_code = country_codes.get(name, None)
    if country_code:
        online_flag = "/tmp/horoscope_flags/" + country_code.lower() + ".png"
        if not os_path.exists(online_flag):
            try:
                import threading

                def download_flag():
                    try:
                        hUtils.download_flags(name)
                    except BaseException:
                        pass

                thread = threading.Thread(target=download_flag)
                thread.daemon = True
                thread.start()
            except BaseException:
                pass

        if os_path.exists(online_flag) and os_path.getsize(online_flag) > 100:
            pngx = online_flag
        else:
            pngx = os_path.join(
                resolveFilename(
                    SCOPE_CURRENT_SKIN,
                    "countries/" +
                    country_code +
                    ".png"))
            if not os_path.isfile(pngx):
                pngx = os_path.join(
                    pluginpath, "countries/" + country_code + ".png")

        if HALIGN == RT_HALIGN_RIGHT:
            icon_pos = (300, 30)    # 300px invece di 400
            icon_size = (50, 40)
            text_pos = (10, 0)      # 10px margine sinistro
            text_size = (280, 100)  # 280px (300-20)
        else:
            icon_pos = (5, 30)
            icon_size = (50, 40)
            text_pos = (120, 0)
            text_size = (300, 100)

    elif name[:3].upper() in [s[:3].upper() for s in selectsign]:
        matched_sign = next(
            (s for s in selectsign if s[:3].upper() == name[:3].upper()), None)
        if matched_sign:
            icon_name = matched_sign[:3].lower()
            pngx = pluginpath + "/iconsx/" + icon_name + ".png"
            if fileExists(pngx):
                pngx = os_path.join(pluginpath, "iconsx/" + icon_name + ".png")

        if HALIGN == RT_HALIGN_RIGHT:
            icon_pos = (320, 5)
            icon_size = (100, 100)
            text_pos = (10, 0)
            text_size = (300, 100)
        else:
            icon_pos = (5, 5)
            icon_size = (100, 100)
            text_pos = (120, 0)
            text_size = (300, 100)

    else:
        pngx = default_icon

    if not os_path.isfile(pngx):
        pngx = default_icon

    try:
        png_data = loadPNG(pngx)
        if png_data:
            res.append(
                MultiContentEntryPixmapAlphaTest(
                    pos=icon_pos,
                    size=icon_size,
                    png=png_data))
    except BaseException:
        pass

    # Testo con normalizzazione Unicode
    try:
        import unicodedata

        if PY3:
            if isinstance(name, bytes):
                text_str = name.decode('utf-8', 'ignore')
            else:
                text_str = str(name)
        else:
            if isinstance(name, unicode):
                text_str = name
            elif isinstance(name, str):
                text_str = name.decode('utf-8', 'ignore')
            else:
                text_str = str(name)

        normalized_text = unicodedata.normalize('NFC', text_str)

        res.append(MultiContentEntryText(
            pos=text_pos,
            size=text_size,
            font=0,
            text=normalized_text,
            flags=HALIGN | RT_VALIGN_CENTER
        ))
    except Exception as e:
        print('Default errorexceptions:', str(e))
        res.append(MultiContentEntryText(
            pos=text_pos,
            size=text_size,
            font=0,
            text=name if name else "",
            flags=HALIGN | RT_VALIGN_CENTER
        ))

    return res


def showlist(data, list):
    plist = []
    # item_height = list.item_height if hasattr(list, 'item_height') else 100

    for idx, name in enumerate(data):
        plist.append(apListEntry(name, idx))
    list.setList(plist)


class hMain(Screen):
    skin = ''
    if isWQHD() or isFHD():
        skin = """
            <screen name="hMain" position="center,center" size="1920,1080" backgroundColor="transparent" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/horoscope/backg.png" position="0,0" zPosition="-2" size="1920,1080" scale="fill" alphatest="blend" />
                <eLabel backgroundColor="red" cornerRadius="3" position="34,1064" size="296,6" zPosition="11" />
                <eLabel backgroundColor="green" cornerRadius="3" position="342,1064" size="300,6" zPosition="11" />
                <widget name="key_red" position="32,1016" size="300,45" zPosition="11" font="lsat; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_green" position="342,1016" size="300,45" zPosition="11" font="lsat; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="list" position="60,90" itemHeight="50" size="500,850" zPosition="5" scrollbarMode="showNever" font="lsat; 42" transparent="1" backgroundColor="#ffffff" foregroundColor="#ffccff" backgroundColorSelected="#743554" foregroundColorSelected="#ffffcc" />
                <widget name="date" position="585,90" halign="center" size="745,65" zPosition="5" font="lsat; 42" valign="center" transparent="1" />
                <widget name="lab1" position="1081,961" halign="center" size="819,50" zPosition="5" font="lsat; 36" valign="center" transparent="1" />
                <widget name="lab2" position="585,400" halign="center" size="745,50" zPosition="5" font="lsat; 36" valign="top" transparent="1" />
                <widget name="lab3" position="864,178" size="200,200" cornerRadius="20" zPosition="5" scale="1" transparent="0" alphatest="blend" />
                <widget name="lab4" position="585,470" halign="center" size="745,453" zPosition="5" font="lsat;34" valign="top" transparent="1" />
            </screen>"""
    elif isHD():
        skin = """
            <screen name="hMain" position="center,center" size="1280,720" backgroundColor="transparent" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/horoscope/backg.png" position="0,0" zPosition="-2" size="1280,720" scale="fill" alphatest="blend" />
                <eLabel backgroundColor="red" cornerRadius="3" position="22,709" size="197,4" zPosition="11" />
                <eLabel backgroundColor="green" cornerRadius="3" position="228,709" size="200,4" zPosition="11" />
                <widget name="key_red" position="21,677" size="200,30" zPosition="11" font="lsat; 20" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_green" position="228,677" size="200,30" zPosition="11" font="lsat; 20" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="list" position="30,169" size="420,470" zPosition="5" scrollbarMode="showNever" font="lsat; 42" transparent="1" backgroundColor="#ffffff" foregroundColor="#ffccff" backgroundColorSelected="#743554" foregroundColorSelected="#ffffcc" />
                <widget name="date" position="290,60" halign="center" size="725,43" zPosition="5" font="lsat; 28" valign="center" transparent="1" />
                <widget name="lab1" position="467,621" halign="center" size="725,35" zPosition="5" font="lsat; 24" valign="top" transparent="1" />
                <widget name="lab2" position="468,213" halign="center" size="725,35" zPosition="5" font="lsat; 24" valign="top" transparent="1" />
                <widget name="lab3" position="784,124" size="80,80" cornerRadius="20" zPosition="5" scale="1" transparent="0" />
                <widget name="lab4" position="468,258" halign="center" size="725,350" zPosition="5" font="lsat;26" valign="top" transparent="1" />
            </screen>
            """

    skin = ctrlSkin('hMain', skin)

    def __init__(self, session):
        Screen.__init__(self, session)

        self.list = []
        self.data = []
        self.pics = []
        self.desc = []

        try:
            import threading

            def clean_cache():
                cleaned = hUtils.cleanup_cache(max_age_days=7)
                if cleaned > 0:
                    print("[Horoscope] Cleaned %d old cached flags" % cleaned)

            thread = threading.Thread(target=clean_cache)
            thread.daemon = True
            thread.start()
        except BaseException:
            pass

        self["lab1"] = Label(_("Please wait, connecting to the server..."))
        self["lab2"] = Label("")
        self["lab3"] = Pixmap()
        self["lab4"] = Label(INFO_RI)

        self["date"] = Label(formatted_date)

        self['list'] = self.list
        self['list'] = apList([])

        self['key_red'] = Label(_('Close'))
        self['key_green'] = Label(_('Select'))
        self['actions'] = ActionMap(
            ['WizardActions', 'ColorActions'],
            {
                'ok': self.key_green,
                'green': self.key_green,
                'back': self.close,
                'red': self.close,
                'cancel': self.close,
            }, -1)

        self.onLayoutFinish.append(self._gotPageLoad)

        # Clean old cache on startup
        try:
            cleaned = hUtils.cleanup_cache(max_age_days=7)
            if cleaned > 0:
                print("[Horoscope] Cleaned %d old cached flags" % cleaned)
        except Exception as e:
            print("[Horoscope] Error cleaning cache:", e)

    def set_title(self):
        self["lab1"].setText(_("Please Select"))
        pass

    def _gotPageLoad(self):
        self.data = []
        self.pics = []
        self.desc = []
        for country, code in country_codes.items():
            self.data.append(str(country))
            self.pics.append(str(code))
            showlist(self.data, self['list'])
        self.set_title()

    def key_green(self):
        selected_item = self['list'].getCurrent()
        print('selected_item=', selected_item)  # Debug

        if selected_item:
            try:
                country_name = selected_item[0]
                url_base = '%s/%s-daily-horoscopes' % (base_url, country_name)
                self.session.open(horoscopeMain, url_base)
            except Exception as error:
                print('Error processing selected item:', error)
        else:
            print("No country selected.")


class horoscopeMain(Screen):
    if isWQHD() or isFHD():
        skin = """
            <screen name="horoscopeMain" position="center,center" size="1920,1080" backgroundColor="transparent" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/horoscope/backg.png" position="0,0" zPosition="-2" size="1920,1080" scale="fill" alphatest="blend" />
                <eLabel backgroundColor="red" cornerRadius="3" position="34,1064" size="296,6" zPosition="11" />
                <eLabel backgroundColor="green" cornerRadius="3" position="342,1064" size="300,6" zPosition="11" />
                <widget name="key_red" position="32,1016" size="300,45" zPosition="11" font="lsat; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_green" position="342,1016" size="300,45" zPosition="11" font="lsat; 30" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="list" position="60,90" size="500,850" zPosition="5" scrollbarMode="showNever" font="lsat; 42" transparent="1" backgroundColor="#ffffff" foregroundColor="#ffccff" backgroundColorSelected="#743554" foregroundColorSelected="#ffffcc" />
                <widget name="sort" position="654,1016" zPosition="4" size="300,47" font="lsat; 34" foregroundColor="#fffff4" backgroundColor="#40000000" transparent="1" halign="center" valign="center" />
                <widget name="date" position="585,90" halign="center" size="745,65" zPosition="5" font="lsat; 42" valign="center" transparent="1" />
                <widget name="lab1" position="1034,976" halign="center" size="873,54" zPosition="5" font="lsat; 36" valign="center" transparent="1" />
                <widget name="lab2" position="582,205" halign="center" size="745,50" zPosition="5" font="lsat; 36" valign="top" transparent="1" />
                <widget name="lab3" position="1382,456" size="200,200" cornerRadius="20" zPosition="5" scale="1" transparent="0" alphatest="blend" />
                <widget name="lab4" position="585,267" halign="center" size="745,635" zPosition="5" font="lsat;34" valign="top" transparent="1" />
            </screen>"""
    elif isHD():
        skin = """
            <screen name="horoscopeMain" position="center,center" size="1280,720" backgroundColor="transparent" flags="wfNoBorder">
                <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/horoscope/backg.png" position="0,0" zPosition="-2" size="1280,720" scale="fill" alphatest="blend" />
                <eLabel backgroundColor="red" cornerRadius="3" position="22,709" size="197,4" zPosition="11" />
                <eLabel backgroundColor="green" cornerRadius="3" position="228,709" size="200,4" zPosition="11" />
                <widget name="list" position="22,165" size="420,470" zPosition="10" scrollbarMode="showNever" font="lsat; 28" transparent="1" backgroundColor="#ffffff" foregroundColor="#ffccff" backgroundColorSelected="#743554" foregroundColorSelected="#ffffcc" />
                <widget name="key_red" position="21,677" size="200,30" zPosition="11" font="lsat; 20" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="key_green" position="228,677" size="200,30" zPosition="11" font="lsat; 20" valign="center" halign="center" backgroundColor="background" transparent="1" foregroundColor="white" />
                <widget name="sort" position="435,677" zPosition="4" size="200,30" font="lsat; 24" foregroundColor="#fffff4" backgroundColor="#40000000" transparent="1" halign="center" valign="center" />
                <widget name="date" position="290,60" halign="center" size="725,43" zPosition="5" font="lsat; 28" valign="center" transparent="1" />
                <widget name="lab1" position="518,660" halign="center" size="725,47" zPosition="5" font="lsat; 22" transparent="1" />
                <widget name="lab2" position="451,112" halign="center" size="391,46" zPosition="5" font="lsat; 24" transparent="1" />
                <widget name="lab3" position="919,303" size="120,120" cornerRadius="20" zPosition="5" scale="1" transparent="0" />
                <widget name="lab4" position="450,165" halign="center" size="394,470" zPosition="5" font="lsat;22" transparent="1" />
            </screen>
            """

    skin = ctrlSkin('horoscopeMain', skin)

    def __init__(self, session, url):
        Screen.__init__(self, session)

        self.list = []
        self.sign = []
        self.pics = []
        self.desc = []
        self.url = url

        self["lab1"] = Label(_("Please wait, connecting to the server..."))
        self["lab2"] = Label("")
        self["lab3"] = Pixmap()
        self["lab4"] = Label("")

        self["date"] = Label("")

        self['list'] = apList([])
        self.currentList = 'list'
        self['key_red'] = Label(_('Close'))
        self['key_green'] = Label(_('Read'))

        self['sort'] = Label()
        if HALIGN == RT_HALIGN_RIGHT:
            self['sort'].setText(_('0 - Halign Left'))
        else:
            self['sort'].setText(_('0 - Halign Right'))

        self['actions'] = ActionMap(['EPGSelectActions',
                                     'OkCancelActions',
                                     'WizardActions',
                                     'NumberActions',
                                     'ColorActions'],
                                    {'ok': self.key_green,
                                     'cancel': self.close,
                                     'back': self.close,
                                     'red': self.close,
                                     'green': self.key_green,
                                     '0': self.arabicx,
                                     'up': self.up,
                                     'down': self.down,
                                     'left': self.left,
                                     'right': self.right,
                                     'epg': self.info,
                                     'info': self.info},
                                    -2)

        self.timer = eTimer()
        if isDreambox:
            self.timer_conn = self.timer.timeout.connect(self.startConnection)
        else:
            self.timer.callback.append(self.startConnection)
        self.onShow.append(self.startShow)
        self.onClose.append(self.delTimer)

    def startShow(self):
        self["lab1"].setText(_("Please wait, connecting to the server..."))
        self.timer.start(10)

    def arabicx(self):
        global HALIGN
        if HALIGN == RT_HALIGN_LEFT:
            HALIGN = RT_HALIGN_RIGHT
            self['sort'].setText(_('0 - Halign Left'))
        elif HALIGN == RT_HALIGN_RIGHT:
            HALIGN = RT_HALIGN_LEFT
            self['sort'].setText(_('0 - Halign Right'))
        self.timer.start(10)

    def startConnection(self):
        self.timer.stop()
        self["date"].setText(formatted_date)

        if PY3 and isinstance(self.url, str):
            self.url = self.url.encode()

        if os_path.exists('/var/lib/dpkg/info'):
            self.data = checkGZIP(self.url)
            self.updateInfo(self.data)
        else:
            getPage(
                self.url).addCallback(
                self.updateInfo).addErrback(
                self.errorLoad)

    def errorLoad(self, error):
        print('Error occurred:', str(error))
        self['lab1'].setText(
            _('Addons Download Failure\nNo internet connection or server down!'))

    def updateInfo(self, page):
        self.sign = []
        self.desc = []
        self.pics = []

        data = page.decode('utf-8', errors='ignore')
        try:
            date_pattern = r"<h3><b>(.*?)</b></h3>"
            date_match = search(date_pattern, data, DOTALL)
            if date_match:
                self.full_date = date_match.group(1)

            signs_pattern = r"<h5>([A-Za-z]+)</h5>\s*<p id=\"daily\">(.*?)</p>"
            signs_matches = findall(signs_pattern, data, DOTALL)

            if not signs_matches:
                print("Nessun segno zodiacale trovato.")

            for sign, description in signs_matches:
                if isinstance(sign, str):
                    sign_prefix = sign[:3].lower()
                    print("Sign: {}, Prefix: {}".format(sign, sign_prefix))

                    if sign_prefix in [s[:3].lower() for s in selectsign]:
                        description = html.unescape(description)
                        self.sign.append(sign)
                        self.desc.append(description)
                        icon_name = sign_prefix
                        icon_path = pluginpath + "/icons/" + icon_name + ".png"

                        if fileExists(icon_path):
                            self.pics.append(icon_path)

            showlist(self.sign, self['list'])
            self.load_infos()

        except Exception as e:
            print("Error processing data:", e)

    def load_infos(self):
        if not self.sign:
            return
        try:
            idx = self['list'].getSelectionIndex()
            if idx < 0 or idx >= len(self.pics):
                print("Invalid index:", idx)
                return

            sign = self.sign[idx]
            info = self.desc[idx]
            pic = self.pics[idx]
            self["lab1"].setText(self.full_date)
            self["lab2"].setText(sign)

            if info:
                self["lab4"].setText(info)

            if self["lab3"].instance:
                self["lab3"].instance.setPixmapFromFile(pic)
        except Exception as e:
            print('Error loading info:', e)

    def up(self):
        self[self.currentList].up()
        self.load_infos()

    def down(self):
        self[self.currentList].down()
        self.load_infos()

    def left(self):
        self[self.currentList].pageUp()
        self.load_infos()

    def right(self):
        self[self.currentList].pageDown()
        self.load_infos()

    def key_green(self):
        i = len(self.sign)
        if i <= 0:
            return
        idx = self['list'].getSelectionIndex()
        if idx < 0 or idx >= len(self.pics):
            print("Indice non valido:", idx)
            return

        sign = self.sign[idx]
        info = self.desc[idx]

        aboutbox = self.session.open(MessageBox, _(
            sign + '\n\n' + info), MessageBox.TYPE_INFO)
        aboutbox.setTitle(sign)

    def delTimer(self):
        del self.timer

    def info(self):
        info_text = _(INFO_RI)
        box = self.session.open(
            MessageBox,
            info_text,
            MessageBox.TYPE_INFO,
            close_on_any_key=True
        )
        box.setTitle(_("Information"))


def main(session, **kwargs):
    session.open(hMain)


def Plugins(path, **kwargs):
    global pluginpath
    pluginpath = path
    add_skin_font()
    try:
        hUtils.initialize_flags()
    except Exception as e:
        print("[Horoscope] Error initializing flag system:", e)

    return PluginDescriptor(
        name=name_plug,
        description=title_plug,
        icon="plugin.png",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        fnc=main)
