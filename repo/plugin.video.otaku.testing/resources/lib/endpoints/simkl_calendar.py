import json
import os
from resources.lib.ui import client, control

baseUrl = 'https://data.simkl.in/calendar/anime.json'


class SimklCalendar:
    def __init__(self):
        self.anime_cache = {}

    def update_calendar(self):
        response = client.request(baseUrl)
        if response:
            simkl_cache = json.loads(response)
            self.set_cached_data(simkl_cache)

    def get_calendar_data(self, mal_id):
        if mal_id in self.anime_cache:
            return self.anime_cache[mal_id]

        simkl_cache = self.get_cached_data()
        if simkl_cache:
            self.simkl_cache = simkl_cache
        else:
            response = client.request(baseUrl)
            if response:
                self.simkl_cache = json.loads(response)
                self.set_cached_data(self.simkl_cache)
            else:
                return None

        for item in self.simkl_cache:
            if item.get('ids', {}).get('mal') == str(mal_id):
                airing_episode = item.get('episode', {}).get('episode')
                self.anime_cache[mal_id] = airing_episode - 1
                return airing_episode
        return None

    def fetch_and_find_simkl_entry(self, mal_id):
        simkl_cache = self.get_cached_data()
        if simkl_cache:
            self.simkl_cache = simkl_cache
        else:
            response = client.request(baseUrl)
            if response:
                self.simkl_cache = json.loads(response)
                self.set_cached_data(self.simkl_cache)
            else:
                return None

        for entry in self.simkl_cache:
            if entry['ids']['mal'] == str(mal_id):
                return entry
        return None

    def get_cached_data(self):
        if os.path.exists(control.simkl_calendar_json):
            with open(control.simkl_calendar_json, 'r') as f:
                return json.load(f)
        return None

    def set_cached_data(self, data):
        with open(control.simkl_calendar_json, 'w') as f:
            json.dump(data, f)