import xbmc
import xbmcgui
import pickle
import service

from resources.lib.ui import control, database
from resources.lib.indexers import aniskip, anime_skip
from resources.lib import WatchlistIntegration

playList = control.playList
player = xbmc.Player

# from resources.lib import OtakuBrowser


class WatchlistPlayer(player):
    def __init__(self):
        super(WatchlistPlayer, self).__init__()
        self.vtag = None
        self.resume_time = None
        self.episode = None
        self._build_playlist = None
        self.mal_id = None
        self._watchlist_update = None
        self.current_time = 0
        self.updated = False
        self.media_type = None
        self.update_percent = control.getInt('watchlist.update.percent')

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

    def handle_player(self, mal_id, watchlist_update, build_playlist, episode, resume_time):
        self.mal_id = mal_id
        self._watchlist_update = watchlist_update
        self._build_playlist = build_playlist
        self.episode = episode
        self.resume_time = resume_time

        # process skip times
        self.process_hianime()
        if not self.skipintro_aniskip or not self.skipoutro_aniskip:
            self.process_aniwave()
        if not self.skipintro_aniskip or not self.skipoutro_aniskip:
            self.process_aniskip()
        if not self.skipintro_aniskip or not self.skipoutro_aniskip:
            self.process_animeskip()

        self.keepAlive()

    # def onPlayBackStarted(self):
    #     pass

    def onPlayBackStarted(self):
        if self._build_playlist and playList.size() == 1:
            self._build_playlist(self.mal_id, self.episode)

        current_ = playList.getposition()
        try:
            self.media_type = playList[current_].getVideoInfoTag().getMediaType()
        except:
            self.media_type = ''

    def onPlayBackStopped(self):
        control.closeAllDialogs()
        playList.clear()

    def onPlayBackEnded(self):
        control.closeAllDialogs()

    def onPlayBackError(self):
        control.closeAllDialogs()
        playList.clear()
        control.exit_(1)

    def getWatchedPercent(self):
        current_position = self.getTime()
        media_length = self.getTotalTime()
        return float(current_position) / float(media_length) * 100 if int(media_length) != 0 else 0

    def onWatchedPercent(self):
        if not self._watchlist_update:
            return
        while self.isPlaying() and not self.updated:
            watched_percentage = self.getWatchedPercent()
            self.current_time = self.getTime()
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
        for inx in range(30):
            if self.isPlayingVideo() and self.getTotalTime() != 0:
                break
            xbmc.sleep(250)

        if not self.isPlayingVideo():
            return

        self.vtag = self.getVideoInfoTag()
        self.media_type = self.vtag.getMediaType()
        control.setSetting('addon.last_watched', self.mal_id)

        self.total_time = int(self.getTotalTime())
        control.closeAllDialogs()
        if self.resume_time:
            player().seekTime(self.resume_time)

        if control.getSetting('general.kodi_language') == 'false':
            # Subtitle Preferences
            subtitle_lang = self.getAvailableSubtitleStreams()
            subtitles = [
                "none", "eng", "jpn", "spa", "fre", "ger",
                "ita", "dut", "rus", "por", "kor", "chi",
                "ara", "hin", "tur", "pol", "swe", "nor",
                "dan", "fin"
            ]
            preferred_subtitle_setting = control.getInt('general.subtitles')

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

            # Audio Preferences
            audio_lang = self.getAvailableAudioStreams()
            audios = ['jpn', 'eng']
            preferred_audio_setting = control.getInt('general.audio')

            if 0 <= preferred_audio_setting < len(audios):
                preferred_audio = audios[preferred_audio_setting]

            try:
                audio_int = audio_lang.index(preferred_audio)
                self.setAudioStream(audio_int)
            except ValueError:
                audio_int = 0
                self.setAudioStream(audio_int)

            if len(audio_lang) == 1:
                if "jpn" not in audio_lang:
                    if control.getBool('general.dubsubtitles'):
                        if preferred_subtitle == "none":
                            self.showSubtitles(False)
                        else:
                            self.showSubtitles(True)
                    else:
                        self.showSubtitles(False)

                if "eng" not in audio_lang:
                    if preferred_subtitle == "none":
                        self.showSubtitles(False)
                    else:
                        self.showSubtitles(True)

            if len(audio_lang) > 1:
                if preferred_audio == "eng":
                    if control.getBool('general.dubsubtitles'):
                        if preferred_subtitle == "none":
                            self.showSubtitles(False)
                        else:
                            self.showSubtitles(True)
                    else:
                        self.showSubtitles(False)

                if preferred_audio == "jpn":
                    if preferred_subtitle == "none":
                        self.showSubtitles(False)
                    else:
                        self.showSubtitles(True)

        if self.media_type == 'movie':
            return self.onWatchedPercent()

        if control.getBool('smartplay.skipintrodialog'):
            if self.skipintro_start < 1:
                self.skipintro_start = 1
            while self.isPlaying():
                self.current_time = int(self.getTime())
                if self.current_time > self.skipintro_end:
                    break
                elif self.current_time > self.skipintro_start:
                    PlayerDialogs().show_skip_intro(self.skipintro_aniskip, self.skipintro_end)
                    break
                xbmc.sleep(1000)
        self.onWatchedPercent()
        # OtakuBrowser.get_sources(self.mal_id, str(self.episode), self.media_type, silent=True)
        endpoint = control.getInt('playingnext.time') if control.getBool('smartplay.playingnextdialog') else 0
        if endpoint != 0:
            while self.isPlaying():
                self.current_time = int(self.getTime())
                if (not self.skipoutro_aniskip and self.total_time - self.current_time <= endpoint) or self.current_time > self.skipoutro_start != 0:
                    PlayerDialogs().display_dialog(self.skipoutro_aniskip, self.skipoutro_end)
                    break
                xbmc.sleep(5000)


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
                '4': 'skip_outro_az.xml'
            }

            setting_value = control.getSetting('general.dialog')
            xml_file = dialog_mapping.get(setting_value)

            # Call PlayingNext with the retrieved XML file
            if xml_file:
                PlayingNext(*(xml_file, control.ADDON_PATH), actionArgs=args).doModal()
        else:
            dialog_mapping = {
                '0': 'playing_next_default.xml',
                '1': 'playing_next_ah2.xml',
                '2': 'playing_next_auramod.xml',
                '3': 'playing_next_af.xml',
                '4': 'playing_next_az.xml'
            }

            setting_value = control.getSetting('general.dialog')
            xml_file = dialog_mapping.get(setting_value)

            # Call PlayingNext with the retrieved XML file
            if xml_file:
                PlayingNext(*(xml_file, control.ADDON_PATH), actionArgs=args).doModal()


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
            '4': 'skip_intro_az.xml'
        }

        setting_value = control.getSetting('general.dialog')
        xml_file = dialog_mapping.get(setting_value)

        # Call SkipIntro with the retrieved XML file
        if xml_file:
            SkipIntro(*(xml_file, control.ADDON_PATH), actionArgs=args).doModal()


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
