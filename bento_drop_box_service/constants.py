from bento_drop_box_service import __version__

__all__ = [
    "SERVICE_NAME",
    "SERVICE_TYPE",
]

SERVICE_NAME = "Bento Drop Box Service"
SERVICE_TYPE = "ca.c3g.bento:drop-box:{}".format(__version__)
