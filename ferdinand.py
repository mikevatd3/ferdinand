from string import punctuation
import json

from flask import Flask, abort, render_template, request, redirect
from sqlalchemy import create_engine
from models import Phrase, Sentence


app = Flask(__name__)

with open("project_conf.json", "r") as f:
    conf = json.load(f)

engine = create_engine(f"sqlite:///projects/{conf['current_project']}.sqlite3")


@app.route("/")
def index():
    project_name = conf["current_project"].replace("_", " ")
    return render_template("index.html", current_project=project_name)


@app.route("/sentences", methods=["GET", "POST"])
def sentences():
    with engine.connect() as db:
        if request.method == "POST":
            words = request.form.get("words")
            sentence_id = Sentence().new(words, db)
            sentence = Sentence().get(sentence_id, db)

            if request.args.get("analyze"):
                return render_template("sentence.html", sentence=sentence, phrases=[])

        sentences = Sentence().all(db)
    return render_template("sentences.html", sentences=sentences)


@app.route("/sentences/<sentence_id>", methods=["GET", "PUT", "DELETE"])
def sentence(sentence_id):
    with engine.connect() as db:
        if request.args.get("edit"):
            sentence = Sentence().get(sentence_id, db)
            return render_template("sentence_edit.html", sentence=sentence, phrases=[])

        if request.method == "DELETE":
            Sentence().delete(sentence_id, db)
            return ""

        if request.method == "PUT":
            words = request.form.get("words")
            Sentence().update(sentence_id, words, db)


        sentence = Sentence().get(sentence_id, db)
        phrases = Phrase().get_for_sentence(sentence_id, db)

        return render_template("sentence.html", sentence=sentence, phrases=phrases)


@app.route("/phrases/analysis", methods=["POST"])
def analysis():
    with engine.connect() as db:
        phrase_parts = []
        # From the html a token will have <word index>@@<word>
        for token, switch in request.form.items():
            if switch == "on":
                index, word = token.split("@@")
                phrase_parts.append((int(index), word))

            if token == "sentence":
                sentence_id = switch

        phrase = " ".join(
            [
                word.lower().strip(punctuation)
                for _, word in sorted(phrase_parts)
            ]
        )
        Phrase().new(sentence_id, phrase, db)
        phrases = Phrase().get_for_sentence(sentence_id, db)

        return render_template("phrases.html", phrases=phrases)



@app.route("/phrases", methods=["GET", "POST"])
def phrases():
    # This should have a query to provide an init and the
    # the plain function will just take a word, definition.
    with engine.connect() as db:
        if request.method == "POST":
            words = request.form.get("words")
            Phrase().new(None, words, db)

        phrases = Phrase().all(db)
        return render_template("phrases.html", phrases=phrases)


@app.route("/phrases/<phrase_id>", methods=["GET", "DELETE"])
def phrase(phrase_id):
    with engine.connect() as db:
        if request.method == "DELETE":
            Phrase().delete(phrase_id, db)
            return ""

        phrase = Phrase().get(phrase_id, db)
        if request.args.get("inline") == "yes":
            return render_template("phrase_inline.html", phrase=phrase)

        if request.args.get("inline_edit") == "yes":
            return render_template("phrase_inline_edit.html", phrase=phrase)

        return render_template("phrase.html", phrase=phrase)


@app.route("/definitions", methods=["POST"])
def definitions():
    acceptable_statuses = {"NEW", "EXPLORING", "ACCEPTED", "STUCK"}
    with engine.connect() as db:
        if request.method == "POST":
            phrase_id = request.form.get("phrase_id")
            definition = request.form.get("definition")
            status = request.form.get("status", "NEW")
            if status not in acceptable_statuses:
                return render_template("error_row.html", phrase_id=phrase_id)
            if definition:  # If the string is None or blank, don't save it.
                Phrase().revise_definition(phrase_id, definition, db)
            if status != "NEW":
                Phrase().set_status(phrase_id, status, db)

            return redirect(f"/phrases/{phrase_id}?inline=yes")

    return abort(404)


@app.route("/help")
def help():
    return render_template("help.html")


if __name__ == "__main__":
    import sys
    from ferdinand_admin import banner_name
    
    debug = "-db" in sys.argv
    
    if debug:
        print("RUNNING IN DEBUG MODE")
    print(banner_name)
    app.run(debug=debug)
