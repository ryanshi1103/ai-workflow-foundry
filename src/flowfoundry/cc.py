"""Entry point for ``python -m flowfoundry.cc`` — the interactive cc launcher."""

import sys

from flowfoundry.workspace.cli.launcher import main


if __name__ == "__main__":
    if sys.argv[1:] == ["--quick"]:
        from flowfoundry.daily import main as daily_main

        sys.exit(daily_main(["--quick"]))
    sys.exit(main())
