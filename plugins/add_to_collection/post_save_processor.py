from picard import log
from picard.collection import Collection, user_collections
from picard.file import File, register_file_post_save_processor

from picard.plugins.add_to_collection import settings
from picard.plugins.add_to_collection.override_module import override_module


def post_save_processor(file: File) -> None:
    collection_id = settings.collection_id()
    if not collection_id:
        log.error("cannot find collection ID setting")
        return
    collection: Collection = user_collections.get(collection_id)
    if not collection:
        log.error(f"cannot find collection with id {collection_id}")
        return
    release_id = file.metadata["musicbrainz_albumid"]
    if release_id not in collection.releases:
        log.debug("Adding release %r to %r", release_id, collection.name)
        collection.add_releases(set([release_id]), callback=lambda: None)


def register_processor() -> None:
    with override_module(post_save_processor):
        register_file_post_save_processor(post_save_processor)
