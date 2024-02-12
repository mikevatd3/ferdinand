from sqlalchemy import text, Connection
from pypika import (
    Table,
    SQLLiteQuery as Query,
    Parameter,
    functions as fn,
    AliasedQuery,
)


class Tables:
    sentences = Table("sentences")
    stacks = Table("stacks")
    phrases = Table("phrases")
    definitions = Table("definitions")
    notes = Table("notes")


class Sentence:
    def __init__(self):
        """
        Kinda weird, but leaving some parts of queries here for later use.
        """
        sub_q = (
            Query.from_(Tables.sentences)
            .select("*")
            .groupby("stack_id")
            .having(fn.Max(Tables.sentences.id))
        )
        self.q_for_latest = (
            Query.with_(sub_q, "top_sentence")
            .from_(Tables.stacks)
            .select(
                Tables.stacks.id,
                Tables.stacks.stale,
                AliasedQuery("top_sentence").words,
            )
            .join(AliasedQuery("top_sentence"))
            .on(AliasedQuery("top_sentence").stack_id == Tables.stacks.id)
        )

    def new(self, words, db: Connection):
        result = db.execute(text("insert into stacks default values;"))
        stack_id = result.lastrowid
        db.commit()

        stmt = (
            Query.into(Tables.sentences)
            .columns("stack_id", "words")
            .insert(stack_id, Parameter(":words"))
        )
        db.execute(text(str(stmt)), {"words": words})
        db.commit()

        return stack_id

    def get(self, stack_id, db: Connection):
        stmt = self.q_for_latest.where(
            Tables.stacks.id == Parameter(":stack_id")
        )
        result = db.execute(text(str(stmt)), {"stack_id": stack_id})

        return result.fetchone()

    def all(self, db: Connection):
        stmt = self.q_for_latest
        result = db.execute(text(str(stmt)))

        return result.fetchall()

    def history(self, stack_id, db: Connection):
        stmt = (
            Query.select("*")
            .from_(Tables.sentences)
            .where(Tables.sentences.stack_id == Parameter(":stack_id"))
        )
        result = db.execute(text(str(stmt)), {"stack_id": stack_id})
        return result.fetchall()

    def goes_stale(self, stack_id, db: Connection):
        stmt = (
            Query.update(Tables.stacks)
            .set(Tables.stacks.stale, True)
            .where(Tables.stacks.id == stack_id)
        )

        result = db.execute(text(str(stmt)))
        db.commit()

        return result.lastrowid

    def refresh(self, stack_id, db: Connection):
        stmt = (
            Query.update(Tables.stacks)
            .set(Tables.stacks.stale, False)
            .where(Tables.stacks.id == stack_id)
        )

        result = db.execute(text(str(stmt)))
        db.commit()

        return result.lastrowid

    def update(self, stack_id, words, db: Connection):
        stmt = (
            Query.into(Tables.sentences)
            .columns("stack_id", "words")
            .insert(
                Parameter(":stack_id"),
                Parameter(":words"),
            )
        )

        db.execute(text(str(stmt)), {"stack_id": stack_id, "words": words})

        phrases = Phrase().get_for_sentence(stack_id, db)
        stale_ids = tuple(
            phrase.id for phrase in phrases if phrase.words not in words.lower()
        )

        stmt = Query.update(Tables.phrases).set(Tables.phrases.stale, False)
        db.execute(text(str(stmt)))
        stmt = (
            Query.update(Tables.phrases)
            .set(Tables.phrases.stale, True)
            .where(Tables.phrases.id.isin(stale_ids))
        )
        db.execute(text(str(stmt)))
        db.commit()

        return stack_id

    def delete(self, stack_id, db: Connection):
        """Deletes the whole stack"""
        db.execute(text("PRAGMA foreign_keys = ON;"))
        stmt = (
            Query.from_(Tables.stacks)
            .delete()
            .where(Tables.stacks.id == Parameter(":stack_id"))
        )

        result = db.execute(text(str(stmt)), {"stack_id": stack_id})
        db.commit()

        return result.lastrowid


class Phrase:
    def __init__(self):
        """
        Sort of worse, but we want to query for the top sentence from the
        stack related to a given phrase.
        """
        sub_q = (
            Query.from_(Tables.sentences)
            .select("*")
            .groupby("stack_id")
            .having(fn.Max(Tables.sentences.id))
        )

        self.q_for_latest = (
            Query.with_(sub_q, "top_sentence")
            .from_(Tables.stacks)
            .select(Tables.stacks.id, AliasedQuery("top_sentence").words)
            .join(AliasedQuery("top_sentence"))
            .on(AliasedQuery("top_sentence").stack_id == Tables.stacks.id)
        )

        self.base_query = (
            Query.with_(self.q_for_latest, "latest_sentences")
            .from_(Tables.phrases)
            .select(
                Tables.phrases.id,
                Tables.phrases.words,
                Tables.phrases.stack_id,
                Tables.phrases.stale,
                Tables.notes.words.as_("notes"),
                AliasedQuery("latest_sentences").id.as_("def_stack_id"),
                AliasedQuery("latest_sentences").words.as_("definition"),
                Tables.notes.definition_status,
            )
            .join(Tables.notes)
            .on(Tables.notes.phrase_id == Tables.phrases.id)
            .left_join(Tables.definitions)
            .on(Tables.definitions.phrase_id == Tables.phrases.id)
            .left_join(AliasedQuery("latest_sentences"))
            .on(
                AliasedQuery("latest_sentences").id
                == Tables.definitions.stack_id
            )
        )

    def new(self, stack_id: int | None, words: str, db: Connection):
        stmt = (
            Query.into(Tables.phrases)
            .columns(
                Tables.phrases.stack_id,
                Tables.phrases.words,
            )
            .insert(
                Parameter(":stack_id"),
                Parameter(":words"),
            )
        )

        result = db.execute(
            text(str(stmt)), {"stack_id": stack_id, "words": words}
        )
        phrase_id = result.lastrowid

        stmt = (
            Query.into(Tables.notes)
            .columns(Tables.notes.phrase_id)
            .insert(phrase_id)
        )

        result = db.execute(text(str(stmt)))
        db.commit()

        return phrase_id

    def get(self, phrase_id, db: Connection):
        stmt = self.base_query.where(
            Tables.phrases.id == Parameter(":phrase_id")
        )

        result = db.execute(text(str(stmt)), {"phrase_id": phrase_id})
        return result.fetchone()

    def all(self, db: Connection):
        result = db.execute(text(str(self.base_query)))
        return result.fetchall()

    def get_for_sentence(self, stack_id, db: Connection):
        stmt = self.base_query.where(
            Tables.phrases.stack_id == Parameter(":stack_id")
        )
        result = db.execute(text(str(stmt)), {"stack_id": stack_id})
        return result.fetchall()

    def revise_definition(self, phrase_id, new_words, db: Connection):
        phrase = self.get(phrase_id, db)
        # This is an upsert, because the phrase may not yet be defined.

        if phrase.definition is None:
            print("new_def_created")
            stack_id = Sentence().new(new_words, db)
            stmt = (
                Query.into(Tables.definitions)
                .columns(
                    Tables.definitions.phrase_id,
                    Tables.definitions.stack_id,
                )
                .insert(
                    Parameter(":phrase_id"),
                    Parameter(":stack_id"),
                )
            )
            db.execute(
                text(str(stmt)), {"phrase_id": phrase_id, "stack_id": stack_id}
            )
            db.commit()
        else:
            stack_id = Sentence().update(phrase.def_stack_id, new_words, db)
            db.commit()

        return phrase_id

    def set_status(self, phrase_id, new_status, db: Connection):
        stmt = (
            Query.update(Tables.notes)
            .set(Tables.notes.definition_status, Parameter(":status"))
            .where(Tables.notes.phrase_id == Parameter(":phrase_id"))
        )

        result = db.execute(
            text(str(stmt)), {"status": new_status, "phrase_id": phrase_id}
        )
        db.commit()

        # change to 'inserted_primary_key'
        return result.lastrowid

    def revise_notes(self, phrase_id, note_text, db: Connection):
        stmt = (
            Query.update(Tables.notes)
            .set(Tables.notes.words, Parameter(":note_text"))
            .where(Tables.notes.phrase_id == Parameter(":phrase_id"))
        )

        result = db.execute(
            text(str(stmt)), {"note_text": note_text, "phrase_id": phrase_id}
        )
        db.commit()

        return result.lastrowid

    def delete(self, phrase_id, db: Connection):
        """Deletes the whole phrase"""
        db.execute(text("PRAGMA foreign_keys = ON;"))
        phrase = self.get(phrase_id, db)
        Sentence().goes_stale(phrase.def_stack_id, db)

        stmt = (
            Query.from_(Tables.phrases)
            .delete()
            .where(Tables.phrases.id == Parameter(":phrase_id"))
        )

        result = db.execute(text(str(stmt)), {"phrase_id": phrase_id})
        db.commit()

        return result.lastrowid

    def rephrase(self, phrase_id, words, db: Connection):
        stmt = (
            Query.update(Tables.phrases)
            .set(Tables.phrases.words, Parameter(":words"))
            .set(Tables.phrases.stale, False)
            .where(Tables.phrases.id == Parameter(":phrase_id"))
        )

        result = db.execute(
            text(str(stmt)), {"words": words, "phrase_id": phrase_id}
        )
        db.commit()

        return result.lastrowid


class Graph:
    """
    The graph view builds a graph of the phrase-sentence relationships
    along

    Research: sqlite graph database
    """

    edges_stmt = (
        Query.select(
            Tables.phrases.id,
            Tables.phrases.words,
            Tables.phrases.stack_id,
            Tables.phrases.stale,
            Tables.definitions.stack_id.as_("def_stack_id"),
        )
        .from_(Tables.phrases)
        .left_join(Tables.definitions)
        .on(Tables.phrases.id == Tables.definitions.phrase_id)
    )

    @classmethod
    def assemble_graph(cls, db):
        nodes = Sentence().all(db)
        edges = db.execute(text(str(cls.edges_stmt)))

        return {
            "nodes": [
                {
                    "id": node.id,
                    "words": node.words,
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.words,
                    "source": edge.stack_id,
                    "target": edge.def_stack_id,
                    "stale": edge.stale,
                }
                for edge in edges
            ],
        }


