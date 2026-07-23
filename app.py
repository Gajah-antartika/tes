from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql

app = Flask(__name__)
app.secret_key = 'super-secret-key-proyek-web'

# Konfigurasi Database (Ganti sesuai kredensial filess.io / local)
DB_HOST = 'kbgffg.h.filess.io'
DB_USER = 'pemrograman_equalstart'
DB_PASSWORD = '759a3a243bd1db84747ec36505287431c3f20258'
DB_NAME = 'pemrograman_equalstart'
DB_PORT = '3307'

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=int(DB_PORT),
        cursorclass=pymysql.cursors.DictCursor
    )

# --- FITUR 1: AUTHENTICATION (REGISTER & LOGIN) ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
            db.commit()
        db.close()
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
        db.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email atau password salah!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# --- FITUR 2: DASHBOARD RINGKASAN ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total_items, SUM(stock) AS total_stock FROM items")
        stats = cursor.fetchone()
        cursor.execute("SELECT category, COUNT(*) as count FROM items GROUP BY category")
        categories = cursor.fetchall()
    db.close()
    
    return render_template('dashboard.html', stats=stats, categories=categories)

# --- FITUR 3: MANAJEMEN PROFIL ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_username = request.form['username']
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("UPDATE users SET username = %s WHERE id = %s", (new_username, session['user_id']))
            db.commit()
        db.close()
        session['username'] = new_username
        flash('Profil berhasil diperbarui!', 'success')
        
    return render_template('profile.html')

# --- FITUR 4, 5, 6, 7: CRUD & PENCARIAN BARANG ---
@app.route('/')
@app.route('/inventory')
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    search_query = request.args.get('search', '')
    filter_category = request.args.get('category', '')
    
    db = get_db()
    with db.cursor() as cursor:
        query = "SELECT * FROM items WHERE name LIKE %s"
        params = [f"%{search_query}%"]
        
        if filter_category:
            query += " AND category = %s"
            params.append(filter_category)
            
        cursor.execute(query, params)
        items = cursor.fetchall()
    db.close()
    
    return render_template('inventory.html', items=items, search_query=search_query, filter_category=filter_category)

@app.route('/item/add', methods=['POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    name = request.form['name']
    category = request.form['category']
    stock = request.form['stock']
    price = request.form['price']
    
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO items (name, category, stock, price) VALUES (%s, %s, %s, %s)", 
                       (name, category, stock, price))
        db.commit()
    db.close()
    flash('Barang berhasil ditambahkan!', 'success')
    return redirect(url_for('inventory'))

@app.route('/item/edit/<int:item_id>', methods=['POST'])
def edit_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    name = request.form['name']
    category = request.form['category']
    stock = request.form['stock']
    price = request.form['price']
    
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE items SET name=%s, category=%s, stock=%s, price=%s WHERE id=%s", 
                       (name, category, stock, price, item_id))
        db.commit()
    db.close()
    flash('Barang berhasil diperbarui!', 'success')
    return redirect(url_for('inventory'))

@app.route('/item/delete/<int:item_id>')
def delete_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
        db.commit()
    db.close()
    flash('Barang berhasil dihapus!', 'warning')
    return redirect(url_for('inventory'))

if __name__ == '__main__':
    app.run(debug=True)