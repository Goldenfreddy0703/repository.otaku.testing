import requests
import xbmcgui

from resources.lib.ui import source_utils, control


class TorBox:
    def __init__(self):
        self.token = control.getSetting('torbox.token')
        self.BaseUrl = "https://api.torbox.app/v1/api"

    def headers(self):
        return {'Authorization': f"Bearer {self.token}"}

    def auth(self):
        self.token = control.input_dialog("Enter API KEY for TorBox:", self.token, xbmcgui.INPUT_ALPHANUM)
        control.setSetting('torbox.token', self.token)
        auth_done = self.status()
        if not auth_done:
            control.ok_dialog(f'{control.ADDON_NAME}: TorBox Auth', "Invalid API KEY!")

    def status(self):
        r = requests.get(f'{self.BaseUrl}/user/me', headers=self.headers())
        if r.ok:
            user_info = r.json()['data']
            control.setSetting('torbox.username', user_info['email'])
            if user_info['plan'] == 0:
                control.setSetting('torbox.auth.status', 'Free')
                control.ok_dialog(f'{control.ADDON_NAME}: TorBox', control.lang(30024))
            elif user_info['plan'] == 1:
                control.setSetting('torbox.auth.status', 'Essential')
            elif user_info['plan'] == 3:
                control.setSetting('torbox.auth.status', 'Standard')
            elif user_info['plan'] == 2:
                control.setSetting('torbox.auth.status', 'Pro')
            control.ok_dialog(control.ADDON_NAME, f'TorBox {control.lang(30023)}')
        return r.ok

    def refreshToken(self):
        pass

    def hash_check(self, hash_list):
        hashes = ','.join(hash_list)
        url = f'{self.BaseUrl}/torrents/checkcached'
        params = {
            'hash': hashes,
            'format': 'list'
        }
        r = requests.get(url, headers=self.headers(), params=params)
        return r.json()['data']

    def addMagnet(self, magnet):
        url = f'{self.BaseUrl}/torrents/createtorrent'
        data = {
            'magnet': magnet
        }
        r = requests.post(url, headers=self.headers(), data=data)
        return r.json()['data']

    def delete_torrent(self, torrent_id):
        url = f'{self.BaseUrl}/torrents/controltorrent'
        data = {
            'torrent_id': str(torrent_id),
            'operation': 'delete'
        }
        r = requests.post(url, headers=self.headers(), json=data)
        return r.ok

    def list_torrents(self):
        url = f'{self.BaseUrl}/torrents/mylist'
        r = requests.get(url, headers=self.headers())
        return r.json()['data']

    def get_torrent_info(self, torrent_id):
        url = f'{self.BaseUrl}/torrents/mylist'
        params = {'id': torrent_id}
        r = requests.get(url, headers=self.headers(), params=params)
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

    def resolve_single_magnet(self, hash_, magnet, episode, pack_select):
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

    def resolve_hoster(self, source):
        return self.request_dl_link(source['folder_id'], source['file']['id'])

    @staticmethod
    def resolve_cloud(source, pack_select):
        if source['hash']:
            best_match = source_utils.get_best_match('short_name', source['hash'], source['episode'], pack_select)
            if not best_match or not best_match['short_name']:
                return
            for f_index, torrent_file in enumerate(source['hash']):
                if torrent_file['short_name'] == best_match['short_name']:
                    return {'folder_id': source['id'], 'file': source['hash'][f_index]}

    def resolve_uncached_source(self, source, runinbackground):
        heading = f'{control.ADDON_NAME}: Cache Resolver'
        torrent = self.addMagnet(source['magnet'])
        torrent_id = torrent['torrent_id']
        torrent_info = self.get_torrent_info(torrent_id)
        control.log(torrent_info)
        if not torrent_info:
            self.delete_torrent(torrent_id)
            control.ok_dialog(control.ADDON_NAME, "BAD LINK")
            return
        else:
            control.notify(heading, "The source is downloading to your cloud")
            return
