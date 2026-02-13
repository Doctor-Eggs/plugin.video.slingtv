# You should have received a copy of the GNU General Public License
# along with Sling.TV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

from resources.lib.classes.auth import Auth
import uuid
from resources.lib.globals import *


class Sling(object):

    def __init__(self, sysARG):
        global HANDLE_ID

        log('__init__')
        self.sysARG = sysARG
        HANDLE_ID = int(self.sysARG[1])
        log('Handle ID => %i' % HANDLE_ID)
        self.endPoints = self.buildEndPoints()
        self.handleID = int(self.sysARG[1])
        self.mode = None
        self.url = None
        self.params = None
        self.name = None
        self.auth = Auth()

        self.getParams()

    def run(self):
        if self.mode == "logout":
            log("logging_out")
            self.auth.logOut()
        else:
            global USER_SUBS, HANDLE_ID
            log(f'Addon {ADDON_NAME} entry...')
            loggedIn, message = self.auth.logIn(self.endPoints, USER_EMAIL, USER_PASSWORD)
            log(f"Sling Class is logIn() ==> Success: {loggedIn} Message: {message}")
            if message != "Already logged in.":
                notificationDialog(message)
            if loggedIn:
                gotSubs, message = self.auth.getUserSubscriptions()
                self.auth.getAccessJWT(self.endPoints)
                if gotSubs:
                    USER_SUBS = message
                log("self.user Subscription Attempt, Success => " + str(gotSubs) + " Message => " + message)
            else:
                sys.exit()

        if self.mode is None:
            self.buildMenu()
        elif self.mode == "ondemand":
            if self.url is not None:
                self.onDemand(self.url)
            else:
                self.onDemandCategories()
        elif self.mode == "ondemand_detail":
            if self.url is not None:
                self.onDemandDetail(self.url)
        elif self.mode == "dvr":
            self.dvr()
        elif self.mode == "dvr_detail":
            if self.url is not None:
                self.dvr_detail(self.url)
        elif self.mode == "play":
            self.play()
        elif self.mode == "settings":
            xbmcaddon.Addon().openSettings()

        xbmcplugin.setContent(int(self.sysARG[1]), CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]), xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]), xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]), xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), updateListing=UPDATE_LISTING, cacheToDisc=False)

        xbmc.executebuiltin('Container.SetSortMethod(1)')

    def getParams(self):
        log('Retrieving parameters')

        self.params = dict(urlParse.parse_qsl(self.sysARG[2][1:]))
        if 'category' in self.params:
            self.params['category'] = binascii.unhexlify(self.params['category']).decode()
        try: self.url = urlLib.unquote(self.params['url'])
        except: pass
        try: self.name = urlLib.unquote_plus(self.params['name'])
        except: pass
        try: self.mode = self.params['mode']
        except: pass

        log(f'\rName: {self.name} | Mode: {self.mode}\rURL: {self.sysARG[0]}{self.sysARG[2]}\rParams:\r{self.params}')

    def buildMenu(self):
        log('Building Menu')        

        if self.mode is None:
            log(f"menu art ICON={ICON} FANART={FANART} ADDON_PATH={ADDON_PATH}", xbmc.LOGERROR)
            addDir("On Demand", self.handleID, '', "ondemand")
            addDir("DVR", self.handleID, '', "dvr")
            addOption("Settings", self.handleID, '', mode='settings')

    def onDemandCategories(self):        
        od_headers = {            
            "Authorization": f"Bearer {SETTINGS.getSetting('access_token_jwt')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "dma": USER_DMA,
            "timezone": USER_OFFSET,
            "geo-zipcode": USER_ZIP,
            "features": "use_ui_4=true,inplace_reno_invalidation=true,gzip_response=true,enable_extended_expiry=true,enable_home_channels=true,enable_iap=true,enable_trash_franchise_iview=false,browse-by-service-ribbon=true,subpack-hub-view=true,entitled_streaming_hub=false,add-premium-channels=false,enable_home_sports_scores=true,enable-basepack-ribbon=true,is_rewards_enabled=false",        
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "CLIENT-CONFIG": "rn-client-config",
            "Client-Version": "6.2.4",
            "Player-Version": "8.10.1",
            "Client-Analytics-ID": "",            
            "Device-Model": "Chrome",                        
            "page_size": "large",            
            "response-config": "ar_browser_1_1",            
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://watch.sling.com",
            "Connection": "keep-alive",
            "Referer": "https://watch.sling.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers"
        }

        url = "https://p-cmwnext-fast.movetv.com/pres/on_demand_all"

        r = requests.get(url, headers=od_headers)

        if r.ok:
            for ribbon in r.json()['ribbons']:
                if "title" in ribbon:
                    addDir(ribbon['title'], self.handleID, ribbon['href'], "ondemand")

    def onDemand(self, url):
        od_headers = {            
            "Authorization": f"Bearer {SETTINGS.getSetting('access_token_jwt')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "dma": USER_DMA,
            "timezone": USER_OFFSET,
            "geo-zipcode": USER_ZIP,
            "Sling-Interaction-ID": str(uuid.uuid4()),
            "features": "use_ui_4=true,inplace_reno_invalidation=true,gzip_response=true,enable_extended_expiry=true,enable_home_channels=true,enable_iap=true,enable_trash_franchise_iview=false,browse-by-service-ribbon=true,subpack-hub-view=true,entitled_streaming_hub=false,add-premium-channels=false,enable_home_sports_scores=true,enable-basepack-ribbon=true,is_rewards_enabled=false",        
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "CLIENT-CONFIG": "rn-client-config",
            "Client-Version": "6.2.4",
            "Player-Version": "8.10.1",
            "Client-Analytics-ID": "",            
            "Device-Model": "Chrome",                        
            # "page_size": "large",            
            "response-config": "ar_browser_1_1",            
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://watch.sling.com",
            "Connection": "keep-alive",
            "Referer": "https://watch.sling.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers"
        }
        r = requests.get(url, headers=od_headers)    

        if r.ok:
            try:
                data = r.json()
                log("ondemand response json => " + json.dumps(data, indent=2), xbmc.LOGERROR)
            except Exception as e:
                log("ondemand response json decode failed: " + str(e), xbmc.LOGERROR)
                data = {}
            for tile in data.get('tiles', []):
                if "title" in tile:
                    try:
                        # name = tile["title"]
                        # stream_url = tile["actions"]["PLAY_CONTENT"]["playback_info"]["url"]
                        # icon = tile["image"]["url"]
                        # addLink(name, self.handleID,  stream_url, "play", info=None, art=icon)
                        name = tile.get("title", "")
                        actions = tile.get("actions", {})
                        icon = tile.get("image", {}).get("url", "")

                        play_info = actions.get("PLAY_CONTENT", {}).get("playback_info", {})
                        stream_url = play_info.get("url", "")
                        program_type = play_info.get("program_type", "")

                        detail_url = actions.get("DETAIL_VIEW", {}).get("url", "")
                        fav_type = actions.get("FAVORITE_WITH_INVALIDATION", {}).get("payload", {}).get("type", "")

                        # Infer series vs movie from payload/detail url/program_type.
                        is_series = (
                            fav_type == "series"
                            or "/detail/series/" in detail_url
                            or program_type == "series"
                        )

                        info = {}
                        if is_series:
                            info["mediatype"] = "tvshow"
                        elif program_type == "movie" or stream_url:
                            info["mediatype"] = "movie"

                        if detail_url:
                            addDir(name, self.handleID, detail_url, "ondemand_detail", art={"thumb": icon, "fanart": icon})
                        elif stream_url:
                            addLink(name, self.handleID, stream_url, "play", info=info, art={"thumb": icon, "fanart": icon})
                    except:
                        pass

    def add_detail_tile(self, tile, detail_data, detail_mode, season_hint=None):
        name = tile.get("title")
        if not name:
            return 0
        icon = tile.get("image", {}).get("url", "")
        actions = tile.get("actions", {})
        play_url = actions.get("PLAY_CONTENT", {}).get("playback_info", {}).get("url", "")
        detail_url = actions.get("DETAIL_VIEW", {}).get("url", "")
        info = {"mediatype": "episode"}
        show_title = detail_data.get("title")
        if show_title:
            info["tvshowtitle"] = show_title
        info["title"] = name
        sort_title = tile.get("title")
        if sort_title:
            info["sorttitle"] = sort_title
        plot = tile.get("description") or tile.get("subtitle")
        if plot:
            info["plot"] = plot
        # Try to infer season/episode from title like "S2 E1: ..."
        title_for_parse = tile.get("title") or name
        match = re.search(r"S(\d+)\s*E(\d+)", title_for_parse)
        if match:
            info["season"] = int(match.group(1))
            info["episode"] = int(match.group(2))
        elif season_hint and str(season_hint).isdigit():
            info["season"] = int(season_hint)
        # duration and genre from attributes
        for attr in tile.get("attributes", []):
            if attr.get("type") == "DURATION" and "dur_value" in attr:
                info["duration"] = int(attr["dur_value"])
            if attr.get("type") == "STRING":
                val = attr.get("str_value", "")
                if "/" in val and "genre" not in info:
                    info["genre"] = val.replace("/", " ")
                if val.startswith(("TV-", "PG", "R", "NR")) and "mpaa" not in info:
                    info["mpaa"] = val
            if attr.get("type") == "ICON":
                icon_key = attr.get("icon", {}).get("key", "")
                if icon_key.startswith("RATING_") and "mpaa" not in info:
                    rating_raw = icon_key.replace("RATING_", "")
                    rating_map = {
                        "TV_14": "TV-14",
                        "TV_MA": "TV-MA",
                        "TV_PG": "TV-PG",
                        "TV_G": "TV-G",
                        "TV_Y7": "TV-Y7",
                        "TV_Y7_FV": "TV-Y7-FV",
                        "TV_Y": "TV-Y",
                        "PG_13": "PG-13",
                        "PG": "PG",
                        "R": "R",
                        "NR": "NR",
                        "G": "G",
                        "NC_17": "NC-17",
                    }
                    info["mpaa"] = rating_map.get(rating_raw, rating_raw.replace("_", "-"))
        # air date from playback_info timestamps if present
        play_info = actions.get("PLAY_CONTENT", {}).get("playback_info", {})
        start_time = play_info.get("start_time") or play_info.get("rec_start_time")
        if start_time:
            try:
                info["premiered"] = datetime.datetime.utcfromtimestamp(int(start_time)).strftime("%Y-%m-%d")
            except Exception:
                pass

        if play_url:
            addLink(name, self.handleID, play_url, "play", info=info, art={"thumb": icon, "fanart": icon})
            return 1
        if detail_url:
            addDir(name, self.handleID, detail_url, detail_mode, art={"thumb": icon, "fanart": icon})
            return 1
        addOption(name, self.handleID, "", mode="info", art={"thumb": icon, "fanart": icon})
        return 1

    def onDemandDetail(self, url):
        log(f"ondemand_detail entry url => {url}", xbmc.LOGERROR)
        od_headers = {            
            "Authorization": f"Bearer {SETTINGS.getSetting('access_token_jwt')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "dma": USER_DMA,
            "timezone": USER_OFFSET,
            "geo-zipcode": USER_ZIP,
            "Sling-Interaction-ID": str(uuid.uuid4()),
            "features": "use_ui_4=true,inplace_reno_invalidation=true,gzip_response=true,enable_extended_expiry=true,enable_home_channels=true,enable_iap=true,enable_trash_franchise_iview=false,browse-by-service-ribbon=true,subpack-hub-view=true,entitled_streaming_hub=false,add-premium-channels=false,enable_home_sports_scores=true,enable-basepack-ribbon=true,is_rewards_enabled=false",        
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "CLIENT-CONFIG": "rn-client-config",
            "Client-Version": "6.2.4",
            "Player-Version": "8.10.1",
            "Client-Analytics-ID": "",            
            "Device-Model": "Chrome",                        
            "response-config": "ar_browser_1_1",            
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://watch.sling.com",
            "Connection": "keep-alive",
            "Referer": "https://watch.sling.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers"
        }

        r = requests.get(url, headers=od_headers)
        log(f"ondemand_detail http status => {r.status_code}", xbmc.LOGERROR)
        log(f"ondemand_detail content-type => {r.headers.get('Content-Type', '')}", xbmc.LOGERROR)
        if not r.ok:
            log(f"ondemand_detail http {r.status_code}: {r.text}", xbmc.LOGERROR)
            return
        try:
            data = r.json()
            log("ondemand detail response json => " + json.dumps(data, indent=2), xbmc.LOGERROR)
        except Exception as e:
            log("ondemand detail json decode failed: " + str(e), xbmc.LOGERROR)
            return

        try:
            detail_type = data.get("type")
            if detail_type == "SERIES":
                globals()["CONTENT_TYPE"] = "episodes"
            elif detail_type == "OFFERING":
                globals()["CONTENT_TYPE"] = "videos"
        except Exception:
            pass

        # For movie offerings, play directly instead of listing related ribbons.
        if data.get("type") == "OFFERING":
            detail_actions = data.get("actions_view", {}).get("actions", {})
            if not detail_actions:
                detail_actions = data.get("actions", {})
            play_url = detail_actions.get("PLAY_CONTENT", {}).get("playback_info", {}).get("url", "")
            name = data.get("title")
            if name and play_url:
                icon = data.get("background_image", {}).get("url", "")
                info = {"title": name, "mediatype": "movie"}
                addLink(name, self.handleID, play_url, "play", info=info, art={"thumb": icon, "fanart": icon})
                return

        def add_tile(tile, season_hint=None):
            return self.add_detail_tile(tile, data, "ondemand_detail", season_hint)

        def fetch_json(fetch_url):
            resp = requests.get(fetch_url, headers=od_headers)
            if not resp.ok:
                log(f"ondemand_detail fetch {resp.status_code}: {fetch_url}", xbmc.LOGERROR)
                return None
            try:
                return resp.json()
            except Exception as e:
                log("ondemand_detail fetch json decode failed: " + str(e), xbmc.LOGERROR)
                return None

        items_added = 0

        ribbons_view = data.get("ribbons_view", {})
        for ribbon in ribbons_view.get("ribbons", []):
            for tile in ribbon.get("tiles", []):
                items_added += add_tile(tile)
            for season_ribbon in ribbon.get("seasons_ribbons", []):
                for tile in season_ribbon.get("tiles", []):
                    items_added += add_tile(tile, season_ribbon.get("title"))

        for ribbon in data.get("ribbons", []):
            for tile in ribbon.get("tiles", []):
                items_added += add_tile(tile)

        if items_added == 0:
            rv_href = ribbons_view.get("href", "")
            if rv_href:
                rv_data = fetch_json(rv_href)
                if rv_data:
                    for ribbon in rv_data.get("ribbons", []):
                        for tile in ribbon.get("tiles", []):
                            items_added += add_tile(tile)
                        for season_ribbon in ribbon.get("seasons_ribbons", []):
                            sr_href = season_ribbon.get("href", "")
                            if sr_href:
                                sr_data = fetch_json(sr_href)
                                if sr_data:
                                    for tile in sr_data.get("tiles", []):
                                        items_added += add_tile(tile, season_ribbon.get("title"))

        if items_added == 0:
            detail_actions = data.get("actions_view", {}).get("actions", {})
            if not detail_actions:
                detail_actions = data.get("actions", {})
            play_url = detail_actions.get("PLAY_CONTENT", {}).get("playback_info", {}).get("url", "")
            name = data.get("title")
            if name and play_url:
                icon = data.get("background_image", {}).get("url", "")
                info = {"title": name}
                if data.get("type") == "OFFERING":
                    info["mediatype"] = "movie"
                addLink(name, self.handleID, play_url, "play", info=info, art={"thumb": icon, "fanart": icon})

    def dvr(self):
        dvr_headers = {            
            "Authorization": f"Bearer {SETTINGS.getSetting('access_token_jwt')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Sling-Interaction-ID": str(uuid.uuid4()),
            "dma": USER_DMA,
            "timezone": USER_OFFSET,
            "geo-zipcode": USER_ZIP,
            "features": "use_ui_4=true,inplace_reno_invalidation=true,gzip_response=true,enable_extended_expiry=true,enable_home_channels=true,enable_iap=true,enable_trash_franchise_iview=false,browse-by-service-ribbon=true,subpack-hub-view=true,entitled_streaming_hub=false,add-premium-channels=false,enable_home_sports_scores=true,enable-basepack-ribbon=true,is_rewards_enabled=false",        
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "CLIENT-CONFIG": "rn-client-config",
            "Client-Version": "6.2.4",
            "Player-Version": "8.10.1",
            "Client-Analytics-ID": "",            
            "Device-Model": "Chrome",                        
            "page_size": "large",            
            "response-config": "ar_browser_1_1",            
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://watch.sling.com",
            "Connection": "keep-alive",
            "Referer": "https://watch.sling.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers"
        }

        url = "https://p-cmwnext.movetv.com/pres/dvr_recordings"

        r = requests.get(url, headers=dvr_headers)
        log(f"dvr http status => {r.status_code}", xbmc.LOGERROR)
        log(f"dvr content-type => {r.headers.get('Content-Type', '')}", xbmc.LOGERROR)
        log("dvr response text => " + r.text, xbmc.LOGERROR)

        if r.ok:
            try:
                data = r.json()
                log("dvr response json => " + json.dumps(data, indent=2))
            except Exception as e:
                log("dvr response json decode failed: " + str(e), xbmc.LOGERROR)
                data = {}
            for ribbon in data.get("ribbons", []):
                for tile in ribbon.get("tiles", []):
                    if "title" in tile:
                        try:
                            name = tile["title"]
                            icon = tile.get("image", {}).get("url", "")
                            detail_url = tile.get("actions", {}).get("DETAIL_VIEW", {}).get("url", "")
                            if detail_url:
                                addDir(name, self.handleID, detail_url, "dvr_detail", art={"thumb": icon, "fanart": icon})
                            else:
                                addOption(name, self.handleID, "", mode="info", art={"thumb": icon, "fanart": icon})
                        except:
                            pass

    def dvr_detail(self, url):
        log(f"dvr_detail entry url => {url}", xbmc.LOGERROR)
        dvr_headers = {            
            "Authorization": f"Bearer {SETTINGS.getSetting('access_token_jwt')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Sling-Interaction-ID": str(uuid.uuid4()),
            "dma": USER_DMA,
            "timezone": USER_OFFSET,
            "geo-zipcode": USER_ZIP,
            "features": "use_ui_4=true,inplace_reno_invalidation=true,gzip_response=true,enable_extended_expiry=true,enable_home_channels=true,enable_iap=true,enable_trash_franchise_iview=false,browse-by-service-ribbon=true,subpack-hub-view=true,entitled_streaming_hub=false,add-premium-channels=false,enable_home_sports_scores=true,enable-basepack-ribbon=true,is_rewards_enabled=false",        
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "CLIENT-CONFIG": "rn-client-config",
            "Client-Version": "6.2.4",
            "Player-Version": "8.10.1",
            "Client-Analytics-ID": "",            
            "Device-Model": "Chrome",                        
            "page_size": "large",            
            "response-config": "ar_browser_1_1",            
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://watch.sling.com",
            "Connection": "keep-alive",
            "Referer": "https://watch.sling.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "TE": "trailers"
        }

        r = requests.get(url, headers=dvr_headers)
        log(f"dvr_detail http status => {r.status_code}", xbmc.LOGERROR)
        log(f"dvr_detail content-type => {r.headers.get('Content-Type', '')}", xbmc.LOGERROR)
        if not r.ok:
            log(f"dvr_detail http {r.status_code}: {r.text}", xbmc.LOGERROR)
            return

        try:
            data = r.json()
            log("dvr detail response json => " + json.dumps(data, indent=2), xbmc.LOGERROR)
        except Exception as e:
            log("dvr detail json decode failed: " + str(e), xbmc.LOGERROR)
            return
        # Set content type based on detail type.
        try:
            detail_type = data.get("type")
            if detail_type == "DVR_SERIES":
                globals()["CONTENT_TYPE"] = "episodes"
            elif detail_type == "OFFERING":
                globals()["CONTENT_TYPE"] = "videos"
        except Exception:
            pass

        def add_tile(tile, season_hint=None):
            return self.add_detail_tile(tile, data, "dvr_detail", season_hint)

        def fetch_json(fetch_url):
            resp = requests.get(fetch_url, headers=dvr_headers)
            if not resp.ok:
                log(f"dvr_detail fetch {resp.status_code}: {fetch_url}", xbmc.LOGERROR)
                return None
            try:
                return resp.json()
            except Exception as e:
                log("dvr_detail fetch json decode failed: " + str(e), xbmc.LOGERROR)
                return None

        items_added = 0

        # Some DVR detail responses nest tiles under ribbons_view -> ribbons -> seasons_ribbons
        ribbons_view = data.get("ribbons_view", {})
        for ribbon in ribbons_view.get("ribbons", []):
            for tile in ribbon.get("tiles", []):
                items_added += add_tile(tile)
            for season_ribbon in ribbon.get("seasons_ribbons", []):
                for tile in season_ribbon.get("tiles", []):
                    items_added += add_tile(tile, season_ribbon.get("title"))

        # Fallback: handle any direct ribbons list
        for ribbon in data.get("ribbons", []):
            for tile in ribbon.get("tiles", []):
                items_added += add_tile(tile)

        # If no items were added, try fetching ribbons_view href and seasonribbons hrefs
        if items_added == 0:
            rv_href = ribbons_view.get("href", "")
            if rv_href:
                rv_data = fetch_json(rv_href)
                if rv_data:
                    for ribbon in rv_data.get("ribbons", []):
                        for tile in ribbon.get("tiles", []):
                            items_added += add_tile(tile)
                        for season_ribbon in ribbon.get("seasons_ribbons", []):
                            sr_href = season_ribbon.get("href", "")
                            if sr_href:
                                sr_data = fetch_json(sr_href)
                                if sr_data:
                                    for tile in sr_data.get("tiles", []):
                                        items_added += add_tile(tile, season_ribbon.get("title"))
        # If still empty, populate a single playable item from the detail payload.
        if items_added == 0:
            detail_actions = data.get("actions_view", {}).get("actions", {})
            if not detail_actions:
                detail_actions = data.get("actions", {})
            play_url = detail_actions.get("PLAY_CONTENT", {}).get("playback_info", {}).get("url", "")
            name = data.get("title")
            if name:
                icon = data.get("background_image", {}).get("url", "")
                info = {}
                if data.get("type") == "OFFERING":
                    info["mediatype"] = "movie"
                info["title"] = name
                plot = data.get("description") or data.get("long_description")
                if plot:
                    info["plot"] = plot
                # Extract year/studio from named_attributes when available.
                for named in data.get("named_attributes", []):
                    if named.get("name") == "Release Year" and named.get("value"):
                        try:
                            info["year"] = int(named["value"][0])
                        except Exception:
                            pass
                    if named.get("name") == "Rating" and named.get("value"):
                        info["mpaa"] = named["value"][0]
                    if named.get("name") == "Networks" and named.get("value"):
                        info["studio"] = named["value"][0]
                for attr in data.get("attributes", []):
                    if attr.get("type") == "DURATION" and "dur_value" in attr:
                        info["duration"] = int(attr["dur_value"])
                    if attr.get("type") == "STRING":
                        val = attr.get("str_value", "")
                        if val.isdigit() and "year" not in info:
                            info["year"] = int(val)
                        if val.startswith(("TV-", "PG", "R", "NR")) and "mpaa" not in info:
                            info["mpaa"] = val
                        if "/" in val and "genre" not in info:
                            info["genre"] = val.replace("/", " ")
                        if "studio" not in info and val:
                            info["studio"] = val
                if play_url:
                    addLink(name, self.handleID, play_url, "play", info=info, art={"thumb": icon, "fanart": icon})
                else:
                    addOption(name, self.handleID, "", mode="info", art={"thumb": icon, "fanart": icon})

    def play(self):
        url = self.url
        name = self.name
        log(f'Playing stream {name}')
        #try:
        playlist = self.auth.getPlaylist(url, self.endPoints)
        if not playlist:
            log("play failed: getPlaylist() returned no data", xbmc.LOGERROR)
            return
        url, license_key, external_id, nba_channel = playlist
        # except:
        #     license_key = ''
        #     external_id = ''
        #     nba_channel = False
        
        log(f'{url} | {license_key} | {external_id}')
        liz = xbmcgui.ListItem(name, path=url)
        
        protocol = 'mpd'
        drm = 'com.widevine.alpha'
        mime_type = 'application/dash+xml'

        if protocol in url:
            is_helper = inputstreamhelper.Helper(protocol, drm=drm)

            if not is_helper.check_inputstream():
                sys.exit()

            liz.setProperty('inputstream', is_helper.inputstream_addon)
            liz.setProperty('inputstream.adaptive.manifest_type', protocol)
            liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=' + USER_AGENT)
            liz.setProperty('inputstream.adaptive.manifest_headers', 'User-Agent=' + USER_AGENT)
            
            if license_key != '':
                liz.setProperty('inputstream.adaptive.license_type', drm)
                liz.setProperty('inputstream.adaptive.license_key', license_key)
            liz.setMimeType(mime_type)

            liz.setContentLookup(False)

            # if nba_channel:
            #     liz.setProperty('ResumeTime', '43200')
            #     liz.setProperty('TotalTime', '1')

        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)

        while not xbmc.Player().isPlayingVideo():
            xbmc.Monitor().waitForAbort(0.25)

        if external_id != '':
            play_back_started = time.time()
            while xbmc.Player().isPlayingVideo() and not xbmc.Monitor().abortRequested():
                position = int(float(xbmc.Player().getTime()))
                duration = int(float(xbmc.Player().getTotalTime()))
                xbmc.Monitor().waitForAbort(3)

            if int(time.time() - play_back_started) > 45:
                self.setResume(external_id, position, duration)

    def setResume(self, external_id, position, duration):
        # If there's only 2 min left delete the resume point
        if duration - position < 120:
            url = f"{self.endPoints['cmwnext_url']}/resumes/v4/resumes/{external_id}"
            payload = {
                    "platform": "browser",
                    "product": "sling"
            }
            requests.delete(url, headers=HEADERS, json=payload, auth=self.auth.getAuth(), verify=VERIFY)
        else:
            url = f"{self.endPoints['cmwnext_url']}/resumes/v4/resumes"
            payload = {
                    "external_id": external_id,
                    "position": position,
                    "duration": duration,
                    "resume_type": "fod",
                    "platform": "browser",
                    "product": "sling"
            }

            requests.put(url, headers=HEADERS, json=payload, auth=self.auth.getAuth(), verify=VERIFY)

    def buildEndPoints(self):
        log(f'Building endPoints\r{WEB_ENDPOINTS}')
        endpoints = {}
        response = requests.get(WEB_ENDPOINTS, headers=HEADERS, verify=VERIFY)
        if response.ok:
            endpoints = response.json()['environments']['production']

        return endpoints
