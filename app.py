from flask import Flask, render_template_string, request, redirect, url_for, session
import os
import json
import datetime

app = Flask(__name__)
app.secret_key = 'marouane_morocco_in_paris_key_2026'

DATA_FILE = 'database_storage.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "users": [
                {"username": "marouane", "password": "123"},
                {"username": "hamza", "password": "123"}
            ],
            "products": [],
            "logs": []
        }
        save_data(initial_data)
        return initial_data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "users" not in data: data["users"] = [{"username": "marouane", "password": "123"}, {"username": "hamza", "password": "123"}]
            if "products" not in data: data["products"] = []
            if "logs" not in data: data["logs"] = []
            return data
    except:
        return {"users": [{"username": "marouane", "password": "123"}, {"username": "hamza", "password": "123"}], "products": [], "logs": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def log_action(username, action, details):
    data = load_data()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = {"timestamp": now, "username": username, "action": action, "details": details}
    data["logs"].insert(0, new_log)
    data["logs"] = data["logs"][:50]
    save_data(data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        data = load_data()
        user = next((u for u in data["users"] if u["username"] == username and u["password"] == password), None)
        if user:
            session['logged_in'] = True
            session['username'] = user["username"]
            return redirect(url_for('index'))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة !"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    data = load_data()
    products = data["products"]
    logs = data["logs"][:15]
    
    return render_template_string(HTML_TEMPLATE, 
                                products=products, 
                                logs=logs,
                                current_user=session.get('username'))

@app.route('/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    name = request.form.get('name', '').strip()
    missing_items = request.form.get('missing_items', '').strip()
    status = request.form.get('status', 'طلبناها')
    current_user = session.get('username', 'marouane')
    
    data = load_data()
    new_id = 1 if not data["products"] else max(p['id'] for p in data["products"]) + 1
    
    new_p = {
        "id": new_id,
        "name": name or "منتج",
        "added_by": current_user,
        "missing_items": missing_items,
        "status": status
    }
    
    data["products"].append(new_p)
    save_data(data)
    
    log_action(current_user, "AJOUT", f"إضافة المنتج: {name}")
    return redirect(url_for('index'))

@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    current_user = session.get('username', 'Inconnu')
    data = load_data()
    
    product = next((p for p in data["products"] if p['id'] == id), None)
    if product:
        log_action(current_user, "SUPPRESSION", f"حذف المنتج [ID: {id}] {product['name']}")
        data["products"] = [p for p in data["products"] if p['id'] != id]
        save_data(data)
        
    return redirect(url_for('index'))

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - Morocco in Paris</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 100%; max-width: 350px; text-align: center; }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; text-align: right; }
        button { background: #27ae60; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 10px; }
        button:hover { background: #219653; }
        .error { color: #e74c3c; font-size: 14px; margin-bottom: 10px; }
        .info-accounts { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 13px; color: #555; text-align: right; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 تسجيل الدخول</h2>
        <div class="info-accounts">
            <b>الحسابات المتاحة:</b><br>
            - <code>marouane</code> (كلمة المرور: <code>123</code>)<br>
            - <code>hamza</code> (كلمة المرور: <code>123</code>)
        </div>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required autocomplete="off">
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول</button>
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة وتتبع المنتجات - Morocco in Paris</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1100px; margin: auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header-flex { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        h1 { color: #2c3e50; margin: 0; font-size: 24px; }
        .header-actions { display: flex; gap: 10px; align-items: center; }
        .btn-logout { background: #c0392b; color: white; padding: 8px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 13px; }
        
        .collapsible-section { margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; background: #fff; }
        .collapsible-btn { background: #34495e; color: white; cursor: pointer; padding: 15px 20px; width: 100%; border: none; text-align: right; outline: none; font-size: 16px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; transition: background 0.3s; }
        .collapsible-btn:hover { background: #2c3e50; }
        .collapsible-content { padding: 20px; display: none; background: #fff; border-top: 1px solid #cbd5e1; }
        .collapsible-content.active { display: block; }

        form.inline-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; align-items: center; }
        form.inline-form input, form.inline-form select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
        form.inline-form button { background: #27ae60; color: white; border: none; padding: 11px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 15px; }
        form.inline-form button:hover { background: #219653; }

        .table-responsive { width: 100%; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 5px; min-width: 600px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: center; font-size: 14px; }
        th { background: #2980b9; color: white; }
        
        .badge-marouane { background: #2980b9; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .badge-hamza { background: #8e44ad; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        
        .badge-ordered { background-color: #f39c12; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-ready { background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-way { background-color: #2980b9; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }

        .btn-danger { background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; }
        .btn-danger:hover { background: #c0392b; }
        .log-box { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; margin-top: 30px; text-align: left; direction: ltr; }
    </style>
</head>
<body>
<div class="container">
    <div class="header-flex">
        <div>
            <h1>Morocco in Paris - تتبع المنتجات والنواقص</h1>
            <small style="color: #666;">متصل حالياً بـ: <b>{{ current_user }}</b></small>
        </div>
        <div class="header-actions">
            <a href="/logout" class="btn-logout">تسجيل الخروج 🚪</a>
        </div>
    </div>

    <!-- قسم 1: إضافة منتج جديد (قابل للطي) -->
    <div class="collapsible-section">
        <button type="button" class="collapsible-btn" onclick="toggleSection('section-add')">
            <span>➕ إضافة منتج جديد أو أمر ناقص (اضغط للفتح/الإغلاق)</span>
            <span>▼</span>
        </button>
        <div id="section-add" class="collapsible-content active">
            <form method="POST" action="/add" class="inline-form">
                <input type="text" name="name" placeholder="اسم المنتج" required>
                <input type="text" name="missing_items" placeholder="الأمور الناقصة للتقييد (مثلاً: أوراق، تغليف...)">
                <select name="status">
                    <option value="طلبناها">طلبناها</option>
                    <option value="موال">موال (جاهز)</option>
                    <option value="فالطريق">فالطريق</option>
                </select>
                <button type="submit">حفظ وإضافة</button>
            </form>
        </div>
    </div>

    <!-- قسم 2: قائمة المنتجات والنواقص (قابل للطي) -->
    <div class="collapsible-section">
        <button type="button" class="collapsible-btn" onclick="toggleSection('section-list')" style="background: #2980b9;">
            <span>📦 قائمة المنتجات والحالة الحالية (اضغط للفتح/الإغلاق)</span>
            <span>▼</span>
        </button>
        <div id="section-list" class="collapsible-content active">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>الرقم</th>
                            <th>اسم المنتج</th>
                            <th>سجله (المسؤول)</th>
                            <th>الأمور الناقصة للتقييد</th>
                            <th>الحالة</th>
                            <th>إجراء</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in products %}
                        <tr>
                            <td>{{ p.id }}</td>
                            <td><b>{{ p.name }}</b></td>
                            <td>
                                {% if p.added_by == 'hamza' %}
                                    <span class="badge-hamza">hamza</span>
                                {% else %}
                                    <span class="badge-marouane">marouane</span>
                                {% endif %}
                            </td>
                            <td>{{ p.missing_items if p.missing_items else 'لا توجد' }}</td>
                            <td>
                                {% if p.status == 'طلبناها' %}
                                    <span class="badge-ordered">طلبناها</span>
                                {% elif p.status == 'موال' %}
                                    <span class="badge-ready">موال</span>
                                {% elif p.status == 'فالطريق' %}
                                    <span class="badge-way">فالطريق</span>
                                {% else %}
                                    <span class="badge-ordered">{{ p.status }}</span>
                                {% endif %}
                            </td>
                            <td>
                                <form action="/delete_product/{{ p.id }}" method="POST" style="margin:0;" onsubmit="return confirm('هل أنت متأكد من حذف هذا العنصر؟');">
                                    <button type="submit" class="btn-danger">🗑️ حذف</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="6" style="color: #777;">لا توجد أي منتجات مسجلة حالياً.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <h3 style="margin-top: 30px; color: #2c3e50; text-align: right;">📋 سجل النشاطات (من قام بماذا؟)</h3>
    <div class="log-box">
        {% for log in logs %}
            <div>[{{ log.timestamp }}] <b>{{ log.username }}</b> -> [{{ log.action }}: {{ log.details }}]</div>
        {% else %}
            <div>No activity logged yet.</div>
        {% endfor %}
    </div>
</div>

<script>
    function toggleSection(sectionId) {
        var content = document.getElementById(sectionId);
        if (content.classList.contains('active')) {
            content.classList.remove('active');
        } else {
            content.classList.add('active');
        }
    }
</script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
