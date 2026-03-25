from flask import Flask, render_template, request, jsonify
from waitress import serve

app = Flask(__name__)

# 比对的二维码数据
# VALID_CODES = {"8000814487", "QWE456"} 8000814487|24|4005352645|3010144585||||

@app.route('/')
def index():
    return render_template('check.html')

@app.route('/check', methods=['POST'])
def check():
    code1 = request.json.get("code1", "")
    code2 = request.json.get("code2", "")
    if code1 and code2:
        if "|" in code1:
            code1 = code1.split("|")[0]
        if "|" in code2:
            code2 = code2.split("|")[0]
    print(code1, code2)
    ok = code1 == code2 and code1 != "" 
    return jsonify({"ok": ok, "msg": "✅ 有效" if ok else "❌ 无效"})

if __name__ == '__main__':
    # serve(app, host='0.0.0.0', port=8888)
    app.run(debug=True, host='0.0.0.0', port=8888)
