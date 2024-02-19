from sqlalchemy import text, Connection
from pypika import (
    Table,
    SQLLiteQuery as Query,
    Parameter,
    functions as fn,
    AliasedQuery,
)


class Tables:
    users = Table("users")
    projects = Table("projects")
    permissions = Table("permissions")


class User:
    @classmethod
    def login(cls, username, password):
        pass

    @classmethod
    def logout(cls, username):
        pass


class Project:
    @classmethod
    def get_all_projects_for_user(cls, username):
        pass

    @classmethod
    def get_project(cls, project_id):
        pass
