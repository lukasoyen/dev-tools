from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from dev_tools.forbidden_tag import find_rule_calls, main, violations

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem


def test_find_rule_calls_for_content_should_return_rule_kinds() -> None:
    content = """
py_venv(name = "venv")
pkg_tar(
    name = "archive",
    tags = ["no-remote"],
)
"""

    assert [rule_call.rule_kind for rule_call in find_rule_calls(content)] == ["py_venv", "pkg_tar"]


def test_find_rule_calls_for_nested_parentheses_should_return_full_rule_body() -> None:
    content = """
py_venv(
    name = name + "_venv",
    deps = [":{}_foo".format(name)],
    tags = ["manual"],
)
"""

    rule_call = next(find_rule_calls(content))

    assert '":{}_foo".format(name)' in rule_call.body
    assert 'tags = ["manual"]' in rule_call.body


def test_violations_for_forbidden_tag_should_return_file(fs: FakeFilesystem) -> None:
    fs.create_file(
        Path("repo/BUILD.bazel"),
        contents="""
py_venv(
    name = "bad",
    tags = ["no-remote"],
)
""",
    )

    assert list(violations(Path("repo/BUILD.bazel"), "no-remote", None)) == [Path("repo/BUILD.bazel")]


def test_violations_for_allowed_rule_kind_should_return_empty_list(fs: FakeFilesystem) -> None:
    fs.create_file(
        Path("repo/BUILD.bazel"),
        contents="""
pkg_tar(
    name = "archive",
    tags = ["no-remote"],
)
""",
    )

    assert list(violations(Path("repo/BUILD.bazel"), "no-remote", re.compile("pkg_tar"))) == []


def test_main_for_violation_should_return_one(fs: FakeFilesystem, capsys) -> None:
    fs.create_file(
        Path("repo/BUILD.bazel"),
        contents="""
py_venv(
    name = "bad",
    tags = ["no-remote"],
)
""",
    )

    assert main(["--forbidden-tag=no-remote", "repo/BUILD.bazel"]) == 1
    assert "contains a rule with `tags` containing `no-remote`" in capsys.readouterr().out
