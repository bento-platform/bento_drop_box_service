import pathlib
from collections.abc import Iterable

from fastapi.testclient import TestClient

from bento_drop_box_service.models import DropBoxEntriesResponse, DropBoxEntry, DropBoxEntryDirectory, DropBoxEntryFile

from .conftest import local_dir
from .test_routes import validate_filtered_tree

test_data = pathlib.Path(local_dir)


def upload_test_data(client: TestClient) -> None:
    # so upload the file name as placeholder content for those.
    for file in sorted(test_data.rglob("*")):
        if not file.is_file() or file.name.startswith("."):
            # Skip .gitkeep (S3 has no empty directories)
            continue
        # Some fixtures are 0 bytes, which the upload route rejects,
        # so upload the file name as placeholder content for those.
        content = file.read_bytes() or file.name.encode()
        res = client.put(f"/objects/{file.relative_to(test_data).as_posix()}", content=content)
        assert res.status_code == 204


def get_tree(client: TestClient, path: str = "/tree") -> tuple[DropBoxEntry, ...]:
    res = client.get(path)
    assert res.status_code == 200
    return DropBoxEntriesResponse.model_validate_json(res.content).root


def entry_names(entries: Iterable[DropBoxEntry]) -> list[str]:
    return sorted(e.root.name for e in entries)


def get_entry(entries: Iterable[DropBoxEntry], name: str) -> DropBoxEntryFile | DropBoxEntryDirectory:
    return next(e.root for e in entries if e.root.name == name)


def get_directory(entries: Iterable[DropBoxEntry], name: str) -> DropBoxEntryDirectory:
    entry = get_entry(entries, name)
    assert isinstance(entry, DropBoxEntryDirectory)
    return entry


def test_s3_upload_and_tree(client_s3: TestClient):
    upload_test_data(client_s3)

    tree = get_tree(client_s3)
    assert entry_names(tree) == ["patate.txt", "some_dir", "tomate.vcf", "zucchini.json"]

    # test_data/patate.txt
    patate = get_entry(tree, "patate.txt")
    assert isinstance(patate, DropBoxEntryFile)
    assert patate.size == (test_data / "patate.txt").stat().st_size
    assert patate.uri.endswith("/objects/patate.txt")

    # test_data/some_dir
    some_dir = get_directory(tree, "some_dir")
    assert entry_names(some_dir.contents) == ["patate.txt", "some_other_dir", "tomate.vcf", "zucchini.json"]
    # test_data/some_dir/some_other_dir
    some_other_dir = get_directory(some_dir.contents, "some_other_dir")
    assert entry_names(some_other_dir.contents) == ["patate.txt", "tomate.vcf", "zucchini.json"]

    # file extension filter (include)
    res = client_s3.get("/tree?include=json")
    validate_filtered_tree(res.json(), ["zucchini.json"], ["some_dir", "some_other_dir"])

    # file extension filter (exclude)
    res = client_s3.get("/tree?ignore=txt&ignore=.json&ignore=.vcf")
    validate_filtered_tree(res.json(), [], [])

    # include and ignore filters cannot be used at the same time
    res = client_s3.get("/tree?include=txt&ignore=json")
    assert res.status_code == 400

    # subdir tree
    sub_tree = get_tree(client_s3, "/tree/some_dir")
    assert entry_names(sub_tree) == ["some_dir"]
    assert entry_names(get_directory(sub_tree, "some_dir").contents) == entry_names(some_dir.contents)


# TODO: fix inconsistent behavior between S3 and local backends
# This test covers the current behavior but should be changed, when we decide how it should behave.
# With s3 backend:      non existing subpath returns 200 with empty JSON
# With local backend:   non existing subpath returns 500
# Probably should be a 400 in both backends
def test_s3_tree_missing_prefix(client_s3: TestClient):
    assert get_tree(client_s3, "/tree/does_not_exist") == ()


def test_s3_download(client_s3: TestClient):
    upload_test_data(client_s3)
    expected = (test_data / "some_dir" / "patate.txt").read_bytes()

    res = client_s3.get("/objects/some_dir/patate.txt")
    assert res.status_code == 200
    assert res.content == expected
    assert res.headers["Content-Disposition"] == 'attachment; filename="patate.txt"'
    assert res.headers["Content-Length"] == str(len(expected))
    assert "ETag" in res.headers

    res = client_s3.post("/objects/some_dir/patate.txt", data={"token": "test"})
    assert res.status_code == 200
    assert res.content == expected


def test_s3_delete(client_s3: TestClient):
    upload_test_data(client_s3)

    res = client_s3.delete("/objects/patate.txt")
    assert res.status_code == 204

    assert "patate.txt" not in entry_names(get_tree(client_s3))
