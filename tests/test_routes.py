import pytest


@pytest.mark.asyncio
async def validate_tree(res):
    tree = await res.get_json()

    assert res.status_code == 200
    assert len(tree) == 2
    assert tree[0]['name'] == 'patate.txt'
    assert 'contents' in tree[1]


@pytest.mark.asyncio
async def test_tree_minio(client_minio):
    res = await client_minio.get("/tree")

    await validate_tree(res)


@pytest.mark.asyncio
async def test_object_download_minio(client_minio):
    res = await client_minio.get("/objects/patate.txt")

    assert res.status_code == 200


@pytest.mark.asyncio
async def test_service_info(client_local):
    res = await client_local.get("/service-info")
    data = await res.get_json()

    assert res.status_code == 200
    assert 'name' in data
    assert 'type' in data


@pytest.mark.asyncio
async def test_tree_local(client_local):
    res = await client_local.get("/tree")

    await validate_tree(res)


@pytest.mark.asyncio
async def test_object_download_local(client_local):
    res = await client_local.get("/objects/patate.txt")
    assert res.status_code == 200

    res = await client_local.get("/objects/some_dir/some_other_dir/patate.txt")
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_object_download_local_404(client_local):
    res = await client_local.get("/objects/peel.txt")
    assert res.status_code == 404

    res = await client_local.get("/objects/some_dir/some_other_dir/peel.txt")
    assert res.status_code == 404

    res = await client_local.get("/objects/some_dir/empty_dir/patate.txt")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_object_download_local_file_as_dir(client_local):
    res = await client_local.get("/objects/patate.txt/tuber")
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_folder_download_error_local(client_local):
    res = await client_local.get("/objects/some_dir/")
    assert res.status_code == 400
