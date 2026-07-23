$ErrorActionPreference = "Stop"
& python -m build
& python "$PSScriptRoot\demo.py"
& python "$PSScriptRoot\package_release.py"

