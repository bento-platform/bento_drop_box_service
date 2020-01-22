import os

import chord_drop_box_service

from chord_lib.auth.flask_decorators import flask_permissions_owner
from flask import Flask, jsonify, request, send_file
from werkzeug.utils import secure_filename


SERVICE_TYPE = "ca.c3g.chord:drop-box:{}".format(chord_drop_box_service.__version__)
SERVICE_ID = os.environ.get("SERVICE_ID", SERVICE_TYPE)

application = Flask(__name__)
application.config.from_mapping(
    SERVICE_TYPE=SERVICE_TYPE,
    SERVICE_ID=SERVICE_ID,
    SERVICE_DATA=os.environ.get("SERVICE_DATA", "data/")
)


# Make data directory/ies if needed
os.makedirs(application.config["SERVICE_DATA"], exist_ok=True)


TRAVERSAL_LIMIT = 16


def recursively_build_directory_tree(directory, level=0):
    return tuple({"name": entry,
                  "path": os.path.abspath(os.path.join(directory, entry)),
                  "contents": recursively_build_directory_tree(os.path.join(directory, entry), level=level+1)}
                 if os.path.isdir(os.path.join(directory, entry))
                 else {"name": entry, "path": os.path.abspath(os.path.join(directory, entry))}
                 for entry in os.listdir(directory)
                 if (level < TRAVERSAL_LIMIT or not os.path.isdir(os.path.join(directory, entry))) and entry[0] != ".")


@application.route("/tree", methods=["GET"])
@flask_permissions_owner
def drop_box_tree():
    return jsonify(recursively_build_directory_tree(application.config["SERVICE_DATA"]))


@application.route("/objects/<path:path>", methods=["GET", "PUT"])
@flask_permissions_owner
def drop_box_retrieve(path):
    directory_items = recursively_build_directory_tree(application.config["SERVICE_DATA"])

    if request.method == "PUT":
        if "file" not in request.files or request.files["file"].filename == "":
            # No file provided
            return application.response_class(status=400)  # TODO: Standard error format

        # TODO: This might not be secure (ok for now due to permissions check)
        upload_path = os.path.realpath(os.path.join(application.config["SERVICE_DATA"],
                                                    os.path.dirname(path), secure_filename(os.path.basename(path))))
        if not os.path.realpath(os.path.join(application.config["SERVICE_DATA"], path)).startswith(
                application.config["SERVICE_DATA"]):
            # Trying to upload outside of the drop box
            return application.response_class(status=400)  # TODO: Standard error format

        if os.path.exists(upload_path):
            # Can't upload to existing path
            return application.response_class(status=400)  # TODO: Standard error format

        try:
            os.makedirs(os.path.dirname(upload_path), mode=0x700, exist_ok=True)
        except FileNotFoundError:  # blank dirname
            pass

        request.files["file"].save(upload_path)
        return application.response_class(status=204)

    # Otherwise, find the file if it exists and return it.
    path_parts = path.split("/")  # TODO: Deal with slashes in file names

    while len(path_parts) > 0:
        part = path_parts[0]
        path_parts = path_parts[1:]

        if part not in {item["name"] for item in directory_items}:
            return application.response_class(status=404)  # TODO: Standard error format

        try:
            node = next(item for item in directory_items if item["name"] == part)

            if "contents" not in node:
                if len(path_parts) > 0:
                    return application.response_class(status=404)  # TODO: Standard error format

                return send_file(node["path"], mimetype="application/octet-stream", as_attachment=True,
                                 attachment_filename=node["name"])

            directory_items = node["contents"]

        except StopIteration:
            return application.response_class(status=404)  # TODO: Standard error format


@application.route("/service-info", methods=["GET"])
def service_info():
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info

    return jsonify({
        "id": application.config["SERVICE_ID"],
        "name": "CHORD Drop Box Service",  # TODO: Should be globally unique?
        "type": application.config["SERVICE_TYPE"],
        "description": "Drop box service for a CHORD application.",
        "organization": {
            "name": "C3G",
            "url": "http://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": chord_drop_box_service.__version__
    })
