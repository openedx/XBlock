"""Utilities available to workbench applications."""


def make_safe_for_html(html):
    """Turn the text `html` into a real HTML string."""
    html = html.replace("&", "&amp;")
    html = html.replace(" ", "&nbsp;")
    html = html.replace("<", "&lt;")
    html = html.replace("\n", "<br>")
    return html
