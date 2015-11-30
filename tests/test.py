# Copyright 2015 A Medium Corporation
import json
import unittest
try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

import requests
import responses

from medium import Client

class TestClient(unittest.TestCase):

    def setUp(self):
        self.client = Client(access_token="myaccesstoken")

    @responses.activate
    def test_exchange_authorization_code(self):
        def response_callback(payload):
            self.assertEqual(payload["code"][0], "mycode")
            self.assertEqual(payload["client_id"][0], "myclientid")
            self.assertEqual(payload["client_secret"][0], "myclientsecret")
            self.assertEqual(payload["grant_type"][0], "authorization_code")
            self.assertEqual(payload["redirect_uri"][0],
                             "http://example.com/cb")
            data = {
                "token_type": "Bearer",
                "access_token": "myaccesstoken",
                "expires_at": 4575744000000,
                "refresh_token": "myrefreshtoken",
                "scope": ["basicProfile"],
            }
            return (201, data)
        self._mock_endpoint("POST", "/v1/tokens", response_callback,
                            is_json=False)

        client = Client(application_id="myclientid",
                        application_secret="myclientsecret")

        # TODO(kyle) Remove after Ceasar's refactoring
        resp = client.exchange_authorization_code("mycode",
                                                  "http://example.com/cb")
        self.assertEqual(resp["access_token"], "myaccesstoken")
        self.assertEqual(resp["refresh_token"], "myrefreshtoken")
        self.assertEqual(resp["scope"], ["basicProfile"])

        # TODO(kyle) Uncomment after Ceasar's refactoring
        # client.exchange_authorization_code("mycode", "http://example.com/cb")
        # self.assertEqual(client.access_token, "myaccesstoken")
        # self.assertEqual(client.refresh_token, "myrefreshtoken")

    @responses.activate
    def test_exchange_refresh_token(self):
        def response_callback(payload):
            self.assertEqual(payload["refresh_token"][0], "myrefreshtoken")
            self.assertEqual(payload["client_id"][0], "myclientid")
            self.assertEqual(payload["client_secret"][0], "myclientsecret")
            self.assertEqual(payload["grant_type"][0], "refresh_token")
            data = {
                "token_type": "Bearer",
                "access_token": "myaccesstoken2",
                "expires_at": 4575744000000,
                "refresh_token": "myrefreshtoken2",
                "scope": ["basicProfile"],
            }
            return (201, data)
        self._mock_endpoint("POST", "/v1/tokens", response_callback,
                            is_json=False)

        client = Client(application_id="myclientid",
                        application_secret="myclientsecret")

        # TODO(kyle) Remove after Ceasar's refactoring
        resp = client.exchange_refresh_token("myrefreshtoken")
        self.assertEqual(resp["access_token"], "myaccesstoken2")
        self.assertEqual(resp["refresh_token"], "myrefreshtoken2")
        self.assertEqual(resp["scope"], ["basicProfile"])

        # TODO(kyle) Uncomment after Ceasar's refactoring
        # client.exchange_refresh_token("myrefreshtoken")
        # self.assertEqual(client.access_token, "myaccesstoken2")
        # self.assertEqual(client.refresh_token, "myrefreshtoken2")

    @responses.activate
    def test_get_current_user(self):
        def response_callback(payload):
            data = {
                "username": "nicki",
                "url": "https://medium.com/@nicki",
                "imageUrl": "https://images.medium.com/0*fkfQiTzT7TlUGGyI.png",
                "id": "5303d74c64f66366f00cb9b2a94f3251bf5",
                "name": "Nicki Minaj",
            }
            return 200, data
        self._mock_endpoint("GET", "/v1/me", response_callback)

        resp = self.client.get_current_user()
        self.assertEqual(resp, {
            "username": "nicki",
            "url": "https://medium.com/@nicki",
            "imageUrl": "https://images.medium.com/0*fkfQiTzT7TlUGGyI.png",
            "id": "5303d74c64f66366f00cb9b2a94f3251bf5",
            "name": "Nicki Minaj",
        })

    @responses.activate
    def test_create_post(self):
        def response_callback(payload):
            self.assertEqual(payload, {
                "title": "Starships",
                "content": "<p>Are meant to flyyyy</p>",
                "contentFormat": "html",
                "tags": ["stars", "ships", "pop"],
                "publishStatus": "draft",
            })

            data = {
                "license": "all-rights-reserved",
                "title": "Starships",
                "url": "https://medium.com/@nicki/55050649c95",
                "tags": ["stars", "ships", "pop"],
                "authorId": "5303d74c64f66366f00cb9b2a94f3251bf5",
                "publishStatus": "draft",
                "id": "55050649c95",
            }
            return 200, data
        self._mock_endpoint(
            "POST",
            "/v1/users/5303d74c64f66366f00cb9b2a94f3251bf5/posts",
            response_callback
        )

        resp = self.client.create_post(
            "5303d74c64f66366f00cb9b2a94f3251bf5",
            "Starships",
            "<p>Are meant to flyyyy</p>",
            "html",
            tags=["stars", "ships", "pop"],
            publish_status="draft"
        )
        self.assertEqual(resp, {
            "license": "all-rights-reserved",
            "title": "Starships",
            "url": "https://medium.com/@nicki/55050649c95",
            "tags": ["stars", "ships", "pop"],
            "authorId": "5303d74c64f66366f00cb9b2a94f3251bf5",
            "publishStatus": "draft",
            "id": "55050649c95",
        })

    @responses.activate
    def test_upload_image(self):
        def response_callback(req):
            self.assertEqual(req.headers["Authorization"],
                             "Bearer myaccesstoken")
            self.assertIn(b"Content-Type: image/png", req.body)
            return 200, {}, json.dumps({
                "url": "https://cdn-images-1.medium.com/0*dlkfjalksdjfl.jpg",
                "md5": "d87e1628ca597d386e8b3e25de3a18bc",
            })
        responses.add_callback(responses.POST, "https://api.medium.com/v1/images",
                               content_type="application/json",
                               callback=response_callback)

        resp = self.client.upload_image("./tests/test.png", "image/png")
        self.assertEqual(resp, {
            "url": "https://cdn-images-1.medium.com/0*dlkfjalksdjfl.jpg",
            "md5": "d87e1628ca597d386e8b3e25de3a18bc",
        })

    def _mock_endpoint(self, method, path, callback, is_json=True):
        def wrapped_callback(req):
            if is_json:
                self.assertEqual(req.headers["Authorization"],
                                 "Bearer myaccesstoken")
            if req.body is not None:
                body = json.loads(req.body) if is_json else parse_qs(req.body)
            else:
                body = None
            status, data = callback(body)
            return (status, {}, json.dumps(data))
        response_method = responses.GET if method == "GET" else responses.POST
        url = "https://api.medium.com" + path
        content_type = ("application/json" if is_json else
                        "application/x-www-form-urlencoded")
        responses.add_callback(response_method, url, content_type=content_type,
                               callback=wrapped_callback)


if __name__ == "__main__":
    unittest.main()
