from pathlib import Path

import keyring
import typer

from medium import Client, MediumError

client = Client()

app = typer.Typer(
    name="medium",
    help="A CLI app for the Medium API using the Medium Python SDK",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=True
)

config_app = typer.Typer(name="config",
                         help="Configuration of Medium CLI",
                         add_completion=False,
                         add_help_option=True,
                         no_args_is_help=True)

app.add_typer(config_app, name="config", help="Configuration of Medium CLI")


@config_app.command()
def set_token(token: str) -> None:
    """
    Sets the access token for the Medium CLI.

    Parameters:
        token (str): The access token to be set.

    Returns:
        None
    """
    keyring.set_password("medium_cli", "access_token", token)
    typer.echo("Token set successfully")


@config_app.command()
def get_token() -> str:
    """
    Retrieves the access token from the keyring and returns it.

    Raises:
        AssertionError: If the access token is not set.

    Returns:
        str: The access token.
    """
    token = keyring.get_password("medium_cli", "access_token")
    assert token, "Token not set. Please run `medium config set-token`"

    typer.echo(f"Token: {token}")
    return token


@config_app.command()
def rm_token() -> None:
    """
    Removes the access token from the keyring.

    Returns:
        None
    """
    keyring.delete_password("medium_cli", "access_token")

    typer.echo("Token removed successfully")


@app.command()
def get_user(token: str = typer.Option(None, "--token", "-T",
                                       help="Optionally pass the self-issued access token directly")) -> dict:
    """
    Retrieves the current user's information from the Medium API.

    Parameters:
        token (str, optional): Optionally pass the self-issued access token directly. Defaults to None.

    Raises:
        AssertionError: If the access token is not set.
        MediumError: If there is an error retrieving the user's information.

    Returns:
        dict: The user's information.
    """
    client.access_token = keyring.get_password("medium_cli", "access_token") if not token else token
    assert client.access_token, "Access token not set. Please run `medium config set-token`"

    try:
        resp = client.get_current_user()
        typer.echo(f"Authenticated as {resp['name']}")
        return resp
    except MediumError as e:
        typer.echo(f"Error: {e}")
        raise typer.Abort()


@app.command()
def upload_image(image: str, token: str = typer.Option(None, "--token", "-T",
                                                       help="Optionally pass the self-issued access token directly")) -> dict:
    """
    Uploads an image to the Medium API.

    Parameters:
        image (str): The path to the image to be uploaded.
        token (str, optional): Optionally pass the self-issued access token directly. Defaults to None.

    Raises:
        AssertionError: If the access token is not set, the image does not exist, or the image format is not supported.
        MediumError: If there is an error uploading the image.

    Returns:
        dict: The response from the Medium API.
    """
    client.access_token = keyring.get_password("medium_cli", "access_token") if not token else token
    assert client.access_token, "Access token not set. Please run `medium config set-token`"

    img_suffix = Path(image).suffix.lower()
    img_path = Path(image).resolve()

    assert img_path.exists(), "Image not found in provided path"

    assert img_suffix in [".png", ".jpg", ".jpeg", ".gif", ".tif",
                          ".tiff"], "Invalid image format. Supported formats are: png, jpg, jpeg, gif, tif, tiff"

    try:
        resp = client.upload_image(file_path=img_path.__str__(), content_type=f"image/{img_suffix[1:]}")
        typer.echo(f"Image uploaded successfully: {resp['url']}")
        return resp
    except MediumError as e:
        typer.echo(f"Error: {e}")
        raise typer.Abort()


@app.command()
def create_post(title: str = typer.Argument(..., help="Title of the post"),
                content: str = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True,
                                              resolve_path=True,
                                              help="Content of the post. Can be a string (raw content) or a file path "
                                                   "to an .html or .md file"),
                content_format: str = typer.Option(None, "--content-format", "-f",
                                                   help="Format of the content. Options: html, markdown"),
                canonical_url: str = typer.Option(None, "--canonical-url", "-c", help="Canonical URL of the post"),
                tags: str = typer.Option(None, "--tags", "-t", help="Comma-separated list of tags"),
                publish_status: str = typer.Option("public", "--publish-status", "-p",
                                                   help="Publish status of the post. Options: draft, public, unlisted"),
                license: str = typer.Option("all-rights-reserved", "--license", "-l",
                                            help="License to publish under. Options: all-rights-reserved (default), "
                                                 "cc-40-by, cc-40-by-sa, cc-40-by-nd, cc-40-by-nc, cc-40-by-nc-nd, "
                                                 "cc-40-by-nc-sa, cc-40-zero, public-domain"),
                token: str = typer.Option(None, "--token", "-T", 
                                          help="Optionally pass the self-issued access token directly")) -> dict:
    """
    Creates a post on Medium.

    Parameters: title (str): The title of the post. content (str): The content of the post. Can be a string (raw
    content) or a file path to an .html or .md file. content_format (str, optional): The format of the content.
    Options: html, markdown. Defaults to None. canonical_url (str, optional): The canonical URL of the post. Defaults
    to None. tags (str, optional): A comma-separated list of tags. Defaults to None. publish_status (str, optional):
    The publish status of the post. Options: draft, public, unlisted. Defaults to "public". license (str, optional):
    The license to publish under. Options: all-rights-reserved (default), cc-40-by, cc-40-by-sa, cc-40-by-nd,
    cc-40-by-nc, cc-40-by-nc-nd, cc-40-by-nc-sa, cc-40-zero, public-domain. Defaults to "all-rights-reserved".
    token (str, optional): Optionally pass the self-issued access token directly. Defaults to None.

    Raises: AssertionError: If the access token is not set, the content does not exist, or the content format is not
    supported. MediumError: If there is an error creating the post.

    Returns:
        dict: The response from the Medium API.
    """
    client.access_token = keyring.get_password("medium_cli", "access_token") if not token else token
    assert client.access_token, "Access token not set. Please run `medium config set-token`"

    if Path(content).exists():
        content = Path(content).resolve()
        content_format = content.suffix.lower() if content_format is None else content_format
        content_format = content_format[
                         1:] if content_format == ".html" else "markdown" if content_format == ".md" else None
    else:
        content = content
        typer.echo("Treating post content as raw input. If you want to use a file, please provide a valid file path.")
        assert content_format, ("To use raw input as content, please provide the format of the content using the "
                                "--content-format option")

    assert content_format in ["html", "markdown"], "Invalid content format. Options: html, markdown"

    tags = tags.split(",") if tags else None

    user_id = client.get_current_user()["id"]

    try:
        resp = client.create_post(user_id=user_id, title=title, content=content, content_format=content_format,
                                  canonical_url=canonical_url, tags=tags, publish_status=publish_status,
                                  license=license)
        typer.echo(f"Post created successfully: {resp['url']}")
        return resp
    except MediumError as e:
        typer.echo(f"Error: {e}")
        raise typer.Abort()


if __name__ == "__main__":
    app()
