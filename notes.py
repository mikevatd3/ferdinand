import mistune
import nh3


def clean_and_render_markup(markup: str):
    """
    Avoiding issues with malicious html being injected into the
    file.
    """

    return nh3.clean(
        mistune.html(markup),
        tag_attribute_values={
            "code": {
                "class": {
                    "language-sql",
                    "language-python",
                    "language-bash",
                    "language-powershell",
                    "language-pearl",
                    "language-c",
                    "language-rust",
                    "language-r",
                }
            }
        },
    )
