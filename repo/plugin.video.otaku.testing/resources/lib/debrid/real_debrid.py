import time
import requests
import xbmc

from resources.lib.ui import control, source_utils


class RealDebrid:
    def __init__(self):
        self.ClientID = control.getSetting('rd.client_id')
        self.ClientSecret = control.getSetting('rd.secret')
        self.token = control.getSetting('realdebrid.token')
        self.refresh = control.getSetting('rd.refresh')
        self.DeviceCode = ''
        self.OauthTimeout = 0
        self.OauthTimeStep = 0
        self.OauthUrl = 'https://api.real-debrid.com/oauth/v2'
        self.BaseUrl = "https://api.real-debrid.com/rest/1.0"
        self.headers = {'Authorization': f"Bearer {self.token}"}


    def auth_loop(self):
        if control.progressDialog.iscanceled():
            control.progressDialog.close()
            return
        xbmc.sleep(self.OauthTimeStep)
        params = {
            'client_id': self.ClientID,
            'code': self.DeviceCode
        }
        r = requests.get(f'{self.OauthUrl}/device/credentials', params=params)
        if r.ok:
            response = r.json()
            control.progressDialog.close()
            control.setSetting('rd.client_id', response['client_id'])
            control.setSetting('rd.secret', response['client_secret'])
            self.ClientSecret = response['client_secret']
            self.ClientID = response['client_id']

    def auth(self):
        self.ClientSecret = ''
        self.ClientID = 'X245A4XAIBGVM'
        params = {
            'client_id': self.ClientID,
            'new_credentials': 'yes'
        }
        resp = requests.get(f'{self.OauthUrl}/device/code', params=params).json()
        copied = control.copy2clip(resp['user_code'])
        display_dialog = (f"{control.lang(30020).format(control.colorstr('https://real-debrid.com/device'))}[CR]"
                          f"{control.lang(30021).format(control.colorstr(resp['user_code']))}")
        if copied:
            display_dialog = f"{display_dialog}[CR]{control.lang(30022)}"
        control.progressDialog.create(f'{control.ADDON_NAME}: Real-Debrid Auth')
        control.progressDialog.update(-1, display_dialog)
        self.OauthTimeout = int(resp['expires_in'])
        self.OauthTimeStep = int(resp['interval'])
        self.DeviceCode = resp['device_code']

        while self.ClientSecret == '':
            self.auth_loop()

        self.token_request()

        user_information = requests.get(f'{self.BaseUrl}/user', headers=self.headers).json()
        if user_information['type'] != 'premium':
            control.ok_dialog(control.ADDON_NAME, control.lang(30024))

    def token_request(self):
        if self.ClientSecret == '':
            return

        postData = {
            'client_id': self.ClientID,
            'client_secret': self.ClientSecret,
            'code': self.DeviceCode,
            'grant_type': 'http://oauth.net/grant_type/device/1.0'
        }

        response = requests.post(f'{self.OauthUrl}/token', data=postData)
        response = response.json()

        control.setSetting('realdebrid.token', response['access_token'])
        control.setSetting('rd.refresh', response['refresh_token'])
        control.setInt('realdebrid.expiry', int(time.time()) + int(response['expires_in']))
        self.token = response['access_token']
        self.refresh = response['refresh_token']
        user_info = requests.get(f'{self.BaseUrl}/user', headers=self.headers).json()
        control.setSetting('realdebrid.username', user_info['username'])
        control.setSetting('realdebrid.auth.status', user_info['type'])
        control.ok_dialog(control.ADDON_NAME, 'Real Debrid %s' % control.lang(30023))

    def refreshToken(self):
        postData = {
            'grant_type': 'http://oauth.net/grant_type/device/1.0',
            'code': self.refresh,
            'client_secret': self.ClientSecret,
            'client_id': self.ClientID
        }
        r = requests.post(f"{self.OauthUrl}/token", data=postData)
        if r.ok:
            response = r.json()
            self.token = response['access_token']
            self.refresh = response['refresh_token']
            self.headers['Authorization'] = f"Bearer {self.token}"
            control.setSetting('realdebrid.token', self.token)
            control.setSetting('rd.refresh', self.refresh)
            control.setInt('realdebrid.expiry', int(time.time()) + int(response['expires_in']))
            user_info = requests.get(f'{self.BaseUrl}/user', headers=self.headers).json()
            control.setSetting('realdebrid.username', user_info['username'])
            control.setSetting('realdebrid.auth.status', user_info['type'])
            control.log('refreshed rd.token')
        else:
            control.log(repr(r), 'warning')

    def addMagnet(self, magnet):
        postData = {
            'magnet': magnet
        }
        response = requests.post(f'{self.BaseUrl}/torrents/addMagnet', headers=self.headers, data=postData).json()
        return response

    def list_torrents(self):
        response = requests.get(f'{self.BaseUrl}/torrents', headers=self.headers).json()
        return response

    def torrentInfo(self, torrent_id):
        return requests.get(f'{self.BaseUrl}/torrents/info/{torrent_id}', headers=self.headers).json()

    def torrentSelect(self, torrentid, fileid='all'):
        postData = {
            'files': fileid
        }
        r = requests.post(f'{self.BaseUrl}/torrents/selectFiles/{torrentid}', headers=self.headers, data=postData)
        return r.ok

    def resolve_hoster(self, link):
        postData = {
            'link': link
        }
        response = requests.post(f'{self.BaseUrl}/unrestrict/link', headers=self.headers, data=postData).json()
        return response['download']

    def deleteTorrent(self, torrent_id):
        requests.delete(f'{self.BaseUrl}/torrents/delete/{torrent_id}', headers=self.headers, timeout=10)

    def resolve_single_magnet(self, hash_, magnet, episode='', pack_select=False):
        pass

    @staticmethod
    def resolve_cloud(source, pack_select):
        if source['torrent_files']:
            best_match = source_utils.get_best_match('path', source['torrent_files'], source['episode'], pack_select)
            if not best_match or not best_match['path']:
                return
            for f_index, torrent_file in enumerate(source['torrent_files']):
                if torrent_file['path'] == best_match['path']:
                    return source['torrent_info']['links'][f_index]

    def resolve_uncached_source(self, source, runinbackground, silent):
        heading = f'{control.ADDON_NAME}: Cache Resolver'
        if not runinbackground:
            control.progressDialog.create(heading, "Caching Progress")
        stream_link = None
        self.addMagnet(source['magnet'])
        torrent = self.list_torrents()[0]
        torrent = self.torrentInfo(torrent['id'])
        if not self.torrentSelect(torrent['id']):
            self.deleteTorrent(torrent['id'])
            control.ok_dialog(control.ADDON_NAME, "BAD LINK")
            if runinbackground:
                return
        else:
            if runinbackground:
                control.notify(heading, "The souce is downloading to your cloud")
                return
            while torrent['status'] != 'downloaded':
                xbmc.sleep(1000)
                if control.progressDialog.iscanceled() or control.abort_requested():
                    break
                torrent = self.torrentInfo(torrent['id'])
                f_body = f'''
            Progress: {torrent['progress']} %
            Seeders: {torrent.get('seeders', 0)}
            Speed: {source_utils.get_size(torrent.get('speed', 0))}
'''
                control.progressDialog.update(int(torrent.get('progress', 0)), f_body)
        control.progressDialog.close()
        if torrent['status'] == 'downloaded':
            torrent_files = [selected for selected in torrent['files'] if selected['selected'] == 1]
            if len(torrent['files']) == 1:
                best_match = torrent_files[0]
            else:
                best_match = source_utils.get_best_match('path', torrent_files, source['episode_re'])
            if not best_match or not best_match['path']:
                return
            for f_index, torrent_file in enumerate(torrent_files):
                if torrent_file['path'] == best_match['path']:
                    hash_ = torrent['links'][f_index]
                    stream_link = self.resolve_hoster(hash_)
                    break
            if not silent:
                control.ok_dialog(heading, f'Finished Caching Source\nThe source has been added to your cloud')
        else:
            self.deleteTorrent(torrent['id'])
        if silent:
            self.deleteTorrent(torrent['id'])
        return stream_link
