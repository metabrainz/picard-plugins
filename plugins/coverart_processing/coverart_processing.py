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
from picard.util import imageinfo
from picard import log
from picard.metadata import register_track_metadata_processor
from picard.plugin import PluginPriority

MAX_DIMENSION = 600 # Set maximum allowable dimensions of image in pixels
MIN_DIMENSION = 400 # Set minimum allowable dimensions of image in pixels

class CoverArtProcessor:
    def __init__(self):
        self.max_dimension = MAX_DIMENSION
        self.min_dimension = MIN_DIMENSION

        self.cache = {}
        log.debug(f"{PLUGIN_NAME}: Initialized with max_dimension={self.max_dimension} and min_dimension={self.min_dimension}.")

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
        """Process the Cover Art Images"""
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
                    log.debug(f"{PLUGIN_NAME}: Ignoring Image {image_index+1} because it is smaller than the minimum allowed dimensions.")
                else:
                    new_image_data = self.resize_image(image.data)
                    metadata.images[image_index].set_data(new_image_data)
                    self.cache[image_hash] = new_image_data
                    log.debug(f"{PLUGIN_NAME}: Resizing Image {image_index+1}.")
                        
            
coverart_processing = CoverArtProcessor()
register_track_metadata_processor(coverart_processing.process_images, priority=PluginPriority.HIGH)
