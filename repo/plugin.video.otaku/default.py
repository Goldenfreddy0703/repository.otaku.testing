# -*- coding: utf-8 -*-
"""
    Otaku Add-on

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# import time
# t0 = time.perf_counter_ns()

import pickle

from resources.lib import OtakuBrowser
from resources.lib.ui import control, database, utils
from resources.lib.ui.router import Route, router_process
from resources.lib.WatchlistIntegration import add_watchlist
from resources.lib.OtakuBrowser import BROWSER


def add_last_watched(items):
    mal_id = control.getSetting("addon.last_watched")
    try:
        kodi_meta = pickle.loads(database.get_show(mal_id)['kodi_meta'])
        last_watched = "%s[I]%s[/I]" % (control.lang(30900), kodi_meta.get('title_userPreferred'))
        items.insert(0, (last_watched, f'animes/{mal_id}/', kodi_meta['poster']))
    except TypeError:
        pass
    return items


@Route('animes/*')
def ANIMES_PAGE(payload, params):
    mal_id, eps_watched = payload.rsplit("/")
    anime_general, content = OtakuBrowser.get_anime_init(mal_id)
    control.draw_items(anime_general, content)


@Route('find_recommendations/*')
def FIND_RECOMMENDATIONS(payload, params):
    path, mal_id, eps_watched = payload.rsplit("/")
    page = params.get('page', 1)
    control.draw_items(BROWSER.get_recommendations(mal_id, int(page)), 'tvshows')


@Route('find_relations/*')
def FIND_RELATIONS(payload, params):
    path, mal_id, eps_watched = payload.rsplit("/")
    control.draw_items(BROWSER.get_relations(mal_id), 'tvshows')


# @Route('watch_order/*')
# def WATCH_ORDER(payload, params):
#     path, mal_id, eps_watched = payload.rsplit("/")
#     control.draw_items(BROWSER.get_watch_order(mal_id), 'tvshows')


@Route('airing_last_season/*')
def AIRING_LAST_SEASON(payload, params):
    control.draw_items(BROWSER.get_airing_last_season(int(payload)), 'tvshows')


@Route('airing_this_season/*')
def AIRING_THIS_SEASON(payload, params):
    control.draw_items(BROWSER.get_airing_this_season(int(payload)), 'tvshows')


@Route('airing_next_season/*')
def AIRING_NEXT_SEASON(payload, params):
    control.draw_items(BROWSER.get_airing_next_season(int(payload)), 'tvshows')


@Route('trending_last_year/*')
def TRENDING_LAST_YEAR(payload, params):
    control.draw_items(BROWSER.get_trending_last_year(int(payload)), 'tvshows')


@Route('trending_this_year/*')
def TRENDING_THIS_YEAR(payload, params):
    control.draw_items(BROWSER.get_trending_this_year(int(payload)), 'tvshows')


@Route('trending_last_season/*')
def TRENDING_LAST_SEASON(payload, params):
    control.draw_items(BROWSER.get_trending_last_season(int(payload)), 'tvshows')


@Route('trending_this_season/*')
def TRENDING_THIS_SEASON(payload, params):
    control.draw_items(BROWSER.get_trending_this_season(int(payload)), 'tvshows')


@Route('all_time_trending/*')
def ALL_TIME_TRENDING(payload, params):
    control.draw_items(BROWSER.get_all_time_trending(int(payload)), 'tvshows')


@Route('popular_last_year/*')
def POPULAR_LAST_YEAR(payload, params):
    control.draw_items(BROWSER.get_popular_last_year(int(payload)), 'tvshows')


@Route('popular_this_year/*')
def POPULAR_THIS_YEAR(payload, params):
    control.draw_items(BROWSER.get_popular_this_year(int(payload)), 'tvshows')


@Route('popular_last_season/*')
def POPULAR_LAST_SEASON(payload, params):
    control.draw_items(BROWSER.get_popular_last_season(int(payload)), 'tvshows')


@Route('popular_this_season/*')
def POPULAR_THIS_SEASON(payload, params):
    control.draw_items(BROWSER.get_popular_this_season(int(payload)), 'tvshows')


@Route('all_time_popular/*')
def ALL_TIME_POPULAR(payload, params):
    control.draw_items(BROWSER.get_all_time_popular(int(payload)), 'tvshows')


@Route('voted_last_year/*')
def VOTED_LAST_YEAR(payload, params):
    control.draw_items(BROWSER.get_voted_last_year(int(payload)), 'tvshows')


@Route('voted_this_year/*')
def VOTED_THIS_YEAR(payload, params):
    control.draw_items(BROWSER.get_voted_this_year(int(payload)), 'tvshows')


@Route('voted_last_season/*')
def VOTED_LAST_SEASON(payload, params):
    control.draw_items(BROWSER.get_voted_last_season(int(payload)), 'tvshows')


@Route('voted_this_season/*')
def VOTED_THIS_SEASON(payload, params):
    control.draw_items(BROWSER.get_voted_this_season(int(payload)), 'tvshows')


@Route('all_time_voted/*')
def ALL_TIME_VOTED(payload, params):
    control.draw_items(BROWSER.get_all_time_voted(int(payload)), 'tvshows')


@Route('favourites_last_year/*')
def FAVOURITES_LAST_YEAR(payload, params):
    control.draw_items(BROWSER.get_favourites_last_year(int(payload)), 'tvshows')


@Route('favourites_this_year/*')
def FAVOURITES_THIS_YEAR(payload, params):
    control.draw_items(BROWSER.get_favourites_this_year(int(payload)), 'tvshows')


@Route('favourites_last_season/*')
def FAVOURITES_LAST_SEASON(payload, params):
    control.draw_items(BROWSER.get_favourites_last_season(int(payload)), 'tvshows')


@Route('favourites_this_season/*')
def FAVOURITES_THIS_SEASON(payload, params):
    control.draw_items(BROWSER.get_favourites_this_season(int(payload)), 'tvshows')


@Route('all_time_favourites/*')
def ALL_TIME_FAVOURITES(payload, params):
    control.draw_items(BROWSER.get_all_time_favourites(int(payload)), 'tvshows')


@Route('top_100/*')
def TOP_100(payload, params):
    control.draw_items(BROWSER.get_top_100(int(payload)), 'tvshows')


@Route('genres/*')
def ANILIST_GENRES_PAGES(payload, params):
    genres, tags, page = payload.rsplit("/")
    if genres or tags:
        control.draw_items(BROWSER.genres_payload(genres, tags, int(page)), 'tvshows')
    else:
        control.draw_items(BROWSER.get_genres(), 'tvshows')


@Route('genre_action/*')
def GENRE_ACTION(payload, params):
    control.draw_items(BROWSER.get_genre_action(int(payload)), 'tvshows')


@Route('genre_adventure/*')
def GENRE_ADVENTURE(payload, params):
    control.draw_items(BROWSER.get_genre_adventure(int(payload)), 'tvshows')


@Route('genre_comedy/*')
def GENRE_COMEDY(payload, params):
    control.draw_items(BROWSER.get_genre_comedy(int(payload)), 'tvshows')


@Route('genre_drama/*')
def GENRE_DRAMA(payload, params):
    control.draw_items(BROWSER.get_genre_drama(int(payload)), 'tvshows')


@Route('genre_ecchi/*')
def GENRE_ECCHI(payload, params):
    control.draw_items(BROWSER.get_genre_ecchi(int(payload)), 'tvshows')


@Route('genre_fantasy/*')
def GENRE_FANTASY(payload, params):
    control.draw_items(BROWSER.get_genre_fantasy(int(payload)), 'tvshows')


@Route('genre_hentai/*')
def GENRE_HENTAI(payload, params):
    control.draw_items(BROWSER.get_genre_hentai(int(payload)), 'tvshows')


@Route('genre_horror/*')
def GENRE_HORROR(payload, params):
    control.draw_items(BROWSER.get_genre_horror(int(payload)), 'tvshows')


@Route('genre_shoujo/*')
def GENRE_SHOUJO(payload, params):
    control.draw_items(BROWSER.get_genre_shoujo(int(payload)), 'tvshows')


@Route('genre_mecha/*')
def GENRE_MECHA(payload, params):
    control.draw_items(BROWSER.get_genre_mecha(int(payload)), 'tvshows')


@Route('genre_music/*')
def GENRE_MUSIC(payload, params):
    control.draw_items(BROWSER.get_genre_music(int(payload)), 'tvshows')


@Route('genre_mystery/*')
def GENRE_MYSTERY(payload, params):
    control.draw_items(BROWSER.get_genre_mystery(int(payload)), 'tvshows')


@Route('genre_psychological/*')
def GENRE_PSYCHOLOGICAL(payload, params):
    control.draw_items(BROWSER.get_genre_psychological(int(payload)), 'tvshows')


@Route('genre_romance/*')
def GENRE_ROMANCE(payload, params):
    control.draw_items(BROWSER.get_genre_romance(int(payload)), 'tvshows')


@Route('genre_sci_fi/*')
def GENRE_SCI_FI(payload, params):
    control.draw_items(BROWSER.get_genre_sci_fi(int(payload)), 'tvshows')


@Route('genre_slice_of_life/*')
def GENRE_SLICE_OF_LIFE(payload, params):
    control.draw_items(BROWSER.get_genre_slice_of_life(int(payload)), 'tvshows')


@Route('genre_sports/*')
def GENRE_SPORTS(payload, params):
    control.draw_items(BROWSER.get_genre_sports(int(payload)), 'tvshows')


@Route('genre_supernatural/*')
def GENRE_SUPERNATURAL(payload, params):
    control.draw_items(BROWSER.get_genre_supernatural(int(payload)), 'tvshows')


@Route('genre_thriller/*')
def GENRE_THRILLER(payload, params):
    control.draw_items(BROWSER.get_genre_thriller(int(payload)), 'tvshows')


@Route('search_history')
def SEARCH_HISTORY(payload, params):
    history = database.getSearchHistory('show')
    if int(control.getSetting('searchhistory')) == 0:
        draw_cm = [('Remove from Item', 'remove_search_item'), ("Edit Search Item...", "edit_search_item")]
        control.draw_items(OtakuBrowser.search_history(history), 'addons', draw_cm)
    else:
        SEARCH(payload, params)


@Route('search/*')
def SEARCH(payload, params):
    query, page = payload.rsplit("/", 1)
    if not query:
        query = control.keyboard(control.lang(30905))
        if not query:
            return control.draw_items([], 'tvshows')
        if int(control.getSetting('searchhistory')) == 0:
            database.addSearchHistory(query, 'show')
        control.draw_items(BROWSER.get_search(query), 'tvshows')
    else:
        control.draw_items(BROWSER.get_search(query, int(page)), 'tvshows')


@Route('remove_search_item/*')
def REMOVE_SEARCH_ITEM(payload, params):
    if 'search/' in payload:
        payload_list = payload.rsplit('search/')[1].rsplit('/', 1)
        if len(payload_list) == 2 and payload_list[0]:
            search_item, page = payload_list
            return database.remove_search(table='show', value=search_item)
    control.notify(control.ADDON_NAME, "Invalid Search Item")


@Route('edit_search_item/*')
def EDIT_SEARCH_ITEM(payload, params):
    if 'search/' in payload:
        payload_list = payload.rsplit('search/')[1].rsplit('/', 1)
        if len(payload_list) == 2 and payload_list[0]:
            search_item, page = payload_list
            query = control.keyboard(control.lang(30905), search_item)
            if query and query != search_item:
                database.remove_search(table='show', value=search_item)
                database.addSearchHistory(query, 'show')
            return
    control.notify(control.ADDON_NAME, "Invalid Search Item")


@Route('play/*')
def PLAY(payload, params):
    mal_id, episode = payload.rsplit("/")
    source_select = bool(params.get('source_select'))
    rescrape = bool(params.get('rescrape'))
    resume_time = params.get('resume')
    if resume_time:
        resume_time = float(resume_time)
        context = control.context_menu([f'Resume from {utils.format_time(resume_time)}', 'Play from beginning'])
        if context == -1:
            return control.exit_code()
        elif context == 1:
            resume_time = None

    sources = OtakuBrowser.get_sources(mal_id, episode, 'show', rescrape, source_select)
    _mock_args = {"mal_id": mal_id, "episode": episode, 'play': True, 'resume_time': resume_time, 'context': rescrape or source_select}
    if control.getSetting('general.playstyle.episode') == '1' or source_select or rescrape:
        from resources.lib.windows.source_select import SourceSelect
        if control.getSetting('general.dialog') == '4':
            SourceSelect(*('source_select_az.xml', control.ADDON_PATH), actionArgs=_mock_args, sources=sources, rescrape=rescrape).doModal()
        else:
            SourceSelect(*('source_select.xml', control.ADDON_PATH), actionArgs=_mock_args, sources=sources, rescrape=rescrape).doModal()
    else:
        from resources.lib.windows.resolver import Resolver
        if control.getSetting('general.dialog') == '4':
            Resolver(*('resolver_az.xml', control.ADDON_PATH), actionArgs=_mock_args).doModal(sources, {}, False)
        else:
            Resolver(*('resolver.xml', control.ADDON_PATH), actionArgs=_mock_args).doModal(sources, {}, False)
    control.exit_code()


@Route('play_movie/*')
def PLAY_MOVIE(payload, params):
    mal_id, eps_watched = payload.rsplit("/")
    source_select = bool(params.get('source_select'))
    rescrape = bool(params.get('rescrape'))
    resume_time = params.get('resume')
    if resume_time:
        resume_time = float(resume_time)
        context = control.context_menu([f'Resume from {utils.format_time(resume_time)}', 'Play from beginning'])
        if context == -1:
            return
        elif context == 1:
            resume_time = None

    sources = OtakuBrowser.get_sources(mal_id, 1, 'movie', rescrape, source_select)
    _mock_args = {'mal_id': mal_id, 'play': True, 'resume_time': resume_time, 'context': rescrape or source_select}
    control.playList.clear()
    if control.getSetting('general.playstyle.movie') == '1' or source_select or rescrape:
        from resources.lib.windows.source_select import SourceSelect
        if control.getSetting('general.dialog') == '4':
            SourceSelect(*('source_select_az.xml', control.ADDON_PATH), actionArgs=_mock_args, sources=sources, rescrape=rescrape).doModal()
        else:
            SourceSelect(*('source_select.xml', control.ADDON_PATH), actionArgs=_mock_args, sources=sources, rescrape=rescrape).doModal()    
    else:
        from resources.lib.windows.resolver import Resolver
        if control.getSetting('general.dialog') == '4':
            Resolver(*('resolver_az.xml', control.ADDON_PATH), actionArgs=_mock_args).doModal(sources, {}, False)
        else:
            Resolver(*('resolver.xml', control.ADDON_PATH), actionArgs=_mock_args).doModal(sources, {}, False)
    control.exit_code()


@Route('marked_as_watched/*')
def MARKED_AS_WATCHED(payload, params):
    from resources.lib.WatchlistFlavor import WatchlistFlavor
    from resources.lib.WatchlistIntegration import watchlist_update_episode

    mal_id, episode = payload.rsplit("/")
    flavor = WatchlistFlavor.get_update_flavor()
    watchlist_update_episode(mal_id, episode)
    control.notify(control.ADDON_NAME, f'Episode #{episode} was Marked as Watched in {flavor.flavor_name}')
    control.execute(f'ActivateWindow(Videos,plugin://{control.ADDON_ID}/watchlist_to_ep/{mal_id}/{episode})')
    control.exit_code()


@Route('delete_anime_database/*')
def DELETE_ANIME_DATABASE(payload, params):
    path, mal_id, eps_watched = payload.rsplit("/")
    database.remove_from_database('shows', mal_id)
    database.remove_from_database('episodes', mal_id)
    database.remove_from_database('show_data', mal_id)
    database.remove_from_database('shows_meta', mal_id)
    control.notify(control.ADDON_NAME, 'Removed from database')
    control.exit_code()


@Route('auth/*')
def AUTH(payload, params):
    if payload == 'realdebrid':
        from resources.lib.debrid.real_debrid import RealDebrid
        RealDebrid().auth()
    elif payload == 'alldebrid':
        from resources.lib.debrid.all_debrid import AllDebrid
        AllDebrid().auth()
    elif payload == 'premiumize':
        from resources.lib.debrid.premiumize import Premiumize
        Premiumize().auth()
    elif payload == 'debridlink':
        from resources.lib.debrid.debrid_link import DebridLink
        DebridLink().auth()


@Route('refresh/*')
def REFRESH(payload, params):
    if payload == 'realdebrid':
        from resources.lib.debrid.real_debrid import RealDebrid
        RealDebrid().refreshToken()
    elif payload == 'debridlink':
        from resources.lib.debrid.debrid_link import DebridLink
        DebridLink().refreshToken()


@Route('fanart_select/*')
def FANART_SELECT(payload, params):
    path, mal_id, eps_watched = payload.rsplit("/")
    if not (episode := database.get_episode(mal_id)):
        OtakuBrowser.get_anime_init(mal_id)
        episode = database.get_episode(mal_id)
    fanart = pickle.loads(episode['kodi_meta'])['image']['fanart'] or []
    fanart_display = fanart + ["None", "Random (Defualt)"]
    fanart += ["None", ""]
    control.draw_items([utils.allocate_item(f, f'fanart/{mal_id}/{i}', False, False, f, fanart=f, landscape=f) for i, f in enumerate(fanart_display)], '')


@Route('fanart/*')
def FANART(payload, params):
    mal_id, select = payload.rsplit('/', 2)
    episode = database.get_episode(mal_id)
    fanart = pickle.loads(episode['kodi_meta'])['image']['fanart'] or []
    fanart_display = fanart + ["None", "Random"]
    fanart += ["None", ""]
    fanart_all = control.getSetting(f'fanart.all').split(',')
    if '' in fanart_all:
        fanart_all.remove('')
    fanart_all += [str(mal_id)]
    control.setSetting(f'fanart.select.{mal_id}', fanart[int(select)])
    control.setSetting(f'fanart.all', ",".join(fanart_all))
    control.ok_dialog(control.ADDON_NAME, f"Fanart Set to {fanart_display[int(select)]}")


# ### Menu Items ###
@Route('')
def LIST_MENU(payload, params):
    MENU_ITEMS = [
        (control.lang(30901), "airing_last_season/1", 'airing_anime.png'),
        (control.lang(30902), "airing_this_season/1", 'airing_anime.png'),
        (control.lang(30903), "airing_next_season/1", 'airing_anime.png'),
        # (control.lang(30904), "movies", 'movies.png'),
        # (control.lang(30905), "tv_shows", 'tv_shows.png'),
        (control.lang(30906), "trending", 'trending.png'),
        (control.lang(30907), "popular", 'popular.png'),
        (control.lang(30908), "voted", 'voted.png'),
        (control.lang(30909), "favourites", 'favourites.png'),
        (control.lang(30910), "top_100/1", 'top_100_anime.png'),
        (control.lang(30911), "genres", 'genres_&_tags.png'),
        (control.lang(30912), "search_history", 'search.png'),
        (control.lang(30913), "tools", 'tools.png')
    ]

    if control.getBool('menu.lastwatched'):
        MENU_ITEMS = add_last_watched(MENU_ITEMS)
    MENU_ITEMS = add_watchlist(MENU_ITEMS)
    MENU_ITEMS_ = MENU_ITEMS[:]
    for i in MENU_ITEMS:
        if control.getSetting(i[1]) == 'false':
            MENU_ITEMS_.remove(i)
    control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in MENU_ITEMS_], 'addons')


# @Route('movies')
# def MOVIES_MENU(payload, params):
#     MOVIES_ITEMS = [
#         (control.lang(30901), "airing_last_season/1", 'airing_anime.png'),
#         (control.lang(30902), "airing_this_season/1", 'airing_anime.png'),
#         (control.lang(30903), "airing_next_season/1", 'airing_anime.png'),
#         (control.lang(30906), "trending", 'trending.png'),
#         (control.lang(30907), "popular", 'popular.png'),
#         (control.lang(30908), "voted", 'voted.png'),
#         (control.lang(30909), "favourites", 'favourites.png'),
#         (control.lang(30910), "top_100/1", 'top_100_anime.png'),
#         (control.lang(30911), "genres", 'genres_&_tags.png'),
#         (control.lang(30912), "search_history_movie", 'search.png')
#     ]

#     if control.getBool('menu.lastwatched'):
#         MOVIES_ITEMS = add_last_watched(MOVIES_ITEMS)
#     MOVIES_ITEMS = add_watchlist(MOVIES_ITEMS)
#     # MOVIES_ITEMS = update_menu_paths(MOVIES_ITEMS, 'movies')
#     MOVIES_ITEMS_ = MOVIES_ITEMS[:]
#     for i in MOVIES_ITEMS:
#         if control.getSetting(i[1]) == 'false':
#             MOVIES_ITEMS_.remove(i)
#     control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in MOVIES_ITEMS_], 'addons')


# @Route('tv_shows')
# def TV_SHOWS_MENU(payload, params):
#     TV_SHOWS_ITEMS = [
#         (control.lang(30901), "airing_last_season/1", 'airing_anime.png'),
#         (control.lang(30902), "airing_this_season/1", 'airing_anime.png'),
#         (control.lang(30903), "airing_next_season/1", 'airing_anime.png'),
#         (control.lang(30906), "trending", 'trending.png'),
#         (control.lang(30907), "popular", 'popular.png'),
#         (control.lang(30908), "voted", 'voted.png'),
#         (control.lang(30909), "favourites", 'favourites.png'),
#         (control.lang(30910), "top_100/1", 'top_100_anime.png'),
#         (control.lang(30911), "genres", 'genres_&_tags.png'),
#         (control.lang(30912), "search_history_tvshow", 'search.png')
#     ]

#     if control.getBool('menu.lastwatched'):
#         TV_SHOWS_ITEMS = add_last_watched(TV_SHOWS_ITEMS)
#     TV_SHOWS_ITEMS = add_watchlist(TV_SHOWS_ITEMS)
#     # TV_SHOWS_ITEMS = update_menu_paths(TV_SHOWS_ITEMS, 'tv_shows')
#     TV_SHOWS_ITEMS_ = TV_SHOWS_ITEMS[:]
#     for i in TV_SHOWS_ITEMS:
#         if control.getSetting(i[1]) == 'false':
#             TV_SHOWS_ITEMS_.remove(i)
#     control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in TV_SHOWS_ITEMS_], 'addons')


@Route('trending')
def TRENDING_MENU(payload, params):
    TRENDING_ITEMS = [
        (control.lang(30914), "trending_last_year/1", 'trending.png'),
        (control.lang(30915), "trending_this_year/1", 'trending.png'),
        (control.lang(30916), "trending_last_season/1", 'trending.png'),
        (control.lang(30917), "trending_this_season/1", 'trending.png'),
        (control.lang(30918), "all_time_trending/1", 'trending.png')
    ]

    TRENDING_ITEMS_ = TRENDING_ITEMS[:]
    for i in TRENDING_ITEMS:
        if control.getSetting(i[1]) == 'false':
            TRENDING_ITEMS_.remove(i)
    control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in TRENDING_ITEMS_], 'addons')


@Route('popular')
def POPULAR_MENU(payload, params):
    POPULAR_ITEMS = [
        (control.lang(30919), "popular_last_year/1", 'popular.png'),
        (control.lang(30920), "popular_this_year/1", 'popular.png'),
        (control.lang(30921), "popular_last_season/1", 'popular.png'),
        (control.lang(30922), "popular_this_season/1", 'popular.png'),
        (control.lang(30923), "all_time_popular/1", 'popular.png')
    ]

    POPULAR_ITEMS_ = POPULAR_ITEMS[:]
    for i in POPULAR_ITEMS:
        if control.getSetting(i[1]) == 'false':
            POPULAR_ITEMS_.remove(i)
    control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in POPULAR_ITEMS_], 'addons')


@Route('voted')
def VOTED_MENU(payload, params):
    VOTED_ITEMS = [
        (control.lang(30924), "voted_last_year/1", 'voted.png'),
        (control.lang(30925), "voted_this_year/1", 'voted.png'),
        (control.lang(30926), "voted_last_season/1", 'voted.png'),
        (control.lang(30927), "voted_this_season/1", 'voted.png'),
        (control.lang(30928), "all_time_voted/1", 'voted.png')
    ]

    VOTED_ITEMS_ = VOTED_ITEMS[:]
    for i in VOTED_ITEMS:
        if control.getSetting(i[1]) == 'false':
            VOTED_ITEMS_.remove(i)
    control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in VOTED_ITEMS_], 'addons')


@Route('favourites')
def FAVOURITES_MENU(payload, params):
    FAVOURITES_ITEMS = [
        (control.lang(30929), "favourites_last_year/1", 'favourites.png'),
        (control.lang(30930), "favourites_this_year/1", 'favourites.png'),
        (control.lang(30931), "favourites_last_season/1", 'favourites.png'),
        (control.lang(30932), "favourites_this_season/1", 'favourites.png'),
        (control.lang(30933), "all_time_favourites/1", 'favourites.png')
    ]

    FAVOURITES_ITEMS_ = FAVOURITES_ITEMS[:]
    for i in FAVOURITES_ITEMS:
        if control.getSetting(i[1]) == 'false':
            FAVOURITES_ITEMS_.remove(i)
    control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in FAVOURITES_ITEMS_], 'addons')


@Route('genres')
def GENRES_MENU(payload, params):
    GENRES_ITEMS = [
        (control.lang(30934), "genres///1", 'genre_multi.png'),
        (control.lang(30935), "genre_action/1", 'genre_action.png'),
        (control.lang(30936), "genre_adventure/1", 'genre_adventure.png'),
        (control.lang(30937), "genre_comedy/1", 'genre_comedy.png'),
        (control.lang(30938), "genre_drama/1", 'genre_drama.png'),
        (control.lang(30939), "genre_ecchi/1", 'genre_ecchi.png'),
        (control.lang(30940), "genre_fantasy/1", 'genre_fantasy.png'),
        (control.lang(30941), "genre_hentai/1", 'genre_hentai.png'),
        (control.lang(30942), "genre_horror/1", 'genre_horror.png'),
        (control.lang(30943), "genre_shoujo/1", 'genre_shoujo.png'),
        (control.lang(30944), "genre_mecha/1", 'genre_mecha.png'),
        (control.lang(30945), "genre_music/1", 'genre_music.png'),
        (control.lang(30946), "genre_mystery/1", 'genre_mystery.png'),
        (control.lang(30947), "genre_psychological/1", 'genre_psychological.png'),
        (control.lang(30948), "genre_romance/1", 'genre_romance.png'),
        (control.lang(30949), "genre_sci_fi/1", 'genre_sci-fi.png'),
        (control.lang(30950), "genre_slice_of_life/1", 'genre_slice_of_life.png'),
        (control.lang(30951), "genre_sports/1", 'genre_sports.png'),
        (control.lang(30952), "genre_supernatural/1", 'genre_supernatural.png'),
        (control.lang(30953), "genre_thriller/1", 'genre_thriller.png')
    ]

    GENRES_ITEMS_ = GENRES_ITEMS[:]
    for i in GENRES_ITEMS:
        if control.getSetting(i[1]) == 'false':
            GENRES_ITEMS_.remove(i)
    control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in GENRES_ITEMS_], 'addons')


# @Route('search')
# def SEARCH_MENU(payload, params):
#     SEARCH_ITEMS = [
#         (control.lang(30954), "search_history", 'search.png'),
#         (control.lang(30955), "search_history_movie", 'search.png'),
#         (control.lang(30956), "search_history_tvshow", 'search.png')
#     ]

#     control.draw_items([utils.allocate_item(name, url, True, False, image) for name, url, image in SEARCH_ITEMS], 'addons')


@Route('tools')
def TOOLS_MENU(payload, params):
    TOOLS_ITEMS = [
        (control.lang(30010), "change_log", {'plot': "View Changelog"}, 'changelog.png'),
        (control.lang(30011), "settings", {'plot': "Open Settings"}, 'open_settings_menu.png'),
        (control.lang(30012), "clear_cache", {'plot': "Clear Cache"}, 'clear_cache.png'),
        (control.lang(30013), "clear_search_history", {'plot': "Clear Search History"}, 'clear_search_history.png'),
        (control.lang(30014), "rebuild_database", {'plot': "Rebuild Database"}, 'rebuild_database.png'),
        (control.lang(30015), "completed_sync", {'plot': "Sync Completed Anime with Otaku"}, "sync_completed.png"),
        (control.lang(30016), 'download_manager', {'plot': "Open Download Manager"}, 'download_manager.png'),
        (control.lang(30017), 'sort_select', {'plot': "Choose Sorting..."}, 'sort_select.png'),
        (control.lang(30018), 'clear_slected_fanart', {'plot': "Clear All Selected Fanart"}, 'wipe_addon_data.png')
    ]

    control.draw_items([utils.allocate_item(name, url, False, False, image, info) for name, url, info, image in TOOLS_ITEMS], 'addons')


# def update_menu_paths(menu_items, base_path):
#     updated_items = []
#     for name, url, image in menu_items:
#         new_url = f"{base_path}/{url}" if not url.startswith(base_path) else url
#         updated_items.append((name, new_url, image))
#     return updated_items


# ### Maintenance ###
@Route('settings')
def SETTINGS(payload, params):
    control.ADDON.openSettings()


@Route('change_log')
def CHANGE_LOG(payload, params):
    import service
    service.getChangeLog()
    if params.get('setting'):
        control.exit_code()


@Route('clear_cache')
def CLEAR_CACHE(payload, params):
    database.cache_clear()
    if params.get('setting'):
        control.exit_code()


@Route('clear_search_history')
def CLEAR_SEARCH_HISTORY(payload, params):
    database.clearSearchHistory()
    control.refresh()
    if params.get('setting'):
        control.exit_code()


@Route('clear_slected_fanart')
def CLEAR_SELECTED_FANART(payload, params):
    fanart_all = control.getSetting(f'fanart.all').split(',')
    for i in fanart_all:
        control.setSetting(f'fanart.select.{i}', '')
    control.setSetting('fanart.all', '')
    control.ok_dialog(control.ADDON_NAME, "Completed")
    if params.get('setting'):
        control.exit_code()


@Route('rebuild_database')
def REBUILD_DATABASE(payload, params):
    from resources.lib.ui.database_sync import MalSyncDatabase
    MalSyncDatabase().re_build_database()
    if params.get('setting'):
        control.exit_code()


@Route('completed_sync')
def COMPLETED_SYNC(payload, params):
    import service
    service.sync_watchlist()
    if params.get('setting'):
        control.exit_code()


@Route('sort_select')
def SORT_SELECT(payload, params):
    from resources.lib.windows.sort_select import SortSelect
    SortSelect(*('sort_select.xml', control.ADDON_PATH)).doModal()


# @Route('filter_select')
# def FILTER_SELECT(payload, params):
#     from resources.lib.windows.filter_select import FilterSelect
#     FilterSelect(*('filter_select.xml', control.ADDON_PATH)).doModal()


@Route('download_manager')
def DOWNLOAD_MANAGER(payload, params):
    from resources.lib.windows.download_manager import DownloadManager
    DownloadManager(*('download_manager.xml', control.ADDON_PATH)).doModal()


@Route('import_settings')
def IMPORT_SETTINGS(payload, params):
    import os
    import xbmcvfs

    setting_xml = os.path.join(control.dataPath, 'settings.xml')

    # Import
    import_location = control.browse(1, f"{control.ADDON_NAME}: Import Setting", 'files', 'settings.xml')
    if not import_location:
        return control.exit_code()
    if not import_location.endswith('settings.xml'):
        control.ok_dialog(control.ADDON_NAME, "Invalid File!")
    else:
        yesno = control.yesno_dialog(control.ADDON_NAME, "Are you sure you want to replace settings.xml?")
        if yesno:
            if xbmcvfs.delete(setting_xml) and xbmcvfs.copy(import_location, setting_xml):
                control.ok_dialog(control.ADDON_NAME, "Replaced settings.xml")
            else:
                control.ok_dialog(control.ADDON_NAME, "Could Not Import File!")
    return control.exit_code()


@Route('export_settings')
def EXPORT_SETTINGS(payload, params):
    import os
    import xbmcvfs

    setting_xml = os.path.join(control.dataPath, 'settings.xml')

    # Export
    export_location = control.browse(3, f"{control.ADDON_NAME}: Export Setting", 'files')
    if not export_location:
        control.ok_dialog(control.ADDON_NAME, "Please Select Export Location!")
    else:
        yesno = control.yesno_dialog(control.ADDON_NAME, "Are you sure you want to save settings.xml?")
        if yesno:
            if xbmcvfs.copy(setting_xml, os.path.join(export_location, 'settings.xml')):
                control.ok_dialog(control.ADDON_NAME, "Saved settings.xml")
            else:
                control.ok_dialog(control.ADDON_NAME, "Could Not Export File!")
    return control.exit_code()


@Route('toggleLanguageInvoker')
def TOGGLE_LANGUAGE_INVOKER(payload, params):
    import service
    service.toggle_reuselanguageinvoker()


if __name__ == "__main__":
    router_process(control.get_plugin_url(), control.get_plugin_params())
    if len(control.playList) > 0:
        import xbmc
        if not xbmc.Player().isPlaying():
            control.playList.clear()

# t1 = time.perf_counter_ns()
# totaltime = (t1-t0)/1_000_000
# control.print(totaltime, 'ms')
