import os
from botocore.exceptions import ClientError
from flask import current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename
from chord_lib.auth.flask_decorators import flask_permissions_owner
from chord_lib.responses.flask_errors import *
from chord_drop_box_service import __version__
from chord_drop_box_service.app import application, bucket
from chord_drop_box_service.minio import S3Tree


def locally_build_directory_tree(directory, level=0):
    return tuple(
        {
            "name": entry,
            "path": os.path.abspath(os.path.join(directory, entry)),
            "contents": locally_build_directory_tree(os.path.join(directory, entry), level=level+1)
        }
        if os.path.isdir(os.path.join(directory, entry))
        else {
            "name": entry,
            "path": os.path.abspath(os.path.join(directory, entry)),
            "size": os.path.getsize(os.path.join(directory, entry))
        }
        for entry in os.listdir(directory)
        if (level < current_app.config["TRAVERSAL_LIMIT"] or
            not os.path.isdir(os.path.join(directory, entry))) and entry[0] != "."
    )


def minio_build_directory_tree():
    tree = S3Tree()

    for obj in bucket.objects.all():
        tree.add_path(obj)

    return tree.serialize()


@application.route("/tree", methods=["GET"])
@flask_permissions_owner
def drop_box_tree():
    if application.config['SERVICE_DATA_SOURCE'] == 'local':
        return jsonify(locally_build_directory_tree(application.config["SERVICE_DATA"]))
    elif application.config['SERVICE_DATA_SOURCE'] == 'minio':
        return jsonify(minio_build_directory_tree())
    else:
        raise flask_internal_server_error("The service source data is not configured properly")


def locally_retrieve(path):
    directory_items = locally_build_directory_tree(application.config["SERVICE_DATA"])

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

        return current_app.response_class(status=204)

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


def minio_retrieve(path):
    if request.method == "PUT":
        raise flask_internal_server_error("Uploading to minio not implemented")
    else:
        try:
            obj = bucket.Object(path)
            content = obj.get()
        except ClientError:
            return flask_not_found_error("Nothing found at specified path")

        filename = path.split('/')[-1]

        return send_file(
            content['Body'],
            mimetype="application/octet-stream",
            as_attachment=True,
            attachment_filename=filename
        )


@application.route("/objects/<path:path>", methods=["GET", "PUT"])
@flask_permissions_owner
def drop_box_retrieve(path):
    # Werkzeug's default is to encode URL to latin1
    # in case we have unicode characters in the filename
    try:
        path = path.encode('iso-8859-1').decode('utf8')
    except UnicodeDecodeError:
        pass

    if application.config['SERVICE_DATA_SOURCE'] == 'local':
        return locally_retrieve(path)
    elif application.config['SERVICE_DATA_SOURCE'] == 'minio':
        return minio_retrieve(path)
    else:
        raise flask_internal_server_error("The service source data is not configured properly")


@application.route("/service-info", methods=["GET"])
def service_info():
    # Spec: https://github.com/ga4gh-discovery/ga4gh-service-info
    return jsonify({
        "id": application.config["SERVICE_ID"],
        "name": application.config["SERVICE_NAME"],
        "type": application.config["SERVICE_TYPE"],
        "description": "Drop box service for a CHORD application.",
        "organization": {
            "name": "C3G",
            "url": "http://www.computationalgenomics.ca"
        },
        "contactUrl": "mailto:david.lougheed@mail.mcgill.ca",
        "version": __version__
    })
