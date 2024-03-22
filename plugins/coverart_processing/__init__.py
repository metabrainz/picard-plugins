PLUGIN_NAME = "CoverArt Processing"
PLUGIN_AUTHOR = "Pranay"
PLUGIN_DESCRIPTION = """
Post Processing Features for the CoverArt Images.
Ignore images smaller than specified width and height.
Resize the image if larger than specified dimensions.
"""
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.2']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from PIL import Image
from io import BytesIO
from picard.plugins.coverart_processing.ui_options_coverart_processing import Ui_CoverartProcessingOptionsPage
from picard.util import imageinfo
from picard import log, config
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.plugin import PluginPriority

MAX_DIMENSION_DEFAULT = 600 # Set default maximum allowable dimensions of image in pixels
MIN_DIMENSION_DEFAULT = 400 # Set default minimum allowable dimensions of image in pixels
MAX_DIMENSION_RANGE = 2000

class CoverArtProcessor:
    def __init__(self):
        self.max_dimension = int(config.setting['max_dimension']) if ('max_dimension' in config.setting and config.setting['max_dimension'] is not None) else MAX_DIMENSION_DEFAULT
        self.min_dimension = int(config.setting['min_dimension']) if ('min_dimension' in config.setting and config.setting['min_dimension'] is not None) else MIN_DIMENSION_DEFAULT
        self.cache = {}

    def ignore_image(self, img_data):
        """Ignore The image file if the dimensions are smaller than predefined"""
        (width, height) = imageinfo.identify(img_data)[:2]
        return width < self.min_dimension or height < self.max_dimension

    def resize_image(self, image_data):
        """Resize the image to max_size if larger than max_size."""
        with Image.open(BytesIO(image_data)) as img:
            width, height = img.size

            if width > self.max_dimension or height > self.max_dimension:
                # Calculate the new size while maintaining aspect ratio
                aspect_ratio = width / height
                if width > height:
                    new_width = self.max_dimension
                    new_height = int(new_width / aspect_ratio)
                else:
                    new_height = self.max_dimension
                    new_width = int(new_height * aspect_ratio)

                img = img.resize((new_width, new_height), Image.LANCZOS)

                with BytesIO() as output:
                    img.save(output, format="JPEG", quality=85)
                    return output.getvalue()

        # If image dimensions are already within the max limit, original image is to be used.
        return image_data

    def process_images(self, album, metadata, track, release):
        """Process the Cover Art Images one by one"""
        try:
            for image_index, image in enumerate(metadata.images):

                image_hash = image.url.toString()
                if image_hash in self.cache:
                    if self.cache[image_hash] is None:
                        metadata.images.pop(image_index)
                    else:
                        metadata.images[image_index].set_data(self.cache[image_hash])

                else:
                    if self.ignore_image(image.data):
                        metadata.images.pop(image_index)
                        self.cache[image_hash] = None
                        log.warning(f"{PLUGIN_NAME}: Ignoring Image {image_index+1} because it is smaller than the minimum allowed dimensions.")
                    else:
                        new_image_data = self.resize_image(image.data)
                        metadata.images[image_index].set_data(new_image_data)
                        self.cache[image_hash] = new_image_data
                        log.info(f"{PLUGIN_NAME}: Resizing Image {image_index+1}.")
        except Exception as ex:
            log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))


# register the plugin track metadata processor with a higher priority so that other image processing 
# plugins can use the resized images.
coverart_processing = CoverArtProcessor()
register_track_metadata_processor(coverart_processing.process_images, priority=PluginPriority.HIGH)

class coverartprocessingOptionsPage(OptionsPage):
    NAME = "coverart_processing"
    TITLE = "Cover Art Processing"
    PARENT = "plugins"

    options = [
        config.IntOption("setting", "min_dimension", 400),
        config.IntOption("setting", "max_dimension", 600),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CoverartProcessingOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        settings = config.setting
        self.ui.spinBox.setMinimum(0)
        self.ui.spinBox.setMaximum(MAX_DIMENSION_RANGE)
        self.ui.spinBox.setValue(settings["min_dimension"])
        self.ui.spinBox_2.setMinimum(0)
        self.ui.spinBox_2.setMaximum(MAX_DIMENSION_RANGE)
        self.ui.spinBox_2.setValue(settings["max_dimension"])

    def save(self):
        self._set_settings(config.setting)
        coverart_processing.min_dimension = int(self.ui.spinBox.value())
        coverart_processing.max_dimension = int(self.ui.spinBox_2.value())
        coverart_processing.cache = {}

    def _set_settings(self, settings):
        settings["min_dimension"] = str(self.ui.spinBox.value())
        settings["max_dimension"] = str(self.ui.spinBox_2.value())


register_options_page(coverartprocessingOptionsPage) # Register the plugin options page