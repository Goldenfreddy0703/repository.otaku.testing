import xbmc
import xbmcgui
import pickle
import service
import json
import threading
import time

from resources.lib.ui import control, database
from resources.lib.endpoints import aniskip, anime_skip, simkl
from resources.lib import WatchlistIntegration, indexers
from resources.lib.endpoints import anilist


playList = control.playList
player = xbmc.Player

# from resources.lib import OtakuBrowser


class WatchlistPlayer(player):
    def __init__(self):
        super(WatchlistPlayer, self).__init__()
        self.vtag = None
        self.episode = None
        self.mal_id = None
        self._watchlist_update = None
        self.current_time = 0
        self.updated = False
        self.media_type = None
        self.update_percent = control.getInt('watchlist.update.percent')
        self.path = ''
        self.context = False

        self.total_time = None
        self.delay_time = control.getInt('skipintro.delay')
        self.skipintro_aniskip_enable = control.getBool('skipintro.aniskip.enable')
        self.skipoutro_aniskip_enable = control.getBool('skipoutro.aniskip.enable')

        self.skipintro_aniskip = False
        self.skipoutro_aniskip = False
        self.skipintro_start = control.getInt('skipintro.delay')
        self.skipintro_end = self.skipintro_start + control.getInt('skipintro.duration') * 60
        self.skipoutro_start = 0
        self.skipoutro_end = 0
        self.skipintro_offset = control.getInt('skipintro.aniskip.offset')
        self.skipoutro_offset = control.getInt('skipoutro.aniskip.offset')

        # Add these for async processing
        self.skip_times_thread = None
        self.skip_times_processed = False


    def handle_player(self, mal_id, watchlist_update, episode, path, context):
        self.mal_id = mal_id
        self._watchlist_update = watchlist_update
        self.episode = episode
        self.path = path
        self.context = context

        # Start processing skip times immediately before playback starts
        self.skip_times_thread = threading.Thread(target=self.process_skip_times)
        self.skip_times_thread.daemon = True
        self.skip_times_thread.start()

        # Continue with playback initialization
        self.keepAlive()

    def onPlayBackStopped(self):
        control.closeAllDialogs()
        playList.clear()
        if self.context and self.path:
            if 10 < self.getWatchedPercent() < 90:
                query = {
                    'jsonrpc': '2.0',
                    'method': 'Files.SetFileDetails',
                    'params': {
                        'file': self.path,
                        'media': 'video',
                        'resume': {
                            'position': self.current_time,
                            'total': self.total_time
                        }
                    },
                    'id': 1
                }
                control.jsonrpc(query)

    def onPlayBackEnded(self):
        control.closeAllDialogs()


    def onPlayBackError(self):
        control.closeAllDialogs()
        playList.clear()


    def build_playlist(self):
        episodes = database.get_episode_list(self.mal_id)

        if not control.getBool('playlist.unaired'):
            airing_episode = simkl.Simkl().get_calendar_data(self.mal_id)
            if not airing_episode:
                airing_episode = anilist.Anilist().get_airing_calendar(self.mal_id)

            if airing_episode:
                if isinstance(airing_episode, int):
                    episodes = episodes[:airing_episode]

        video_data = indexers.process_episodes(episodes, '') if episodes else []
        playlist = control.bulk_dir_list(video_data, True)[self.episode:]
        for i in playlist:
            control.playList.add(url=i[0], listitem=i[1])


    def getWatchedPercent(self):
        return (self.current_time / self.total_time) * 100 if self.total_time != 0 else 0


    def onWatchedPercent(self):
        if not self._watchlist_update:
            return
        while self.isPlaying() and not self.updated:
            self.current_time = self.getTime()
            watched_percentage = self.getWatchedPercent()
            if watched_percentage > self.update_percent:
                self._watchlist_update(self.mal_id, self.episode)
                self.updated = True

                # Retrieve the status and total episode count from kodi_meta
                show = database.get_show(self.mal_id)
                if show:
                    kodi_meta = pickle.loads(show['kodi_meta'])
                    status = kodi_meta.get('status')
                    episodes = kodi_meta.get('episodes')
                    if self.episode == episodes:
                        if status in ['Finished Airing', 'FINISHED']:
                            WatchlistIntegration.set_watchlist_status(self.mal_id, 'completed')
                            WatchlistIntegration.set_watchlist_status(self.mal_id, 'COMPLETED')
                            xbmc.sleep(3000)
                            service.sync_watchlist(True)
                    else:
                        WatchlistIntegration.set_watchlist_status(self.mal_id, 'watching')
                        WatchlistIntegration.set_watchlist_status(self.mal_id, 'current')
                        WatchlistIntegration.set_watchlist_status(self.mal_id, 'CURRENT')
                break
            xbmc.sleep(5000)


    def keepAlive(self):
        # Don't try to get video info until we're sure playback has started
        playback_started = False
        for _ in range(30):  # Increase timeout for slower systems
            try:
                if self.isPlayingVideo():
                    self.vtag = self.getVideoInfoTag()
                    self.media_type = self.vtag.getMediaType()
                    self.total_time = int(self.getTotalTime())
                    if self.total_time > 0:
                        playback_started = True
                        break
            except RuntimeError:
                # Handle the "not playing" error gracefully
                pass
            xbmc.sleep(250)  # Wait longer between checks

        if not playback_started:
            control.log('Failed to start video playback', 'warning')
            return

        # Continue with the rest of the method after playback is confirmed
        unique_ids = database.get_mapping_ids(self.mal_id, 'mal_id')
        source_type = control.getSetting('source_type')

        # Trakt scrobbling support
        if control.getBool('trakt.enabled'):
            control.clearGlobalProp('script.trakt.ids')
            control.setGlobalProp('script.trakt.ids', json.dumps(unique_ids))

        # Set the last watched episode
        control.setSetting('addon.last_watched', self.mal_id)

        # Continue with audio/subtitle setup which is needed immediately
        self.setup_audio_and_subtitles(source_type)

        # Handle playlist building if needed
        if self.media_type == 'episode' and playList.size() == 1:
            self.build_playlist()

        # Handle different media types
        if self.media_type == 'movie':
            self.onWatchedPercent()
        else:
            # Start monitoring for watchlist updates in background
            watchlist_thread = threading.Thread(target=self.onWatchedPercent)
            watchlist_thread.daemon = True
            watchlist_thread.start()

            # Start montoring for skip intro/outro
            self.monitor_playback()

        control.closeAllDialogs()

    def process_skip_times(self):
        """Process all skip time sources in background thread"""
        if self.skipintro_aniskip_enable or self.skipoutro_aniskip_enable:
            # Process in order of efficiency (local settings first, then API calls)
            self.process_hianime()
            if not self.skipintro_aniskip or not self.skipoutro_aniskip:
                self.process_aniwave()
            if not self.skipintro_aniskip or not self.skipoutro_aniskip:
                self.process_aniskip()
            if not self.skipintro_aniskip or not self.skipoutro_aniskip:
                self.process_animeskip()

        self.skip_times_processed = True


    def setup_audio_and_subtitles(self, source_type):
        """Handle audio and subtitle setup"""
        # This contains your existing audio/subtitle setup code from keepAlive
        if not control.getBool('general.kodi_language') or source_type not in ['embed', 'direct']:
            query = {
                'jsonrpc': '2.0',
                "method": "Player.GetProperties",
                "params": {
                    "playerid": 1,
                    "properties": ["subtitles", "audiostreams"]
                },
                "id": 1
            }

            audios = ['jpn', 'eng']

            subtitles = [
                "none", "eng", "jpn", "spa", "fre", "ger",
                "ita", "dut", "rus", "por", "kor", "chi",
                "ara", "hin", "tur", "pol", "swe", "nor",
                "dan", "fin"
            ]

            keywords = {
                1: 'dialogue',
                2: ['signs', 'songs'],
                3: control.getSetting('subtitles.customkeyword')
            }

            response = control.jsonrpc(query)

            if 'result' in response:
                player_properties = response['result']
                audio_streams = player_properties.get('audiostreams', [])
                subtitle_streams = player_properties.get('subtitles', [])
            else:
                audio_streams = []
                subtitle_streams = []

            preferred_audio = int(control.getSetting('general.audio'))
            preferred_subtitle_setting = int(control.getSetting('general.subtitles'))
            preferred_subtitle_keyword = int(control.getSetting('subtitles.keywords'))

            preferred_audio_streams = audios[preferred_audio]
            preferred_subtitle_lang = subtitles[preferred_subtitle_setting]
            preferred_keyword = keywords[preferred_subtitle_keyword]

            # Set preferred audio stream
            for stream in audio_streams:
                if stream['language'] == preferred_audio_streams:
                    self.setAudioStream(stream['index'])
                    break
            else:
                # If no preferred audio stream is found, set to the default audio stream
                for stream in audio_streams:
                    if stream.get('isdefault', False):
                        self.setAudioStream(stream['index'])
                        break
                else:
                    # If no default audio stream is found, set to the first available audio stream
                    self.setAudioStream(audio_streams[0]['index'])

            # Set preferred subtitle stream
            subtitle_int = None
            if control.getSetting('general.subtitles.keyword') == 'true':
                for index, sub in enumerate(subtitle_streams):
                    if sub['language'] == preferred_subtitle_lang:
                        sub_name_lower = sub['name'].lower()
                        if isinstance(preferred_keyword, list):
                            if any(kw in sub_name_lower for kw in preferred_keyword):
                                subtitle_int = index
                                break
                        elif preferred_keyword and preferred_keyword in sub_name_lower:
                            subtitle_int = index
                            break
            else:
                for index, sub in enumerate(subtitle_streams):
                    if sub['language'] == preferred_subtitle_lang:
                        subtitle_int = index
                        break

            if subtitle_int is None:
                # If no preferred subtitle stream is found, set to the default subtitle stream
                for index, sub in enumerate(subtitle_streams):
                    if sub.get('isdefault', False):
                        subtitle_int = index
                        break
                else:
                    # If no default subtitle stream is found, set to the first available subtitle stream with the preferred language
                    for index, sub in enumerate(subtitle_streams):
                        if sub['language'] == preferred_subtitle_lang:
                            subtitle_int = index
                            break
                    else:
                        # If no subtitle stream with the preferred language is found, set to the first available subtitle stream
                        subtitle_int = 0

            if subtitle_int is not None:
                self.setSubtitleStream(subtitle_int)

            # Enable and Disable Subtitles based on audio streams
            if len(audio_streams) == 1:
                if "jpn" not in audio_streams:
                    if control.getBool('general.dubsubtitles'):
                        if preferred_subtitle_lang == "none":
                            self.showSubtitles(False)
                        else:
                            self.showSubtitles(True)
                    else:
                        self.showSubtitles(False)

                if "eng" not in audio_streams:
                    if preferred_subtitle_lang == "none":
                        self.showSubtitles(False)
                    else:
                        self.showSubtitles(True)

            if len(audio_streams) > 1:
                if preferred_audio_streams == "eng":
                    if control.getBool('general.dubsubtitles'):
                        if preferred_subtitle_lang == "none":
                            self.showSubtitles(False)
                        else:
                            self.showSubtitles(True)
                    else:
                        self.showSubtitles(False)

                if preferred_audio_streams == "jpn":
                    if preferred_subtitle_lang == "none":
                        self.showSubtitles(False)
                    else:
                        self.showSubtitles(True)

        elif source_type in ['embed', 'direct']:
            subtitle_lang = self.getAvailableSubtitleStreams()
            subtitles = [
                "none", "eng", "jpn", "spa", "fre", "ger",
                "ita", "dut", "rus", "por", "kor", "chi",
                "ara", "hin", "tur", "pol", "swe", "nor",
                "dan", "fin"
            ]
            preferred_subtitle_setting = int(control.getSetting('general.subtitles'))

            if 0 <= preferred_subtitle_setting < len(subtitles):
                preferred_subtitle = subtitles[preferred_subtitle_setting]
            else:
                preferred_subtitle = "eng"

            try:
                subtitle_int = subtitle_lang.index(preferred_subtitle)
                self.setSubtitleStream(subtitle_int)
            except ValueError:
                subtitle_int = 0
                self.setSubtitleStream(subtitle_int)

            if preferred_subtitle == "none":
                self.showSubtitles(False)
            else:
                self.showSubtitles(True)


    def monitor_playback(self):
        """Monitor playback for skip intro/outro points with improved performance"""
        try:
            intro_shown = False
            outro_shown = False
            endpoint = control.getInt('playingnext.time') if control.getBool('smartplay.playingnextdialog') else 0

            # Use a shorter maximum wait time for skip times processing
            max_wait_time = 5  # seconds
            start_time = time.time()  # Use Python's time module instead of Kodi infoLabel

            # More efficient wait with better timeout handling
            while not self.skip_times_processed and self.isPlaying():
                # Check if we've waited long enough
                if time.time() - start_time > max_wait_time:
                    control.log('Skip times processing timeout reached', 'info')
                    break

                # Use a shorter sleep to be more responsive
                xbmc.sleep(100)

            # Avoid busy-waiting loop by using a state machine approach
            check_delay = 1000  # milliseconds between checks
            last_check = time.time()

            while self.isPlaying():
                # Only perform checks on intervals to reduce CPU load
                current_time = time.time()
                if (current_time - last_check) * 1000 < check_delay:
                    xbmc.sleep(50)  # Small sleep to prevent CPU hogging
                    continue

                last_check = current_time

                try:
                    # Get current playback position
                    self.current_time = int(self.getTime())

                    # Adjust check frequency based on proximity to skip points
                    if not intro_shown and self.skipintro_aniskip:
                        time_to_intro = self.skipintro_start - self.current_time
                        if 0 < time_to_intro < 5:  # Within 5 seconds of intro
                            check_delay = 200  # Check more frequently near intro time
                        else:
                            check_delay = 1000  # Normal check interval

                    # Skip intro logic with error handling
                    if not intro_shown and control.getBool('smartplay.skipintrodialog'):
                        # Ensure we have valid intro points
                        if self.skipintro_start < 1:
                            self.skipintro_start = 1

                        # Check if we're in the intro range
                        if self.skipintro_start <= self.current_time <= self.skipintro_end:
                            try:
                                PlayerDialogs().show_skip_intro(self.skipintro_aniskip, self.skipintro_end)
                            except Exception as e:
                                control.log(f"Error showing skip intro dialog: {str(e)}", "error")
                            intro_shown = True
                        elif self.current_time > self.skipintro_end:
                            intro_shown = True

                    # Skip outro/Playing next logic with error handling
                    if not outro_shown and endpoint != 0:
                        outro_condition = False

                        # Check if we're in outro range
                        if not self.skipoutro_aniskip:
                            outro_condition = (self.total_time - self.current_time <= endpoint)
                        else:
                            outro_condition = (self.skipoutro_start != 0 and self.current_time >= self.skipoutro_start)

                        if outro_condition:
                            try:
                                PlayerDialogs().display_dialog(self.skipoutro_aniskip, self.skipoutro_end)
                            except Exception as e:
                                control.log(f"Error showing outro dialog: {str(e)}", "error")
                            outro_shown = True

                    # Exit conditions to prevent unnecessary looping
                    if intro_shown and (outro_shown or endpoint == 0):
                        break

                except Exception as e:
                    # Log errors but continue monitoring
                    control.log(f"Error in monitor_playback loop: {str(e)}", "error")
                    check_delay = 1000  # Reset to normal interval after error

        except Exception as e:
            # Catch-all error handler to prevent complete freezes
            control.log(f"Critical error in monitor_playback: {str(e)}", "error")


    def process_aniskip(self):
        if self.skipintro_aniskip_enable:
            skipintro_aniskip_res = aniskip.get_skip_times(self.mal_id, self.episode, 'op')
            if skipintro_aniskip_res:
                skip_times = skipintro_aniskip_res['results'][0]['interval']
                self.skipintro_start = int(skip_times['startTime']) + self.skipintro_offset
                self.skipintro_end = int(skip_times['endTime']) + self.skipintro_offset
                self.skipintro_aniskip = True

        if self.skipoutro_aniskip_enable:
            skipoutro_aniskip_res = aniskip.get_skip_times(self.mal_id, self.episode, 'ed')
            if skipoutro_aniskip_res:
                skip_times = skipoutro_aniskip_res['results'][0]['interval']
                self.skipoutro_start = int(skip_times['startTime']) + self.skipoutro_offset
                self.skipoutro_end = int(skip_times['endTime']) + self.skipoutro_offset
                self.skipoutro_aniskip = True


    def process_animeskip(self):
        show_meta = database.get_show_meta(self.mal_id)
        anilist_id = pickle.loads(show_meta['meta_ids'])['anilist_id']

        if self.skipintro_aniskip_enable or self.skipoutro_aniskip_enable:
            skip_times = anime_skip.get_time_stamps(anime_skip.get_episode_ids(str(anilist_id), int(self.episode)))
            intro_start = None
            intro_end = None
            outro_start = None
            outro_end = None
            if skip_times:
                for skip in skip_times:
                    if self.skipintro_aniskip_enable:
                        if intro_start is None and skip['type']['name'] in ['Intro', 'New Intro', 'Branding']:
                            intro_start = int(skip['at'])
                        elif intro_end is None and intro_start is not None and skip['type']['name'] in ['Canon']:
                            intro_end = int(skip['at'])
                    if self.skipoutro_aniskip_enable:
                        if outro_start is None and skip['type']['name'] in ['Credits', 'New Credits']:
                            outro_start = int(skip['at'])
                        elif outro_end is None and outro_start is not None and skip['type']['name'] in ['Canon', 'Preview']:
                            outro_end = int(skip['at'])

            if intro_start is not None and intro_end is not None:
                self.skipintro_start = intro_start + self.skipintro_offset
                self.skipintro_end = intro_end + self.skipintro_offset
                self.skipintro_aniskip = True
            if outro_start is not None and outro_end is not None:
                self.skipoutro_start = int(outro_start) + self.skipoutro_offset
                self.skipoutro_end = int(outro_end) + self.skipoutro_offset
                self.skipoutro_aniskip = True


    def process_aniwave(self):
        if self.skipintro_aniskip_enable:
            aniwave_skipintro_start = control.getInt('aniwave.skipintro.start')
            if aniwave_skipintro_start != -1:
                self.skipintro_start = aniwave_skipintro_start + self.skipintro_offset
                self.skipintro_end = control.getInt('aniwave.skipintro.end') + self.skipintro_offset
                self.skipintro_aniskip = True
        if self.skipoutro_aniskip_enable:
            aniwave_skipoutro_start = control.getInt('aniwave.skipoutro.start')
            if aniwave_skipoutro_start != -1:
                self.skipoutro_start = aniwave_skipoutro_start + self.skipoutro_offset
                self.skipoutro_end = control.getInt('aniwave.skipoutro.end') + self.skipoutro_offset
                self.skipoutro_aniskip = True


    def process_hianime(self):
        if self.skipintro_aniskip_enable:
            hianime_skipintro_start = control.getInt('hianime.skipintro.start')
            if hianime_skipintro_start != -1:
                self.skipintro_start = hianime_skipintro_start + self.skipintro_offset
                self.skipintro_end = control.getInt('hianime.skipintro.end') + self.skipintro_offset
                self.skipintro_aniskip = True
        if self.skipoutro_aniskip_enable:
            hianime_skipoutro_start = control.getInt('hianime.skipoutro.start')
            if hianime_skipoutro_start != -1:
                self.skipoutro_start = hianime_skipoutro_start + self.skipoutro_offset
                self.skipoutro_end = control.getInt('hianime.skipoutro.end') + self.skipoutro_offset
                self.skipoutro_aniskip = True


class PlayerDialogs(xbmc.Player):
    def __init__(self):
        super(PlayerDialogs, self).__init__()
        self.playing_file = self.getPlayingFile()

    def display_dialog(self, skipoutro_aniskip, skipoutro_end):
        if playList.size() == 0 or playList.getposition() == (playList.size() - 1):
            return
        if self.playing_file != self.getPlayingFile() or not self.isPlayingVideo() or not self._is_video_window_open():
            return
        self._show_playing_next(skipoutro_aniskip, skipoutro_end)

    def _show_playing_next(self, skipoutro_aniskip, skipoutro_end):
        from resources.lib.windows.playing_next import PlayingNext
        args = self._get_next_item_args()
        args['skipoutro_end'] = skipoutro_end
        if skipoutro_aniskip:
            dialog_mapping = {
                '0': 'skip_outro_default.xml',
                '1': 'skip_outro_ah2.xml',
                '2': 'skip_outro_auramod.xml',
                '3': 'skip_outro_af.xml',
                '4': 'skip_outro_af2.xml',
                '5': 'skip_outro_az.xml'
            }

            setting_value = control.getSetting('general.dialog')
            xml_file = dialog_mapping.get(setting_value)

            # Call PlayingNext with the retrieved XML file
            if xml_file:
                PlayingNext(xml_file, control.ADDON_PATH, actionArgs=args).doModal()
        else:
            dialog_mapping = {
                '0': 'playing_next_default.xml',
                '1': 'playing_next_ah2.xml',
                '2': 'playing_next_auramod.xml',
                '3': 'playing_next_af.xml',
                '4': 'playing_next_af2.xml',
                '5': 'playing_next_az.xml'
            }

            setting_value = control.getSetting('general.dialog')
            xml_file = dialog_mapping.get(setting_value)

            # Call PlayingNext with the retrieved XML file
            if xml_file:
                PlayingNext(xml_file, control.ADDON_PATH, actionArgs=args).doModal()

    @staticmethod
    def show_skip_intro(skipintro_aniskip, skipintro_end):
        from resources.lib.windows.skip_intro import SkipIntro
        args = {
            'item_type': 'skip_intro',
            'skipintro_aniskip': skipintro_aniskip,
            'skipintro_end': skipintro_end
        }

        dialog_mapping = {
            '0': 'skip_intro_default.xml',
            '1': 'skip_intro_ah2.xml',
            '2': 'skip_intro_auramod.xml',
            '3': 'skip_intro_af.xml',
            '4': 'skip_intro_af2.xml',
            '5': 'skip_intro_az.xml'
        }

        setting_value = control.getSetting('general.dialog')
        xml_file = dialog_mapping.get(setting_value)

        # Call SkipIntro with the retrieved XML file
        if xml_file:
            SkipIntro(xml_file, control.ADDON_PATH, actionArgs=args).doModal()

    @staticmethod
    def _get_next_item_args():
        current_position = playList.getposition()
        _next_info = playList[current_position + 1]
        next_info = {
            'item_type': "playing_next",
            'thumb': [_next_info.getArt('thumb')],
            'name': _next_info.getLabel()
        }
        return next_info

    @staticmethod
    def _is_video_window_open():
        return False if xbmcgui.getCurrentWindowId() != 12005 else True
