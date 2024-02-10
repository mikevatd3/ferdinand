from pathlib import Path
import json
import sys
import os
import argparse
from sqlalchemy import create_engine, text


__version__ = "0.0.0"


banner_name = """
 .d888                     888 d8b                                 888 
d88P"                      888 Y8P                                 888 
888                        888                                     888 
888888 .d88b.  888d888 .d88888 888 88888b.   8888b.  88888b.   .d88888 
888   d8P  Y8b 888P"  d88" 888 888 888 "88b     "88b 888 "88b d88" 888 
888   88888888 888    888  888 888 888  888 .d888888 888  888 888  888 
888   Y8b.     888    Y88b 888 888 888  888 888  888 888  888 Y88b 888 
888    "Y8888  888     "Y88888 888 888  888 "Y888888 888  888  "Y88888
"""


PROJECTS_PATH = Path.cwd() / "projects"
SQL_INIT = Path.cwd() / "sql"


def update_config(project_name):
    with open(Path.cwd() / "project_conf.json", "r") as f:
        try:
            conf = json.load(f)
            conf["current_project"] = project_name
        except (json.JSONDecodeError, KeyError):
            conf = {"current_project": project_name}

    with open(Path.cwd() / "project_conf.json", "w") as f:
        json.dump(conf, f)


def create_new_project(project_name):
    db_path = PROJECTS_PATH / f"{project_name}.sqlite3"
    if db_path.exists():
        print(
            """ERROR: There is currently a project in your projects folder with that name."""
        )
        sys.exit(0)

    if len(project_name.split()) > 1:
        print("""ERROR: Project name cannot include spaces, use '_' instead.""")
        sys.exit(0)

    # set the configuration up
    update_config(project_name)

    # set up the sqlite db
    db = create_engine(f"sqlite:///projects/{project_name}.sqlite3")
    
    # create all database tables
    with db.connect() as conn:
        for file in [
            "definitions.sql",
            "notes.sql",
            "phrases.sql",
            "sentences.sql",
            "stacks.sql",
        ]:
            with open(SQL_INIT / file) as f:
                conn.execute(text(f.read()))
                conn.commit()


def switch_to_project(project_name):
    db_path = PROJECTS_PATH / f"{project_name}.sqlite3"

    if not db_path.exists():
        print(
            """ERROR: Project name doesn't match a project in your projects folder."""
        )
        projects = os.listdir(PROJECTS_PATH)
        if projects:
            print("Projects available:")
            for db in projects:
                print(f"    - {Path(db).stem}")

        print(
            """If you're trying to start a new project, provide the -n or --new flag."""
        )
        sys.exit(0)

    # set the configuration up
    update_config(project_name)


parser = argparse.ArgumentParser(
    prog="Ferdinand analysis tool",
    description=banner_name,
)

parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"Ferdinand analysis tool {__version__}",
)

parser.add_argument(
    "project_name",
    help="The name of an existing project, or a new project when providing the -n/--new flag.",
)

parser.add_argument(
    "-n",
    "--new",
    action="store_true",
    help="Create a new project with the project name provided.",
)


def main():
    namespace = parser.parse_args()
    if namespace.new:
        create_new_project(namespace.project_name)
    else:
        switch_to_project(namespace.project_name)


if __name__ == "__main__":
    main()
