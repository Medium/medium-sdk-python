# Medium SDK for Python

This repository contains the open source SDK for integrating
[Medium](https://medium.com/)'s OAuth2 REST API with your Python app.

For full API documentation, see our [developer docs](https://github.com/Medium/medium-api-docs).

## Usage



To use the client, you first need to obtain an access token, which requires
an authorization code from the user. Send them to the URL given by
``Client.get_authorization_url()`` and then have them enter their
authorization code to exchange it for an access token.

```python
from medium import Client

# Contact developers@medium.com to get your application_kd and application_secret.
client = Client(application_id="MY_APPLICATION_ID",
                application_secret="MY_APPLICATION_SECRET")

# Obtain an access token, by sending the user to the authorization URL and
# exchanging their authorization code for an access token.

redirect_url = "https://yoursite.com/callback/medium"
authorize_url = client.get_authorization_url(
    state="secretstate",
    redirect_url=redirect_url,
    scopes=["basicProfile", "publishPost"]
)
print 'Go to: {}'.format(authorize_url)
print 'Copy the authorization code.'
authorization_code = raw_input('Enter the authorization code here: ')
client.exchange_authorization_code(authorization_code, redirect_url)

# Now that you have an access token, you can use the rest of the client's
# methods. For example, to get the profile details of user identified by the
# access token:

print client.get_current_user()

# And to create a draft post:

post = client.create_post(
    user_id=user["id"],
    title="Title",
    content="<h2>Title</h2><p>Content</p>",
    content_format="html", publish_status="draft"
)
print "My new post!", post["url"]
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
