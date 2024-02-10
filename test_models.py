import json
import datetime
from pathlib import Path
from pytest import fixture
from sqlalchemy import create_engine
from models import Sentence, Phrase
from ferdinand_admin import create_new_project, switch_to_project, PROJECTS_PATH

SAVE_CONFIG = {"current_project": "default"}

# need pytest code to run db setup
def setup_module():
    with open("project_conf.json", "r") as f:
        conf = json.load(f)
        SAVE_CONFIG["current_project"] = conf["current_project"]

    test_db = f"test_{datetime.datetime.now().strftime('%Y%m%d')}"
    try:
        create_new_project(test_db)
    except:
        Path.unlink(PROJECTS_PATH / f"{test_db}.sqlite3")
        create_new_project(test_db)


def teardown_module():
    test_db = f"test_{datetime.datetime.now().strftime('%Y%m%d')}"
    switch_to_project(SAVE_CONFIG["current_project"])
    Path.unlink(PROJECTS_PATH / f"{test_db}.sqlite3")


@fixture
def db():
    test_db = f"test_{datetime.datetime.now().strftime('%Y%m%d')}"
    db = create_engine(f"sqlite:///projects/{test_db}.sqlite3")
    
    con = db.connect()
    yield con
    con.close()

# [x] Sentence Interface
# [x] Create  --  Create new sentence (on a new stack)
# [x]  Read    --  Read the top sentence off the stack
#     -- [x] get (phrases in separate query)
#     -- [x] all
#     -- [x] history
# [x] Update  --  Add a new sentence to the top of the stack
#     -- [ ] Need to set sub phrases as 'STALE'
# [x] Delete  --  Delete stack (in the future 'deactivate')

# [ ]  Phrase Interface
# [x]  Create  --  Create phrase linked to a sentence stack
#     - [x]  also create note and set default status to NEW
# [x]  Read    --  Read phrase with any associated definition and notes
#     -- [x]  get (one) always with sentence and status -- notes optional
#     -- [x]  all -- always with sentence and status
#     -- [x]  filter by stack_id
# [x]  Update  --  Update definition status, add sentence revision to stack, add notes
#     - [x]  update_def_status
#     - [x]  upsert_definition
#     - [x]  update_note_text
# [ ] Delete  --  Delete phrase and assocated definition stack(s) (in the future 'deactivate')


# SENTENCE CREATE
def test_new_sentence(db):
    words = "This is the first sentence to define."
    stack_id = Sentence().new(words, db)
    sentences = Sentence().all(db)

    assert stack_id == 1
    assert len(list(sentences)) == 1
    assert sentences[0].words == words


# SENTENCE GET BASIC
def test_get_sentence(db):
    words = "This is the second sentence to define."
    stack_id = Sentence().new(words, db)

    sentence = Sentence().get(stack_id, db)

    assert sentence.words == words


# SENTENCE GET AFTER UPDATE
def test_get_sentence_after_updates(db):
    words = "This is the third sentence to define."
    stack_id = Sentence().new(words, db)

    new_words = "This is the fourth sentence to define."
    new_stack_id = Sentence().update(stack_id, new_words, db)
    sentence = Sentence().get(stack_id, db)

    assert stack_id == new_stack_id
    assert sentence.words == new_words


# SENTENCE DELETE
def test_delete_sentence(db):
    words = "This is the fifth sentence."
    stack_id = Sentence().new(words, db)
    Sentence().delete(stack_id, db)

    result = Sentence().get(stack_id, db)

    assert result == None


# PHRASE CREATE
def test_create_new_phrase(db):
    words = "This is the sixth sentence."
    phrase = "sixth sentence"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, phrase, db)

    phrase = Phrase().get(phrase_id, db)

    assert phrase.words == "sixth sentence"


# PHRASE GET
def test_get_phrase(db):
    words = "This is the seventh sentence."
    clip = "seventh sentence"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)

    phrase = Phrase().get(phrase_id, db)

    assert phrase.definition == None
    assert phrase.definition_status == "NEW"

def test_get_for_sentence(db):
    words = "This is the eighth sentence."
    clip = "the eighth"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)

    phrases = Phrase().get_for_sentence(stack_id, db)

    assert phrases[0].definition == None
    assert phrases[0].definition_status == "NEW"


# PHRASE UPDATE
# This is really an alias of a sentence and status update
# So don't call it an update.
def test_revise_phrase_definition(db):
    words = "This is the eighth sentence."
    clip = "the eighth"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)
    
    definition = "The eighth is whatever comes after the seventh."
    Phrase().revise_definition(phrase_id, definition, db)
    phrase = Phrase().get(phrase_id, db)

    assert phrase.definition == definition



def test_set_status(db):
    words = "This is the nine sentence."
    clip = "nine"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)
    
    definition = "Nine isn't the best number but isn't the worst really."
    Phrase().revise_definition(phrase_id, definition, db)
    phrase = Phrase().get(phrase_id, db)

    assert phrase.definition == definition

def test_stale_def(db):
    words = "This is the best sentence."
    clip = "best sentence"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)
    
    Sentence().update(stack_id, "This is the best pizza.", db)
    phrase = Phrase().get(phrase_id, db)

    assert phrase.stale == True


# PHRASE DELETE
def test_delete_phrase(db):
    words = "This is the best sentence."
    clip = "best sentence"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)

    Phrase().delete(phrase_id, db)
    
    assert Phrase().get(phrase_id, db) == None


def test_update_status(db):
    words = "This is the best sentence."
    clip = "best sentence"

    stack_id = Sentence().new(words, db)
    phrase_id = Phrase().new(stack_id, clip, db)

    Phrase().set_status(phrase_id, "ACCEPTED", db)
    phrase = Phrase().get(phrase_id, db)

    assert phrase.definition_status == "ACCEPTED"
