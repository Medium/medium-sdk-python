# Copyright 2015 A Medium Corporation
from os.path import basename
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import requests

BASE_PATH = "https://api.medium.com"


class Client(object):
    """A client for the Medium OAuth2 REST API."""

    def __init__(self, application_id=None, application_secret=None,
                 access_token=None):
        self.application_id = application_id
        self.application_secret = application_secret
        self.access_token = access_token

    def get_authorization_url(self, state, redirect_url, scopes):
        """Get a URL for users to authorize the application.

        :param str state: A string that will be passed back to the redirect_url
        :param str redirect_url: The URL to redirect after authorization
        :param list scopes: The scopes to grant the application
        :returns: str
        """
        qs = {
            "client_id": self.application_id,
            "scope": ",".join(scopes),
            "state": state,
            "response_type": "code",
            "redirect_uri": redirect_url,
        }

        return "https://medium.com/m/oauth/authorize?" + urlencode(qs)

    def exchange_authorization_code(self, code, redirect_url):
        """Exchange the authorization code for a long-lived access token, and
        set the token on the current Client.

        :param str code: The code supplied to the redirect URL after a user
            authorizes the application
        :param str redirect_url: The same redirect URL used for authorizing
            the application
        :returns: A dictionary with the new authorizations ::
            {
                'token_type': 'Bearer',
                'access_token': '...',
                'expires_at': 1449441560773,
                'refresh_token': '...',
                'scope': ['basicProfile', 'publishPost']
            }
        """
        data = {
            "code": code,
            "client_id": self.application_id,
            "client_secret": self.application_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_url,
        }
        return self._request_and_set_auth_code(data)

    def exchange_refresh_token(self, refresh_token):
        """Exchange the supplied refresh token for a new access token, and
        set the token on the current Client.

        :param str refresh_token: The refresh token, as provided by
            ``exchange_authorization_code()``
        :returns: A dictionary with the new authorizations ::
            {
                'token_type': 'Bearer',
                'access_token': '...',
                'expires_at': 1449441560773,
                'refresh_token': '...',
                'scope': ['basicProfile', 'publishPost']
            }
        """
        data = {
            "refresh_token": refresh_token,
            "client_id": self.application_id,
            "client_secret": self.application_secret,
            "grant_type": "refresh_token",
        }
        return self._request_and_set_auth_code(data)

    def get_current_user(self):
        """Fetch the data for the currently authenticated user.

        Requires the ``basicProfile`` scope.

        :returns: A dictionary with the users data ::

            {
                'username': 'kylehg',
                'url': 'https://medium.com/@kylehg',
                'imageUrl': 'https://cdn-images-1.medium.com/...',
                'id': '1f86...',
                'name': 'Kyle Hardgrave'
            }
        """
        return self._request("GET", "/v1/me")

    def create_post(self, user_id, title, content, content_format, tags=None,
                    canonical_url=None, publish_status=None, license=None):
        """Create a post for the current user.

        Requires the ``publishPost`` scope.

        :param str user_id: The application-specific user ID as returned by
            ``get_current_user()``
        :param str title: The title of the post
        :param str content: The content of the post, in HTML or Markdown
        :param str content_format: The format of the post content, either
            ``html`` or ``markdown``
        :param list tags: (optional), List of tags for the post, max 3
        :param str canonical_url: (optional), A rel="canonical" link for
            the post
        :param str publish_status: (optional), What to publish the post as,
            either ``public``, ``unlisted``, or ``draft``. Defaults to
            ``public``.
        :param license: (optional), The license to publish the post under:
            - ``all-rights-reserved`` (default)
            - ``cc-40-by``
            - ``cc-40-by-sa``
            - ``cc-40-by-nd``
            - ``cc-40-by-nc``
            - ``cc-40-by-nc-nd``
            - ``cc-40-by-nc-sa``
            - ``cc-40-zero``
            - ``public-domain``
        :returns: A dictionary with the post data ::

            {
                'canonicalUrl': '',
                'license': 'all-rights-reserved',
                'title': 'My Title',
                'url': 'https://medium.com/@kylehg/55050649c95',
                'tags': ['python', 'is', 'great'],
                'authorId': '1f86...',
                'publishStatus': 'draft',
                'id': '55050649c95'
            }
        """
        data = {
            "title": title,
            "content": content,
            "contentFormat": content_format,
        }
        if tags is not None:
            data["tags"] = tags
        if canonical_url is not None:
            data["canonicalUrl"] = canonical_url
        if publish_status is not None:
            data["publishStatus"] = publish_status
        if license is not None:
            data["license"] = license

        path = "/v1/users/%s/posts" % user_id
        return self._request("POST", path, json=data)

    def upload_image(self, file_path, content_type):
        """Upload a local image to Medium for use in a post.

        Requires the ``uploadImage`` scope.

        :param str file_path: The file path of the image
        :param str content_type: The type of the image. Valid values are
            ``image/jpeg``, ``image/png``, ``image/gif``, and ``image/tiff``.
        :returns: A dictionary with the image data ::

            {
                'url': 'https://cdn-images-1.medium.com/0*dlkfjalksdjfl.jpg',
                'md5': 'd87e1628ca597d386e8b3e25de3a18b8'
            }
        """
        with open(file_path, "rb") as f:
            filename = basename(file_path)
            files = {"image": (filename, f, content_type)}
            return self._request("POST", "/v1/images", files=files)

    def _request_and_set_auth_code(self, data):
        """Request an access token and set it on the current client."""
        result = self._request("POST", "/v1/tokens", form_data=data)
        self.access_token = result["access_token"]
        return result

    def _request(self, method, path, json=None, form_data=None, files=None):
        """Make a signed request to the given route."""
        url = BASE_PATH + path
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "Authorization": "Bearer %s" % self.access_token,
        }

        resp = requests.request(method, url, json=json, data=form_data,
                                files=files, headers=headers)
        json = resp.json()
        if 200 <= resp.status_code < 300:
            try:
                return json["data"]
            except KeyError:
                return json

        raise MediumError("API request failed", json)


class MediumError(Exception):
    """Wrapper for exceptions generated by the Medium API."""

    def __init__(self, message, resp={}):
        self.resp = resp
        try:
            error = resp["errors"][0]
        except KeyError:
            error = {}
        self.code = error.get("code", -1)
        self.msg = error.get("message", message)
        super(MediumError, self).__init__(self.msg)
