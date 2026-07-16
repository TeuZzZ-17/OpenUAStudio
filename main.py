"""OpenUAStudio entry point.

Launches the integrated Urban Assault asset workbench.  The main window
contains the 3D/BASE/SET.BAS tools and opens the complete Wireframe Editor
from the menu bar.

Usage:
    python main.py [path/to/asset.base | path/to/SET.BAS]
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from assembly_window import AssemblyWindow

APP_TITLE = "OpenUAStudio"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    # Each window composes its own full title.  Keep the platform from
    # appending a second "OpenUAStudio" label to document titles.
    app.setApplicationDisplayName("")

    window = AssemblyWindow()
    window.setWindowTitle(APP_TITLE)
    window.show()

    if len(sys.argv) > 1:
        window.open_base(sys.argv[1])

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
