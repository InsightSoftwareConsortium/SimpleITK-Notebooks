# Custom pytest CLI options must be registered via pytest_addoption in a
# conftest.py (pytest parses arguments before test modules are imported, so
# this hook cannot live in test_notebooks.py itself). This lets CI split
# notebook testing into separate static/dynamic steps while local runs
# default to doing both.
def pytest_addoption(parser):
    parser.addoption(
        "--analysis",
        action="store",
        default="both",
        choices=["static", "dynamic", "both"],
        help=(
            "Which notebook analysis to run in "
            "Test_notebooks::test_python_notebook/test_r_notebook: "
            "'static' (no output/broken-links/spelling checks), "
            "'dynamic' (execute notebook, check for errors), "
            "or 'both' (default, used for local testing)."
        ),
    )
