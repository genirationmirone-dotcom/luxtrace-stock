from flask import Flask, render_template_string, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
import os
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marouane_stock_permanent.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    invoice = db.Column(db.String(200), nullable=True)

class PersonalExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200), nullable=True)
    invoice = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

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

@app.route('/', methods=['GET'])
def index():
    search_query = request.args.get('search', '')
    if search_query:
        products = Product.query.filter(
            (Product.name.contains(search_query)) | 
            (Product.id.like(f"%{search_query}%"))
        ).all()
    else:
        products = Product.query.all()
        
    expenses = PersonalExpense.query.all()
    total_personal = sum(exp.amount for exp in expenses)
    total_expenses = sum(p.price * p.quantity for p in products)
    logo_file = get_logo_filename()
    
    return render_template_string(HTML_TEMPLATE, 
                                products=products, 
                                expenses=expenses,
                                total_expenses=total_expenses, 
                                total_personal=total_personal,
                                search_query=search_query,
                                logo_file=logo_file)

@app.route('/add', methods=['POST'])
def add_product():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Général').strip()
    price_input = request.form.get('price', '')
    price = float(price_input) if price_input else 0.0
    quantity = int(request.form.get('quantity', 1) or 1)
    status = request.form.get('status', 'Disponible')
    
    invoice_filename = ""
    if 'invoice' in request.files:
        inv_file = request.files['invoice']
        if inv_file.filename != '':
            invoice_filename = "inv_" + inv_file.filename
            inv_path = os.path.join(app.config['UPLOAD_FOLDER'], invoice_filename)
            inv_file.save(inv_path)

    if not name:
        name = "Produit Sans Nom"
        
    new_p = Product(
        name=name, 
        category=category, 
        price=price, 
        quantity=quantity, 
        status=status, 
        image="", 
        invoice=invoice_filename
    )
    db.session.add(new_p)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_expense', methods=['POST'])
def add_expense():
    date = request.form.get('date', '')
    amount = float(request.form.get('amount', 0) or 0)
    note = request.form.get('note', '')
    
    inv_filename = ""
    if 'invoice' in request.files:
        file = request.files['invoice']
        if file.filename != '':
            inv_filename = "exp_" + file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], inv_filename))
            
    new_exp = PersonalExpense(date=date, amount=amount, note=note, invoice=inv_filename)
    db.session.add(new_exp)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/export_report')
def export_report():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Categorie', 'Prix', 'Quantite', 'Statut'])
    for p in Product.query.all():
        writer.writerow([p.id, p.name, p.category, p.price, p.quantity, p.status])
    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=Rapport_Stock.csv"})

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Gestion Intelligente - Marouane</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header-flex { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }
        .logo-title { display: flex; align-items: center; gap: 15px; }
        .logo-title img { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; border: 2px solid #2980b9; }
        h1 { color: #2c3e50; margin: 0; }
        form { background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e1e1e1; margin-bottom: 20px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        form input, form select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; flex: 1; min-width: 130px; }
        form button { background: #27ae60; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
        th { background: #2980b9; color: white; }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .card { background: #e8f4f8; padding: 15px; border-radius: 8px; flex: 1; border-left: 5px solid #2980b9; }
    </style>
</head>
<body>
<div class="container">
    <div class="header-flex">
        <div class="logo-title">
            {% if logo_file %}
                <img src="{{ url_for('static', filename='uploads/' + logo_file) }}" alt="Logo">
            {% endif %}
            <h1>Gestion de Stock & Factures</h1>
        </div>
        <a href="/export_report" style="background:#8e44ad; color:white; padding:10px 15px; border-radius:5px; text-decoration:none;">📥 Télécharger Rapport CSV</a>
    </div>

    <div class="stats">
        <div class="card">
            <h3>Total Dépenses Stock</h3>
            <p style="font-size: 20px; font-weight: bold; color: #2c3e50;">€ {{ "%.2f"|format(total_expenses) }}</p>
        </div>
        <div class="card" style="background: #eafaf1; border-left-color: #27ae60;">
            <h3>Total Dépenses Personnelles</h3>
            <p style="font-size: 20px; font-weight: bold; color: #27ae60;">€ {{ "%.2f"|format(total_personal) }}</p>
        </div>
    </div>

    <form method="GET" action="/" style="background: #f1f4f6;">
        <input type="text" name="search" placeholder="Rechercher par Nom ou ID..." value="{{ search_query }}">
        <button type="submit" style="background: #2980b9;">Rechercher</button>
        {% if search_query %}
            <a href="/" style="background: #e74c3c; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none;">Réinitialiser</a>
        {% endif %}
    </form>

    <h2>Ajouter un Produit / Facture</h2>
    <form method="POST" action="/add" enctype="multipart/form-data">
        <input type="text" name="name" placeholder="Nom du produit">
        <input type="text" name="category" placeholder="Catégorie">
        <input type="number" step="0.01" name="price" placeholder="Prix (€)">
        <input type="number" name="quantity" placeholder="Quantité" value="1">
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
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Nom</th>
                <th>Catégorie</th>
                <th>Prix (€)</th>
                <th>Quantité</th>
                <th>Statut</th>
                <th>Facture</th>
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
                    {% if p.invoice %}
                        <a href="{{ url_for('static', filename='uploads/' + p.invoice) }}" target="_blank">📄 Voir</a>
                    {% else %}
                        -
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

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

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Montant (€)</th>
                <th>Note</th>
                <th>Justificatif</th>
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
                    {% if exp.invoice %}
                        <a href="{{ url_for('static', filename='uploads/' + exp.invoice) }}" target="_blank">📄 Voir</a>
                    {% else %}
                        -
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
