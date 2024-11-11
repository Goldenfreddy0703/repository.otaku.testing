_REGISTERED_ROUTES = []


class Route:
    def __init__(self, route_path):
        self._path = route_path
        self._is_wildcard = False
        if route_path.endswith("*"):
            self._is_wildcard = True
            self._path = route_path[:-1]

    def __call__(self, func):
        self._func = func
        _REGISTERED_ROUTES.append(self)
        return func

    @property
    def path(self):
        return self._path

    @property
    def wildcard(self):
        return self._is_wildcard

    @property
    def func(self):
        return self._func


def router_process(url, params=None):
    if not params:
        params = {}
    payload = "/".join(url.split("/")[1:])
    for route_obj in _REGISTERED_ROUTES:
        if url == route_obj.path or (route_obj.wildcard and url.startswith(route_obj.path)):
            return route_obj.func(payload, params)
