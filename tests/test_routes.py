from fastapi import Response
from fastapi.testclient import TestClient
from bento_drop_box_service.backends.base import DropBoxEntry


def validate_tree(tree: list[DropBoxEntry]):
    assert len(tree) == 4
    root_expected_names = ["tomate.vcf", "zucchini.json", "patate.txt", "some_dir"]
    some_dir_expected_names = ["tomate.vcf", "zucchini.json", "patate.txt", "some_other_dir", "empty_dir"]
    some_other_dir_expected_names = ["tomate.vcf", "zucchini.json", "patate.txt"]

    root_names = [entry["name"] for entry in tree]
    assert sorted(root_names) == sorted(root_expected_names)

    some_dir = next((entry for entry in tree if entry["name"] == "some_dir"), None)
    some_dir_names = [entry["name"] for entry in some_dir["contents"]]
    assert sorted(some_dir_names) == sorted(some_dir_expected_names)

    some_other_dir = next((entry for entry in some_dir["contents"] if entry["name"] == "some_other_dir"), None)
    some_other_dir_names = [entry["name"] for entry in some_other_dir["contents"]]
    assert sorted(some_other_dir_names) == sorted(some_other_dir_expected_names)


def validate_subtree_some_dir(tree: list[DropBoxEntry]):
    assert len(tree) == 5
    some_dir_expected_names = ["tomate.vcf", "zucchini.json", "patate.txt", "some_other_dir", "empty_dir"]
    some_dir_names = [entry["name"] for entry in tree]
    assert sorted(some_dir_names) == sorted(some_dir_expected_names)


def validate_filtered_tree(tree: list[DropBoxEntry], expected_files: list[str], expected_directories: list[str]):
    if not expected_files:
        assert len(tree) == 0
    else:
        for node in tree:
            if node.get("uri"):
                # entry for a file
                assert node["name"] in expected_files
            else:
                # else directory
                assert node["name"] in expected_directories
                assert node["name"] != "empty_dir"
                if child_contents := node.get("contents"):
                    validate_filtered_tree(child_contents, expected_files, expected_directories)


def test_service_info(client_local: TestClient):
    res = client_local.get("/service-info")
    data = res.json()

    assert res.status_code == 200
    assert "name" in data
    assert "type" in data


def test_tree_local(client_local: TestClient):
    res = client_local.get("/tree")
    assert res.status_code == 200
    validate_tree(res.json())

    res = client_local.get("/tree?include=json")
    validate_filtered_tree(res.json(), ["zucchini.json"], ["some_dir", "some_other_dir"])

    res = client_local.get("/tree?include=json&include=.vcf")
    validate_filtered_tree(res.json(), ["tomate.vcf", "zucchini.json"], ["some_dir", "some_other_dir"])

    res = client_local.get("/tree?ignore=txt")
    validate_filtered_tree(res.json(), ["tomate.vcf", "zucchini.json"], ["some_dir", "some_other_dir"])

    res = client_local.get("/tree?ignore=txt&ignore=.json&ignore=.vcf")
    validate_filtered_tree(res.json(), [], [])

    res = client_local.get("/tree?include=txt&ignore=json")
    assert res.status_code == 400


def test_tree_subpath_local(client_local: TestClient):
    res = client_local.get("/tree/some_dir")
    assert res.status_code == 200
    validate_subtree_some_dir(res.json())

    res = client_local.get("/tree/some_dir?include=json")
    validate_filtered_tree(res.json(), ["zucchini.json"], ["some_other_dir"])

    res = client_local.get("/tree/some_dir?ignore=txt")
    validate_filtered_tree(res.json(), ["tomate.vcf", "zucchini.json"], ["some_other_dir"])

    res = client_local.get("/tree/some_dir?include=txt&ignore=json")
    assert res.status_code == 400


def test_object_download_local(client_local: TestClient):
    res = client_local.get("/objects/patate.txt")
    assert res.status_code == 200

    res = client_local.get("/objects/some_dir/some_other_dir/patate.txt")
    assert res.status_code == 200

    res = client_local.post("/objects/patate.txt", data={"token": "test"})
    assert res.status_code == 200

    res = client_local.post("/objects/some_dir/some_other_dir/patate.txt", data={"token": "test"})
    assert res.status_code == 200


def test_object_download_local_404(client_local: TestClient):
    res = client_local.get("/objects/peel.txt")
    assert res.status_code == 404

    res = client_local.get("/objects/some_dir/some_other_dir/peel.txt")
    assert res.status_code == 404

    res = client_local.get("/objects/some_dir/empty_dir/patate.txt")
    assert res.status_code == 404


def test_object_download_local_file_as_dir(client_local: TestClient):
    res = client_local.get("/objects/patate.txt/tuber")
    assert res.status_code == 400


def test_folder_download_error_local(client_local: TestClient):
    res = client_local.get("/objects/some_dir/")
    assert res.status_code == 400
