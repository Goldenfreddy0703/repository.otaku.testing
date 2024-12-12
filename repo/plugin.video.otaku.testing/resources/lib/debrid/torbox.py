import requests

from resources.lib.ui import source_utils, control


class TorBox:
    def __init__(self):
        self.token = control.getSetting('torbox.token')
        self.BaseUrl = "https://api.torbox.app/v1/api"
        self.headers = {'Authorization': f"Bearer {self.token}"}

    def auth(self):
        pass

    def refreshToken(self):
        pass

    def hash_check(self, hash_list):
        hashes = ','.join(hash_list)
        url = f'{self.BaseUrl}/torrents/checkcached'
        params = {
            'hash': hashes,
            'format': 'list'
        }
        r = requests.get(url, headers=self.headers, params=params)
        return r.json()['data']

    def addMagnet(self, magnet):
        url = f'{self.BaseUrl}/torrents/createtorrent'
        data = {
            'magnet': magnet
        }
        r = requests.post(url, headers=self.headers, data=data)
        return r.json()['data']

    def delete_torrent(self, torrent_id):
        url = f'{self.BaseUrl}/torrents/controltorrent'
        data = {
            'torrent_id': str(torrent_id),
            'operation': 'delete'
        }
        r = requests.post(url, headers=self.headers, data=data)
        return r.ok

    def list_torrents(self):
        url = f'{self.BaseUrl}/torrents/mylist'
        r = requests.get(url, headers=self.headers)
        return r.json()['data']

    def get_torrent_info(self, torrent_id):
        url = f'{self.BaseUrl}/torrents/mylist'
        params = {
            'id': torrent_id
        }
        r = requests.get(url, headers=self.headers, params=params)
        return r.json()['data']

    def request_dl_link(self, torrent_id, file_id=-1):
        url = f'{self.BaseUrl}/torrents/requestdl'
        params = {
            'token': self.token,
            'torrent_id': torrent_id
        }
        if file_id >= 0:
            params['file_id'] = file_id
        r = requests.get(url, params=params)
        return r.json()['data']

    def resolve_single_magnet(self, hash_, magnet, episode, pack_select=False):
        torrent = self.addMagnet(magnet)
        torrentId = torrent['torrent_id']
        torrent_info = self.get_torrent_info(torrentId)
        folder_details = [{'fileId': x['id'], 'path': x['name']} for x in torrent_info['files']]

        if episode:
            selected_file = source_utils.get_best_match('path', folder_details, str(episode), pack_select)
            if selected_file and selected_file['fileId'] is not None:
                stream_link = self.request_dl_link(torrentId, selected_file['fileId'])
                self.delete_torrent(torrentId)
                return stream_link

        self.delete_torrent(torrentId)

    @staticmethod
    def resolve_cloud(source, pack_select):
        if source['hash']:
            best_match = source_utils.get_best_match('short_name', source['hash'], source['episode'], pack_select)
            if not best_match or not best_match['short_name']:
                return
            for f_index, torrent_file in enumerate(source['hash']):
                if torrent_file['short_name'] == best_match['short_name']:
                    return source['hash'][f_index]
