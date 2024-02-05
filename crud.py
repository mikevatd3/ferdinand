import json
from sqlalchemy import create_engine, text
from pypika import (
    SQLLiteQuery as Query,
    Table,
    Order,
    functions as fn,
    AliasedQuery,
)


PAGE_SIZE = 10


with open("project_conf.json", "r") as f:
    conf = json.load(f)


db = create_engine(f"sqlite:///projects/{conf['current_project']}.sqlite3")


class Sentence:
    def __init__(self):
        self.table = Table("sentences")

    def get(self, id):
        stmt = Query.from_(self.table).select("*").where(self.table.id == id)
        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))

            return result.fetchone()

    def all(self):
        stmt = Query.from_(self.table).select("*")
        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))

            return result.fetchall()

    def new(self, words: str):
        stmt = Query.into(self.table).columns("words").insert(words)
        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))
            conn.commit()

            stmt = (
                Query.from_(self.table)
                .select("*")
                .where(self.table.id == result.lastrowid)
            )

            result = conn.execute(text(str(stmt)))

            return result.fetchone()


class Definable:
    def __init__(self):
        self.table = Table("phrases")

    def get(self, id, return_definition=False):
        stmt = (
            Query.from_(self.table)
            .select(
                self.table.id,
                self.table.words,
            )
            .where(self.table.id == id)
        )
        if return_definition:
            sentences = Table("sentences")
            definitions = Table("definitions")
            stmt = (
                stmt.select(
                    sentences.words.as_("definition"),
                    sentences.id.as_("definition_id"),
                )
                .left_join(definitions)
                .on(definitions.phrase_id == self.table.id)
                .left_join(sentences)
                .on(definitions.sentence_id == sentences.id)
            )
        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))
            return result.fetchone()

    def get_from_sentence(self, sentence_id):
        stmt = (
            Query.from_(self.table)
            .select("*")
            .where(self.table.sentence_id == sentence_id)
        )
        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))

            return result.fetchall()

    def all(self, return_definitions=False):
        stmt = Query.from_(self.table).select(self.table.id, self.table.words)

        if return_definitions:
            sentences = Table("sentences")
            definitions = Table("definitions")

            latest_defs = (
                Query.from_(definitions)
                .select("*")
                .groupby(definitions.timestamp)
                .having(fn.Max(definitions.timestamp))
                .orderby(definitions.timestamp)
            )

            stmt = (
                stmt.with_(latest_defs, "latest_defs")
                .select(
                    sentences.words.as_("definition"),
                    sentences.id.as_("definition_id"),
                )
                .left_join(AliasedQuery("latest_defs"))
                .on(AliasedQuery("latest_defs").phrase_id == self.table.id)
                .left_join(sentences)
                .on(AliasedQuery("latest_defs").sentence_id == sentences.id)
            )

        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))

            return result.fetchall()

    def new(self, sentence_id: int, words: str):
        stmt = (
            Query.into(self.table)
            .columns("sentence_id", "words")
            .insert(sentence_id, words)
        )
        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))
            conn.commit()

            stmt = (
                Query.from_(self.table)
                .select("*")
                .where(self.table.id == result.lastrowid)
            )

            result = conn.execute(text(str(stmt)))

            return result.fetchone()

    def delete(self, phrase_id):
        stmt = (
            Query.from_(self.table).delete().where(self.table.id == phrase_id)
        )
        with db.connect() as conn:
            conn.execute(text(str(stmt)))
            conn.commit()


class Definition:
    def __init__(self):
        self.table = Table("definitions")

    def get_for_phrase(self, phrase_id):
        stmt = (
            Query.from_(self.table)
            .select("*")
            .where(self.table.phrase_id == phrase_id)
            .orderby(self.table.timestamp, order=Order.desc)
        )

        with db.connect() as conn:
            result = conn.execute(text(str(stmt)))
            return result.fetchone()

    def new(self, phrase_id, sentence_id):
        stmt = (
            Query.into(self.table)
            .columns("phrase_id", "sentence_id")
            .insert(phrase_id, sentence_id)
        )
        with db.connect() as conn:
            conn.execute(text(str(stmt)))
            conn.commit()
