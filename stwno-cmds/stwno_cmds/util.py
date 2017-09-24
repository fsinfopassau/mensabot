import inspect
import os
import subprocess

import pkg_resources


def get_version():
    pkg_data = pkg_resources.require("stwno_cmds")[0]  # FIXME
    try:
        git_rev = subprocess.check_output(
            ["git", "describe", "--always"],
            cwd=os.path.dirname(inspect.getfile(inspect.currentframe()))
        ).decode('ascii').strip()
    except NotADirectoryError:
        git_rev = "release"
    # FIXME pkg_data.version is invalid when installed via "develop" and setup.py changes
    return "{} {} {}".format(pkg_data.project_name.title(), pkg_data.version, git_rev)
    # return "{} {} {} [{}]".format(pkg_data.project_name.title(), pkg_data.version, git_rev, DEPLOY_MODE)
