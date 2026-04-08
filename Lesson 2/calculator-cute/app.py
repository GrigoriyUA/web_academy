from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def calculate(expression):
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return None, "Invalid characters"
        result = eval(expression)
        return result, None
    except ZeroDivisionError:
        return None, "Division by zero"
    except Exception:
        return None, "Invalid expression"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calc():
    data = request.get_json()
    expression = data.get("expression", "")
    result, error = calculate(expression)
    if error:
        return jsonify({"error": error})
    return jsonify({"result": result})


if __name__ == "__main__":
    import threading, webbrowser
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5001")).start()
    app.run(debug=False, port=5001)
