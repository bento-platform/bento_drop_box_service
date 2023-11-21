from bento_lib.service_info import GA4GHServiceType
from bento_drop_box_service import __version__

__all__ = [
    "BENTO_SERVICE_KIND",
    "SERVICE_TYPE",
]

BENTO_SERVICE_KIND = "drop-box"
SERVICE_TYPE: GA4GHServiceType = {
    "group": "ca.c3g.bento",
    "artifact": BENTO_SERVICE_KIND,
    "version": __version__,
}
