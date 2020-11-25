import json
from functools import partial
from typing import Callable, List, NamedTuple, Optional, TypeVar
from urllib.parse import urlsplit, urlunsplit

from picard.webservice import WebService
from PyQt5.QtCore import QByteArray
from PyQt5.QtNetwork import QNetworkReply

from . import obj

DEEZER_HOST = 'api.deezer.com'
DEEZER_PORT = 443


T = TypeVar('T', bound=obj.Object)
SearchCallback = Callable[[List[T], Optional[QNetworkReply.NetworkError]], None]
APIURLCallback = Callable[[Optional[T], Optional[QNetworkReply.NetworkError]], None]


class SearchOptions(NamedTuple('SearchOptions', [('artist', str), ('album', str), ('track', str), ('label', str)])):
    """
    Options for the advanced search.
    """

    def __str__(self):
        options = ['{}:"{}"'.format(k, v) for k, v in self._asdict().items() if v]
        return ' '.join(options)


# Python 3.5 cannot set defaults values in an othodox way.
SearchOptions.__new__.__defaults__ = ('',) * len(SearchOptions._fields)


class Client:
    def __init__(self, webservice: WebService):
        self.webservice = webservice
        self._get = partial(self.webservice.get, DEEZER_HOST, DEEZER_PORT)

    def advanced_search(self, options: SearchOptions, callback: SearchCallback[obj.Object]):
        path = '/search'

        def handler(document: QByteArray, _: QNetworkReply, error: Optional[QNetworkReply.NetworkError]):
            try:
                parsed_doc = json.loads(str(document, 'utf-8'))
            except json.JSONDecodeError:
                callback([], error)
            else:
                callback([obj.parse_json(dct) for dct in parsed_doc['data']], error)

        self._get(path,
                  queryargs={'q': str(options)},
                  parse_response_type=None,
                  handler=handler)

    def obj_from_url(self, url: str, callback: APIURLCallback[obj.Object]):
        def handler(document: QByteArray, _: QNetworkReply, error: Optional[QNetworkReply.NetworkError]):
            try:
                deezer_obj = obj.parse_json(str(document, 'utf-8'))
            except json.JSONDecodeError:
                deezer_obj = None
            finally:
                callback(deezer_obj, error)

        self._get(self._remove_language_path(urlsplit(url).path),
                  parse_response_type=None,
                  handler=handler)

    @staticmethod
    def api_url(url: str) -> str:
        parsed = urlsplit(url)
        path = Client._remove_language_path(parsed.path)
        return urlunsplit((parsed.scheme, DEEZER_HOST, path, parsed.query, parsed.fragment))

    @staticmethod
    def _remove_language_path(path: str) -> str:
        # Deezer has a 2-letter language path, e.g. /us/track/123.
        lang_len = 2
        paths = path[1:].split('/', maxsplit=1)
        return path[lang_len + 1:] if len(paths[0]) == lang_len else path
