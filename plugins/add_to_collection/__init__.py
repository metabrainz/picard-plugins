from picard.plugins.add_to_collection.manifest import *
from picard.plugins.add_to_collection import options, post_save_processor

options.register_options()
post_save_processor.register_processor()
