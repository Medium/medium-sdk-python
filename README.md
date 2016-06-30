# Medium SDK for Python

This repository contains the open source SDK for integrating
[Medium](https://medium.com/)'s OAuth2 REST API with your Python app.

For full API documentation, see our [developer docs](https://github.com/Medium/medium-api-docs).

## Installing dependencies

To install dependencies using pip:

```
pip install -r requirements.txt
```

## Usage

```python
from medium import Client

# Go to http://medium.com/me/applications to get your application_id and application_secret.
client = Client(application_id="MY_APPLICATION_ID", application_secret="MY_APPLICATION_SECRET")

# Build the URL where you can send the user to obtain an authorization code.
auth_url = client.get_authorization_url("secretstate", "https://yoursite.com/callback/medium",
                                        ["basicProfile", "publishPost"])

# (Send the user to the authorization URL to obtain an authorization code.)

# Exchange the authorization code for an access token.
auth = client.exchange_authorization_code("YOUR_AUTHORIZATION_CODE",
                                          "https://yoursite.com/callback/medium")

# The access token is automatically set on the client for you after
# a successful exchange, but if you already have a token, you can set it
# directly.
client.access_token = auth["access_token"]

# Get profile details of the user identified by the access token.
user = client.get_current_user()

# Create a draft post.
post = client.create_post(user_id=user["id"], title="Title", content="<h2>Title</h2><p>Content</p>",
                          content_format="html", publish_status="draft")

# When your access token expires, use the refresh token to get a new one.
client.exchange_refresh_token(auth["refresh_token"])

# Confirm everything went ok. post["url"] has the location of the created post.
print "My new post!", post["url"]
```

## Running tests

To run tests against this package, first install the test requirements and make
sure that the `medium` package is exportable. (We recommend using virtualenv.)

```bash
$ pip install -r tests/requirements.txt
$ pip install -e .
```

Then run the primary test file:

```bash
$ python tests/test.py
```

## Contributing

Questions, comments, bug reports, and pull requests are all welcomed. If you
haven't contributed to a Medium project before please head over to the [Open
Source Project](https://github.com/Medium/opensource#note-to-external-contributors)
and fill out an OCLA (it should be pretty painless).

## Authors

- [Kyle Hardgrave](https://github.com/kylehg)

## License

Copyright 2015 [A Medium Corporation](https://medium.com/)

Licensed under Apache License Version 2.0. Details in the attached LICENSE file.
