# Copyright 2015 A Medium Corporation
from os.path import basename
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import requests


def _request(method, path, access_token, json=None, form_data=None,
             files=None):
    """Make a signed request to the given route."""
    url = "https://api.medium.com/v1" + path
    headers = {
        "Accept": "application/json",
        "Accept-Charset": "utf-8",
        "Authorization": "Bearer {}".format(access_token),
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


class Client(object):
    """
    A client for the Medium OAuth2 REST API.

    >>> client = Client(application_id="MY_APPLICATION_ID",
    ...                 application_secret="MY_APPLICATION_SECRET")

    To use the client, you first need to obtain an access token, which requires
    an authorization code from the user. Send them to the URL given by
    ``Client.get_authorization_url()`` and then have them enter their
    authorization code to exchange it for an access token.

    >>> client.access_token
    None
    >>> redirect_url = "https://yoursite.com/callback/medium"
    >>> authorize_url = client.get_authorization_url(
    ...     state="secretstate",
    ...     redirect_url=redirect_url,
    ...     scopes=["basicProfile", "publishPost"]
    ... )
    >>> print 'Go to: {}'.format(authorize_url)
    Go to: https://medium.com/m/oauth/authorize?scope=basicProfile%2Cpublish...
    >>> print 'Copy the authorization code.'
    Copy the authorization code.
    >>> authorization_code = raw_input('Enter the authorization code here: ')
    >>> client.exchange_authorization_code(authorization_code, redirect_url)
    >>> client.access_token
    ...

    The access token will expire after some time. To refresh it:

    >>> client.exchange_refresh_token()

    Once you have an access token, you can use the rest of the client's
    methods. For example, to get the profile details of user identified by the
    access token:

    >>> user = client.get_current_user()

    And to create a draft post:

    >>> post = client.create_post(
    ...     user_id=user["id"],
    ...     title="Title",
    ...     content="<h2>Title</h2><p>Content</p>",
    ...     content_format="html", publish_status="draft"
    ... )

    """
    def __init__(self, application_id=None, application_secret=None,
                 access_token=None, refresh_token=None):
        self.application_id = application_id
        self.application_secret = application_secret
        self.access_token = access_token
        self.refresh_token = refresh_token

    def get_authorization_url(self, state, redirect_url, scopes):
        """Get a URL for users to authorize the application.

        :param str state:
            A string that will be passed back to the redirect_url
        :param str redirect_url:
            The URL to redirect after authorization
        :param list scopes:
            The scopes to grant the application
        :returns: str
        """
        return "https://medium.com/m/oauth/authorize?" + urlencode({
            "client_id": self.application_id,
            "response_type": "code",
            "redirect_uri": redirect_url,
            "scope": ",".join(scopes),
            "state": state,
        })

    def _get_tokens(self, **kwargs):
        return _request('POST', '/tokens', self.access_token, **kwargs)

    def exchange_authorization_code(self, code, redirect_url):
        """
        Exchange the authorization code for a long-lived access token, and set
        both the access token and refresh on the current Client.

        :param str code:
            The code supplied to the redirect URL after a user authorizes the
            application.
        :param str redirect_url:
            The same redirect URL used for authorizing the application.
        """
        tokens = self._get_tokens(form_data={
            "client_id": self.application_id,
            "client_secret": self.application_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_url,
        })
        self.access_token = tokens['access_token']
        self.refresh_token = tokens['refresh_token']

    def exchange_refresh_token(self):
        """
        Exchange the supplied refresh token for a new access token, and set the
        token on the current Client.
        """
        self.access_token = self._get_tokens(form_data={
            "client_id": self.application_id,
            "client_secret": self.application_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        })['access_token']

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
        return _request("GET", "/me", self.access_token)

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
        json = {
            "title": title,
            "content": content,
            "contentFormat": content_format,
        }
        if tags is not None:
            json["tags"] = tags
        if canonical_url is not None:
            json["canonicalUrl"] = canonical_url
        if publish_status is not None:
            json["publishStatus"] = publish_status
        if license is not None:
            json["license"] = license

        return _request("POST", "/users/{}/posts".format(user_id),
                        self.access_token, json=json)

    def upload_image(self, file_path, content_type):
        """Upload a local image to Medium for use in a post.

        Requires the ``uploadImage`` scope.

        :param str file_path:
            The file path of the image
        :param str content_type:
            The type of the image. Valid values are
            ``image/jpeg``, ``image/png``, ``image/gif``, and ``image/tiff``.
        :returns: A dictionary with the image data::

            {
                'url': 'https://cdn-images-1.medium.com/0*dlkfjalksdjfl.jpg',
                'md5': 'd87e1628ca597d386e8b3e25de3a18b8'
            }
        """
        with open(file_path, "rb") as f:
            return _request("POST", "/images", self.access_token, files={
                "image": (basename(file_path), f, content_type)
            })


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
