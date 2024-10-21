import pickle
import re
import requests
import itertools

from functools import partial
from bs4 import BeautifulSoup
from resources.lib.ui import database, source_utils
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.indexers import malsync


class Sources(BrowserBase):
    _BASE_URL = 'https://gogoanime3.co/'

    def get_sources(self, mal_id, episode, get_backup):
        show = database.get_show(mal_id)
        kodi_meta = pickle.loads(show['kodi_meta'])
        title = kodi_meta.get('name')
        title = self._clean_title(title)

        slugs = database.get_(malsync.get_slugs, 168, mal_id=mal_id, site='Gogoanime')
        if not slugs:
            headers = {'Referer': self._BASE_URL}
            params = {
                'keyword': title,
                'id': -1,
                'link_web': self._BASE_URL
            }
            r = requests.get('https://ajax.gogo-load.com/site/loadAjaxSearch', headers=headers, params=params)
            r = r.json().get('content')

            if not r and ':' in title:
                title = title.split(':')[0]
                params['keyword'] = title
                r = requests.get('https://ajax.gogo-load.com/site/loadAjaxSearch', headers=headers, params=params)
                r = r.json().get('content')

            soup = BeautifulSoup(r, 'html.parser')
            items = soup.find_all('div', {'class': 'list_search_ajax'})
            if len(items) == 1:
                slugs = [items[0].find('a').get('href').split('/')[-1]]
            else:
                slugs = [
                    item.find('a').get('href').split('/')[-1]
                    for item in items
                    if ((item.a.text.strip() + '  ').lower()).startswith((title + '  ').lower())
                    or ((item.a.text.strip() + '  ').lower()).startswith((title + ' (Dub)  ').lower())
                    or ((item.a.text.strip() + '  ').lower()).startswith((title + ' (TV)  ').lower())
                    or ((item.a.text.strip() + '  ').lower()).startswith((title + ' (TV) (Dub)  ').lower())
                    or ((item.a.text.strip().replace(' - ', ' ') + '  ').lower()).startswith((title + '  ').lower())
                    or (item.a.text.strip().replace(':', ' ') + '   ').startswith(title + '   ')
                ]
            if not slugs:
                slugs = database.get_(get_backup, 168, mal_id, 'Gogoanime')
                if not slugs:
                    return []
        slugs = list(slugs.keys()) if isinstance(slugs, dict) else slugs
        mapfunc = partial(self._process_gogo, episode=episode)
        all_results = list(map(mapfunc, slugs))
        all_results = list(itertools.chain(*all_results))
        return all_results

    def _process_gogo(self, slug, episode):
        if slug.startswith('http'):
            slug = slug.split('/')[-1]
        url = "{0}{1}-episode-{2}".format(self._BASE_URL, slug, episode)
        headers = {'Referer': self._BASE_URL}
        title = (slug.replace('-', ' ')).title() + '  Episode-{0}'.format(episode)
        r = requests.get(url, headers=headers).text

        if not r:
            url = '{0}category/{1}'.format(self._BASE_URL, slug)
            html = requests.get(url, headers=headers).text
            mid = re.findall(r'value="([^"]+)"\s*id="movie_id"', html)
            if mid:
                params = {'ep_start': episode,
                          'ep_end': episode,
                          'id': mid[0],
                          'alias': slug}
                eurl = 'https://ajax.gogo-load.com/ajax/load-list-episode'
                r2 = requests.get(eurl, headers=headers, params=params).text
                soup2 = BeautifulSoup(r2, 'html.parser')
                eslug = soup2.find('a')
                if eslug:
                    eslug = eslug.get('href').strip()
                    url = "{0}{1}".format(self._BASE_URL[:-1], eslug)
                    r = requests.get(url, headers=headers).text

        soup = BeautifulSoup(r, 'html.parser')
        sources = []
        for element in soup.select('.anime_muti_link > ul > li'):
            server = element.get('class')[0]
            link = element.a.get('data-video')

            if server.lower() in self.embeds():
                if link.startswith('//'):
                    link = 'https:' + link

                source = {
                    'release_title': title,
                    'hash': link,
                    'type': 'embed',
                    'quality': 0,
                    'debrid_provider': '',
                    'provider': 'gogo',
                    'size': 'NA',
                    'byte_size': 0,
                    'info': source_utils.getInfo(slug) + [server],
                    'lang': source_utils.getAudio_lang(title)
                }
                sources.append(source)

        return sources
