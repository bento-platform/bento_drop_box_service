import os

import chord_drop_box_service

from flask import Flask, jsonify

application = Flask(__name__)
application.config.from_mapping(
    SERVICE_DATA=os.environ.get("SERVICE_DATA", "data/")
)


# Make data directory/ies if needed
os.makedirs(application.config["SERVICE_DATA"], exist_ok=True)


@application.route("/tree", methods=["GET"])
def drop_box_tree():
    # TODO: List directories as well
    return jsonify([
        {"name": f, "path": "file://{}".format(os.path.abspath(os.path.join(application.config["SERVICE_DATA"], f)))}
        for f in sorted(os.listdir(application.config["SERVICE_DATA"]))
        if not os.path.isdir(os.path.join(application.config["SERVICE_DATA"], f))
    ])


@application.route("/service-info", methods=["GET"])
def service_info():
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info

    return jsonify({
        "id": "ca.distributedgenomics.chord_drop_box_service",  # TODO: Should be globally unique
        "name": "CHORD Drop Box Service",                       # TODO: Should be globally unique
        "type": "urn:chord:drop_box_service",                   # TODO
        "description": "Drop box service for a CHORD application.",
        "organization": {
            "name": "GenAP",
            "url": "https://genap.ca/"
        },
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": chord_drop_box_service.__version__
    })
