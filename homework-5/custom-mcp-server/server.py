from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("lorem-ipsum-server")

LOREM_IPSUM_PATH = Path(__file__).parent / "lorem-ipsum.md"


def _read_words(word_count: int) -> str:
    text = LOREM_IPSUM_PATH.read_text(encoding="utf-8")
    words = text.split()
    return " ".join(words[:word_count])


# Resources are URIs that Claude can read from (e.g., files, APIs).
# This resource accepts a word_count path parameter and returns that many
# words from lorem-ipsum.md.
@mcp.resource("lorem://ipsum/{word_count}")
def lorem_resource(word_count: int = 30) -> str:
    """Return word_count words from the lorem ipsum source file."""
    return _read_words(word_count)


# Tools are actions Claude can call to perform operations (e.g., reading a
# file, running a command). This tool wraps the resource so Claude can invoke
# it directly with an optional word_count argument.
@mcp.tool()
def read(word_count: int = 30) -> str:
    """Return exactly word_count words from the lorem ipsum source file."""
    return _read_words(word_count)


if __name__ == "__main__":
    mcp.run()