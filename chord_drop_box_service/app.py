import os
import sys
import traceback

import boto3
from flask import Flask, jsonify, request, send_file
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.utils import secure_filename

import chord_drop_box_service
from chord_lib.auth.flask_decorators import flask_permissions_owner
from chord_lib.responses.flask_errors import *


SERVICE_TYPE = "ca.c3g.chord:drop-box:{}".format(chord_drop_box_service.__version__)
SERVICE_ID = os.environ.get("SERVICE_ID", SERVICE_TYPE)

SERVICE_DATA = os.environ.get("SERVICE_DATA", "data/")
MINIO_URL = os.environ.get("MINIO_URL", None)

application = Flask(__name__)
application.config.from_mapping(
    SERVICE_TYPE=SERVICE_TYPE,
    SERVICE_ID=SERVICE_ID,
    SERVICE_DATA_SOURCE='minio' if MINIO_URL else 'local',
    MINIO_URL=MINIO_URL,
    MINIO_USERNAME=os.environ.get('MINIO_USERNAME') if MINIO_URL else None,
    MINIO_PASSWORD=os.environ.get('MINIO_PASSWORD') if MINIO_URL else None,
    MINIO_BUCKET=os.environ.get('MINIO_BUCKET') if MINIO_URL else None,
    SERVICE_DATA=None if MINIO_URL else SERVICE_DATA
)


# Make data directory/ies if needed
if application.config['SERVICE_DATA_SOURCE'] == 'local':
    os.makedirs(application.config["SERVICE_DATA"], exist_ok=True)


TRAVERSAL_LIMIT = 16


# TODO: Figure out common pattern and move to chord_lib

def _wrap_tb(func):
    # TODO: pass exception?
    def handle_error(_e):
        print("[CHORD Lib] Encountered error:", file=sys.stderr)
        traceback.print_exc()
        return func()
    return handle_error


def _wrap(func):
    return lambda _e: func()


application.register_error_handler(Exception, _wrap_tb(flask_internal_server_error))  # Generic catch-all
application.register_error_handler(BadRequest, _wrap(flask_bad_request_error))
application.register_error_handler(NotFound, _wrap(flask_not_found_error))


if application.config['SERVICE_DATA_SOURCE'] == 'minio':
    minio = boto3.resource(
        's3',
        endpoint_url=application.config['MINIO_URL'],
        aws_access_key_id=application.config['MINIO_USERNAME'],
        aws_secret_access_key=application.config['MINIO_PASSWORD']
    )
    bucket = minio.Bucket(application.config['MINIO_BUCKET'])


def recursively_build_directory_tree(directory, level=0):
    return tuple({"name": entry,
                  "path": os.path.abspath(os.path.join(directory, entry)),
                  "contents": recursively_build_directory_tree(os.path.join(directory, entry), level=level+1)}
                 if os.path.isdir(os.path.join(directory, entry))
                 else {"name": entry,
                       "path": os.path.abspath(os.path.join(directory, entry)),
                       "size": os.path.getsize(os.path.join(directory, entry))}
                 for entry in os.listdir(directory)
                 if (level < TRAVERSAL_LIMIT or not os.path.isdir(os.path.join(directory, entry))) and entry[0] != ".")


class S3File():
    def __init__(self, obj, name):
        self.name = name
        self.path = obj.key
        self.size = obj.size

    def serialize(self):
        return {
            "name": self.name,
            "path": self.path,
            "size": self.size
        }


class S3Directory():
    # The path argument keeps track of where we are in the nested
    # directories
    def __init__(self, obj, path=None):
        self.directories = []
        self.files = []

        if '/' not in obj.key:
            raise Exception('Not a directory')

        if path:
            path_parts = path.split('/')
        else:
            path_parts = obj.key.split('/')

        self.name = path_parts[0]

        if len(path_parts) > 1:
            remaining_path = '/'.join(path_parts[1:])
            self.add_path(obj, remaining_path)
        else:
            file_obj = S3File(obj, path_parts[0])
            self.files.append(file_obj)

    def dir_exists(self, name):
        for d in self.directories:
            if d.name == name:
                return d
        
        return None

    def add_path(self, obj, path):
        if '/' in path:
            path_parts = path.split('/')
            directory = self.dir_exists(path_parts[0])

            if directory:
                directory.add_path(obj, '/'.join(path_parts[1:]))
            else:
                directory = S3Directory(obj, path)
                self.directories.append(directory)
        else:
            file_obj = S3File(obj, path)
            self.files.append(file_obj)

    def serialize(self):
        return {
            "contents": [entry.serialize() for entry in self.files + self.directories],
            "name": self.name
        }


class S3Tree():
    def __init__(self):
        self.directories = []
        self.files = []

    def dir_exists(self, name):
        for d in self.directories:
            if d.name == name:
                return d
        
        return None

    def add_path(self, obj):
        if '/' in obj.key:
            path_parts = obj.key.split('/')
            directory = self.dir_exists(path_parts[0])

            if directory:
                directory.add_path(obj, '/'.join(path_parts[1:]))
            else:
                directory = S3Directory(obj)
                self.directories.append(directory)
        else:
            file_obj = S3File(obj, obj.key)
            self.files.append(file_obj)

    def serialize(self):
        return tuple(
            entry.serialize() for entry in self.files + self.directories
        )


def minio_build_directory_tree():
    tree = S3Tree()

    for obj in bucket.objects.all():
        tree.add_path(obj)

    return tree.serialize()


#def minio_build_directory_tree(bucket):
#    bucket = minio.Bucket('patate')
#    objs = bucket.objects.all()
#    dir_tree = []
#
#    dirs = []
#    files = []
#
#    for obj in objs:
#        if '/' in obj.key:
#            for part in reversed(obj.key.split('/')):
#            entry = {
#                "name": obj.key.split('/')[0],
#                "path": obj.key.split('/')[0],
#                "contents": minio_parse_directory_tree(obj.key)
#        else:
#            files.append(obj)


@application.route("/tree", methods=["GET"])
@flask_permissions_owner
def drop_box_tree():
    if application.config['SERVICE_DATA_SOURCE'] == 'local':
        return jsonify(recursively_build_directory_tree(application.config["SERVICE_DATA"]))
    elif application.config['SERVICE_DATA_SOURCE'] == 'minio':
        return jsonify(minio_build_directory_tree())
    else:
        raise flask_internal_server_error("The service source data is not configured properly")


def locally_retrieve(path):
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


def minio_retrieve(path):
    return flask_not_found_error("Nothing found at specified path")


@application.route("/objects/<path:path>", methods=["GET", "PUT"])
@flask_permissions_owner
def drop_box_retrieve(path):
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
