from bento_lib.service_info.helpers import build_bento_service_type
from bento_lib.service_info.types import GA4GHServiceType
from bento_drop_box_service import __version__

__all__ = [
    "BENTO_SERVICE_KIND",
    "SERVICE_TYPE",
]

BENTO_SERVICE_KIND = "drop-box"
SERVICE_TYPE: GA4GHServiceType = build_bento_service_type(BENTO_SERVICE_KIND, __version__)
