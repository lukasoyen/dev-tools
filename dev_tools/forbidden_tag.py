from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING

from dev_tools.build_file_parsing_util import find_rule_calls, rule_has_tag
from dev_tools.git_hook_utils import create_default_parser

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator, Sequence
    from pathlib import Path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = create_default_parser()
    parser.add_argument("--forbidden-tag", required=True)
    parser.add_argument("--allow-in-rule-kind")
    return parser.parse_args(argv)


def violations(
    path: Path,
    forbidden_tag: str,
    allowed_rule_kind_re: re.Pattern[str] | None,
) -> Iterator[Path]:
    content = path.read_text()
    for rule_call in find_rule_calls(content):
        is_allowed_rule_kind = allowed_rule_kind_re and allowed_rule_kind_re.search(rule_call.rule_kind)
        if not is_allowed_rule_kind and rule_has_tag(rule_call.body, forbidden_tag):
            yield path


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    allowed_rule_kind_re = re.compile(args.allow_in_rule_kind) if args.allow_in_rule_kind else None
    found_violation = False
    for filename in args.filenames:
        for violation in violations(filename, args.forbidden_tag, allowed_rule_kind_re):
            if args.allow_in_rule_kind:
                print(
                    f"Error: {violation} contains a rule with `tags` containing `{args.forbidden_tag}` outside "
                    f"a rule kind matching /{args.allow_in_rule_kind}/."
                )
            else:
                print(f"Error: {violation} contains a rule with `tags` containing `{args.forbidden_tag}`.")
            found_violation = True
    return 1 if found_violation else 0


if __name__ == "__main__":
    sys.exit(main())
