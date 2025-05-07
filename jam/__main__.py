# nuitka-project: --include-package-data=resources
# nuitka-project: --include-module=arcade.future
# nuitka-project: --force-stderr-spec=err.txt
# nuitka-project: --report=compilation-report.xml
# nuitka-project: --standalone
# nuitka-project: --product-name="Station"
# nuitka-project: --product-version="0.2.0.1"
# nuitka-project: --file-description="Created by DigiDuncan and DragonMoffon"
# nuitka-project-if: {OS} == "Darwin":
#   nuitka-project: --macos-create-app-bundle
#   nuitka-project: --macos-app-icon=icon.ico
# nuitka-project-if: {OS} == "Windows":
#   nuitka-project: --windows-console-mode=disable
#   nuitka-project: --windows-icon-from-ico=icon.ico

from jam.main import main

if __name__ == "__main__":
    main()
