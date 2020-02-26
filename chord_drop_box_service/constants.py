from chord_drop_box_service import __version__

__all__ = [
    "SERVICE_NAME",
    "SERVICE_TYPE",
]

SERVICE_NAME = "CHORD Drop Box Service"
SERVICE_TYPE = "ca.c3g.chord:drop-box:{}".format(__version__)
