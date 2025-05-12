def validate_tree(res):
    tree = res.json()

    assert res.status_code == 200
    assert len(tree) == 2
    assert tree[0]["name"] == "patate.txt"
    assert "contents" in tree[1]


def validate_empty_tree(res):
    tree = res.json()

    assert res.status_code == 200
    assert len(tree) == 1
    assert "contents" in tree[0]
    assert tree[0]["name"] == "some_dir"
    for dir in tree[0]["contents"]:
        assert dir["contents"] == []


def test_service_info(client_local):
    res = client_local.get("/service-info")
    data = res.json()

    assert res.status_code == 200
    assert "name" in data
    assert "type" in data


def test_tree_local(client_local):
    res = client_local.get("/tree")
    validate_tree(res)

    res = client_local.get("/tree?include=txt")
    validate_tree(res)

    res = client_local.get("/tree?ignore=txt")
    validate_empty_tree(res)

    res = client_local.get("/tree?include=txt&ignore=json")
    assert res.status_code == 400


def test_object_download_local(client_local):
    res = client_local.get("/objects/patate.txt")
    assert res.status_code == 200

    res = client_local.get("/objects/some_dir/some_other_dir/patate.txt")
    assert res.status_code == 200

    res = client_local.post("/objects/patate.txt", data={"token": "test"})
    assert res.status_code == 200

    res = client_local.post("/objects/some_dir/some_other_dir/patate.txt", data={"token": "test"})
    assert res.status_code == 200


def test_object_download_local_404(client_local):
    res = client_local.get("/objects/peel.txt")
    assert res.status_code == 404

    res = client_local.get("/objects/some_dir/some_other_dir/peel.txt")
    assert res.status_code == 404

    res = client_local.get("/objects/some_dir/empty_dir/patate.txt")
    assert res.status_code == 404


def test_object_download_local_file_as_dir(client_local):
    res = client_local.get("/objects/patate.txt/tuber")
    assert res.status_code == 400


def test_folder_download_error_local(client_local):
    res = client_local.get("/objects/some_dir/")
    assert res.status_code == 400
