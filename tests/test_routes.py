def validate_tree(res):
    tree = res.get_json()

    assert res.status_code == 200
    assert len(tree) == 2
    assert tree[0]['name'] == 'patate.txt'
    assert 'contents' in tree[1]


def test_tree_minio(client_minio):
    res = client_minio.get("/tree")

    validate_tree(res)


def test_object_download_minio(client_minio):
    res = client_minio.get("/objects/patate.txt")

    assert res.status_code == 200


def test_service_info(client_minio):
    res = client_minio.get("/service-info")
    data = res.get_json()

    assert res.status_code == 200
    assert 'name' in data
    assert 'type' in data


def test_tree_local(client_local):
    res = client_local.get("/tree")

    validate_tree(res)


def test_object_download_local(client_local):
    res = client_local.get("/objects/patate.txt")

    assert res.status_code == 200
