import requests
import pickle
import datetime
import time

from functools import partial
from resources.lib.ui import utils, database, control
from resources.lib import indexers
from resources import jz


class JikanAPI:
    def __init__(self):
        self.baseUrl = "https://api.jikan.moe/v4"

    def get_anime_info(self, mal_id):
        r = requests.get(f'{self.baseUrl}/anime/{mal_id}')
        return r.json()['data']

    def get_episode_meta(self, mal_id):
        # url = f'{self.baseUrl}/anime/{mal_id}/videos/episodes'
        url = f'{self.baseUrl}/anime/{mal_id}/episodes'  # no pictures but can handle 100 per page
        r = requests.get(url)
        res = r.json()
        if not res['pagination']['has_next_page']:
            res_data = res['data']
        else:
            res_data = res['data']
            for i in range(2, res['pagination']['last_visible_page'] + 1):
                params = {
                    'page': i
                }
                r = requests.get(url, params=params)
                if not r.ok:
                    control.ok_dialog(control.ADDON_NAME, f"{r.json()}")
                    return res_data
                res = r.json()
                res_data += res['data']
                if not res['pagination']['has_next_page']:
                    break
                if i % 3 == 0:
                    time.sleep(2)
        return res_data

    @staticmethod
    def parse_episode_view(res, mal_id, season, poster, fanart, eps_watched, update_time, tvshowtitle, dub_data, filler_data, episodes=None):
        episode = res['mal_id']
        url = f"{mal_id}/{episode}"
        title = res.get('title')
        if not title:
            title = res["episode"]
        image = res['images']['jpg']['image_url'] if res.get('images') else poster
        info = {
            'UniqueIDs': {'mal_id': str(mal_id)},
            'title': title,
            'season': season,
            'episode': episode,
            'plot': 'No plot available',
            'tvshowtitle': tvshowtitle,
            'mediatype': 'episode'
        }
        if eps_watched and int(eps_watched) >= episode:
            info['playcount'] = 1

        try:
            filler = filler_data[episode - 1]
        except (IndexError, TypeError):
            filler = ''

        code = jz.get_second_label(info, dub_data)
        if not code and control.settingids.filler:
            filler = code = control.colorstr(filler, color="red") if filler == 'Filler' else filler
        info['code'] = code

        parsed = utils.allocate_item(title, f"play/{url}", False, True, image, info, fanart, poster)
        kodi_meta = pickle.dumps(parsed)
        if not episodes or kodi_meta != episodes[episode - 1]['kodi_meta']:
            database.update_episode(mal_id, season, episode, update_time, kodi_meta, filler)

        if control.settingids.clean_titles and info.get('playcount') != 1:
            parsed['info']['title'] = res['episode']
            parsed['info']['plot'] = None
        return parsed

    def process_episode_view(self, mal_id, poster, fanart, eps_watched, tvshowtitle, dub_data, filler_data):
        update_time = datetime.date.today().isoformat()

        result = self.get_anime_info(mal_id)
        if not result:
            return []

        title_list = [name['title'] for name in result['titles']]

        season = utils.get_season(title_list)
        result_ep = self.get_episode_meta(mal_id)
        mapfunc = partial(self.parse_episode_view, mal_id=mal_id, season=season, poster=poster, fanart=fanart, eps_watched=eps_watched, update_time=update_time, tvshowtitle=tvshowtitle, dub_data=dub_data, filler_data=filler_data)
        all_results = sorted(list(map(mapfunc, result_ep)), key=lambda x: x['info']['episode'])

        if control.getBool('override.meta.api') and control.getBool('override.meta.notify'):
            control.notify("Jikanmoa", f'{tvshowtitle} Added to Database', icon=poster)
        return all_results

    def append_episodes(self, mal_id, episodes, eps_watched, poster, fanart, tvshowtitle, filler_data=None, dub_data=None):
        update_time = datetime.date.today().isoformat()
        last_updated = datetime.datetime.fromtimestamp(time.mktime(time.strptime(episodes[0].get('last_updated'), '%Y-%m-%d')))
        diff = (datetime.datetime.today() - last_updated).days
        if diff > control.getInt('interface.check.updates'):
            result = self.get_episode_meta(mal_id)
            season = episodes[0]['season']
            mapfunc2 = partial(self.parse_episode_view, mal_id=mal_id, season=season, poster=poster, fanart=fanart, eps_watched=eps_watched, update_time=update_time, tvshowtitle=tvshowtitle, dub_data=dub_data, filler_data=filler_data, episodes=episodes)
            all_results = list(map(mapfunc2, result))
            control.notify("Jikanmoa", f'{tvshowtitle} Appended to Database', icon=poster)
        else:
            mapfunc1 = partial(indexers.parse_episodes, eps_watched=eps_watched, dub_data=dub_data)
            all_results = list(map(mapfunc1, episodes))
        return all_results

    def get_episodes(self, mal_id, show_meta):
        kodi_meta = pickle.loads(database.get_show(mal_id)['kodi_meta'])
        kodi_meta.update(pickle.loads(show_meta['art']))
        fanart = kodi_meta.get('fanart')
        poster = kodi_meta.get('poster')
        tvshowtitle = kodi_meta['title_userPreferred']
        if not (eps_watched := kodi_meta.get('eps_watched')) and control.settingids.watchlist_data:
            from resources.lib.WatchlistFlavor import WatchlistFlavor
            flavor = WatchlistFlavor.get_update_flavor()
            if flavor and flavor.flavor_name in WatchlistFlavor.get_enabled_watchlist_list():
                data = flavor.get_watchlist_anime_entry(mal_id)
                if data.get('eps_watched'):
                    eps_watched = kodi_meta['eps_watched'] = data['eps_watched']
                    database.update_kodi_meta(mal_id, kodi_meta)
        episodes = database.get_episode_list(mal_id)
        dub_data = indexers.process_dub(mal_id, kodi_meta['ename']) if control.getBool('jz.dub') else None
        if episodes:
            if kodi_meta['status'] not in ["FINISHED", "Finished Airing"]:
                from resources.jz import anime_filler
                filler_data = anime_filler.get_data(kodi_meta['ename'])
                return self.append_episodes(mal_id, episodes, eps_watched, poster, fanart, tvshowtitle, filler_data, dub_data), 'episodes'
            return indexers.process_episodes(episodes, eps_watched, dub_data), 'episodes'

        if kodi_meta['episodes'] is None or kodi_meta['episodes'] > 99:
            from resources.jz import anime_filler
            filler_data = anime_filler.get_data(kodi_meta['ename'])
        else:
            filler_data = None
        return self.process_episode_view(mal_id, poster, fanart, eps_watched, tvshowtitle, dub_data, filler_data), 'episodes'

    def get_anime(self, filter_type, page):
        perpage = 25
        params = {
            "limit": perpage,
            "page": page,
            "filter": filter_type
        }
        r = requests.get(f'{self.baseUrl}/top/anime', params)
        return r.json()
