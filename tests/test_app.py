import pytest
from page_analyzer.app import app


def test_index_route():
    response = app.test_client().get('/')
    assert response.status_code == 200


def test_urls_route():
    response = app.test_client().get('/urls')
    assert response.status_code == 200


# from werkzeug.test import Client
# from werkzeug.testapp import test_app


# @pytest.fixture()
# def app_fixture():
#    app.config.update({"TESTING": True, })

    # other setup can go here

#    yield app

    # clean up / reset resources here


# @pytest.fixture()
# def client(app_fixture):
#    return app_fixture.test_client()


# @pytest.fixture()
# def runner(app_fixture):
#    return app_fixture.test_cli_runner()


# @pytest.fixture()
# def client():
#    return Client(test_app)


# def test_request(client):
#    response = client.get("/")
#    assert response.status_code == 200
#    assert b"<h2>Hello, World!</h2>" in response.data


def test_test():
    # TODO Нужно добавить тесты
    assert True
