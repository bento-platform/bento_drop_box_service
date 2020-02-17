import os

import chord_drop_box_service

from chord_lib.auth.flask_decorators import flask_permissions_owner
from chord_lib.responses.flask_errors import *
from flask import Flask, jsonify, request, send_file
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.utils import secure_filename


SERVICE_TYPE = "ca.c3g.chord:drop-box:{}".format(chord_drop_box_service.__version__)
SERVICE_NAME = "CHORD Drop Box Service"

application = Flask(__name__)
application.config.from_mapping(
    SERVICE_ID=os.environ.get("SERVICE_ID", SERVICE_TYPE),
    SERVICE_DATA=os.environ.get("SERVICE_DATA", "data/"),
    TRAVERSAL_LIMIT=16,
)

# Generic catch-all
application.register_error_handler(Exception, flask_error_wrap_with_traceback(flask_internal_server_error,
                                                                              service_name=SERVICE_NAME))
application.register_error_handler(BadRequest, flask_error_wrap(flask_bad_request_error))
application.register_error_handler(NotFound, flask_error_wrap(flask_not_found_error))


# Make data directory/ies if needed
os.makedirs(application.config["SERVICE_DATA"], exist_ok=True)


def recursively_build_directory_tree(directory, level=0):
    return tuple({"name": entry,
                  "path": os.path.abspath(os.path.join(directory, entry)),
                  "contents": recursively_build_directory_tree(os.path.join(directory, entry), level=level+1)}
                 if os.path.isdir(os.path.join(directory, entry))
                 else {"name": entry,
                       "path": os.path.abspath(os.path.join(directory, entry)),
                       "size": os.path.getsize(os.path.join(directory, entry))}
                 for entry in os.listdir(directory)
                 if (level < application.config["TRAVERSAL_LIMIT"] or not os.path.isdir(os.path.join(directory, entry)))
                 and entry[0] != ".")


@application.route("/tree", methods=["GET"])
@flask_permissions_owner
def drop_box_tree():
    return jsonify(recursively_build_directory_tree(application.config["SERVICE_DATA"]))


@application.route("/objects/<path:path>", methods=["GET", "PUT"])
@flask_permissions_owner
def drop_box_retrieve(path):
    directory_items = recursively_build_directory_tree(application.config["SERVICE_DATA"])

    if request.method == "PUT":
        content_length = int(request.headers.get("Content-Length", "0"))
        if content_length == 0:
            return flask_bad_request_error("No file provided or no/zero content length specified")

        # TODO: This might not be secure (ok for now due to permissions check)
        upload_path = os.path.realpath(os.path.join(application.config["SERVICE_DATA"],
                                                    os.path.dirname(path), secure_filename(os.path.basename(path))))
        if not os.path.realpath(os.path.join(application.config["SERVICE_DATA"], path)).startswith(
                os.path.realpath(application.config["SERVICE_DATA"])):
            # TODO: Mark against user
            return flask_bad_request_error("Cannot upload outside of the drop box")

        if os.path.exists(upload_path):
            return flask_bad_request_error("Cannot upload to an existing path")

        try:
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        except FileNotFoundError:  # blank dirname
            pass

        bytes_left = content_length
        with open(upload_path, "wb") as f:
            while bytes_left > 0:
                chunk = request.stream.read(4096)  # Chunk size: 4096
                f.write(chunk)
                bytes_left -= len(chunk)

        return application.response_class(status=204)

    # Otherwise, find the file if it exists and return it.
    path_parts = path.split("/")  # TODO: Deal with slashes in file names

    while len(path_parts) > 0:
        part = path_parts[0]
        path_parts = path_parts[1:]

        if part not in {item["name"] for item in directory_items}:
            return flask_not_found_error("Nothing found at specified path")

        try:
            node = next(item for item in directory_items if item["name"] == part)

            if "contents" not in node:
                if len(path_parts) > 0:
                    return flask_bad_request_error("Cannot retrieve a directory")

                return send_file(node["path"], mimetype="application/octet-stream", as_attachment=True,
                                 attachment_filename=node["name"])

            directory_items = node["contents"]

        except StopIteration:
            return flask_not_found_error("Nothing found at specified path")


@application.route("/service-info", methods=["GET"])
def service_info():
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info

    return jsonify({
        "id": application.config["SERVICE_ID"],
        "name": SERVICE_NAME,
        "type": SERVICE_TYPE,
        "description": "Drop box service for a CHORD application.",
        "organization": {
            "name": "C3G",
            "url": "http://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": chord_drop_box_service.__version__
    })
