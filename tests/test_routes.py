from fastapi import Response
from bento_drop_box_service.config import Config


def validate_tree(res: Response):
    tree = res.json()

    assert res.status_code == 200
    assert len(tree) == 4
    assert tree[0]["name"] == "patate.txt"
    assert "contents" in tree[1]


def validate_subtree(res: Response):
    tree = res.json()

    assert res.status_code == 200
    assert len(tree) == 5
    assert tree[1]["name"] == "patate.txt"
    assert "contents" in tree[0]
    assert "contents" in tree[2]


def validate_filtered_tree(res: Response, expected_files: list[str], num_directories: int = 1):
    tree = res.json()

    assert res.status_code == 200
    assert len(tree) == num_directories + len(expected_files)

    for index in range(len(expected_files)):
        assert tree[index + num_directories]["name"] == expected_files[index]

    for dir in tree[0]["contents"]:
        assert dir["name"] in expected_files or "empty_dir"


def test_service_info(client_local: Config):
    res = client_local.get("/service-info")
    data = res.json()

    assert res.status_code == 200
    assert "name" in data
    assert "type" in data


def test_tree_local(client_local: Config):
    res = client_local.get("/tree")
    validate_tree(res)

    res = client_local.get("/tree?include=json")
    validate_filtered_tree(res, ["zucchini.json"])

    res = client_local.get("/tree?include=json&include=.vcf")
    validate_filtered_tree(res, ["tomate.vcf", "zucchini.json"])

    res = client_local.get("/tree?ignore=txt")
    validate_filtered_tree(res, ["tomate.vcf", "zucchini.json"])

    res = client_local.get("/tree?ignore=txt&ignore=.json&ignore=.vcf")
    validate_filtered_tree(res, [])

    res = client_local.get("/tree?include=txt&ignore=json")
    assert res.status_code == 400


def test_tree_subpath_local(client_local: Config):
    res = client_local.get("/tree/some_dir")
    validate_subtree(res)

    res = client_local.get("/tree/some_dir?include=json")
    validate_filtered_tree(res, ["zucchini.json"], 2)

    res = client_local.get("/tree/some_dir?ignore=txt")
    validate_filtered_tree(res, ["tomate.vcf", "zucchini.json"], 2)

    res = client_local.get("/tree/some_dir?include=txt&ignore=json")
    assert res.status_code == 400


def test_object_download_local(client_local: Config):
    res = client_local.get("/objects/patate.txt")
    assert res.status_code == 200

    res = client_local.get("/objects/some_dir/some_other_dir/patate.txt")
    assert res.status_code == 200

    res = client_local.post("/objects/patate.txt", data={"token": "test"})
    assert res.status_code == 200

    res = client_local.post("/objects/some_dir/some_other_dir/patate.txt", data={"token": "test"})
    assert res.status_code == 200


def test_object_download_local_404(client_local: Config):
    res = client_local.get("/objects/peel.txt")
    assert res.status_code == 404

    res = client_local.get("/objects/some_dir/some_other_dir/peel.txt")
    assert res.status_code == 404

    res = client_local.get("/objects/some_dir/empty_dir/patate.txt")
    assert res.status_code == 404


def test_object_download_local_file_as_dir(client_local: Config):
    res = client_local.get("/objects/patate.txt/tuber")
    assert res.status_code == 400


def test_folder_download_error_local(client_local: Config):
    res = client_local.get("/objects/some_dir/")
    assert res.status_code == 400
