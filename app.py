import cs50
import re
from flask import Flask, abort, redirect, render_template, request
from html import escape
from werkzeug.exceptions import default_exceptions, HTTPException

from helpers import lines, sentences, substrings

# Configure application
app = Flask(__name__)

# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Handle requests for / via GET (and POST)"""
    return render_template("index.html")


@app.route("/compare", methods=["POST"])
def compare():
    """Handle requests for /compare via POST"""

    # Leer archivos
    if not request.files["file1"] or not request.files["file2"]:
        abort(400, "missing file")
    try:
        file1 = request.files["file1"].read().decode("utf-8")
        file2 = request.files["file2"].read().decode("utf-8")
    except Exception:
        abort(400, "invalid file")

    # Compara archivos
    if not request.form.get("algorithm"):
        abort(400, "missing algorithm")
    elif request.form.get("algorithm") == "lines":
        regexes = [f"^{re.escape(match)}$" for match in lines(file1, file2)]
    elif request.form.get("algorithm") == "sentences":
        regexes = [re.escape(match) for match in sentences(file1, file2)]
    elif request.form.get("algorithm") == "substrings":
        if not request.form.get("length"):
            abort(400, "missing length")
        elif not int(request.form.get("length")) > 0:
            abort(400, "invalid length")
        regexes = [re.escape(match) for match in substrings(
            file1, file2, int(request.form.get("length")))]
    else:
        abort(400, "invalid algorithm")

    # Destaca en amarillo el contenido de los archivos
    highlights1 = highlight(file1, regexes)
    highlights2 = highlight(file2, regexes)

    # Comparacion de salida
    return render_template("compare.html", file1=highlights1, file2=highlights2)


def highlight(s, regexes):
    """Highlight all instances of regexes in s."""

    # Obtiene los intervalos de las palabras que hacen MATCH
    intervals = []
    for regex in regexes:
        if not regex:
            continue
        matches = re.finditer(regex, s, re.MULTILINE)
        for match in matches:
            intervals.append((match.start(), match.end()))
    intervals.sort(key=lambda x: x[0])

    # Combina intervalos para obtener áreas resaltadas
    highlights = []
    for interval in intervals:
        if not highlights:
            highlights.append(interval)
            continue
        last = highlights[-1]

        # Si los intervalos se superponen, combínalo ( MACHINE LEARNING )
        if interval[0] <= last[1]:
            new_interval = (last[0], interval[1])
            highlights[-1] = new_interval

        # De lo contrario, comience un nuevo punto culminante ( MACHINE LEARNING )
        else:
            highlights.append(interval)

    # Mantener la lista de regiones: cada una es un índice de inicio, un índice final, un resaltado
    regions = []

    #Si no hay MATCH , entonces no mantenga nada resaltado  ( MACHINE LEARNING )
    if not highlights:
        regions = [(0, len(s), False)]

    # Si la primera región no está resaltada, designe como tal  ( MACHINE LEARNING )
    elif highlights[0][0] != 0:
        regions = [(0, highlights[0][0], False)]

    # Recorreodos las palabras y  aspectos destacados y agregue regiones
    for start, end in highlights:
        if start != 0:
            prev_end = regions[-1][1]
            if start != prev_end:
                regions.append((prev_end, start, False))
        regions.append((start, end, True))

    # Agregue la región final no resaltada si es necesario
    if regions[-1][1] != len(s):
        regions.append((regions[-1][1], len(s), False))

    # Combina regiones en el resultado final
    result = ""
    for start, end, highlighted in regions:
        escaped = escape(s[start:end])
        if highlighted:
            result += f"<span>{escaped}</span>"
        else:
            result += escaped
    return result


@app.errorhandler(HTTPException)
def errorhandler(error):
    """Handle errors"""
    return render_template("error.html", error=error), error.code


# https://github.com/pallets/flask/pull/2314
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run(debug=True)