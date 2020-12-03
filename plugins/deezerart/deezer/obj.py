import enum
import json
from typing import Any, List, Mapping, Optional, Union

# This module is a perfect target for dataclasses.
# Picard though supports Python 3.5+, so we cannot
# use dataclasses for compatibility reasons.


class APIObject:
    """
    Base class from Deezer API objects.
    """
    fields = []  # type: List[str]

    def __init__(self, **kwargs):
        if len(self.fields) == 0:
            raise NotImplementedError(type(self).__name__ + ' cannot have an empty field list')
        for field in self.fields:
            setattr(self, field, kwargs.get(field))

    def __eq__(self, other):
        for field in self.fields:
            if getattr(self, field) != getattr(other, field):
                return False
        return True


class Artist(APIObject):
    """
    The Artist API object.
    """
    fields = ['name']


class CoverSize(enum.Enum):
    """
    Cover size selector.
    """
    THUMBNAIL = 'small'
    SMALL = ''
    MEDIUM = 'medium'
    BIG = 'big'
    LARGE = 'xl'


class Album(APIObject):
    """
    The Album API object.
    """
    fields = ['title', 'cover']

    def cover_url(self, cover_size: CoverSize) -> str:
        """
        Get the album cover URL based on the size wanted.
        """
        return '{}?size={}'.format(self.cover, cover_size.value)


class Track(APIObject):
    """
    The Track API object.
    """
    fields = ['album', 'artist']


available_objects = {c.__name__.lower(): c for c in APIObject.__subclasses__()}


def parse_json(data: Union[str, Mapping[str, Any]]) -> APIObject:
    if isinstance(data, str):
        return json.loads(data, object_hook=_dict_to_object)

    def convert_inner(data: Mapping[str, Any]):
        """
        Traverse the dictionaries with post-order
        algorithm to convert dict objects in Object instances.
        """
        for k, v in data.items():
            if isinstance(v, dict):
                data[k] = convert_inner(v)
        return _dict_to_object(data)

    convert_inner(data)
    return _dict_to_object(data)


def _dict_to_object(data: Mapping[str, Any]) -> Optional[APIObject]:
    try:
        obj_type = data['type']
        obj_class = available_objects[obj_type]
    except KeyError:
        return None
    else:
        return obj_class(**data)
