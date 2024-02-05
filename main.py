from string import punctuation
import json

from flask import Flask, abort, render_template, request, redirect
from crud import Definable, Sentence, Definition


app = Flask(__name__)


with open("project_conf.json") as f:
    conf = json.load(f)


@app.route("/")
def index():
    project_name = conf["current_project"].replace("_", " ")
    return render_template("index.html" , current_project=project_name)


@app.route("/sentences", methods=["GET", "POST"])
def sentences():
    if request.method == "POST":
        words = request.form.get("sentence")
        sentence = Sentence().new(words)

        return render_template("sentence.html", sentence=sentence, phrases=[])

    sentences = Sentence().all()
    return render_template("sentences.html", sentences=sentences)


@app.route("/sentences/<sentence_id>", methods=["GET"])
def sentence(sentence_id):
    sentence = Sentence().get(sentence_id)
    phrases = Definable().get_from_sentence(sentence_id)

    return render_template("sentence.html", sentence=sentence, phrases=phrases)


@app.route("/definables", methods=["GET", "POST"])
def definables():
    # This should have a query to provide an init and the
    # the plain function will just take a word, definition.
    if request.method == "POST":
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
        Definable().new(sentence_id, phrase)
        phrases = Definable().get_from_sentence(sentence_id)

        return render_template("phrases.html", phrases=phrases)

    phrases = Definable().all(return_definitions=True)
    return render_template("phrases.html", phrases=phrases)


@app.route("/definables/<phrase_id>", methods=["GET", "DELETE"])
def definable(phrase_id):
    if request.method == "DELETE":
        Definable().delete(phrase_id)
        return ""

    phrase = Definable().get(phrase_id, return_definition=True)
    if request.args.get("inline") == "yes":
        return render_template("phrase_inline.html", phrase=phrase)

    if request.args.get("inline_edit") == "yes":
        return render_template("phrase_inline_edit.html", phrase=phrase)

    return render_template("phrase.html", phrase=phrase)


@app.route("/definitions", methods=["POST"])
def definitions():
    if request.method == "POST":
        phrase_id = request.form.get("phrase_id")
        definition = request.form.get("definition")
        if definition: # If the string is None or blank, don't save it.
            sentence = Sentence().new(definition)
            Definition().new(phrase_id, sentence.id)

        return redirect(f"/definables/{phrase_id}?inline=yes")

    return abort(404)


@app.route("/help")
def help():
    return render_template("help.html")


if __name__ == "__main__":
    from manager import banner_name
    print(banner_name)
    app.run()
