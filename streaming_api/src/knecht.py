

from tools import Converter

converter = Converter(object_name="Rom - S01 E07.mkv")
converter.download_object()
# converter.get_media_info()
converter.media_to_dash(monitor=True)