from flask import url_for


class S3File:
    def __init__(self, obj, name):
        self.name = name
        self.path = obj.key
        self.size = obj.size

    def serialize(self):
        return {
            "name": self.name,
            "path": url_for('drop_box_service.drop_box_retrieve', path=self.path, _external=True),
            "size": self.size
        }


class S3Directory:
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


class S3Tree:
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
