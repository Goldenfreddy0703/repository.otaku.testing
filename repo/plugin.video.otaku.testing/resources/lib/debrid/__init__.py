import threading

from copy import deepcopy
from resources.lib.debrid import real_debrid, all_debrid, debrid_link, premiumize, torbox
from resources.lib.ui import control

premiumizeCached = []
realdebridCached = []
alldebridCached = []
debridlinkCached = []
torboxCached = []

premiumizeUnCached = []
realdebridUnCached = []
alldebridUnCached = []
debridlinkUnCached = []
torboxUnCached = []
threads = []


def torrentCacheCheck(torrent_list):
    enabled_debrids = control.enabled_debrid()
    if enabled_debrids['realdebrid']:
        t = threading.Thread(target=real_debrid_worker, args=(deepcopy(torrent_list),))
        t.start()
        threads.append(t)

    if enabled_debrids['debridlink']:
        t = threading.Thread(target=debrid_link_worker, args=(deepcopy(torrent_list),))
        threads.append(t)
        t.start()

    if enabled_debrids['premiumize']:
        t = threading.Thread(target=premiumize_worker, args=(deepcopy(torrent_list),))
        t.start()
        threads.append(t)

    if enabled_debrids['alldebrid']:
        t = threading.Thread(target=all_debrid_worker, args=(deepcopy(torrent_list),))
        t.start()
        threads.append(t)

    if enabled_debrids['torbox']:
        t = threading.Thread(target=torbox_worker, args=(deepcopy(torrent_list),))
        t.start()
        threads.append(t)

    for i in threads:
        i.join()

    cached_list = realdebridCached + premiumizeCached + alldebridCached + debridlinkCached + torboxCached
    uncached_list = realdebridUnCached + premiumizeUnCached + alldebridUnCached + debridlinkUnCached + torboxUnCached
    return cached_list, uncached_list


def all_debrid_worker(torrent_list):
    if len(torrent_list) != 0:
        for i in torrent_list:
            i['debrid_provider'] = 'Alldebrid'
            alldebridUnCached.append(i)


def debrid_link_worker(torrent_list):
    if len(torrent_list) != 0:
        cache_check = debrid_link.DebridLink().check_hash([i['hash'] for i in torrent_list])
        if cache_check:
            for i in torrent_list:
                i['debrid_provider'] = 'Debrid-Link'
                if i['hash'] in list(cache_check.keys()):
                    debridlinkCached.append(i)
                else:
                    debridlinkUnCached.append(i)


def real_debrid_worker(torrent_list):
    hash_list = [i['hash'] for i in torrent_list]
    if len(hash_list) != 0:
        for torrent in torrent_list:
            torrent['debrid_provider'] = 'Real-Debrid'
            realdebridUnCached.append(torrent)


def premiumize_worker(torrent_list):
    hash_list = [i['hash'] for i in torrent_list]
    if len(hash_list) != 0:
        premiumizeCache = premiumize.Premiumize().hash_check(hash_list)
        premiumizeCache = premiumizeCache['response']

        for index, torrent in enumerate(torrent_list):
            torrent['debrid_provider'] = 'Premiumize'
            if premiumizeCache[index] is True:
                premiumizeCached.append(torrent)
            else:
                premiumizeUnCached.append(torrent)


def torbox_worker(torrent_list):
    hash_list = [i['hash'] for i in torrent_list]
    if len(hash_list) != 0:
        cache_check = [i['hash'] for i in torbox.TorBox().hash_check(hash_list)]
        for torrent in torrent_list:
            torrent['debrid_provider'] = 'TorBox'
            if torrent['hash'] in cache_check:
                torboxCached.append(torrent)
            else:
                torboxUnCached.append(torrent)
