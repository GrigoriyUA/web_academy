from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Калорії на 100 г / мл
FOODS = {
    # Фрукти
    "яблуко":           {"cal": 52,  "unit": "г",  "emoji": "🍎"},
    "банан":            {"cal": 89,  "unit": "г",  "emoji": "🍌"},
    "апельсин":         {"cal": 47,  "unit": "г",  "emoji": "🍊"},
    "виноград":         {"cal": 67,  "unit": "г",  "emoji": "🍇"},
    "полуниця":         {"cal": 32,  "unit": "г",  "emoji": "🍓"},
    "кавун":            {"cal": 30,  "unit": "г",  "emoji": "🍉"},
    "груша":            {"cal": 57,  "unit": "г",  "emoji": "🍐"},
    "манго":            {"cal": 65,  "unit": "г",  "emoji": "🥭"},
    "авокадо":          {"cal": 160, "unit": "г",  "emoji": "🥑"},
    "лимон":            {"cal": 29,  "unit": "г",  "emoji": "🍋"},
    "персик":           {"cal": 39,  "unit": "г",  "emoji": "🍑"},
    "вишня":            {"cal": 50,  "unit": "г",  "emoji": "🍒"},
    "ананас":           {"cal": 50,  "unit": "г",  "emoji": "🍍"},
    # Овочі
    "морква":           {"cal": 41,  "unit": "г",  "emoji": "🥕"},
    "огірок":           {"cal": 15,  "unit": "г",  "emoji": "🥒"},
    "помідор":          {"cal": 18,  "unit": "г",  "emoji": "🍅"},
    "картопля":         {"cal": 77,  "unit": "г",  "emoji": "🥔"},
    "броколі":          {"cal": 34,  "unit": "г",  "emoji": "🥦"},
    "кукурудза":        {"cal": 86,  "unit": "г",  "emoji": "🌽"},
    "часник":           {"cal": 149, "unit": "г",  "emoji": "🧄"},
    "цибуля":           {"cal": 40,  "unit": "г",  "emoji": "🧅"},
    "шпинат":           {"cal": 23,  "unit": "г",  "emoji": "🥬"},
    "гриби":            {"cal": 22,  "unit": "г",  "emoji": "🍄"},
    "баклажан":         {"cal": 25,  "unit": "г",  "emoji": "🍆"},
    "перець болгарський":{"cal": 31, "unit": "г",  "emoji": "🫑"},
    # М'ясо та риба
    "куряча грудка":    {"cal": 165, "unit": "г",  "emoji": "🍗"},
    "куряче стегно":    {"cal": 209, "unit": "г",  "emoji": "🍗"},
    "яловичина":        {"cal": 250, "unit": "г",  "emoji": "🥩"},
    "свинина":          {"cal": 297, "unit": "г",  "emoji": "🥩"},
    "сьомга":           {"cal": 208, "unit": "г",  "emoji": "🐟"},
    "тунець":           {"cal": 144, "unit": "г",  "emoji": "🐟"},
    "тунець консерва":  {"cal": 96,  "unit": "г",  "emoji": "🥫"},
    "креветки":         {"cal": 99,  "unit": "г",  "emoji": "🦐"},
    "ковбаса варена":   {"cal": 260, "unit": "г",  "emoji": "🌭"},
    "сосиски":          {"cal": 290, "unit": "г",  "emoji": "🌭"},
    # Молочне
    "яйце":             {"cal": 155, "unit": "г",  "emoji": "🥚"},
    "молоко":           {"cal": 61,  "unit": "мл", "emoji": "🥛"},
    "кефір":            {"cal": 51,  "unit": "мл", "emoji": "🥛"},
    "сметана 20%":      {"cal": 206, "unit": "г",  "emoji": "🥛"},
    "йогурт натуральний":{"cal": 61, "unit": "г",  "emoji": "🫙"},
    "сир твердий":      {"cal": 402, "unit": "г",  "emoji": "🧀"},
    "сир кисломолочний":{"cal": 121, "unit": "г",  "emoji": "🧀"},
    "вершкове масло":   {"cal": 717, "unit": "г",  "emoji": "🧈"},
    # Зернові
    "рис варений":      {"cal": 130, "unit": "г",  "emoji": "🍚"},
    "гречка варена":    {"cal": 92,  "unit": "г",  "emoji": "🍚"},
    "вівсянка варена":  {"cal": 68,  "unit": "г",  "emoji": "🥣"},
    "макарони варені":  {"cal": 131, "unit": "г",  "emoji": "🍝"},
    "хліб білий":       {"cal": 265, "unit": "г",  "emoji": "🍞"},
    "хліб чорний":      {"cal": 201, "unit": "г",  "emoji": "🍞"},
    "лаваш":            {"cal": 277, "unit": "г",  "emoji": "🫓"},
    # Горіхи та бобові
    "горіхи волоські":  {"cal": 654, "unit": "г",  "emoji": "🥜"},
    "мигдаль":          {"cal": 579, "unit": "г",  "emoji": "🥜"},
    "арахіс":           {"cal": 567, "unit": "г",  "emoji": "🥜"},
    "квасоля":          {"cal": 127, "unit": "г",  "emoji": "🫘"},
    "сочевиця варена":  {"cal": 116, "unit": "г",  "emoji": "🫘"},
    "нут варений":      {"cal": 164, "unit": "г",  "emoji": "🫘"},
    # Солодке
    "шоколад темний":   {"cal": 546, "unit": "г",  "emoji": "🍫"},
    "шоколад молочний": {"cal": 535, "unit": "г",  "emoji": "🍫"},
    "мед":              {"cal": 304, "unit": "г",  "emoji": "🍯"},
    "цукор":            {"cal": 387, "unit": "г",  "emoji": "🍬"},
    "морозиво":         {"cal": 207, "unit": "г",  "emoji": "🍦"},
    "торт":             {"cal": 340, "unit": "г",  "emoji": "🎂"},
    "печиво":           {"cal": 430, "unit": "г",  "emoji": "🍪"},
    "пончик":           {"cal": 452, "unit": "г",  "emoji": "🍩"},
    # Готові страви / фастфуд
    "піца":             {"cal": 266, "unit": "г",  "emoji": "🍕"},
    "бургер":           {"cal": 295, "unit": "г",  "emoji": "🍔"},
    "картопля фрі":     {"cal": 312, "unit": "г",  "emoji": "🍟"},
    "суші":             {"cal": 150, "unit": "г",  "emoji": "🍣"},
    "борщ":             {"cal": 49,  "unit": "мл", "emoji": "🍲"},
    "суп курячий":      {"cal": 36,  "unit": "мл", "emoji": "🍲"},
    # Напої
    "сік апельсиновий": {"cal": 45,  "unit": "мл", "emoji": "🧃"},
    "кола":             {"cal": 42,  "unit": "мл", "emoji": "🥤"},
    "пиво":             {"cal": 43,  "unit": "мл", "emoji": "🍺"},
    "вино червоне":     {"cal": 85,  "unit": "мл", "emoji": "🍷"},
    "кава чорна":       {"cal": 2,   "unit": "мл", "emoji": "☕"},
    "кава з молоком":   {"cal": 40,  "unit": "мл", "emoji": "☕"},
    # Олії
    "соняшникова олія": {"cal": 884, "unit": "мл", "emoji": "🫙"},
    "оливкова олія":    {"cal": 884, "unit": "мл", "emoji": "🫙"},
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def search():
    q = request.args.get("q", "").lower().strip()
    if not q:
        return jsonify([])
    results = [
        {"name": name, "cal": info["cal"], "unit": info["unit"], "emoji": info["emoji"]}
        for name, info in FOODS.items()
        if q in name.lower()
    ]
    results.sort(key=lambda x: x["name"].lower().index(q))
    return jsonify(results[:8])


@app.route("/api/calories", methods=["POST"])
def calories():
    data = request.get_json()
    name = data.get("name", "").lower().strip()
    qty  = data.get("qty", 0)
    if name not in FOODS:
        return jsonify({"error": f'Продукт "{name}" не знайдено'})
    try:
        qty = float(qty)
        if qty <= 0:
            return jsonify({"error": "Кількість має бути більше 0"})
    except (ValueError, TypeError):
        return jsonify({"error": "Невірна кількість"})
    info = FOODS[name]
    total = round(info["cal"] * qty / 100, 1)
    return jsonify({
        "name":  name,
        "emoji": info["emoji"],
        "cal":   info["cal"],
        "unit":  info["unit"],
        "qty":   qty,
        "total": total,
    })


if __name__ == "__main__":
    import threading, webbrowser
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5003")).start()
    app.run(debug=False, port=5003)
