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


if __name__ == "__main__":

    html = """
# Here is a html thing

## Here is an h2

Here is some paragraph text as you'd expect.

```sql
select * from blah
where blah.num > 5
orderby blah.timestamp;
```
"""

    print(clean_and_render_markup(html))
