## GLOBALS ##

import base64, calendar, datetime, hashlib, inputstreamhelper, json, os, random, requests, sys, time, re
import traceback, urllib, xmltodict, string, binascii

import xbmc, xbmcvfs, xbmcplugin, xbmcgui, xbmcaddon


urlLib = urllib.parse
urlParse = urlLib


KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
ADDON_NAME = 'Sling TV'
ADDON_ID = 'plugin.video.slingtv'
ADDON_URL = 'plugin://plugin.video.slingtv/'
SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
SETTINGS_LOC = SETTINGS.getAddonInfo('profile')
ADDON_PATH = SETTINGS.getAddonInfo('path')
ADDON_VERSION = SETTINGS.getAddonInfo('version')
ICON = SETTINGS.getAddonInfo('icon')
FANART = SETTINGS.getAddonInfo('fanart')
LANGUAGE = SETTINGS.getLocalizedString

# Sign In Settings
USER_EMAIL = SETTINGS.getSetting('User_Email')
USER_PASSWORD = SETTINGS.getSetting('User_Password')

# Hidden Settings
ACCESS_TOKEN = SETTINGS.getSetting('access_token')
ACCESS_TOKEN_JWT = SETTINGS.getSetting('access_token_jwt')
SUBSCRIBER_ID = SETTINGS.getSetting('subscriber_id')
DEVICE_ID = SETTINGS.getSetting('device_id')
USER_SUBS = SETTINGS.getSetting('user_subs')
LEGACY_SUBS = SETTINGS.getSetting('legacy_subs')
USER_DMA = SETTINGS.getSetting('user_dma')
USER_OFFSET = SETTINGS.getSetting('user_offset')
USER_ZIP = SETTINGS.getSetting('user_zip')
FREE_ACCOUNT = SETTINGS.getSetting('free_account')

# EPG Settings
FREE_STREAMS = SETTINGS.getSetting('include_free_channels')
if FREE_STREAMS == 'true' or FREE_ACCOUNT == 'true':
    LEGACY_SUBS += '268,658' 


CACHE = False
UPDATE_LISTING = False
DEBUG_CODE = SETTINGS.getSetting('Debug')
debug = dict(urlParse.parse_qsl(DEBUG_CODE))
CHANNELS = (FREE_ACCOUNT == 'false' or 'channels' in debug)

ANDROID_USER_AGENT = "Sling%20TV/8.4.5.444191 CFNetwork/1485 Darwin/23.1.0"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/69.0.3497.100 Safari/537.36'

HEADERS = {'Accept': '*/*',
           'Origin': 'https://www.sling.com',
           'User-Agent': USER_AGENT,
           'Content-Type': 'application/json;charset=UTF-8',
           'Referer': 'https://www.sling.com',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'en-US,en;q=0.9'}
BASE_URL = 'https://watch.sling.com'
BASE_API = 'https://ums.p.sling.com'
BASE_WEB = 'https://webapp.movetv.com'
BASE_GEO = 'https://p-geo.movetv.com/geo?subscriber_id={}&device_id={}'
MAIN_URL = '%s/config/android/sling/menu_tabs.json' % BASE_WEB
USER_INFO_URL = '%s/v2/user.json' % BASE_API
WEB_ENDPOINTS = '%s/config/env-list/browser-sling.json' % (BASE_WEB)
MYTV = '%s/config/shared/pages/mytv.json' % (BASE_WEB)
CONFIG = '%s/config/browser/sling/config.json' % (BASE_WEB)
VERIFY = True
PRINTABLE = set(string.printable)
CONTENT_TYPE = 'Episodes'


def log(msg, level=xbmc.LOGDEBUG):
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log("------------------------------------------------")
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '- ' + msg, level)
    xbmc.log("------------------------------------------------")

def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval


def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)


def yesNoDialog(str1, header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, no, yes, autoclose)


def yesNoCustomDialog(msg, header=ADDON_NAME, custom='', yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesnocustom(header, msg, custom, no, yes, autoclose)


def notificationDialog(message, header=ADDON_NAME, sound=False, time=1000, icon=ICON):
    try:
        xbmcgui.Dialog().notification(header, message, icon, time, sound)
    except:
        xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))


def loadJSON(string1):
    try:
        return json.loads(string1)
    except Exception as e:
        log("loadJSON Failed! " + str(e), xbmc.LOGERROR)
        return {}


def dumpJSON(string1):
    try:
        return json.dumps(string1)
    except Exception as e:
        log("dumpJSON Failed! " + str(e), xbmc.LOGERROR)
        return ''


def stringToDate(string, date_format):
    if "." in string:
        string = string[0:string.index(".")]
    try:
        return datetime.datetime.strptime(str(string), date_format)
    except TypeError:
        return datetime.datetime(*(time.strptime(str(string), date_format)[0:6]))


def sortGroup(str):
    arr = str.split(',')
    arr = sorted(arr)
    return ','.join(arr)


def utcToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def strip(str):
    return "".join(list(filter(lambda x: x in PRINTABLE, str)))


def addDir(name, handleID, url, mode, info=None, art=None, menu=None):
    global CONTENT_TYPE, ADDON_URL
    log('Adding directory %s' % name)
    directory = xbmcgui.ListItem(name)
    directory.setProperty('IsPlayable', 'false')
    if info is None: directory.setInfo(type='Video', infoLabels={'mediatype': 'videos', 'title': name})
    else:
        if 'mediatype' in info: CONTENT_TYPE = '%ss' % info['mediatype']
        directory.setInfo(type='Video', infoLabels=info)
    if art is None: directory.setArt({'thumb': ICON, 'fanart': FANART})
    else: directory.setArt(art)

    if menu is not None:
        directory.addContextMenuItems(menu)

    try:
        name = urlLib.quote_plus(name)
    except:
        name = urlLib.quote_plus(strip(name))
    if url != '':
        url = ('%s?url=%s&mode=%s&name=%s' % (ADDON_URL, urlLib.quote_plus(url), mode, name))
    else:
        url = ('%s?mode=%s&name=%s' % (ADDON_URL, mode, name))
    log('Directory %s URL: %s' % (name, url))
    xbmcplugin.addDirectoryItem(handle=handleID, url=url, listitem=directory, isFolder=True)
    xbmcplugin.addSortMethod(handle=handleID, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def addOption(name, handleID, url, mode, info=None, art=None, menu=None):
    global CONTENT_TYPE, ADDON_URL
    log('Adding directory %s' % name)
    directory = xbmcgui.ListItem(name)
    directory.setProperty('IsPlayable', 'false')
    if info is None: directory.setInfo(type='Video', infoLabels={'mediatype': 'videos', 'title': name})
    else:
        if 'mediatype' in info: CONTENT_TYPE = '%ss' % info['mediatype']
        directory.setInfo(type='Video', infoLabels=info)
    if art is None: directory.setArt({'thumb': ICON, 'fanart': FANART})
    else: directory.setArt(art)

    if menu is not None:
        directory.addContextMenuItems(menu)

    try:
        name = urlLib.quote_plus(name)
    except:
        name = urlLib.quote_plus(strip(name))
    if url != '':
        url = ('%s?url=%s&mode=%s&name=%s' % (ADDON_URL, urlLib.quote_plus(url), mode, name))
    else:
        url = ('%s?mode=%s&name=%s' % (ADDON_URL, mode, name))
    log('Directory %s URL: %s' % (name, url))
    xbmcplugin.addDirectoryItem(handle=handleID, url=url, listitem=directory, isFolder=False)
    xbmcplugin.addSortMethod(handle=handleID, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def addLink(name, handleID,  url, mode, info=None, art=None, total=0, contextMenu=None, properties=None):
    global CONTENT_TYPE, ADDON_URL
    log('Adding link %s' % name)
    link = xbmcgui.ListItem(name)
    if mode == 'info': link.setProperty('IsPlayable', 'false')
    else: link.setProperty('IsPlayable', 'true')
    if info is None: link.setInfo(type='Video', infoLabels={'mediatype': 'video', 'title': name})
    else:
        if 'mediatype' in info: CONTENT_TYPE = '%ss' % info['mediatype']
        link.setInfo(type='Video', infoLabels=info)
    if art is None: link.setArt({'thumb': ICON, 'fanart': FANART})
    else: link.setArt(art)
    if contextMenu is not None: link.addContextMenuItems(contextMenu)
    if properties is not None:
        log('Adding Properties: %s' % str(properties))
        for key, value in properties.items():
            link.setProperty(key, str(value))
    try:
        name = urlLib.quote_plus(name)
    except:
        name = urlLib.quote_plus(strip(name))
    if url != '':
        url = ('%s?url=%s&mode=%s&name=%s' % (
            ADDON_URL, urlLib.quote_plus(url), mode, name))
    else:
        url = ('%s?mode=%s&name=%s' % (ADDON_URL, mode, name))
    xbmcplugin.addDirectoryItem(handle=handleID, url=url, listitem=link, totalItems=total)
    xbmcplugin.addSortMethod(handle=handleID, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)


def get_env_url():
    log('Building endPoints\r%s' % WEB_ENDPOINTS)
    endpoints = {}
    response = requests.get(WEB_ENDPOINTS, headers=HEADERS, verify=VERIFY)
    if response.ok:
        endpoints = response.json()['environments']['production']

    return endpoints


def restart_iptv():
    pvr_toggle_off = '{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", ' \
                     '"params": {"addonid": "pvr.iptvsimple", "enabled": false}, "id": 1}'
    pvr_toggle_on = '{"jsonrpc": "2.0", "method": "Addons.SetAddonEnabled", ' \
                    '"params": {"addonid": "pvr.iptvsimple", "enabled": true}, "id": 1}'
    xbmc.executeJSONRPC(pvr_toggle_off)
    xbmc.Monitor().waitForAbort(5)
    xbmc.executeJSONRPC(pvr_toggle_on)

