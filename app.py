from flask import Flask, render_template_string, request, redirect, url_for, Response, session
from flask_sqlalchemy import SQLAlchemy
import os
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marouane_hamza_full_track.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = 'marouane_hamza_full_track_key_2026'

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# جدول المستخدمين
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# جدول المنتجات مع تتبع شكون زادو وشكون مسحو (في حالة أرشيف الحذف أو إظهاره)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    invoice = db.Column(db.String(200), nullable=True)
    added_by = db.Column(db.String(50), nullable=True)

# جدول المصاريف الشخصية
class PersonalExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200), nullable=True)
    invoice = db.Column(db.String(200), nullable=True)
    added_by = db.Column(db.String(50), nullable=True)

# جدول سجل العمليات (History / Audit Log) لتتبع من أضاف ومن مسح بدقة
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False) # 'AJOUT' أو 'SUPPRESSION'
    details = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='marouane').first():
        db.session.add(User(username='marouane', password='123'))
    if not User.query.filter_by(username='hamza').first():
        db.session.add(User(username='hamza', password='123'))
    db.session.commit()

def get_logo_filename():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        return None
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.lower().startswith('logo') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return f
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            return f
    return None

def log_action(username, action, details):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = ActivityLog(timestamp=now, username=username, action=action, details=details)
    db.session.add(log)
    db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['logged_in'] = True
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect !"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    error = None
    success = None
    if request.method == 'POST':
        old_pass = request.form.get('old_password')
        new_pass = request.form.get('new_password')
        confirm_pass = request.form.get('confirm_password')
        
        current_username = session.get('username')
        user = User.query.filter_by(username=current_username).first()
        
        if user.password != old_pass:
            error = "L'ancien mot de passe est incorrect !"
        elif not new_pass or len(new_pass.strip()) == 0:
            error = "Veuillez entrer un nouveau mot de passe valide."
        elif new_pass != confirm_pass:
            error = "Les nouveaux mots de passe ne correspondent pas !"
        else:
            user.password = new_pass.strip()
            db.session.commit()
            success = "Mot de passe modifié avec succès !"
            
    return render_template_string(CHANGE_PASSWORD_TEMPLATE, error=error, success=success)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    search_query = request.args.get('search', '')
    if search_query:
        products = Product.query.filter(
            (Product.name.contains(search_query)) | 
            (Product.id.like(f"%{search_query}%"))
        ).all()
    else:
        products = Product.query.all()
        
    expenses = PersonalExpense.query.all()
    logs = ActivityLog.query.order_by(ActivityLog.id.desc()).limit(15).all() # آخر 15 نشاط للتتبع
    
    total_personal = sum(exp.amount for exp in expenses)
    total_expenses = sum(p.price * p.quantity for p in products)
    logo_file = get_logo_filename()
    
    return render_template_string(HTML_TEMPLATE, 
                                products=products, 
                                expenses=expenses,
                                logs=logs,
                                total_expenses=total_expenses, 
                                total_personal=total_personal,
                                search_query=search_query,
                                logo_file=logo_file,
                                current_user=session.get('username'))

@app.route('/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Général').strip()
    price = float(request.form.get('price') or 0.0)
    quantity = int(request.form.get('quantity') or 1)
    status = request.form.get('status', 'Disponible')
    current_user = session.get('username', 'marouane')
    
    invoice_filename = ""
    if 'invoice' in request.files:
        inv_file = request.files['invoice']
        if inv_file.filename != '':
            invoice_filename = "inv_" + inv_file.filename
            inv_file.save(os.path.join(app.config['UPLOAD_FOLDER'], invoice_filename))

    new_p = Product(name=name or "Produit", category=category, price=price, quantity=quantity, status=status, image="", invoice=invoice_filename, added_by=current_user)
    db.session.add(new_p)
    db.session.commit()
    
    log_action(current_user, "AJOUT", f"Ajout du produit: {name} (Prix: {price}€)")
    return redirect(url_for('index'))

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    date = request.form.get('date', '')
    amount = float(request.form.get('amount') or 0.0)
    note = request.form.get('note', '')
    current_user = session.get('username', 'marouane')
    
    inv_filename = ""
    if 'invoice' in request.files:
        file = request.files['invoice']
        if file.filename != '':
            inv_filename = "exp_" + file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], inv_filename))
            
    new_exp = PersonalExpense(date=date, amount=amount, note=note, invoice=inv_filename, added_by=current_user)
    db.session.add(new_exp)
    db.session.commit()
    
    log_action(current_user, "AJOUT", f"Ajout dépense personnelle: {amount}€ ({note})")
    return redirect(url_for('index'))

@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    current_user = session.get('username', 'Inconnu')
    product = Product.query.get_or_404(id)
    
    log_action(current_user, "SUPPRESSION", f"Suppression du produit [ID: {product.id}] {product.name} (Ajouté initialement par: {product.added_by})")
    
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_expense/<int:id>', methods=['POST'])
def delete_expense(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    current_user = session.get('username', 'Inconnu')
    expense = PersonalExpense.query.get_or_404(id)
    
    log_action(current_user, "SUPPRESSION", f"Suppression dépense [ID: {expense.id}] Montant: {expense.amount}€ (Ajouté par: {expense.added_by})")
    
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/export_report')
def export_report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Categorie', 'Prix', 'Quantite', 'Statut', 'Ajoute par'])
    for p in Product.query.all():
        writer.writerow([p.id, p.name, p.category, p.price, p.quantity, p.status, p.added_by])
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=Rapport_Stock.csv"})

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Marouane & Hamza</title>
    <style>
        body { font-family: Arial, sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 100%; max-width: 350px; text-align: center; }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #27ae60; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 10px; }
        button:hover { background: #219653; }
        .error { color: #e74c3c; font-size: 14px; margin-bottom: 10px; }
        .info-accounts { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 13px; color: #555; text-align: left; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 Connexion</h2>
        <div class="info-accounts">
            <b>Comptes disponibles :</b><br>
            - <code>marouane</code> (Mot de passe: <code>123</code>)<br>
            - <code>hamza</code> (Mot de passe: <code>123</code>)
        </div>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Nom d'utilisateur" required autocomplete="off">
            <input type="password" name="password" placeholder="Mot de passe" required>
            <button type="submit">Se connecter</button>
        </form>
    </div>
</body>
</html>
"""

CHANGE_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Changer le mot de passe</title>
    <style>
        body { font-family: Arial, sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); width: 100%; max-width: 350px; text-align: center; }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #e67e22; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px; margin-top: 10px; }
        button:hover { background: #d35400; }
        .error { color: #e74c3c; font-size: 14px; margin-bottom: 10px; }
        .success { color: #27ae60; font-size: 14px; margin-bottom: 10px; }
        .link { margin-top: 15px; display: block; font-size: 14px; color: #2980b9; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔑 Modifier Mot de Passe</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if success %}<div class="success">{{ success }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="old_password" placeholder="Ancien mot de passe" required>
            <input type="password" name="new_password" placeholder="Nouveau mot de passe" required>
            <input type="password" name="confirm_password" placeholder="Confirmer le nouveau" required>
            <button type="submit">Mettre à jour</button>
        </form>
        <a href="/" class="link">⬅️ Retour à l'accueil</a>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestion Stock - Marouane & Hamza</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header-flex { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;}
        .logo-title { display: flex; align-items: center; gap: 15px; }
        .logo-title img { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #2980b9; }
        h1 { color: #2c3e50; margin: 0; font-size: 24px; }
        .header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        form { background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e1e1e1; margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        form input, form select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; flex: 1; min-width: 130px; }
        form button { background: #27ae60; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .table-responsive { width: 100%; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; min-width: 600px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
        th { background: #2980b9; color: white; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .card-stat { background: #e8f4f8; padding: 15px; border-radius: 8px; flex: 1; min-width: 200px; border-left: 5px solid #2980b9; }
        .btn-danger { background: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; text-decoration: none; }
        .btn-danger:hover { background: #c0392b; }
        .btn-logout { background: #c0392b; color: white; padding: 8px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 13px; }
        .btn-pass { background: #e67e22; color: white; padding: 8px 12px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 13px; }
        .badge-marouane { background: #2980b9; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .badge-hamza { background: #8e44ad; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .log-box { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
<div class="container">
    <div class="header-flex">
        <div class="logo-title">
            {% if logo_file %}
                <img src="{{ url_for('static', filename='uploads/' + logo_file) }}" alt="Logo">
            {% endif %}
            <div>
                <h1>Gestion de Stock & Dépenses</h1>
                <small style="color: #666;">Connecté en tant que: <b>{{ current_user }}</b></small>
            </div>
        </div>
        <div class="header-actions">
            <a href="/export_report" style="background:#16a085; color:white; padding:8px 12px; border-radius:5px; text-decoration:none; font-weight:bold; font-size:13px;">📥 Rapport</a>
            <a href="/change_password" class="btn-pass">🔑 Changer Code</a>
            <a href="/logout" class="btn-logout">Déconnexion 🚪</a>
        </div>
    </div>

    <div class="stats">
        <div class="card-stat">
            <h3>Total Dépenses Stock</h3>
            <p style="font-size: 20px; font-weight: bold; color: #2c3e50;">€ {{ "%.2f"|format(total_expenses) }}</p>
        </div>
        <div class="card-stat" style="background: #eafaf1; border-left-color: #27ae60;">
            <h3>Total Dépenses Personnelles</h3>
            <p style="font-size: 20px; font-weight: bold; color: #27ae60;">€ {{ "%.2f"|format(total_personal) }}</p>
        </div>
    </div>

    <form method="GET" action="/" style="background: #f1f4f6;">
        <input type="text" name="search" placeholder="Rechercher par Nom ou ID..." value="{{ search_query }}">
        <button type="submit" style="background: #2980b9;">Rechercher</button>
        {% if search_query %}
            <a href="/" style="background: #e74c3c; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; display:inline-block; line-height:normal;">Réinitialiser</a>
        {% endif %}
    </form>

    <h2>Ajouter un Produit / Facture</h2>
    <form method="POST" action="/add" enctype="multipart/form-data">
        <input type="text" name="name" placeholder="Nom du produit" required>
        <input type="text" name="category" placeholder="Catégorie" required>
        <input type="number" step="0.01" name="price" placeholder="Prix (€)" required>
        <input type="number" name="quantity" placeholder="Quantité" value="1" required>
        <select name="status">
            <option value="Disponible">Disponible</option>
            <option value="Reçu">Reçu</option>
        </select>
        <div style="flex:1; min-width:180px;">
            <label style="font-size:11px; display:block; color:#555;">Facture (JPG/PNG):</label>
            <input type="file" name="invoice" accept=".jpg, .jpeg, .png">
        </div>
        <button type="submit">Enregistrer</button>
    </form>

    <h2>Inventaire des Produits</h2>
    <div class="table-responsive">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nom</th>
                    <th>Catégorie</th>
                    <th>Prix (€)</th>
                    <th>Quantité</th>
                    <th>Statut</th>
                    <th>Ajouté par</th>
                    <th>Facture</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for p in products %}
                <tr>
                    <td>{{ p.id }}</td>
                    <td>{{ p.name }}</td>
                    <td>{{ p.category }}</td>
                    <td>€ {{ "%.2f"|format(p.price) }}</td>
                    <td>{{ p.quantity }}</td>
                    <td>{{ p.status }}</td>
                    <td>
                        {% if p.added_by == 'hamza' %}
                            <span class="badge-hamza">hamza</span>
                        {% else %}
                            <span class="badge-marouane">marouane</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if p.invoice %}
                            <a href="{{ url_for('static', filename='uploads/' + p.invoice) }}" target="_blank">📄 Voir</a>
                        {% else %}
                            -
                        {% endif %}
                    </td>
                    <td>
                        <form action="/delete_product/{{ p.id }}" method="POST" style="margin:0; background:none; border:none; padding:0;" onsubmit="return confirm('Voulez-vous vraiment supprimer ce produit ?');">
                            <button type="submit" class="btn-danger">🗑️ Supprimer</button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="9" style="color: #777;">Aucun produit trouvé.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <h2 style="margin-top: 40px;">Gestion des Dépenses Personnelles</h2>
    <form method="POST" action="/add_expense" enctype="multipart/form-data">
        <input type="date" name="date" required>
        <input type="number" step="0.01" name="amount" placeholder="Montant (€)" required>
        <input type="text" name="note" placeholder="Note / Description">
        <div style="flex:1; min-width:180px;">
            <label style="font-size:11px; display:block; color:#555;">Justificatif (JPG/PDF):</label>
            <input type="file" name="invoice" accept=".jpg, .jpeg, .png, .pdf">
        </div>
        <button type="submit" style="background: #e67e22;">Ajouter Dépense</button>
    </form>

    <div class="table-responsive">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Date</th>
                    <th>Montant (€)</th>
                    <th>Note</th>
                    <th>Ajouté par</th>
                    <th>Justificatif</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for exp in expenses %}
                <tr>
                    <td>{{ exp.id }}</td>
                    <td>{{ exp.date }}</td>
                    <td>€ {{ "%.2f"|format(exp.amount) }}</td>
                    <td>{{ exp.note }}</td>
                    <td>
                        {% if exp.added_by == 'hamza' %}
                            <span class="badge-hamza">hamza</span>
                        {% else %}
                            <span class="badge-marouane">marouane</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if exp.invoice %}
                            <a href="{{ url_for('static', filename='uploads/' + exp.invoice) }}" target="_blank">📄 Voir</a>
                        {% else %}
                            -
                        {% endif %}
                    </td>
                    <td>
                        <form action="/delete_expense/{{ exp.id }}" method="POST" style="margin:0; background:none; border:none; padding:0;" onsubmit="return confirm('Voulez-vous vraiment supprimer cette dépense ?');">
                            <button type="submit" class="btn-danger">🗑️ Supprimer</button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="7" style="color: #777;">Aucune dépense enregistrée.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- سجل الأنشطة والعمليات (مراقبة من أضاف ومن مسح) -->
    <h3 style="margin-top: 40px; color: #2c3e50;">📋 Journal d'activité (Qui a fait quoi ?)</h3>
    <div class="log-box">
        {% for log in logs %}
            <div>[{{ log.timestamp }}] <b>{{ log.username }}</b> -> [{{ log.action }}]: {{ log.details }}</div>
        {% else %}
            <div>Aucune activité enregistrée pour le moment.</div>
        {% endfor %}
    </div>
</div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
