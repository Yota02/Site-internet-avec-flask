from flask import abort, request, Flask, send_from_directory, session, render_template, flash, redirect, url_for, make_response
from datetime import datetime
import mysql.connector
from werkzeug.utils import secure_filename
import os
from flask_mysqldb import MySQL,MySQLdb
import MySQLdb.cursors
import base64
import logging
import time

app = Flask(__name__)
app.secret_key = '74$mo7iokz&qmhfgg35r+641a(vqw4pkfdp7bl4ogqimv2*9pj'# Clé secrète utilisée pour les sessions utilisateur

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = 'static/uploads/image'

# Paramètres de configuration de la base de données MySQL
cnx = mysql.connector.connect(host = 'localhost',
                              user = 'root',
                              password = '',
                              database = 'bdmain')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'bdmain'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Dossier de téléchargement pour les fichiers uploadés

mysql = MySQL(app)
cur = cnx.cursor()
with app.app_context():
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

logger = logging.getLogger('logs') # Initialise le logger avec un niveau de log INFO
logger.setLevel(logging.INFO) # Crée un handler pour écrire les logs dans un fichier
file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')# Formatteur pour le handler
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)# Ajoute le handler au logger



dir = 'static/uploads/avatar'
@app.before_first_request
def clear_sessions():
    session.clear()
    for f in os.listdir(dir):
        os.remove(os.path.join(dir, f))
    
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

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
    
@app.route("/param")
def param():
    try:
        if 'id' not in session:# Vérification de la session
            return redirect(url_for('login'))
        id = session['id']# Récupération de l'identifiant de l'utilisateur
        cur = cnx.cursor()
        txt = f"SELECT id FROM avatar WHERE id = {id};"
        cur.execute(txt)
        result = cur.fetchall()
        cur.close()
        print(result)
        if result:# Vérification si l'avatar existe en base de données

            for f in os.listdir(dir):
                os.remove(os.path.join(dir, f))
            logger.info(f"Dossier avatar Vider")
            
            cur = cnx.cursor()# Récupération du nom de l'image de l'avatar en base de données
            txt = f"SELECT file_name FROM avatar WHERE id = {id};"
            cur.execute(txt)
            resulta = cur.fetchall()
            session.pop('avatar', None)
            print(resulta)
            session['avatar'] = resulta[0][0]
            session['pp'] = True
            cur.close()
            
            cur = cnx.cursor()
            txt = f"SELECT image_data, file_name FROM avatar WHERE id = {id};"
            cur.execute(txt)
            image_data, file_name = cur.fetchone()

            with open(os.path.join(app.root_path, 'static', 'uploads', 'avatar', file_name), 'wb') as f:# Sauvegarde de l'avatar dans le dossier des uploads
                f.write(image_data)

            logger.info(f"Session['avatar'] : {session['avatar']}")
            logger.info(f"Avatar recupere et sauvegarde : {file_name}")
            
            cur.close()
            return render_template('param.html', image_name=file_name)# Affichage de la page param.html avec le nom de l'image de l'avatar
        else:
            logger.warning("Avatar non trouve en base de donnees")# Si l'avatar n'existe pas en base de données
            return render_template('param.html')
    except Exception as e:# En cas d'erreur, affichage de la page d'erreur
        logger.error(f"Erreur dans la recuperation de l'avatar : {e}")
        return redirect('errorhandler')

@app.route("/admin")
def admin():
    return render_template('admin.html')

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

ERROR_MESSAGES = {
    'NOT_LOGGED_IN': 'You must be logged in to upload an avatar.',
    'NO_FILE_SELECTED': 'Please select a file to upload.',
    'FILE_TYPE_NOT_ALLOWED': 'File type not allowed.',
    'UPLOAD_ERROR': 'An error occurred during upload. Please try again later.',
}

@app.route("/upload_pp", methods=["POST"])
def upload_pp():
    UPLOAD_FOLDER = 'static/uploads/avatar'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    id = session.get('id')
    if not id:
        return render_template('page_not_found.html', message=ERROR_MESSAGES['NOT_LOGGED_IN'])
    try:
        file = request.files['file']
        if not file:
            return render_template('page_not_found.html', message=ERROR_MESSAGES['NO_FILE_SELECTED'])
        if not allowed_file(file.filename):
            return render_template('page_not_found.html', message=ERROR_MESSAGES['FILE_TYPE_NOT_ALLOWED'])
        cur = mysql.connection.cursor()
        now = datetime.now()
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        with open(file_path, 'rb') as f:
            image_data = f.read()
        query = "INSERT INTO avatar (id, file_name, uploaded_on, image_data, image_type) VALUES (%s, %s, %s, %s, %s)"
        cur.execute(query , (id, filename, now, image_data, file.content_type))
        mysql.connection.commit()
        session['pp'] = True
        cur.close()
        flash('File uploaded successfully')
    except Exception as e:
        logger.error(f"Error during avatar upload: {e}")
        return render_template('page_not_found.html', message=ERROR_MESSAGES['UPLOAD_ERROR'])
    return render_template('param.html', image_name = filename)


@app.route("/modif_pp", methods=["POST", "GET"])
def modif_pp():
    UPLOAD_FOLDER = 'static/uploads/avatar'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    id = session['id']
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now = datetime.now()
    file_input_name = 'files[]'
    if request.method == 'POST':
        try:
            files = request.files.getlist(file_input_name)
            for file in files:
                if file and allowed_file(file.filename):
                    for f in os.listdir(app.config['UPLOAD_FOLDER']):
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    with open(file_path, 'rb') as f:
                        image_data = f.read()
                    cur1.execute("UPDATE avatar SET file_name = %s, uploaded_on = %s, image_data = %s WHERE id = %s", [filename, now, image_data, id])
                    mysql.connection.commit()
                    session['pp'] = True
                    session['avatar'] = filename
                    logger.info('Le fichier %s a ete telecharge avec succes')
                    return render_template('param.html', image_name = filename)
            flash('File(s) successfully uploaded')
        except Exception as e:
            app.logger.error('Error uploading file(s): %s', e)
            flash('An error occurred while uploading the file(s). Please try again later.')
    else:
        app.logger.error('No file uploaded')
    cur1.close()
    return render_template('param.html', image_name = filename )

if __name__=='__main__':
    app.run(debug= True)