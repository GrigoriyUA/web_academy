import math
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

ALLOWED_CHARS = set("0123456789+-*/().% ")


def make_context(mode="deg"):
    to_r   = math.radians if mode == "deg" else lambda x: x
    from_r = math.degrees if mode == "deg" else lambda x: x

    def _safe_tan(x):
        r = to_r(x)
        if abs(math.cos(r)) < 1e-15:
            raise ValueError("Undefined (tan 90°)")
        return math.tan(r)

    return {
        "__builtins__": {},
        "sin":  lambda x: math.sin(to_r(x)),
        "cos":  lambda x: math.cos(to_r(x)),
        "tan":  _safe_tan,
        "asin": lambda x: from_r(math.asin(x)),
        "acos": lambda x: from_r(math.acos(x)),
        "atan": lambda x: from_r(math.atan(x)),
        "sqrt": math.sqrt,
        "log":  math.log10,
        "ln":   math.log,
        "abs":  abs,
        "pi":   math.pi,
        "e":    math.e,
    }


def calculate(expression, mode="deg"):
    try:
        clean = expression.replace("^", "**")
        if not all(c in ALLOWED_CHARS or c.isalpha() or c in "^_" for c in clean):
            return None, "Invalid characters"
        ctx = make_context(mode)
        result = eval(clean, ctx)  # noqa: S307
        if not isinstance(result, (int, float)):
            return None, "Invalid expression"
        if math.isnan(result) or math.isinf(result):
            return None, "Math error"
        return result, None
    except ZeroDivisionError:
        return None, "Division by zero"
    except ValueError as exc:
        return None, str(exc)
    except Exception:
        return None, "Invalid expression"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calc():
    data = request.get_json()
    expression = data.get("expression", "")
    mode = data.get("mode", "deg")
    result, error = calculate(expression, mode)
    if error:
        return jsonify({"error": error})
    return jsonify({"result": result})


if __name__ == "__main__":
    import threading, webbrowser
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5002")).start()
    app.run(debug=False, port=5002)
