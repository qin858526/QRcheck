from flask import Flask, render_template, request, jsonify
from waitress import serve
from datetime import datetime
import logging
import sqlite3

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(),logging.FileHandler('app.log', encoding='utf-8', mode='a+')])


app = Flask(__name__)

# 比对的二维码数据
# VALID_CODES = {"8000814487", "QWE456"} 8000814487|24|4005352645|3010144585||||

def init_db():
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS CheckResults
                 (   id INTEGER PRIMARY KEY AUTOINCREMENT,
                     code1 TEXT, 
                     code2 TEXT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     result TEXT)''')
    # # 插入一些测试数据
    # c.execute("INSERT INTO CheckResults (code1, code2) VALUES ('8000814487', '8000814487')")
    # c.execute("INSERT INTO CheckResults (code1, code2) VALUES ('QWE456', 'QWE456')")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('login.html')

# 二维码比对逻辑
@app.route('/check', methods=['POST'])
def check():
    try:
        code1 = request.json.get("code1", "")
        code2 = request.json.get("code2", "")
        if code1 and code2:
            if "|" in code1:
                code1 = code1.split("|")[0]
            if "|" in code2:
                code2 = code2.split("|")[0]
        ok = code1 == code2 and code1 != "" 
        log_check_result(code1, code2, "有效" if ok else "无效")
        return jsonify({"ok": ok, "msg": "✅ 有效" if ok else "❌ 无效"})
    except Exception as e:
        logging.error(f"比对出错：{str(e)}", exc_info=True)
        return jsonify({"ok": False, "msg": f"❌ 错误： {str(e)}"})

# 查询历史比对记录
@app.route('/history')
def history():
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    c.execute("SELECT id, code1, code2, timestamp, result FROM CheckResults ORDER BY timestamp DESC")
    records = c.fetchall()
    conn.close()
    # print("查询历史记录:", records)
    return render_template('history.html', records=records)

# 记录比对结果到数据库
def log_check_result(code1, code2, result):
    conn = sqlite3.connect('CheckResult.db')
    c = conn.cursor()
    beijing_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print("记录比对结果:", code1, code2, result)
    c.execute("INSERT INTO CheckResults (code1, code2, result, timestamp) VALUES (?, ?, ?, ?)", (code1, code2, result, beijing_time))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8888)
    # app.run(debug=True, host='0.0.0.0', port=8888)
