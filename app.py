from flask import abort, request, Flask, send_from_directory, session, render_template, flash, redirect, url_for, make_response
from datetime import datetime, timedelta
import mysql.connector
from werkzeug.utils import secure_filename
import os
from flask_mysqldb import MySQL,MySQLdb
import MySQLdb.cursors
import base64

app = Flask(__name__)

cnx = mysql.connector.connect(host = 'localhost',
                              user = 'root',
                              password = '',
                              database = 'bdmain')


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = 'static/uploads/image'

app.secret_key = '74$mo7iokz&qmhfgg35r+641a(vqw4pkfdp7bl4ogqimv2*9pj'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'bdmain'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)
cur = cnx.cursor()
image_name = 'static/uploads/avatar/icone_defaut.png'

dir = 'static/uploads/avatar'
@app.before_first_request
def clear_sessions():
    session.clear()
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))
    

with app.app_context():
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(os.path.join(app.root_path, 'static', 'uploads', 'avatar'), filename)

@app.route('/save-image')
def save_image():
    try:
        # Connexion à la base de données
        cur = cnx.cursor()

        # Récupération des données de l'image
        cur.execute("SELECT image_data, file_name FROM avatar WHERE id=1")
        image_data, file_name = cur.fetchone()

        # Sauvegarde de l'image dans le dossier d'uploads
        with open(os.path.join(app.root_path, 'static', 'uploads', 'avatar', image_name), 'wb') as f:
            f.write(image_data)

        # Fermeture de la connexion à la base de données
        cur.close()

        return "L'image a été sauvegardée avec succès !"
    except Exception as e:
        return str(e)





@app.route("/")
def index():
    return render_template('index.html')

@app.route("/uploadimage")
def uploadimage():
    return render_template('upload.html')

@app.route('/upload_avatar')
def upload_avatar():
    return render_template('upload_avatar.html')

@app.route('/update', methods =['GET', 'POST'])
def update():
    if request.method == 'POST' :
        mail = session['mail']
        pseudo = request.form.get('pseudo')
        mdp = request.form.get('password')
        mail2 = request.form.get('mail')
        val = mail2, pseudo, mdp, mail
        sql = "UPDATE user SET mail = %s, pseudo = %s, password = %s WHERE mail = %s"
        cur.execute(sql, val)
        mysql.connection.commit()
        cur.close()
        return render_template('index.html')
    else :
        return render_template('update.html')
    
@app.route("/login", methods =['GET', 'POST'])
def login():
    cur = cnx.cursor()
    msg = ''
    if request.method == 'POST' :
        mail = request.form['mail']
        password = request.form['password']
        cur.execute('SELECT * FROM user WHERE mail = %s AND password = %s', (mail, password))
        account = cur.fetchone() 
        cur.close()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['mail'] = account[1]
            session['pseudo'] = account[2]
            session['date'] = account[4]
            msg = 'Logged in successfully !'
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect pseudo / password !'
        return render_template('login.html', msg = msg)
    else : 
        return render_template('login.html')
    
@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route("/param")
def param():
    id = session['id']
    cur = cnx.cursor()
    txt = f"SELECT file_name FROM avatar WHERE id = {id};"
    cur.execute(txt)
    result = cur.fetchall()
    cur.close()
    if result :
        session['avatar'] = result[0][0]
        cur = cnx.cursor()
        txt = f"SELECT image_data, file_name FROM avatar WHERE id = {id};"
        cur.execute(txt)
        image_data, file_name = cur.fetchone()
        with open(os.path.join(app.root_path, 'static', 'uploads', 'avatar', file_name), 'wb') as f:
            f.write(image_data)
        print('image bien télécharger')

        return render_template('param.html', image_name=file_name)
    else :
        return render_template('param.html')

    
@app.route("/admin")
def admin():
    return render_template('admin.html')

@app.route("/avatar")
def avatar():
    if 'avatar' in session:
        file = os.path.join(dir, session['avatar'])
        return file
    else:
        abort(404)
        return file

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('mail', None)
    session.pop('id', None)
    session.pop('pseudo', None)
    session.pop('date', None)
    session.pop('avatar', None)
    session.pop('pp', None)
    return redirect(url_for('index'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    cur = cnx.cursor()
    msg = ''
    if request.method == 'POST' :
        pseudo = request.form.get('pseudo')
        mdp = request.form.get('password')
        mail = request.form.get('mail')
        date = datetime.now()
        cur.execute('SELECT * FROM user WHERE mail = %s AND password = %s', (mail, mdp))
        account = cur.fetchone()
        if account:
            msg = 'Account already exists !'
        else:
            cur.execute('INSERT INTO user (mail, pseudo, password, date) VALUES (%s, %s, %s, %s)', (mail, pseudo, mdp, date))
            cnx.commit()
            msg = 'You have successfully registered !'
            session['loggedin'] = True
            session['id'] = account[0]
            session['mail'] = account[1]
            session['pseudo'] = account[2]
            session['date'] = account[4]
            cur.close()
    else:
        if 'pseudo' in session:
            return redirect(url_for('index'))
    return render_template('index.html', msg = msg)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.route('/delete')
def delete():
    mail = session['mail']
    sql = f"DELETE FROM user WHERE mail = '{mail}'"
    cur.execute(sql)
    msg = "suppréssion réussis"
    logout()
    return render_template('index.html') 

def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
@app.route("/upload",methods=["POST","GET"])
def upload():
    UPLOAD_FOLDER = 'static/uploads/image'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    id = session['id']
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now = datetime.now()
    if request.method == 'POST':
        files = request.files.getlist('files[]')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cur1.execute("INSERT INTO images (id, file_name, uploaded_on) VALUES (%s, %s, %s)",[id, filename, now])
                mysql.connection.commit()
        cur1.close()   
        flash('File(s) successfully uploaded')    
    return redirect('/')

@app.route("/Vider", methods =['GET', 'POST'])
def Vider():
    msg = ''
    print("quelque chose")
    if request.method == 'POST' :
        table = request.form.get('table')
        val = chr(table)
        sql = "DELETE FROM '%s'"
        cur.execute(sql, val)
        cur.execute(sql)
        mysql.connection.commit()
        msg = f"table {table} bien vidé !"
    return render_template('admin.html', msg = msg)

@app.route('/profile')
def profile():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    if len(files) == 0:
        return render_template('param.html')
    else:
        image_name = files[0]
        return render_template('param.html', image_name=image_name)

@app.route("/upload_pp",methods=["POST","GET"])
def upload_pp():
    UPLOAD_FOLDER = 'static/uploads/avatar'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    id = session['id']
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now = datetime.now()
    if request.method == 'POST':
            files = request.files.getlist('files[]')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    with open(file_path, 'rb') as f:
                        image_data = f.read()

                    query = "INSERT INTO avatar (id, file_name, uploaded_on, image_data, image_type) VALUES (%s, %s, %s, %s, %s)"
                    cur1.execute(query , (id, filename, now, image_data, file.content_type))
                    mysql.connection.commit()
                    session['pp'] = True
                    session['avatar'] = filename
                    cur1.close()

                    redirect(url_for('upload_pp'))
            flash('File(s) successfully uploaded')    
    return redirect('param')

@app.route("/modif_pp",methods=["POST","GET"])
def modif_pp():
    UPLOAD_FOLDER = 'static/uploads/avatar'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    id = session['id']
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now = datetime.now()
    if request.method == 'POST':
            files = request.files.getlist('files[]')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    cur1.execute("UPDATE avatar SET file_name = %s, uploaded_on = %s WHERE id = %s",[filename, now, id])
                    mysql.connection.commit()
                    session['pp'] = True
                    session['avatar'] = filename
                    cur1.close()   
                    return redirect('/profile')
            flash('File(s) successfully uploaded')    
    return redirect('param')

if __name__=='__main__':
    app.run(debug= True)