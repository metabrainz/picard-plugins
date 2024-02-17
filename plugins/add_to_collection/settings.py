from picard.config import TextOption, get_config
from typing import Optional

COLLECTION_ID = "add_to_collection_id"


def collection_id_option() -> TextOption:
    return TextOption(section="setting", name=COLLECTION_ID, default=None)


def collection_id() -> Optional[str]:
    config = get_config()
    if COLLECTION_ID in config.setting:
        return config.setting[COLLECTION_ID]
    return None


def set_collection_id(value: str) -> None:
    config = get_config()
    config.setting[COLLECTION_ID] = value
