from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret_key'

# --- USERS ---
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user': {'password': 'user123', 'role': 'user'}
}

# --- ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if user in users and users[user]['password'] == pwd:
            session['username'] = user
            session['role'] = users[user]['role']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    conn = sqlite3.connect("tollgate.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM log_entry WHERE status = 'Allowed'")
    allowed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM log_entry WHERE status = 'Stolen'")
    stolen = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM not_match")
    not_match = cursor.fetchone()[0]
    conn.close()
    return render_template("dashboard.html",
                           user=session['username'],
                           role=session['role'],
                           allowed=allowed,
                           stolen=stolen,
                           not_match=not_match)

@app.route('/log_entry')
def log_entry():
    con = sqlite3.connect('tollgate.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM log_entry ORDER BY timestamp DESC")
    data = cur.fetchall()
    con.close()
    return render_template('log_entry.html', data=data)

@app.route('/not_match')
def not_match():
    con = sqlite3.connect('tollgate.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM not_match ORDER BY timestamp DESC")
    data = cur.fetchall()
    con.close()
    return render_template('not_match.html', data=data)

@app.route('/stolen', methods=['GET', 'POST'])
def stolen():
    if 'role' not in session:
        return redirect('/')
    con = sqlite3.connect('tollgate.db')
    cur = con.cursor()
    if request.method == 'POST' and session['role'] == 'admin':
        if 'add' in request.form:
            number = request.form['number']
            cur.execute("INSERT OR IGNORE INTO stolen_vehicles (vehicle_number) VALUES (?)", (number,))
            con.commit()
        elif 'delete' in request.form:
            cur.execute("DELETE FROM stolen_vehicles WHERE id = ?", (request.form['id'],))
            con.commit()
    cur.execute("SELECT * FROM stolen_vehicles")
    data = cur.fetchall()
    con.close()
    return render_template('stolen.html', data=data, role=session['role'])

@app.route('/search')
def search():
    if 'username' not in session:
        return redirect('/')
    query = request.args.get('query', '').strip()
    conn = sqlite3.connect("tollgate.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT 'Log Entry' as source, vehicle_number, status, timestamp FROM log_entry WHERE vehicle_number LIKE ?
        UNION
        SELECT 'Not Match', rfid_number || ' / ' || extracted_number, '', timestamp FROM not_match WHERE rfid_number LIKE ? OR extracted_number LIKE ?
        UNION
        SELECT 'Stolen', vehicle_number, '', NULL FROM stolen_vehicles WHERE vehicle_number LIKE ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%",))
    results = cur.fetchall()
    conn.close()
    return render_template("search_results.html", query=query, results=results)

@app.route('/download_csv')
def download_csv():
    if 'username' not in session:
        return redirect('/')
    conn = sqlite3.connect("tollgate.db")
    cursor = conn.cursor()
    cursor.execute("SELECT vehicle_number, status, timestamp FROM log_entry")
    rows = cursor.fetchall()
    conn.close()
    csv = "Vehicle Number,Status,Timestamp\n"
    csv += "\n".join([",".join(str(cell) for cell in row) for row in rows])
    return Response(csv, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=log_entry.csv"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
