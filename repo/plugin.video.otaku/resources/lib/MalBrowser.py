import time
import requests
import json
import random
import pickle
import ast
import re

from bs4 import BeautifulSoup
from functools import partial
from resources.lib.ui import database, control, utils, get_meta
from resources.lib.ui.divide_flavors import div_flavor


class MalBrowser:
    _URL = "https://api.jikan.moe/v4"

    def __init__(self):
        self._TITLE_LANG = ['title', 'title_english'][int(control.getSetting("titlelanguage"))]
        self.perpage = control.getInt('interface.perpage.general.mal')
        self.format_in_type = ['tv', 'movie', 'tv_special', 'special', 'ova', 'ona', 'music'][int(control.getSetting('contentformat.menu'))] if control.getBool('contentformat.bool') else ''
        self.status = ['airing', 'complete', 'upcoming'][int(control.getSetting('contentstatus.menu.mal'))] if control.getBool('contentstatus.bool') else ''
        self.rating = ['g', 'pg', 'pg13', 'r17', 'r', 'rx'][int(control.getSetting('contentrating.menu.mal'))] if control.getBool('contentrating.bool') else ''
        self.adult = 'true' if control.getSetting('search.adult') == "false" else 'false'

    @staticmethod
    def open_completed():
        try:
            with open(control.completed_json) as file:
                completed = json.load(file)
        except FileNotFoundError:
            completed = {}
        return completed

    @staticmethod
    def handle_paging(hasnextpage, base_url, page):
        if not hasnextpage or not control.is_addon_visible() and control.getBool('widget.hide.nextpage'):
            return []
        next_page = page + 1
        name = "Next Page (%d)" % next_page
        return [utils.allocate_item(name, base_url % next_page, True, False, 'next.png', {'plot': name}, 'next.png')]

    def process_mal_view(self, res, base_plugin_url, page):
        get_meta.collect_meta(res['data'])
        mapfunc = partial(self.base_mal_view, completed=self.open_completed())
        all_results = list(map(mapfunc, res['data']))
        hasNextPage = res['pagination']['has_next_page']
        all_results += self.handle_paging(hasNextPage, base_plugin_url, page)
        return all_results

    def process_res(self, res):
        self.database_update_show(res)
        get_meta.collect_meta([res])
        return database.get_show(res['mal_id'])

    @staticmethod
    def get_season_year(period='current'):
        import datetime
        date = datetime.datetime.today()
        year = date.year
        month = date.month
        seasons = ['WINTER', 'SPRING', 'SUMMER', 'FALL']
        season_start_dates = {
            'WINTER': datetime.date(year, 1, 1),
            'SPRING': datetime.date(year, 4, 1),
            'SUMMER': datetime.date(year, 7, 1),
            'FALL': datetime.date(year, 10, 1)
        }
        season_end_dates = {
            'WINTER': datetime.date(year, 3, 31),
            'SPRING': datetime.date(year, 6, 30),
            'SUMMER': datetime.date(year, 9, 30),
            'FALL': datetime.date(year, 12, 31)
        }
        
        if period == "next":
            season = seasons[int((month - 1) / 3 + 1) % 4]
            if season == 'WINTER':
                year += 1
        elif period == "last":
            season = seasons[int((month - 1) / 3 - 1) % 4]
            if season == 'FALL' and month <= 3:
                year -= 1
        else:
            season = seasons[int((month - 1) / 3)]
        
        # Adjust the start and end dates for this season
        season_start_date = season_start_dates[season]
        season_end_date = season_end_dates[season]
        
        # Adjust the start and end dates for this year
        year_start_date = datetime.date(year, 1, 1)
        year_end_date = datetime.date(year, 12, 31)
    
        # Adjust the start and end dates for last season
        last_season_index = (seasons.index(season) - 1) % 4
        last_season = seasons[last_season_index]
        last_season_year = year if last_season != 'FALL' or month > 3 else year - 1
        season_start_date_last = season_start_dates[last_season].replace(year=last_season_year)
        season_end_date_last = season_end_dates[last_season].replace(year=last_season_year)
        
        # Adjust the start and end dates for last year
        year_start_date_last = datetime.date(year - 1, 1, 1)
        year_end_date_last = datetime.date(year - 1, 12, 31)
    
        # Adjust the start and end dates for next season
        next_season_index = (seasons.index(season) + 1) % 4
        next_season = seasons[next_season_index]
        next_season_year = year if next_season != 'WINTER' else year + 1
        season_start_date_next = season_start_dates[next_season].replace(year=next_season_year)
        season_end_date_next = season_end_dates[next_season].replace(year=next_season_year)
    
        # Adjust the start and end dates for next year
        year_start_date_next = datetime.date(year + 1, 1, 1)
        year_end_date_next = datetime.date(year + 1, 12, 31)
    
        return (season, year, year_start_date, year_end_date, season_start_date, season_end_date,
                season_start_date_last, season_end_date_last, year_start_date_last, year_end_date_last,
                season_start_date_next, season_end_date_next, year_start_date_next, year_end_date_next)
    

    def get_anime(self, mal_id):
        res = database.get(self.get_base_res, 24, f"{self._URL}/anime/{mal_id}")
        return self.process_res(res['data'])
    

    def get_recommendations(self, mal_id, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult
        }
        recommendations = database.get(self.get_base_res, 24, f'{self._URL}/anime/{mal_id}/recommendations', params)
        mapfunc = partial(self.recommendation_relation_view, completed=self.open_completed())
        all_results = list(map(mapfunc, recommendations['data']))
        return all_results
    

    def get_relations(self, mal_id):
        relations = database.get(self.get_base_res, 24, f'{self._URL}/anime/{mal_id}/relations')

        relation_res = []
        count = 0
        for relation in relations['data']:
            for entry in relation['entry']:
                if entry['type'] == 'anime':
                    res_data = database.get(self.get_base_res, 24, f"{self._URL}/anime/{mal_id}")['data']
                    res_data['relation'] = relation['relation']
                    relation_res.append(res_data)
                    if count % 3 == 0:
                        time.sleep(2)
                    count += 1
        mapfunc = partial(self.base_mal_view, completed=self.open_completed())
        all_results = list(map(mapfunc, relation_res))
        return all_results
    

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
            count = 0
            for idmal in mal_ids:
                mal_item = database.get(self.get_base_res, 24, f'{self._URL}/anime/{idmal}')
                if mal_item is not None:
                    watch_order_list.append(mal_item['data'])
                    if count % 3 == 0:
                        time.sleep(2)
                    count += 1
    
        mapfunc = partial(self.base_mal_view, completed=self.open_completed())
        all_results = list(map(mapfunc, watch_order_list))
        return all_results
    

    def get_search(self, query, page=1):
        params = {
            "q": query,
            "page": page,
            "limit": self.perpage,
            'sfw': self.adult
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        search = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(search, f"search/{query}/%d", page)
    

    def get_airing_last_season(self, page):
        season, year, _, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('last')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
        }
        
        if self.format_in_type:
            params['type'] = self.format_in_type
    
        airing = database.get(self.get_base_res, 24, f"{self._URL}/seasons/{year}/{season}", params)
        return self.process_mal_view(airing, "airing_last_season/%d", page)
    

    def get_airing_this_season(self, page):
        season, year, _, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('this')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult
        }
        
        if self.format_in_type:
            params['type'] = self.format_in_type

        airing = database.get(self.get_base_res, 24, f"{self._URL}/seasons/{year}/{season}", params)
        return self.process_mal_view(airing, "airing_this_season/%d", page)
    

    def get_airing_next_season(self, page):
        season, year, _, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('next')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        airing = database.get(self.get_base_res, 24, f"{self._URL}/seasons/{year}/{season}", params)
        return self.process_mal_view(airing, "airing_next_season/%d", page)


    def get_trending_last_year(self, page):
        _, _, _, _, _, _, _, _, year_start_date_last, year_end_date_last, _, _, _, _ = self.get_season_year('last')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date_last,
            'end_date': year_end_date_last,
            'order_by': 'members',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        trending = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(trending, "trending_last_year/%d", page)
    

    def get_trending_this_year(self, page):
        _, _, year_start_date, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date,
            'order_by': 'members',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        trending = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(trending, "trending_this_year/%d", page)
    

    def get_trending_last_season(self, page):
        _, _, _, _, _, _, season_start_date_last, season_end_date_last, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date_last,
            'end_date': season_end_date_last,
            'order_by': 'members',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        trending = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(trending, "trending_last_season/%d", page)
    

    def get_trending_this_season(self, page):
        _, _, _, _, season_start_date, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date,
            'order_by': 'members',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        trending = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(trending, "trending_this_season/%d", page)
    
    
    def get_all_time_trending(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        trending = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(trending, "all_time_trending/%d", page)
    

    def get_popular_last_year(self, page):
        _, _, _, _, _, _, _, _, year_start_date_last, year_end_date_last, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date_last,
            'end_date': year_end_date_last,
            'order_by': 'popularity',
            'sort': 'asc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        popular = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(popular, "popular_last_year/%d", page)
    

    def get_popular_this_year(self, page):
        _, _, year_start_date, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date,
            'order_by': 'popularity',
            'sort': 'asc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        popular = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(popular, "popular_this_year/%d", page)
    

    def get_popular_last_season(self, page):
        _, _, _, _, _, _, season_start_date_last, season_end_date_last, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date_last,
            'end_date': season_end_date_last,
            'order_by': 'popularity',
            'sort': 'asc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        popular = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(popular, "popular_last_season/%d", page)
    

    def get_popular_this_season(self, page):
        _, _, _, _, season_start_date, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date,
            'order_by': 'popularity',
            'sort': 'asc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        popular = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(popular, "popular_this_season/%d", page)
    

    def get_all_time_popular(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'popularity',
            'sort': 'asc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        popular = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(popular, "all_time_popular/%d", page)
    

    def get_voted_last_year(self, page):
        _, _, _, _, _, _, _, _, year_start_date_last, year_end_date_last, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date_last,
            'end_date': year_end_date_last,
            'order_by': 'score',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating


        voted = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(voted, "voted_last_year/%d", page)
    

    def get_voted_this_year(self, page):
        _, _, year_start_date, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date,
            'order_by': 'score',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        voted = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(voted, "voted_this_year/%d", page)
    

    def get_voted_last_season(self, page):
        _, _, _, _, _, _, season_start_date_last, season_end_date_last, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date_last,
            'end_date': season_end_date_last,
            'order_by': 'score',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        voted = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(voted, "voted_last_season/%d", page)
    

    def get_voted_this_season(self, page):
        _, _, _, _, season_start_date, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date,
            'order_by': 'score',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        voted = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(voted, "voted_this_season/%d", page)
    

    def get_all_time_voted(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'score',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        voted = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(voted, "all_time_voted/%d", page)
    

    def get_favourites_last_year(self, page):
        _, _, _, _, _, _, _, _, year_start_date_last, year_end_date_last, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date_last,
            'end_date': year_end_date_last,
            'order_by': 'favorites',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        favourites = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(favourites, "favourites_last_year/%d", page)
    

    def get_favourites_this_year(self, page):
        _, _, year_start_date, _, _, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': year_start_date,
            'order_by': 'favorites',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        favourites = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(favourites, "favourites_this_year/%d", page)
    

    def get_favourites_last_season(self, page):
        _, _, _, _, _, _, season_start_date_last, season_end_date_last, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date_last,
            'end_date': season_end_date_last,
            'order_by': 'favorites',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        favourites = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(favourites, "favourites_last_season/%d", page)
    

    def get_favourites_this_season(self, page):
        _, _, _, _, season_start_date, _, _, _, _, _, _, _, _, _ = self.get_season_year('')
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'start_date': season_start_date,
            'order_by': 'favorites',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        favourites = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(favourites, "favourites_this_season/%d", page)
    

    def get_all_time_favourites(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'favorites',
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        favourites = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(favourites, "all_time_favourites/%d", page)
    

    def get_top_100(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        top_100 = database.get(self.get_base_res, 24, f"{self._URL}/top/anime", params)
        return self.process_mal_view(top_100, "top_100/%d", page)


    def get_genre_action(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "1",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_action = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_action, "genre_action/%d", page)
    

    def get_genre_adventure(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "2",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_adventure = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_adventure, "genre_adventure/%d", page)
    

    def get_genre_comedy(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "4",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_comedy = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_comedy, "genre_comedy/%d", page)
    

    def get_genre_drama(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "8",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_drama = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_drama, "genre_drama/%d", page)
    

    def get_genre_ecchi(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "9",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_ecchi = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_ecchi, "genre_ecchi/%d", page)
    

    def get_genre_fantasy(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "10",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_fantasy = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_fantasy, "genre_fantasy/%d", page)
    

    def get_genre_hentai(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "12",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_hentai = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_hentai, "genre_hentai/%d", page)
    

    def get_genre_horror(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "14",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_horror = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_horror, "genre_horror/%d", page)
    

    def get_genre_shoujo(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "25",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_shoujo = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_shoujo, "genre_shoujo/%d", page)
    

    def get_genre_mecha(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "18",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_mecha = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_mecha, "genre_mecha/%d", page)
    

    def get_genre_music(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "19",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_music = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_music, "genre_music/%d", page)
    

    def get_genre_mystery(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "7",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_mystery = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_mystery, "genre_mystery/%d", page)
    

    def get_genre_psychological(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "40",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_psychological = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_psychological, "genre_psychological/%d", page)
    

    def get_genre_romance(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "22",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_romance = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_romance, "genre_romance/%d", page)
    

    def get_genre_sci_fi(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "24",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_sci_fi = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_sci_fi, "genre_sci_fi/%d", page)
    

    def get_genre_slice_of_life(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "36",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_slice_of_life = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_slice_of_life, "genre_slice_of_life/%d", page)
    

    def get_genre_sports(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "30",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_sports = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_sports, "genre_sports/%d", page)
    

    def get_genre_supernatural(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "37",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_supernatural = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_supernatural, "genre_supernatural/%d", page)
    

    def get_genre_thriller(self, page):
        params = {
            'page': page,
            'limit': self.perpage,
            'sfw': self.adult,
            'order_by': 'members',
            "genres": "41",
            'sort': 'desc'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genre_thriller = database.get(self.get_base_res, 24, f"{self._URL}/anime", params)
        return self.process_mal_view(genre_thriller, "genre_thriller/%d", page)
    

    @staticmethod
    def get_base_res(url, params=None):
        r = requests.get(url, params=params)
        return r.json()


    @div_flavor
    def recommendation_relation_view(self, res, completed=None, mal_dub=None):
        if res.get('entry'):
            res = res['entry']
        if not completed:
            completed = {}

        mal_id = res['mal_id']
        title = res['title']
        if res.get('relation'):
            title += ' [I]%s[/I]' % control.colorstr(res['relation'], 'limegreen')

        info = {
            'UniqueIDs': {'mal_id': str(mal_id)},
            'title': title,
            'mediatype': 'tvshow'
        }

        if completed.get(str(mal_id)):
            info['playcount'] = 1

        dub = True if mal_dub and mal_dub.get(str(res.get('idMal'))) else False

        image = res['images']['webp']['large_image_url'] if res.get('images') else None

        base = {
            "name": title,
            "url": f'animes/{mal_id}/',
            "image": image,
            "poster": image,
            'fanart': image,
            "banner": image,
            "info": info
        }

        return utils.parse_view(base, True, False, dub)

    def get_genres(self):
        res = database.get(self.get_base_res, 24, f'{self._URL}/genres/anime')

        genre = res['data']
        genres_list = []
        for x in genre:
            genres_list.append(x['name'])
        multiselect = control.multiselect_dialog(control.lang(30911), genres_list)
        if not multiselect:
            return []
        genre_display_list = []
        for selection in multiselect:
            if selection < len(genres_list):
                genre_display_list.append(str(genre[selection]['mal_id']))
        return self.genres_payload(genre_display_list, [], 1)

    def genres_payload(self, genre_list, tag_list, page):
        if not isinstance(genre_list, list):
            genre_list = ast.literal_eval(genre_list)

        genre = ','.join(genre_list)
        params = {
            'page': page,
            'limit': self.perpage,
            'genres': genre,
            'sfw': self.adult,
            'order_by': 'popularity'
        }

        if self.format_in_type:
            params['type'] = self.format_in_type

        if self.status:
            params['status'] = self.status

        if self.rating:
            params['rating'] = self.rating

        genres = database.get(self.get_base_res, 24, f'{self._URL}/anime', params)
        return self.process_mal_view(genres, f"genres/{genre_list}/{tag_list}/%d", page)


    @div_flavor
    def base_mal_view(self, res, completed=None, mal_dub=None):
        if not completed:
            completed = {}

        mal_id = res['mal_id']

        if not database.get_show(mal_id):
            self.database_update_show(res)

        show_meta = database.get_show_meta(mal_id)
        kodi_meta = pickle.loads(show_meta.get('art')) if show_meta else {}

        title = res[self._TITLE_LANG] or res['title']
        rating = res.get('rating')
        if rating == 'Rx - Hentai':
            title += ' - ' + control.colorstr("Adult", 'red')
        if res.get('relation'):
            title += ' [I]%s[/I]' % control.colorstr(res['relation'], 'limegreen')

        info = {
            'UniqueIDs': {'mal_id': str(mal_id)},
            'title': title,
            'plot': res.get('synopsis'),
            'mpaa': rating,
            'duration': self.duration_to_seconds(res.get('duration')),
            'genre': [x['name'] for x in res.get('genres', [])],
            'studio': [x['name'] for x in res.get('studios', [])],
            'status': res.get('status'),
            'mediatype': 'tvshow'
        }

        if completed.get(str(mal_id)):
            info['playcount'] = 1

        try:
            start_date = res['aired']['from']
            info['premiered'] = start_date[:10]
            info['year'] = res.get('year', int(start_date[:3]))
        except TypeError:
            pass

        if isinstance(res.get('score'), float):
            info['rating'] = {'score': res['score']}
            if isinstance(res.get('scored_by'), int):
                info['rating']['votes'] = res['scored_by']

        if res.get('trailer'):
            info['trailer'] = f"plugin://plugin.video.youtube/play/?video_id={res['trailer']['youtube_id']}"


        dub = True if mal_dub and mal_dub.get(str(mal_id)) else False

        image = res['images']['webp']['large_image_url']
        base = {
            "name": title,
            "url": f'animes/{mal_id}/',
            "image": image,
            "poster": image,
            'fanart': kodi_meta['fanart'] if kodi_meta.get('fanart') else image,
            "banner": image,
            "info": info
        }

        if kodi_meta.get('thumb'):
            base['landscape'] = random.choice(kodi_meta['thumb'])
        if kodi_meta.get('clearart'):
            base['clearart'] = random.choice(kodi_meta['clearart'])
        if kodi_meta.get('clearlogo'):
            base['clearlogo'] = random.choice(kodi_meta['clearlogo'])

        if res.get('type') in ['Movie', 'ONA', 'Special', 'TV Special'] and res['episodes'] == 1:
            base['url'] = f'play_movie/{mal_id}/'
            base['info']['mediatype'] = 'movie'
            return utils.parse_view(base, False, True, dub)
        return utils.parse_view(base, True, False, dub)


    def database_update_show(self, res):
        mal_id = res['mal_id']

        try:
            start_date = res['aired']['from']
        except TypeError:
            start_date = None

        title_userPreferred = res[self._TITLE_LANG] or res['title']

        name = res['title']
        ename = res['title_english']
        titles = f"({name})|({ename})"

        kodi_meta = {
            'name': name,
            'ename': ename,
            'title_userPreferred': title_userPreferred,
            'start_date': start_date,
            'query': titles,
            'episodes': res['episodes'],
            'poster': res['images']['webp']['large_image_url'],
            'status': res.get('status'),
            'format': res.get('type'),
            'plot': res.get('synopsis'),
            'duration': self.duration_to_seconds(res.get('duration'))
        }

        if isinstance(res.get('score'), float):
            kodi_meta['rating'] = {'score': res['score']}
            if isinstance(res.get('scored_by'), int):
                kodi_meta['rating']['votes'] = res['scored_by']

        database.update_show(mal_id, pickle.dumps(kodi_meta))

    @staticmethod
    def duration_to_seconds(duration_str):
        # Regular expressions to match hours, minutes, and seconds
        hours_pattern = re.compile(r'(\d+)\s*hr')
        minutes_pattern = re.compile(r'(\d+)\s*min')
        seconds_pattern = re.compile(r'(\d+)\s*sec')

        # Extract hours, minutes, and seconds
        hours_match = hours_pattern.search(duration_str)
        minutes_match = minutes_pattern.search(duration_str)
        seconds_match = seconds_pattern.search(duration_str)

        # Convert to integers, default to 0 if not found
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        seconds = int(seconds_match.group(1)) if seconds_match else 0

        # Calculate total duration in seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds

        return total_seconds