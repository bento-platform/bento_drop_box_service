import os
from typing import Tuple

from chord_lib.responses.flask_errors import flask_bad_request_error, flask_not_found_error
from flask import current_app, send_file
from werkzeug import Request, Response
from werkzeug.utils import secure_filename

from .base import DropBoxBackend


class LocalBackend(DropBoxBackend):
    def _get_directory_tree(self, directory, level=0) -> Tuple[dict, ...]:
        return tuple(
            {
                "name": entry,
                "path": os.path.abspath(os.path.join(directory, entry)),
                "contents": self._get_directory_tree(os.path.join(directory, entry), level=level + 1)
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

    def get_directory_tree(self) -> Tuple[dict]:
        return self._get_directory_tree(current_app.config["SERVICE_DATA"])

    def upload_to_path(self, request: Request, path: str, content_length: int) -> Response:
        # TODO: This might not be secure (ok for now due to permissions check)
        upload_path = os.path.realpath(os.path.join(current_app.config["SERVICE_DATA"],
                                                    os.path.dirname(path), secure_filename(os.path.basename(path))))
        if not os.path.realpath(os.path.join(current_app.config["SERVICE_DATA"], path)).startswith(
                os.path.realpath(current_app.config["SERVICE_DATA"])):
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

    def retrieve_from_path(self, path: str) -> Response:
        directory_items = self.get_directory_tree()

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
