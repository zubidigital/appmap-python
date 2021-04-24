# flake8: noqa: E402
# pylint: disable=unused-import, redefined-outer-name

import pytest

from .appmap_test_base import AppMapTestBase

pytest.importorskip('django')

import django.conf
import django.db
import django.test
import appmap.django  # noqa: F401


# Note that with django configured this way, django.test.Client
# requests for '/test' will print warning messages that look like
# `WARNING:django.request:Not Found: /test`. These don't appear to
# indicate a problem.
django.conf.settings.configure(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    ROOT_URLCONF=()
)


class TestDjango(AppMapTestBase):
    def test_sql_capture(self, events):
        conn = django.db.connections['default']
        conn.cursor().execute('SELECT 1').fetchall()

        assert events[0].sql_query['sql'] == 'SELECT 1'


    def test_http_capture(self, events):
        client = django.test.Client()
        client.get('/test')

        assert events[0].http_server_request.items() >= {
            'request_method': 'GET',
            'path_info': '/test',
            'protocol': 'HTTP/1.1'
        }.items()

        assert events[1].http_server_response == {
            'status_code': 404,
            'mime_type': 'text/html'
        }


    def test_message_capture_post(self, events):
        client = django.test.Client()
        client.post('/test', { 'my_param': 'example' },
            content_type='application/json; charset=UTF-8',
            HTTP_AUTHORIZATION='token "test-token"',
            HTTP_ACCEPT='application/json',
            HTTP_ACCEPT_LANGUAGE='pl'
        )

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.str',
                'object_id': events[0].message[0]['object_id'],
                'value': "'example'"
            }
        ]
        assert events[0].http_server_request.items() >= {
            'request_method': 'POST',
            'path_info': '/test',
            'protocol': 'HTTP/1.1',
            'authorization': 'token "test-token"',
            'mime_type': 'application/json; charset=UTF-8',
        }.items()

        assert events[0].http_server_request['headers'].items() >= {
            'Accept': 'application/json',
            'Accept-Language': 'pl'
        }.items()

    def test_message_capture_get(self, events):
        client = django.test.Client()
        client.get('/test', { 'my_param': 'example' })

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.str',
                'object_id': events[0].message[0]['object_id'],
                'value': "'example'"
            }
        ]

    def test_message_capture_get_arr(self, events):
        client = django.test.Client()
        client.get('/test', { 'my_param': ['example', 'example2'] })

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.list',
                'object_id': events[0].message[0]['object_id'],
                'value': "['example', 'example2']"
            },
        ]


    def test_message_capture_post_form_urlencoded(self, events):
        client = django.test.Client()
        client.post('/test', 'my_param=example', content_type='application/x-www-form-urlencoded')

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.str',
                'object_id': events[0].message[0]['object_id'],
                'value': "'example'"
            }
        ]

    def test_message_capture_put(self, events):
        client = django.test.Client()
        client.put('/test', { 'my_param': 'example' }, content_type='application/json')

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.str',
                'object_id': events[0].message[0]['object_id'],
                'value': "'example'"
            }
        ]


    def test_message_capture_post_bad_json(self, events):
        client = django.test.Client()
        client.post('/test?my_param=example', "bad json", content_type='application/json')

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.str',
                'object_id': events[0].message[0]['object_id'],
                'value': "'example'"
            }
        ]


    def test_message_capture_post_multipart(self, events):
        client = django.test.Client()
        client.post('/test', { 'my_param': 'example' })

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.str',
                'object_id': events[0].message[0]['object_id'],
                'value': "'example'"
            }
        ]


    def test_message_capture_post_with_query(self, events):
        client = django.test.Client()
        client.post('/test?my_param=get', { 'my_param': 'example' })

        assert events[0].message == [
            {
                'name': 'my_param',
                'class': 'builtins.list',
                'object_id': events[0].message[0]['object_id'],
                'value': "['get', 'example']"
            }
        ]
