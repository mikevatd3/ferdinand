from string import punctuation
import json
from typing import Iterator

from flask import (
    Flask, 
    abort, 
    render_template, 
    request, 
    redirect, 
    jsonify
)
from sqlalchemy import create_engine

from notes import clean_and_render_markup
from phrase_models import Phrase, Sentence, Graph

app = Flask(__name__)

with open("project_conf.json", "r") as f:
    conf = json.load(f)

engine = create_engine(f"sqlite:///projects/{conf['current_project']}.sqlite3")
project_name = conf["current_project"].replace("_", " ")


@app.route("/")
def index():
    return render_template("index.html", current_project=project_name)


@app.route("/sentences", methods=["GET", "POST"])
def sentences():
    if (phrase_id := request.args.get("inline_add_for")):
        return render_template("sentence_inline_add.html", phrase_id=phrase_id)

    with engine.connect() as db:
        if request.method == "POST":
            words = request.form.get("words")
            sentence_id = Sentence().new(words, db)
            sentence = Sentence().get(sentence_id, db)

            if request.args.get("analyze"):
                return render_template(
                    "sentence.html",
                    sentence=sentence,
                    phrases=[],
                    current_project=project_name,
                )

        sentences = Sentence().all(db)

    return render_template(
        "sentences.html", sentences=sentences, current_project=project_name
    )


@app.route("/sentences/<sentence_id>", methods=["GET", "PUT", "DELETE"])
def sentence(sentence_id):
    with engine.connect() as db:
        if request.args.get("edit"):
            sentence = Sentence().get(sentence_id, db)
            return render_template(
                "sentence_edit.html",
                sentence=sentence,
                phrases=[],
                current_project=project_name,
            )

        if request.method == "DELETE":
            Sentence().delete(sentence_id, db)
            return ""

        if request.method == "PUT":
            if request.args.get("refresh") == "yes":
                Sentence().refresh(sentence_id, db)
                sentence = Sentence().get(sentence_id, db)

                return render_template(
                    "sentence_inline.html", sentence=sentence
                )

            words = request.form.get("words")
            Sentence().update(sentence_id, words, db)

        sentence = Sentence().get(sentence_id, db)
        phrases = Phrase().get_for_sentence(sentence_id, db)

        return render_template(
            "sentence.html",
            sentence=sentence,
            phrases=phrases,
            current_project=project_name,
        )


def extract_phrase(parts: Iterator[tuple[str, str]]) -> tuple[int, str]:
    phrase_parts = []
    # From the html a token will have <word index>@@<word>
    sentence_id = -1
    for token, switch in parts:
        if switch == "on":
            index, word = token.split("@@")
            phrase_parts.append((int(index), word))

        if token == "sentence":
            sentence_id = switch

    return sentence_id, " ".join(
        [word.lower().strip(punctuation) for _, word in sorted(phrase_parts)]
    )


@app.route("/phrases/analysis", methods=["POST"])
def analysis():
    with engine.connect() as db:
        sentence_id, phrase = extract_phrase(request.form.items())

        Phrase().new(sentence_id, phrase, db)
        phrases = Phrase().get_for_sentence(sentence_id, db)

        return render_template(
            "phrases.html", phrases=phrases, current_project=project_name
        )


@app.route("/phrases", methods=["GET", "POST"])
def phrases():
    # This should have a query to provide an init and the
    # the plain function will just take a word, definition.
    with engine.connect() as db:
        if request.method == "POST":
            words = request.form.get("words")
            Phrase().new(None, words, db)

        phrases = Phrase().all(db)
        return render_template(
            "phrases.html", phrases=phrases, current_project=project_name
        )


@app.route("/phrases/<phrase_id>", methods=["GET", "DELETE", "PUT"])
def phrase(phrase_id):
    with engine.connect() as db:
        if request.method == "DELETE":
            Phrase().delete(phrase_id, db)
            return ""

        if request.method == "PUT":
            if request.args.get("rephrase") == "yes":
                sentence_id, phrase = extract_phrase(request.form.items())

                Phrase().rephrase(phrase_id, phrase, db)
                phrase = Phrase().get(phrase_id, db)

                sentence = Sentence().get(sentence_id, db)
                phrases = Phrase().get_for_sentence(sentence_id, db)

                return render_template(
                    "sentence.html",
                    sentence=sentence,
                    phrases=phrases,
                    current_project=project_name,
                )

            notes = request.form.get("notes", "")
            status = request.form.get("status", "")
            Phrase().revise_notes(phrase_id, notes, db)
            Phrase().set_status(phrase_id, status, db)

            phrase = Phrase().get(phrase_id, db)

            return render_template(
                "phrase.html",
                phrase=phrase,
                current_project=project_name,
                notes=clean_and_render_markup(phrase.notes),
            )

        phrase = Phrase().get(phrase_id, db)
        if request.args.get("inline") == "yes":
            return render_template(
                "phrase_inline.html",
                phrase=phrase,
                current_project=project_name,
            )

        if request.args.get("inline_edit") == "yes":
            return render_template(
                "phrase_inline_edit.html",
                phrase=phrase,
                current_project=project_name,
            )

        if request.args.get("rephrase") == "yes":
            sentence = Sentence().get(phrase.stack_id, db)
            return render_template(
                "sentence_rephrase_edit_controls.html",
                phrase=phrase,
                sentence=sentence,
                current_project=project_name,
            )
        if request.args.get("edit") == "yes":
            return render_template(
                "phrase_edit.html", phrase=phrase, current_project=project_name
            )

        return render_template(
            "phrase.html",
            phrase=phrase,
            current_project=project_name,
            notes=clean_and_render_markup(phrase.notes),
        )


@app.route("/definitions", methods=["POST"])
def definitions():
    acceptable_statuses = {"NEW", "EXPLORING", "ACCEPTED", "STUCK"}
    with engine.connect() as db:
        if request.method == "POST":
            phrase_id = request.form.get("phrase_id")
            words = request.form.get("definition")
            status = request.form.get("status", "NEW")

            if status not in acceptable_statuses:
                return render_template(
                    "error_row.html",  # This doesn't exist.
                    phrase_id=phrase_id,
                    current_project=project_name,
                )

            if words:  # If the string is None or blank, don't save it.
                Phrase().revise_definition(phrase_id, words, db)
            if status != "NEW":
                Phrase().set_status(phrase_id, status, db)

            if request.args.get("inline_add") == "yes":
                phrase = Phrase().get(phrase_id, db)
                return render_template(
                    "sentence_simple.html",
                    phrase=phrase,
                )

            return redirect(f"/phrases/{phrase_id}?inline=yes")

    return abort(404)


@app.route("/help")
def help():
    return render_template("help.html", current_project=project_name)


@app.route("/graph/data")
def graph_data():
    with engine.connect() as db:
        graph = Graph.assemble_graph(db)

        return jsonify(graph)


if __name__ == "__main__":
    import sys
    from ferdinand_admin import banner_name

    debug = "-db" in sys.argv

    if debug:
        print("RUNNING IN DEBUG MODE")
    print(banner_name)
    app.run(debug=debug)
