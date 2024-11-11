import threading

from resources.lib.debrid import real_debrid, premiumize, all_debrid, debrid_link
from resources.lib.ui import control


class TorrentCacheCheck:
    def __init__(self):
        self.premiumizeCached = []
        self.realdebridCached = []
        self.all_debridCached = []
        self.debrid_linkCached = []

        self.premiumizeUnCached = []
        self.realdebridUnCached = []
        self.all_debridUnCached = []
        self.debrid_linkUnCached = []
        self.threads = []

    def torrentCacheCheck(self, torrent_list):
        if control.real_debrid_enabled():
            t = threading.Thread(target=self.real_debrid_worker, args=[torrent_list])
            t.start()
            self.threads.append(t)

        if control.debrid_link_enabled():
            t = threading.Thread(target=self.debrid_link_worker, args=[torrent_list])
            self.threads.append(t)
            t.start()

        if control.premiumize_enabled():
            t = threading.Thread(target=self.premiumize_worker, args=[torrent_list])
            t.start()
            self.threads.append(t)

        if control.all_debrid_enabled():
            t = threading.Thread(target=self.all_debrid_worker, args=[torrent_list])
            t.start()
            self.threads.append(t)

        for i in self.threads:
            i.join()

        cached_list = self.realdebridCached + self.premiumizeCached + self.all_debridCached + self.debrid_linkCached
        uncashed_list = self.realdebridUnCached + self.premiumizeUnCached + self.all_debridUnCached + self.debrid_linkUnCached
        return cached_list, uncashed_list

    def all_debrid_worker(self, torrent_list):
        api = all_debrid.AllDebrid()
        if len(torrent_list) == 0:
            return
        cache_check = api.check_hash([i['hash'] for i in torrent_list])
        if not cache_check:
            return
        cached_items = [m.get('hash') for m in cache_check if m.get('instant') is True]

        for i in torrent_list:
            i['debrid_provider'] = 'all_debrid'
            if i['hash'] in cached_items:
                self.all_debridCached.append(i)
            else:
                self.all_debridUnCached.append(i)

    def debrid_link_worker(self, torrent_list):
        if len(torrent_list) == 0:
            return
        cache_check = debrid_link.DebridLink().check_hash([i['hash'] for i in torrent_list])
        if not cache_check:
            return
        for i in torrent_list:
            i['debrid_provider'] = 'debrid_link'
            if i['hash'] in list(cache_check.keys()):
                self.debrid_linkCached.append(i)
            else:
                self.debrid_linkUnCached.append(i)

    def real_debrid_worker(self, torrent_list):
        hash_list = [i['hash'] for i in torrent_list]
        if len(hash_list) == 0:
            return
        api = real_debrid.RealDebrid()
        realDebridCache = api.checkHash(hash_list)
        for torrent in torrent_list:
            hash_info = realDebridCache.get(torrent['hash'], {})
            torrent['debrid_provider'] = 'real_debrid'
            if 'rd' in hash_info and len(hash_info['rd']) >= 1:
                self.realdebridCached.append(torrent)
            else:
                self.realdebridUnCached.append(torrent)

    def premiumize_worker(self, torrent_list):
        hash_list = [i['hash'] for i in torrent_list]
        if len(hash_list) == 0:
            return
        premiumizeCache = premiumize.Premiumize().hash_check(hash_list)
        premiumizeCache = premiumizeCache['response']

        for index, torrent in enumerate(torrent_list):
            torrent['debrid_provider'] = 'premiumize'
            if premiumizeCache[index] is True:
                self.premiumizeCached.append(torrent)
            else:
                self.premiumizeUnCached.append(torrent)
