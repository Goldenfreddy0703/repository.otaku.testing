import re
import requests
import threading

from resources.lib.ui import source_utils
from resources.lib.ui.BrowserBase import BrowserBase
from resources.lib.debrid import real_debrid, premiumize, all_debrid


class Sources(BrowserBase):
    def __init__(self):
        self.cloud_files = []
        self.threads = []

    def get_sources(self, debrid, query, episode):
        if debrid.get('real_debrid'):
            t = threading.Thread(target=self.rd_cloud_inspection, args=(query, episode,))
            t.start()
            self.threads.append(t)
        if debrid.get('premiumize'):
            t = threading.Thread(target=self.premiumize_cloud_inspection, args=(query, episode,))
            t.start()
            self.threads.append(t)
        if debrid.get('all_debrid'):
            t = threading.Thread(target=self.alldebrid_cloud_inspection, args=(query, episode,))
            t.start()
            self.threads.append(t)
        for i in self.threads:
            i.join()
        return self.cloud_files

    def rd_cloud_inspection(self, query, episode):
        api = real_debrid.RealDebrid()
        torrents = api.list_torrents()
        filenames = [re.sub(r'\[.*?]\s*', '', i['filename'].replace(',', '')) for i in torrents]
        filenames_query = ','.join(filenames)
        r = requests.get('https://armkai.vercel.app/api/fuzzypacks', params={"dict": filenames_query, "match": query})
        resp = r.json()

        for i in resp:
            torrent = torrents[i]
            filename = re.sub(r'\[.*?]', '', torrent['filename']).lower()
            if source_utils.is_file_ext_valid(filename) and episode not in filename:
                continue
            torrent_info = api.torrentInfo(torrent['id'])
            torrent_files = [selected for selected in torrent_info['files'] if selected['selected'] == 1]

            if len(torrent_files) > 1 and len(torrent_info['links']) == 1:
                continue

            if not any(source_utils.is_file_ext_valid(tor_file['path'].lower()) for tor_file in torrent_files):
                continue

            self.cloud_files.append(
                {
                    'quality': source_utils.getQuality(torrent_files[0]['path']),
                    'lang': source_utils.getAudio_lang(torrent_files[0]['path']),
                    'hash': torrent_info['links'],
                    'provider': 'Cloud',
                    'type': 'cloud',
                    'release_title': torrent['filename'],
                    'info': source_utils.getInfo(torrent_files[0]['path']),
                    'debrid_provider': 'real_debrid',
                    'size': source_utils.get_size(torrent['bytes']),
                    'byte_size': torrent['bytes'],
                    'torrent': torrent,
                    'torrent_files': torrent_files,
                    'torrent_info': torrent_info,
                    'episode': episode
                }
            )

    def premiumize_cloud_inspection(self, query, episode):
        cloud_items = premiumize.Premiumize().list_folder('')

        filenames = [re.sub(r'\[.*?]\s*', '', i['name'].replace(',', '')) for i in cloud_items]
        filenames_query = ','.join(filenames)
        r = requests.get('https://armkai.vercel.app/api/fuzzypacks', params={"dict": filenames_query, "match": query})
        resp = r.json()
        for i in resp:
            torrent = cloud_items[i]
            filename = re.sub(r'\[.*?]', '', torrent['name']).lower()

            if torrent['type'] == 'file' and source_utils.is_file_ext_valid(filename):
                if episode in filename.rsplit('-', 1)[1]:
                    self.add_premiumize_cloud_item(torrent)
                else:
                    continue

            torrent_folder = premiumize.Premiumize().list_folder(torrent['id'])
            identified_file = source_utils.get_best_match('name', torrent_folder, episode)
            self.add_premiumize_cloud_item(identified_file)

    def alldebrid_cloud_inspection(self, query, episode):
        api = all_debrid.AllDebrid()
        torrents = api.list_torrents()['links']
        filenames = [re.sub(r'\[.*?]\s*', '', i['filename'].replace(',', '')) for i in torrents]
        filenames_query = ','.join(filenames)
        r = requests.get('https://armkai.vercel.app/api/fuzzypacks', params={"dict": filenames_query, "match": query})
        resp = r.json()
        for i in resp:
            torrent = torrents[i]
            filename = re.sub(r'\[.*?]', '', torrent['filename']).lower()
            if source_utils.is_file_ext_valid(filename) and episode not in filename:
                continue

            torrent_info = api.link_info(torrent['link'])
            torrent_files = torrent_info['infos']

            if len(torrent_files) > 1 and len(torrent_info['links']) == 1:
                continue

            if not any(source_utils.is_file_ext_valid(tor_file['filename'].lower()) for tor_file in torrent_files):
                continue

            url = api.resolve_hoster(torrent['link'])
            self.cloud_files.append(
                {
                    'quality': source_utils.getQuality(torrent['filename']),
                    'lang': source_utils.getAudio_lang(torrent['filename']),
                    'hash': url,
                    'provider': 'Cloud',
                    'type': 'cloud',
                    'release_title': torrent['filename'],
                    'info': source_utils.getInfo(torrent['filename']),
                    'debrid_provider': 'all_debrid',
                    'size': source_utils.get_size(torrent['size']),
                    'byte_size': torrent['size'],
                    'episode': episode
                }
            )

    def add_premiumize_cloud_item(self, item):
        self.cloud_files.append({
            'quality': source_utils.getQuality(item['name']),
            'lang': source_utils.getAudio_lang(item['name']),
            'hash': item['link'],
            'provider': 'Cloud',
            'type': 'cloud',
            'release_title': item['name'],
            'info': source_utils.getInfo(item['name']),
            'debrid_provider': 'premiumize',
            'size': source_utils.get_size(int(item['size'])),
            'byte_size': int(item['size'])
        })
