import threading
import time
import xbmc

from resources.lib.pages import nyaa, animetosho, debrid_cloudfiles, animixplay, animepahe, hianime, gogoanime, localfiles
from resources.lib.ui import control, database
from resources.lib.windows.get_sources_window import GetSources
from resources.lib.windows import sort_select


def getSourcesHelper(actionargs):
    if control.getSetting('general.dialog') == '4':
        sources_window = Sources('get_sources_az.xml', control.ADDON_PATH, actionargs=actionargs)
    else:
        sources_window = Sources('get_sources.xml', control.ADDON_PATH, actionargs=actionargs)
    sources = sources_window.doModal()
    del sources_window
    return sources


class Sources(GetSources):
    def __init__(self, xml_file, location, actionargs=None):
        super(Sources, self).__init__(xml_file, location, actionargs)
        self.torrentProviders = ['nyaa', 'animetosho', 'Cloud Inspection']
        self.embedProviders = ['animix', 'animepahe', 'gogo', 'hianime']
        self.localProviders = ['Local Inspection']
        self.remainingProviders = self.embedProviders + self.torrentProviders + self.localProviders

        self.torrents_qual_len = [0, 0, 0, 0, 0]
        self.embeds_qual_len = [0, 0, 0, 0, 0]
        self.return_data = []
        self.progress = 1
        self.threads = []

        self.cloud_files = []
        self.torrentSources = []
        self.torrentCacheSources = []
        self.torrentUnCacheSources = []
        self.embedSources = []
        self.usercloudSources = []
        self.local_files = []

    def getSources(self, args):
        query = args['query']
        mal_id = args['mal_id']
        episode = args['episode']
        status = args['status']
        media_type = args['media_type']
        duration = args['duration']
        rescrape = args['rescrape']
        # source_select = args['source_select']
        get_backup = args['get_backup']

        self.setProperty('process_started', 'true')

        # set skipintro times to -1 before scraping
        control.setSetting('hianime.skipintro.start', '-1')
        control.setSetting('hianime.skipintro.end', '-1')

        # set skipoutro times to -1 before scraping
        control.setSetting('hianime.skipoutro.start', '-1')
        control.setSetting('hianime.skipoutro.end', '-1')

        if control.real_debrid_enabled() or control.all_debrid_enabled() or control.debrid_link_enabled() or control.premiumize_enabled():
            t = threading.Thread(target=self.user_cloud_inspection, args=(query, mal_id, episode))
            t.start()
            self.threads.append(t)

            if control.getBool('provider.nyaa'):
                t = threading.Thread(target=self.nyaa_worker, args=(query, mal_id, episode, status, media_type, rescrape))
                t.start()
                self.threads.append(t)
            else:
                self.remainingProviders.remove('nyaa')

            if control.getBool('provider.animetosho'):
                t = threading.Thread(target=self.animetosho_worker, args=(query, mal_id, episode, status, media_type, rescrape))
                t.start()
                self.threads.append(t)
            else:
                self.remainingProviders.remove('animetosho')

        else:
            for provider in self.torrentProviders:
                self.remainingProviders.remove(provider)

        ### local ###
        if control.getBool('provider.localfiles'):
            t = threading.Thread(target=self.user_local_inspection, args=(query, mal_id, episode, rescrape))
            t.start()
            self.threads.append(t)
        else:
            self.remainingProviders.remove('Local Inspection')

        ### embeds ###
        if control.getBool('provider.hianime'):
            t = threading.Thread(target=self.hianime_worker, args=(mal_id, episode, rescrape))
            t.start()
            self.threads.append(t)
        else:
            self.remainingProviders.remove('hianime')

        if control.getBool('provider.gogo'):
            t = threading.Thread(target=self.gogo_worker, args=(mal_id, episode, rescrape, get_backup))
            t.start()
            self.threads.append(t)
        else:
            self.remainingProviders.remove('gogo')

        if control.getBool('provider.animix'):
            t = threading.Thread(target=self.animix_worker, args=(mal_id, episode, rescrape))
            t.start()
            self.threads.append(t)
        else:
            self.remainingProviders.remove('animix')

        if control.getBool('provider.animepahe'):
            t = threading.Thread(target=self.animepahe_worker, args=(mal_id, episode, rescrape))
            t.start()
            self.threads.append(t)
        else:
            self.remainingProviders.remove('animepahe')

        timeout = 60 if rescrape else int(control.getSetting('general.timeout'))
        start_time = time.perf_counter()
        runtime = 0

        while runtime < timeout:
            if not self.silent:
                self.updateProgress()
                self.update_properties("4K: %s | 1080: %s | 720: %s | SD: %s| EQ: %s" % (
                    control.colorstr(self.torrents_qual_len[0] + self.embeds_qual_len[0]),
                    control.colorstr(self.torrents_qual_len[1] + self.embeds_qual_len[1]),
                    control.colorstr(self.torrents_qual_len[2] + self.embeds_qual_len[2]),
                    control.colorstr(self.torrents_qual_len[3] + self.embeds_qual_len[3]),
                    control.colorstr(self.torrents_qual_len[4] + self.embeds_qual_len[4])
                ))
            xbmc.sleep(500)
        
            if (self.canceled or len(self.remainingProviders) < 1 and runtime > 7 or
                (control.settingids.terminateoncloud and len(self.cloud_files) > 0) or 
                (control.settingids.terminateonlocal and len(self.local_files) > 0)):
                break

            runtime = time.perf_counter() - start_time
            self.progress = runtime / timeout * 100
        
        if len(self.torrentSources) + len(self.embedSources) + len(self.cloud_files) + len(self.local_files) == 0:
            self.return_data = []
        else:
            self.return_data = self.sortSources(self.torrentSources, self.embedSources, self.cloud_files, self.local_files, media_type, duration)
        self.close()
        return self.return_data

    def nyaa_worker(self, query, mal_id, episode, status, media_type, rescrape):
        all_sources = database.get(nyaa.Sources().get_sources, 8, query, mal_id, episode, status, media_type, rescrape, key='nyaa')
        self.torrentUnCacheSources += all_sources['uncached']
        self.torrentCacheSources += all_sources['cached']
        self.torrentSources += all_sources['cached'] + all_sources['uncached']
        self.remainingProviders.remove('nyaa')

    def animetosho_worker(self, query, mal_id, episode, status, media_type, rescrape):
        all_sources = database.get(animetosho.Sources().get_sources, 8, query, mal_id, episode, status, media_type, rescrape, key='animetosho')
        self.torrentUnCacheSources += all_sources['uncached']
        self.torrentCacheSources += all_sources['cached']
        self.torrentSources += all_sources['cached'] + all_sources['uncached']
        self.remainingProviders.remove('animetosho')

    ### embeds ###
    def hianime_worker(self, mal_id, episode, rescrape):
        hianime_sources = database.get(hianime.Sources().get_sources, 8, mal_id, episode, key='hianime')
        self.embedSources += hianime_sources
        for x in hianime_sources:
            if x and x['skip'].get('intro') and x['skip']['intro']['start'] != 0:
                control.setSetting('hianime.skipintro.start', str(x['skip']['intro']['start']))
                control.setSetting('hianime.skipintro.end', str(x['skip']['intro']['end']))
            if x and x['skip'].get('outro') and x['skip']['outro']['start'] != 0:
                control.setSetting('hianime.skipoutro.start', str(x['skip']['outro']['start']))
                control.setSetting('hianime.skipoutro.end', str(x['skip']['outro']['end']))
        self.remainingProviders.remove('hianime')

    def gogo_worker(self, mal_id, episode, rescrape, get_backup):
        self.embedSources += database.get(gogoanime.Sources().get_sources, 8, mal_id, episode, get_backup, key='gogoanime')
        self.remainingProviders.remove('gogo')

    def animix_worker(self, mal_id, episode, rescrape):
        self.embedSources += database.get(animixplay.Sources().get_sources, 8, mal_id, episode, key='animixplay')
        self.remainingProviders.remove('animix')

    def animepahe_worker(self, mal_id, episode, rescrape):
        self.embedSources += database.get(animepahe.Sources().get_sources, 8, mal_id, episode, key='animepahe')
        self.remainingProviders.remove('animepahe')

    def user_local_inspection(self, query, mal_id, episode, rescrape):
        self.local_files += localfiles.Sources().get_sources(query, mal_id, episode)
        self.remainingProviders.remove('Local Inspection')

    def user_cloud_inspection(self, query, mal_id, episode):
        debrid = {}
        if control.real_debrid_enabled() and control.getSetting('rd.cloudInspection') == 'true':
            debrid['real_debrid'] = True
        if control.premiumize_enabled() and control.getSetting('premiumize.cloudInspection') == 'true':
            debrid['premiumize'] = True
        if control.all_debrid_enabled() and control.getSetting('alldebrid.cloudInspection') == 'true':
            debrid['all_debrid'] = True
        self.cloud_files += debrid_cloudfiles.Sources().get_sources(debrid, query, episode)
        self.remainingProviders.remove('Cloud Inspection')

    @staticmethod
    def sortSources(torrent_list, embed_list, cloud_files, local_files, media_type, duration):
        all_list = torrent_list + embed_list + cloud_files + local_files
        sortedList = [x for x in all_list if control.getInt('general.minResolution') <= x['quality'] <= control.getInt('general.maxResolution')]
    
        # Filter by size
        filter_option = control.getSetting('general.fileFilter')
    
        if filter_option == '1':
            # web speed limit
            webspeed = int(control.getSetting('general.webspeed'))
            len_in_sec = int(duration) * 60
    
            _torrent_list = torrent_list
            torrent_list = [i for i in _torrent_list if i['size'] != 'NA' and ((float(i['size'][:-3]) * 8000) / len_in_sec) <= webspeed]
    
        elif filter_option == '2':
            # hard limit
            _torrent_list = torrent_list
    
            if media_type == 'movie':
                max_GB = float(control.getSetting('general.movie.maxGB'))
                min_GB = float(control.getSetting('general.movie.minGB'))
            else:
                max_GB = float(control.getSetting('general.episode.maxGB'))
                min_GB = float(control.getSetting('general.episode.minGB'))
    
            torrent_list = []
            for i in _torrent_list:
                if i['size'] != 'NA':
                    size = float(i['size'][:-3])
                    unit = i['size'][-2:].strip()
    
                    if unit == 'MB':
                        size /= 1024  # convert MB to GB for comparison
    
                    if min_GB <= size <= max_GB:
                        torrent_list.append(i)

        # Filter by release title
        if control.getSetting('general.release_title_filter.enabled') == 'true':
            release_title_filter1 = control.getSetting('general.release_title_filter.value1')
            release_title_filter2 = control.getSetting('general.release_title_filter.value2')
            release_title_filter3 = control.getSetting('general.release_title_filter.value3')
            release_title_filter4 = control.getSetting('general.release_title_filter.value4')
            release_title_filter5 = control.getSetting('general.release_title_filter.value5')

            # Get the new settings
            exclude_filter1 = control.getSetting('general.release_title_filter.exclude1') == 'true'
            exclude_filter2 = control.getSetting('general.release_title_filter.exclude2') == 'true'
            exclude_filter3 = control.getSetting('general.release_title_filter.exclude3') == 'true'
            exclude_filter4 = control.getSetting('general.release_title_filter.exclude4') == 'true'
            exclude_filter5 = control.getSetting('general.release_title_filter.exclude5') == 'true'

            _torrent_list = torrent_list
            release_title_logic = control.getSetting('general.release_title_filter.logic')
            if release_title_logic == '0':
                # AND filter
                torrent_list = [
                    i for i in _torrent_list
                    if (not exclude_filter1 or release_title_filter1 not in i['release_title'])
                    and (not exclude_filter2 or release_title_filter2 not in i['release_title'])
                    and (not exclude_filter3 or release_title_filter3 not in i['release_title'])
                    and (not exclude_filter4 or release_title_filter4 not in i['release_title'])
                    and (not exclude_filter5 or release_title_filter5 not in i['release_title'])
                ]
            if release_title_logic == '1':
                # OR filter
                torrent_list = [
                    i for i in _torrent_list
                    if (release_title_filter1 != "" and (exclude_filter1 ^ (release_title_filter1 in i['release_title'])))
                    or (release_title_filter2 != "" and (exclude_filter2 ^ (release_title_filter2 in i['release_title'])))
                    or (release_title_filter3 != "" and (exclude_filter3 ^ (release_title_filter3 in i['release_title'])))
                    or (release_title_filter4 != "" and (exclude_filter4 ^ (release_title_filter4 in i['release_title'])))
                    or (release_title_filter5 != "" and (exclude_filter5 ^ (release_title_filter5 in i['release_title'])))
                ]
    
        # Update sortedList to include the filtered torrent_list
        sortedList = [x for x in sortedList if x in torrent_list or x in embed_list or x in cloud_files or x in local_files]

        # Filter out sources
        if control.getSetting('general.disable265') == 'true':
            sortedList = [i for i in sortedList if 'HEVC' not in i['info']]
        if control.getSetting('general.disablebatch') == 'true':
            sortedList = [i for i in sortedList if 'BATCH' not in i['info']]
        lang = int(control.getSetting("general.source"))
        if lang != 1:
            langs = [0, 1, 2]
            sortedList = [i for i in sortedList if i['lang'] != langs[lang]]

        # Sort Sources
        SORT_METHODS = sort_select.SORT_METHODS
        sort_options = sort_select.sort_options
        for x in range(len(SORT_METHODS), 0, -1):
            reverse = sort_options[f'sortmethod.{x}.reverse']
            method = SORT_METHODS[int(sort_options[f'sortmethod.{x}'])]
            sortedList = getattr(sort_select, f'sort_by_{method}')(sortedList, not reverse)
        return sortedList

    def updateProgress(self):
        self.torrents_qual_len = [
            len([i for i in self.torrentSources if i['quality'] == 4]),
            len([i for i in self.torrentSources if i['quality'] == 3]),
            len([i for i in self.torrentSources if i['quality'] == 2]),
            len([i for i in self.torrentSources if i['quality'] == 1]),
            len([i for i in self.torrentSources if i['quality'] == 0])
        ]

        self.embeds_qual_len = [
            len([i for i in self.embedSources if i['quality'] == 4]),
            len([i for i in self.embedSources if i['quality'] == 3]),
            len([i for i in self.embedSources if i['quality'] == 2]),
            len([i for i in self.embedSources if i['quality'] == 1]),
            len([i for i in self.embedSources if i['quality'] == 0])
        ]

