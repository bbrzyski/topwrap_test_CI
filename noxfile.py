# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
from collections import defaultdict
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory, TemporaryFile
from typing import Dict, List, Tuple

import nox
from nox.command import CommandFailed

PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]


@nox.session(reuse_venv=True)
def pre_commit(session: nox.Session) -> None:
    session.run("pre-commit", "install")
    session.run("pre-commit", "run", "--all-files")


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Options are defined in pyproject.toml and .flake8 files"""
    session.install(".[lint]")
    session.run("isort", ".")
    session.run("black", ".")
    session.run("flake8", ".")
    session.run("codespell", "-w")


@nox.session()
def test_lint(session: nox.Session) -> None:
    session.install(".[lint]")
    session.run("isort", "--check", ".")
    session.run("black", "--check", ".")
    session.run("flake8", ".")
    session.run("codespell")


# Coverage report generation will work only with packages installed
# in development mode. For more details, check
# https://github.com/pytest-dev/pytest-cov/issues/388


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    session.install("-e", ".[tests,topwrap-parse]")
    session.run("pytest", "-rs", "--cov-report", "html:cov_html", "--cov=topwrap", "tests")


def prepare_pyenv(session: nox.Session) -> dict:
    env = os.environ.copy()
    path = env.get("PATH")

    project_dir = Path(__file__).absolute().parent
    env["PYENV_ROOT"] = env.get("PYENV_ROOT", f"{project_dir}/.nox/pyenv")

    pyenv_bin = PurePath(env["PYENV_ROOT"]) / "bin"
    pyenv_shims = PurePath(env["PYENV_ROOT"]) / "shims"
    path = f"{pyenv_bin}:{pyenv_shims}:{path}"
    env["PATH"] = path

    # Install Pyenv
    if not shutil.which("pyenv", path=path):
        session.error(
            "\n'pyenv' command not found, you can install it by executing:"
            "\n    curl https://pyenv.run | bash"
            "\nSee https://github.com/pyenv/pyenv?tab=readme-ov-file#installation for more information"
        )

    # Install required Python versions if these don't exist
    for ver in PYTHON_VERSIONS:
        if not shutil.which(f"python{ver}", path=path):
            session.log(f"Installing Python {ver}")
            session.run("pyenv", "install", ver, external=True, env=env)

    # Detect which versions are provided by Pyenv
    pythons_in_pyenv = []
    for ver in PYTHON_VERSIONS:
        if shutil.which(f"python{ver}", path=pyenv_shims):
            pythons_in_pyenv += [ver]

    # Allow using Pythons from Pyenv
    if pythons_in_pyenv:
        session.log(f"Configuring Pythons from Pyenv, versions: {pythons_in_pyenv}")
        session.run("pyenv", "global", *pythons_in_pyenv, external=True, env=env)

    return env


@nox.session
def tests_in_env(session: nox.Session) -> None:
    env = prepare_pyenv(session)
    session.run("nox", "-s", "tests", external=True, env=env)


@nox.session
def build(session: nox.Session) -> None:
    session.install("-e", ".[deploy]")
    session.run("python3", "-m", "build")
    if len(session.posargs) < 1 or session.posargs[0] != "--no-test":
        session.notify("_install_test")


# this exists separately in order to have a fresh venv without topwrap installed in development mode
@nox.session
def _install_test(session: nox.Session) -> None:
    package_file = next(Path().glob("dist/topwrap*.tar.gz"), None)
    assert package_file is not None, "Cannot find source package in the dist/ directory"
    session.install(f"{package_file}[tests,topwrap-parse]")
    session.run(
        "pytest",
        "-rs",
        "--cov-report",
        "html:cov_html",
        "--cov=topwrap",
        "--import-mode=append",
        "tests",
    )


@nox.session
def doc_gen(session: nox.Session) -> None:
    session.install(".[docs]")
    session.run("make", "-C", "docs", "html", external=True)
    session.run("make", "-C", "docs", "latexpdf", external=True)
    session.run("cp", "docs/build/latex/topwrap.pdf", "docs/build/html", external=True)


@nox.session
def pyright_check(session: nox.Session) -> None:
    # this is a wrapper for _pyright_check that installs dependencies
    session.install(".[tests]")
    compare_with_main = "compare" in session.posargs

    if compare_with_main:
        session.run("nox", "-s", "_pyright_check", "--", "compare")
    else:
        session.run("nox", "-s", "_pyright_check")


@nox.session
def _pyright_check(session: nox.Session) -> None:
    # this is not supposed to be called outright, use `pyright_check`
    session.install(".")
    compare_with_main = "compare" in session.posargs

    # counting down errors on branch
    def count_down_errors() -> Tuple[Dict[str, int], Dict[str, int]]:
        errortypes = defaultdict(int)
        errorfiles = defaultdict(int)
        with TemporaryFile() as f:
            session.run("pyright", "--outputjson", stdout=f, success_codes=[0, 1], external=True)
            f.seek(0)
            errors_data = json.load(f)
            for errno in errors_data["generalDiagnostics"]:
                errortypes[errno["rule"]] += 1
                errorfiles[str(Path(errno["file"]).relative_to(Path(".").resolve()))] += 1
        return (errortypes, errorfiles)

    errortypes, errorfiles = count_down_errors()

    errortypes_main = defaultdict(int)
    errorfiles_main = defaultdict(int)
    if compare_with_main:
        # save location of used config
        pyproject_origin = Path(os.getcwd(), "pyproject.toml")

        with TemporaryDirectory() as dir:
            # copy into temp dir and go into it
            shutil.copytree(Path("."), dir, dirs_exist_ok=True)
            with session.chdir(Path(dir)):
                # switch to main and replace pyproject
                session.run("git", "switch", "main", "--force", external=True)
                session.run("rm", "pyproject.toml", external=True)
                shutil.copy(pyproject_origin, dir)

                # counting down errors on main
                errortypes_main, errorfiles_main = count_down_errors()

        for type in errortypes_main:
            if type not in errortypes:
                errortypes[type] = 0

        for file in errorfiles_main:
            if file not in errorfiles:
                errorfiles[file] = 0

    # human readable pyright output
    session.run("pyright", success_codes=[0, 1], external=True)

    columns = 3 if compare_with_main else 2

    from prettytable import PrettyTable

    def print_table(
        header: List[str], columns: int, errtypes: Dict[str, int], errtypes_main: Dict[str, int]
    ) -> None:
        t = PrettyTable(header[:columns])
        for errtype, num in sorted(errtypes.items(), key=lambda x: x[1], reverse=True):
            t.add_row([errtype, num, num - errtypes_main[errtype]][:columns])
        print(t)

    print_table(["Error", "Count", "Change"], columns, errortypes, errortypes_main)
    print_table(["File", "Errors", "Change"], columns, errorfiles, errorfiles_main)

    if compare_with_main:
        for errtype, num in errorfiles.items():
            if num - errorfiles_main[errtype] > 0:
                raise CommandFailed()
