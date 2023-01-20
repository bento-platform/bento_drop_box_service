from bento_drop_box_service import __version__

__all__ = [
    "BENTO_SERVICE_KIND",
    "SERVICE_NAME",
    "SERVICE_TYPE",
]

BENTO_SERVICE_KIND = "drop-box"
SERVICE_NAME = "Bento Drop Box Service"
SERVICE_TYPE = {
    "group": "ca.c3g.bento",
    "artifact": BENTO_SERVICE_KIND,
    "version": __version__,
}
