import ast
import json
import pickle
import random
import requests
import re

from bs4 import BeautifulSoup
from functools import partial
from resources.lib.ui import database, get_meta, utils, control
from resources.lib.ui.divide_flavors import div_flavor


class AniListBrowser:
    _URL = "https://graphql.anilist.co"

    def __init__(self):
        self._TITLE_LANG = ["romaji", 'english'][int(control.getSetting("titlelanguage"))]
        self.perpage = int(control.getSetting('interface.perpage.general.anilist'))
        self.year_type = int(control.getSetting('contentyear.menu')) if control.getBool('contentyear.bool') else 0
        self.season_type = int(control.getSetting('contentseason.menu')) if control.getBool('contentseason.bool') else -1
        self.format_in_type = ['TV', 'MOVIE', 'TV_SHORT', 'SPECIAL', 'OVA', 'ONA', 'MUSIC'][int(control.getSetting('contentformat.menu'))] if control.getBool('contentformat.bool') else ''
        self.status = ['RELEASING', 'FINISHED', 'NOT_YET_RELEASED', 'CANCELLED'][int(control.getSetting('contentstatus.menu.anilist'))] if control.getBool('contentstatus.bool') else ''
        self.countryOfOrigin_type = ['JP', 'KR', 'CN', 'TW'][int(control.getSetting('contentorigin.menu'))] if control.getBool('contentorigin.bool') else ''
    
    @staticmethod
    def handle_paging(hasnextpage, base_url, page):
        if not hasnextpage or not control.is_addon_visible() and control.getBool('widget.hide.nextpage'):
            return []
        next_page = page + 1
        name = "Next Page (%d)" % next_page
        return [utils.allocate_item(name, base_url % next_page, True, False, 'next.png', {'plot': name}, 'next.png')]
    
    def get_season_year(self, period='current'):
        import datetime
        date = datetime.datetime.today()
        year = date.year
        month = date.month
        seasons = ['WINTER', 'SPRING', 'SUMMER', 'FALL']

        if self.year_type:
            if 1916 < self.year_type <= year + 1:
                year = self.year_type
            else:
                control.notify(control.ADDON_NAME, "Invalid year. Please select a year between 1916 and {0}.".format(year + 1))
                return None, None

        if self.season_type > -1:
            season_id = self.season_type
        else:
            season_id = int((month - 1) / 3)

        if period == "next":
            season = seasons[(season_id + 1) % 4]
            if season == 'WINTER':
                year += 1
        elif period == "last":
            season = seasons[(season_id - 1) % 4]
            if season == 'FALL' and month <= 3:
                year -= 1
        else:
            season = seasons[season_id]

        return season, year
    

    def get_airing_last_season(self, page):
        season, year = self.get_season_year('last')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "TRENDING_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        airing = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(airing, "airing_last_season/%d", page)
    

    def get_airing_this_season(self, page):
        season, year = self.get_season_year('this')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        airing = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(airing, "airing_this_season/%d", page)


    def get_airing_next_season(self, page):
        season, year = self.get_season_year('next')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        airing = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(airing, "airing_next_season/%d", page)
    

    def get_trending_last_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year - 1}%',
            'sort': "TRENDING_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        trending = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(trending, "trending_last_year/%d", page)


    def get_trending_this_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year}%',
            'sort': "TRENDING_DESC"
        }
        
        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        trending = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(trending, "trending_this_year/%d", page)
    

    def get_trending_last_season(self, page):
        season, year = self.get_season_year('last')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "TRENDING_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        trending = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(trending, "trending_last_season/%d", page)
    

    def get_trending_this_season(self, page):
        season, year = self.get_season_year('this')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "TRENDING_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        trending = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(trending, "trending_this_season/%d", page)
    

    def get_all_time_trending(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'sort': "TRENDING_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        trending = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(trending, "all_time_trending/%d", page)
    

    def get_popular_last_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year - 1}%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        popular = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(popular, "popular_last_year/%d", page)


    def get_popular_this_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year}%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        popular = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(popular, "popular_this_year/%d", page)


    def get_popular_last_season(self, page):
        season, year = self.get_season_year('last')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        popular = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(popular, "popular_last_season/%d", page)
    

    def get_popular_this_season(self, page):
        season, year = self.get_season_year('this')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        popular = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(popular, "popular_this_season/%d", page)
    

    def get_all_time_popular(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        popular = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(popular, "all_time_popular/%d", page)
    

    def get_voted_last_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year - 1}%',
            'sort': "SCORE_DESC"
        }
        
        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        voted = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(voted, "voted_last_year/%d", page)
    

    def get_voted_this_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year}%',
            'sort': "SCORE_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        voted = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(voted, "voted_this_year/%d", page)
    

    def get_voted_last_season(self, page):
        season, year = self.get_season_year('last')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "SCORE_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        voted = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(voted, "voted_last_season/%d", page)
    

    def get_voted_this_season(self, page):
        season, year = self.get_season_year('this')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "SCORE_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        voted = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(voted, "voted_this_season/%d", page)
    

    def get_all_time_voted(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'sort': "SCORE_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        voted = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(voted, "all_time_voted/%d", page)
    

    def get_favourites_last_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year - 1}%',
            'sort': "FAVOURITES_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        favourites = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(favourites, "favourites_last_year/%d", page)
    

    def get_favourites_this_year(self, page):
        season, year = self.get_season_year('')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'year': f'{year}%',
            'sort': "FAVOURITES_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        favourites = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(favourites, "favourites_this_year/%d", page)
    

    def get_favourites_last_season(self, page):
        season, year = self.get_season_year('last')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "FAVOURITES_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        favourites = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(favourites, "favourites_last_season/%d", page)
    

    def get_favourites_this_season(self, page):
        season, year = self.get_season_year('this')
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'season': season,
            'year': f'{year}%',
            'sort': "FAVOURITES_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        favourites = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(favourites, "favourites_this_season/%d", page)
    

    def get_all_time_favourites(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'sort': "FAVOURITES_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        favourites = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(favourites, "all_time_favourites/%d", page)
    

    def get_top_100(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'sort': "SCORE_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        top_100 = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(top_100, "top_100/%d", page)
    

    def get_genre_action(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Action",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_action/%d", page)
    

    def get_genre_adventure(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Adventure",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_adventure/%d", page)
    

    def get_genre_comedy(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Comedy",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_comedy/%d", page)
    

    def get_genre_drama(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Drama",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_drama/%d", page)
    

    def get_genre_ecchi(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Ecchi",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_ecchi/%d", page)
    

    def get_genre_fantasy(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Fantasy",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_fantasy/%d", page)
    

    def get_genre_hentai(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Hentai",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_hentai/%d", page)
    
    
    def get_genre_horror(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Horror",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_horror/%d", page)
    

    def get_genre_shoujo(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Shoujo",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_shoujo/%d", page)
    

    def get_genre_mecha(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Mecha",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_mecha/%d", page)
    

    def get_genre_music(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Music",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_music/%d", page)
    

    def get_genre_mystery(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Mystery",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_mystery/%d", page)
    

    def get_genre_psychological(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Psychological",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_psychological/%d", page)
    

    def get_genre_romance(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Romance",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_romance/%d", page)
    

    def get_genre_sci_fi(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Sci-Fi",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_sci_fi/%d", page)
    

    def get_genre_slice_of_life(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Slice of Life",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_slice_of_life/%d", page)
    

    def get_genre_sports(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Sports",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_sports/%d", page)
    

    def get_genre_supernatural(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Supernatural",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_supernatural/%d", page)
    

    def get_genre_thriller(self, page):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'type': "ANIME",
            'includedGenres': "Thriller",
            'sort': "POPULARITY_DESC"
        }

        if self.format_in_type:
            variables['format'] = self.format_in_type

        if self.countryOfOrigin_type:
            variables['countryOfOrigin'] = self.countryOfOrigin_type

        if self.status:
            variables['status'] = self.status

        genre = database.get(self.get_base_res, 24, variables)
        return self.process_anilist_view(genre, "genre_thriller/%d", page)


    def get_search(self, query, page=1):
        variables = {
            'page': page,
            'perpage': self.perpage,
            'search': query,
            'sort': "SEARCH_MATCH",
            'type': "ANIME"
        }
        search = self.get_search_res(variables)
        if control.getSetting('search.adult') == "true":
            variables['isAdult'] = True
            search_adult = self.get_search_res(variables)
            for i in search_adult["ANIME"]:
                i['title']['english'] = f'{i["title"]["english"]} - {control.colorstr("Adult", "red")}'
            search['ANIME'] += search_adult['ANIME']
        return self.process_anilist_view(search, f"search/{query}/%d", page)

    def get_recommendations(self, mal_id, page):
        variables = {
            'page': page,
            'perPage': self.perpage,
            'idMal': mal_id
        }
        recommendations = database.get(self.get_recommendations_res, 24, variables)
        return self.process_recommendations_view(recommendations, f'find_recommendations/{mal_id}/?page=%d', page)

    def get_relations(self, mal_id):
        variables = {
            'idMal': mal_id
        }
        relations = database.get(self.get_relations_res, 24, variables)
        return self.process_relations_view(relations)
    
    def get_watch_order(self, mal_id):
        url = 'https://chiaki.site/?/tools/watch_order/id/{}'.format(mal_id)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
    
        # Find the element with the desired information
        anime_info = soup.find('tr', {'data-id': str(mal_id)})
    
        watch_order_list = []
        if anime_info is not None:
            # Find all 'a' tags in the entire page with href attributes that match the desired URL pattern
            mal_links = soup.find_all('a', href=re.compile(r'https://myanimelist\.net/anime/\d+'))
    
            # Extract the MAL IDs from these tags
            mal_ids = [re.search(r'\d+', link['href']).group() for link in mal_links]
    
            watch_order_list = []
            for idmal in mal_ids:
                variables = {
                    'idMal': int(idmal),
                    'type': "ANIME"
                }
    
                anilist_item = database.get(self.get_anilist_res_with_mal_id, 24, variables)
                if anilist_item is not None:
                    watch_order_list.append(anilist_item)
    
        return self.process_watch_order_view(watch_order_list)

    def get_anime(self, mal_id):
        variables = {
            'idMal': mal_id,
            'type': "ANIME"
        }
        anilist_res = database.get(self.get_anilist_res, 24, variables)
        return self.process_res(anilist_res)

    def get_base_res(self, variables):
        query = '''
        query (
            $page: Int=1,
            $perpage: Int=20
            $type: MediaType,
            $isAdult: Boolean = false,
            $format:[MediaFormat],
            $countryOfOrigin:CountryCode
            $season: MediaSeason,
            $includedGenres: [String],
            $year: String,
            $status: MediaStatus,
            $sort: [MediaSort] = [POPULARITY_DESC, SCORE_DESC]
        ) {
            Page (page: $page, perPage: $perpage) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    format_in: $format,
                    type: $type,
                    genre_in: $includedGenres,
                    season: $season,
                    startDate_like: $year,
                    sort: $sort,
                    status: $status
                    isAdult: $isAdult
                    countryOfOrigin: $countryOfOrigin
                ) {
                    id
                    idMal
                    title {
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    bannerImage
                    startDate {
                        year,
                        month,
                        day
                    }
                    description
                    synonyms
                    format
                    episodes
                    status
                    genres
                    duration
                    countryOfOrigin
                    averageScore
                    trailer {
                        id
                        site
                    }
                    characters (
                        page: 1,
                        sort: ROLE,
                        perPage: 10,
                    ) {
                        edges {
                            node {
                                name {
                                    userPreferred
                                }
                            }
                            voiceActors (language: JAPANESE) {
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                }
            }
        }
        '''
        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        json_res = results['data']['Page']
        return json_res

    def get_search_res(self, variables):
        query = '''
        query (
            $page: Int=1,
            $perpage: Int=20
            $type: MediaType,
            $isAdult: Boolean = false,
            $search: String,
            $sort: [MediaSort] = [SCORE_DESC, POPULARITY_DESC]
        ) {
            Page (page: $page, perPage: $perpage) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    type: $type,
                    search: $search,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    idMal
                    title {
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    bannerImage
                    startDate {
                        year,
                        month,
                        day
                    }
                    description
                    synonyms
                    format
                    episodes
                    status
                    genres
                    duration
                    countryOfOrigin
                    averageScore
                    trailer {
                        id
                        site
                    }
                    characters (
                        page: 1,
                        sort: ROLE,
                        perPage: 10,
                    ) {
                        edges {
                            node {
                                name {
                                    userPreferred
                                }
                            }
                            voiceActors (language: JAPANESE) {
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                }
            }
        }
        '''

        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        json_res = results['data']['Page']
        return json_res

    def get_recommendations_res(self, variables):
        query = '''
        query ($idMal: Int, $page: Int, $perpage: Int=20) {
          Media(idMal: $idMal, type: ANIME) {
            id
            recommendations(page: $page, perPage: $perpage, sort: [RATING_DESC, ID]) {
              pageInfo {
                hasNextPage
              }
              edges {
                node {
                  id
                  rating
                  mediaRecommendation {
                    id
                    idMal
                    title {
                      romaji
                      english
                    }
                    genres
                    averageScore
                    description(asHtml: false)
                    coverImage {
                      extraLarge
                    }
                    bannerImage
                    startDate {
                      year
                      month
                      day
                    }
                    format
                    episodes
                    duration
                    status
                    studios {
                      edges {
                        node {
                          name
                        }
                      }
                    }
                    trailer {
                        id
                        site
                    }
                    characters (perPage: 10) {
                      edges {
                        node {
                          name {
                            full
                            native
                            userPreferred
                          }
                        }
                        voiceActors(language: JAPANESE) {
                          id
                          name {
                            full
                            native
                            userPreferred
                          }
                          image {
                            large
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        '''

        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        json_res = results['data']['Media']['recommendations']
        return json_res

    def get_relations_res(self, variables):
        query = '''
        query ($idMal: Int) {
          Media(idMal: $idMal, type: ANIME) {
            relations {
              edges {
                relationType
                node {
                  id
                  idMal
                  title {
                    romaji
                    english
                  }
                  genres
                  averageScore
                  description(asHtml: false)
                  coverImage {
                    extraLarge
                  }
                  bannerImage
                  startDate {
                    year
                    month
                    day
                  }
                  format
                  episodes
                  duration
                  status
                  studios {
                    edges {
                      node {
                        name
                      }
                    }
                  }
                  trailer {
                    id
                    site
                  }
                  characters (perPage: 10) {
                    edges {
                      node {
                        name {
                          full
                          native
                          userPreferred
                        }
                      }
                      voiceActors(language: JAPANESE) {
                        id
                        name {
                          full
                          native
                          userPreferred
                        }
                        image {
                          large
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        '''

        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        json_res = results['data']['Media']['relations']
        return json_res

    def get_anilist_res(self, variables):
        query = '''
        query($idMal: Int, $type: MediaType){
            Media(idMal: $idMal, type: $type) {
                id
                idMal
                title {
                    romaji,
                    english
                }
                coverImage {
                    extraLarge
                }
                bannerImage
                startDate {
                    year,
                    month,
                    day
                }
                description
                synonyms
                format
                episodes
                status
                genres
                duration
                countryOfOrigin
                averageScore
                characters (
                    page: 1,
                    sort: ROLE,
                    perPage: 10,
                ) {
                    edges {
                        node {
                            name {
                                userPreferred
                            }
                        }
                        voiceActors (language: JAPANESE) {
                            name {
                                userPreferred
                            }
                            image {
                                large
                            }
                        }
                    }
                }
                studios {
                    edges {
                        node {
                            name
                        }
                    }
                }
                trailer {
                    id
                    site
                }
            }
        }
        '''

        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        if "errors" in results.keys():
            return
        json_res = results['data']['Media']
        return json_res
    
    def get_anilist_res_with_mal_id(self, variables):
        query = '''
        query($idMal: Int, $type: MediaType){Media(idMal: $idMal, type: $type) {
            id
            idMal
            title {
                userPreferred,
                romaji,
                english
            }
            coverImage {
                extraLarge
            }
            bannerImage
            startDate {
                year,
                month,
                day
            }
            description
            synonyms
            format
            episodes
            status
            genres
            duration
            countryOfOrigin
            averageScore
            characters (
                page: 1,
                sort: ROLE,
                perPage: 10,
            ) {
                edges {
                    node {
                        name {
                            userPreferred
                        }
                    }
                    voiceActors (language: JAPANESE) {
                        name {
                            userPreferred
                        }
                        image {
                            large
                        }
                    }
                }
            }
            studios {
                edges {
                    node {
                        name
                    }
                }
            }
            }
        }
        '''
        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        if "errors" in results.keys():
            return
        json_res = results['data']['Media']
        return json_res

    def process_anilist_view(self, json_res, base_plugin_url, page):
        hasNextPage = json_res['pageInfo']['hasNextPage']
        get_meta.collect_meta(json_res['ANIME'])
        mapfunc = partial(self.base_anilist_view, completed=self.open_completed())
        all_results = list(filter(lambda x: True if x else False, map(mapfunc, json_res['ANIME'])))
        all_results += self.handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def process_recommendations_view(self, json_res, base_plugin_url, page):
        hasNextPage = json_res['pageInfo']['hasNextPage']
        res = [edge['node']['mediaRecommendation'] for edge in json_res['edges'] if edge['node']['mediaRecommendation']]
        get_meta.collect_meta(res)
        mapfunc = partial(self.base_anilist_view, completed=self.open_completed())
        all_results = list(filter(lambda x: True if x else False, map(mapfunc, res)))
        all_results += self.handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def process_relations_view(self, json_res):
        res = []
        for edge in json_res['edges']:
            if edge['relationType'] != 'ADAPTATION':
                tnode = edge['node']
                tnode['relationType'] = edge['relationType']
                res.append(tnode)
        get_meta.collect_meta(res)
        mapfunc = partial(self.base_anilist_view, completed=self.open_completed())
        all_results = list(filter(lambda x: True if x else False, map(mapfunc, res)))
        return all_results
    
    def process_watch_order_view(self, json_res):
        res = json_res
        get_meta.collect_meta(res)
        mapfunc = partial(self.base_anilist_view, completed=self.open_completed())
        all_results = list(filter(lambda x: True if x else False, map(mapfunc, res)))
        return all_results

    def process_res(self, res):
        self.database_update_show(res)
        get_meta.collect_meta([res])
        return database.get_show(res['idMal'])

    @div_flavor
    def base_anilist_view(self, res, completed=None, mal_dub=None):
        if not completed:
            completed = {}
        anilist_id = res['id']
        mal_id = res.get('idMal')

        if not mal_id:
            return

        if not database.get_show(mal_id):
            self.database_update_show(res)

        show_meta = database.get_show_meta(mal_id)
        kodi_meta = pickle.loads(show_meta.get('art')) if show_meta else {}

        title = res['title'][self._TITLE_LANG] or res['title']['romaji']

        if res.get('relationType'):
            title += ' [I]%s[/I]' % control.colorstr(res['relationType'], 'limegreen')

        if desc := res.get('description'):
            desc = desc.replace('<i>', '[I]').replace('</i>', '[/I]')
            desc = desc.replace('<b>', '[B]').replace('</b>', '[/B]')
            desc = desc.replace('<br>', '[CR]')
            desc = desc.replace('\n', '')

        info = {
            'UniqueIDs': {'anilist_id': str(anilist_id), 'mal_id': str(mal_id)},
            'genre': res.get('genres'),
            'title': title,
            'plot': desc,
            'status': res.get('status'),
            'mediatype': 'tvshow',
            'country': res.get('countryOfOrigin', '')
        }

        if completed.get(str(mal_id)):
            info['playcount'] = 1

        try:
            start_date = res.get('startDate')
            info['premiered'] = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
            info['year'] = start_date['year']
        except TypeError:
            pass

        try:
            cast = []
            for i, x in enumerate(res['characters']['edges']):
                role = x['node']['name']['userPreferred']
                actor = x['voiceActors'][0]['name']['userPreferred']
                actor_hs = x['voiceActors'][0]['image']['large']
                cast.append({'name': actor, 'role': role, 'thumbnail': actor_hs, 'index': i})
            info['cast'] = cast
        except IndexError:
            pass

        info['studio'] = [x['node'].get('name') for x in res['studios']['edges']]

        try:
            info['rating'] = {'score': res.get('averageScore') / 10.0}
        except TypeError:
            pass
        try:
            info['duration'] = res['duration'] * 60
        except TypeError:
            pass

        try:
            if res['trailer']['site'] == 'youtube':
                info['trailer'] = f"plugin://plugin.video.youtube/play/?video_id={res['trailer']['id']}"
            else:
                info['trailer'] = f"plugin://plugin.video.dailymotion_com/?url={res['trailer']['id']}&mode=playVideo"
        except (KeyError, TypeError):
            pass

        dub = True if mal_dub and mal_dub.get(str(mal_id)) else False

        image = res['coverImage']['extraLarge']
        base = {
            "name": title,
            "url": f'animes/{mal_id}/',
            "image": image,
            "poster": image,
            'fanart': kodi_meta['fanart'] if kodi_meta.get('fanart') else image,
            "banner": res.get('bannerImage'),
            "info": info
        }

        if kodi_meta.get('thumb'):
            base['landscape'] = random.choice(kodi_meta['thumb'])
        if kodi_meta.get('clearart'):
            base['clearart'] = random.choice(kodi_meta['clearart'])
        if kodi_meta.get('clearlogo'):
            base['clearlogo'] = random.choice(kodi_meta['clearlogo'])
        if res['format'] in ['MOVIE', 'ONA', 'SPECIAL'] and res['episodes'] == 1:
            base['url'] = f'play_movie/{mal_id}/'
            base['info']['mediatype'] = 'movie'
            return utils.parse_view(base, False, True, dub)
        return utils.parse_view(base, True, False, dub)

    def database_update_show(self, res):
        mal_id = res.get('idMal')

        if not mal_id:
            return

        try:
            start_date = res['startDate']
            start_date = '{}-{:02}-{:02}'.format(start_date['year'], start_date['month'], start_date['day'])
        except TypeError:
            start_date = None

        try:
            duration = res['duration'] * 60 
        except (KeyError, TypeError):
            duration = 0

        title_userPreferred = res['title'][self._TITLE_LANG] or res['title']['romaji']

        name = res['title']['romaji']
        ename = res['title']['english']
        titles = f"({name})|({ename})"

        if desc := res.get('description'):
            desc = desc.replace('<i>', '[I]').replace('</i>', '[/I]')
            desc = desc.replace('<b>', '[B]').replace('</b>', '[/B]')
            desc = desc.replace('<br>', '[CR]')
            desc = desc.replace('\n', '')


        kodi_meta = {
            'name': name,
            'ename': ename,
            'title_userPreferred': title_userPreferred,
            'start_date': start_date,
            'query': titles,
            'episodes': res['episodes'],
            'poster': res['coverImage']['extraLarge'],
            'status': res.get('status'),
            'format': res.get('format', ''),
            'plot': desc,
            'duration': duration
        }

        try:
            kodi_meta['rating'] = {'score': res.get('averageScore') / 10.0}
        except TypeError:
            pass

        database.update_show(mal_id, pickle.dumps(kodi_meta))


    def get_genres(self):
        query = '''
        query {
            genres: GenreCollection,
            tags: MediaTagCollection {
                name
                isAdult
            }
        }
        '''

        r = requests.post(self._URL, json={'query': query})
        results = r.json()
        if not results:
            # genres_list = ['Action', 'Adventure', 'Comedy', 'Drama', 'Ecchi', 'Fantasy', 'Hentai', "Horror", 'Mahou Shoujo', 'Mecha', 'Music', 'Mystery', 'Psychological', 'Romance', 'Sci-Fi', 'Slice of Life', 'Sports', 'Supernatural', 'Thriller']
            genres_list = ['error']
        else:
            genres_list = results['data']['genres']
        # if 'Hentai' in genres_list:
        #     genres_list.remove('Hentai')
        try:
            tags_list = [x['name'] for x in results['tags'] if not x['isAdult']]
        except KeyError:
            tags_list = []
        multiselect = control.multiselect_dialog(control.lang(30934), genres_list + tags_list)
        if not multiselect:
            return []
        genre_display_list = []
        tag_display_list = []
        for selection in multiselect:
            if selection < len(genres_list):
                genre_display_list.append(genres_list[selection])
            else:
                tag_display_list.append(tag_display_list[selection])
        return self.genres_payload(genre_display_list, tag_display_list, 1)

    def genres_payload(self, genre_list, tag_list, page):
        query = '''
        query (
            $page: Int,
            $perPage: Int=20,
            $type: MediaType,
            $isAdult: Boolean = false,
            $genre_in: [String],
            $sort: [MediaSort] = [SCORE_DESC, POPULARITY_DESC]
        ) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                }
                ANIME: media (
                    type: $type,
                    genre_in: $genre_in,
                    sort: $sort,
                    isAdult: $isAdult
                ) {
                    id
                    idMal
                    title {
                        romaji,
                        english
                    }
                    coverImage {
                        extraLarge
                    }
                    bannerImage
                    startDate {
                        year,
                        month,
                        day
                    }
                    description
                    synonyms
                    format
                    episodes
                    status
                    genres
                    duration
                    isAdult
                    countryOfOrigin
                    averageScore
                    trailer {
                        id
                        site
                    }
                    characters (
                        page: 1,
                        sort: ROLE,
                        perPage: 10,
                    ) {
                        edges {
                            node {
                                name {
                                    userPreferred
                                }
                            }
                            voiceActors (language: JAPANESE) {
                                name {
                                    userPreferred
                                }
                                image {
                                    large
                                }
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                }
            }
        }
        '''
        if not isinstance(genre_list, list):
            genre_list = ast.literal_eval(genre_list)
        if not isinstance(tag_list, list):
            tag_list = ast.literal_eval(tag_list)
        variables = {
            'page': page,
            'perPage': self.perpage,
            'type': "ANIME"
        }
        if genre_list:
            variables['genre_in'] = genre_list
        if tag_list:
            variables['tag_in'] = tag_list
        if 'Hentai' in genre_list:
            variables['isAdult'] = True
        return self.process_genre_view(query, variables, f"genres/{genre_list}/{tag_list}/%d", page)

    def process_genre_view(self, query, variables, base_plugin_url, page):
        r = requests.post(self._URL, json={'query': query, 'variables': variables})
        results = r.json()
        anime_res = results['data']['Page']['ANIME']
        hasNextPage = results['data']['Page']['pageInfo']['hasNextPage']
        mapfunc = partial(self.base_anilist_view, completed=self.open_completed())
        get_meta.collect_meta(anime_res)
        all_results = list(map(mapfunc, anime_res))
        all_results += self.handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    @staticmethod
    def open_completed():
        try:
            with open(control.completed_json) as file:
                completed = json.load(file)
        except FileNotFoundError:
            completed = {}
        return completed
    