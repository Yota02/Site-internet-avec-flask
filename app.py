from flask import request, Flask, session, render_template, flash, redirect, url_for, jsonify
from datetime import datetime
import mysql.connector
from werkzeug.utils import secure_filename
import os
from flask_mysqldb import MySQL,MySQLdb
import MySQLdb.cursors
import logging
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
import json


app = Flask(__name__)
socketio = SocketIO(app)
bcrypt = Bcrypt(app)


app.secret_key = '74$mo7iokz&qmhfgg35r+641a(vqw4pkfdp7bl4ogqimv2*9pj'# Cle secrète utilisee pour les sessions utilisateur

MAX_FILE_SIZE = 10 * 1024 * 1024 # 10 Mo en octets
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
UPLOAD_FOLDER = 'static/uploads/image'
ERROR_MESSAGES = {
    'NOT_LOGGED_IN': 'You must be logged in to upload an avatar.',
    'NO_FILE_SELECTED': 'Please select a file to upload.',
    'FILE_TYPE_NOT_ALLOWED': 'File type not allowed.',
    'UPLOAD_ERROR': 'An error occurred during upload. Please try again later.',
}

# Paramètres de configuration de la base de donnees MySQL
cnx = mysql.connector.connect(host = 'localhost',
                              user = 'root',
                              password = '',
                              database = 'bdmain')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'bdmain'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER # Dossier de telechargement pour les fichiers uploades

mysql = MySQL(app)
cur = cnx.cursor()
with app.app_context():
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

logger = logging.getLogger('logs') # Initialise le logger avec un niveau de log INFO
logger.setLevel(logging.INFO) # Cree un handler pour ecrire les logs dans un fichier
file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')# Formatteur pour le handler
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)# Ajoute le handler au logger

dir = 'static/uploads/avatar'# Definition du chemin d'accès au repertoire à vider
@app.before_first_request # Fonction executee avant la première requête envoyee à l'application
def clear_sessions():
    try:
        session.clear() # Effacer toutes les variables de session enregistrees
        for f in os.listdir(dir): # Parcourir tous les fichiers dans le repertoire specifie
            os.remove(os.path.join(dir, f)) # Supprimer chaque fichier dans le repertoire
        logging.info("Cleared avatar directory") # Enregistrer un message de log indiquant que le repertoire a ete vide
    except Exception as e:
        logging.error(f"Error while clearing avatar directory: {e}") # Enregistrer un message de log en cas d'erreur
 
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
        hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')
        val = mail2, pseudo, hashed_password, mail
        sql = "UPDATE user SET mail = %s, pseudo = %s, password = %s WHERE mail = %s"
        cur.execute(sql, val)
        mysql.connection.commit()
        cur.close()
        return render_template('index.html')
    else :
        return render_template('update.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    cur = cnx.cursor()
    msg = ''
    if request.method == 'POST':
        mail = request.form['mail']
        password = request.form['password']
        cur.execute("SELECT * FROM user WHERE mail = %(mail)s", {"mail": mail})
        account = cur.fetchone()
        cur.close()
        if account:
            hashed_password = account[3]
            if bcrypt.check_password_hash(hashed_password, password):
                session['loggedin'] = True
                session['id'] = account[0]
                session['mail'] = account[1]
                session['pseudo'] = account[2]
                session['date'] = account[4]
                msg = 'Logged in successfully!'
                return render_template('index.html', msg=msg)
        msg = 'Incorrect email or password!'
        return render_template('login.html', msg=msg)
    else:
        return render_template('login.html')

@app.route("/param")# Definition de la route /param et de la fonction associee
def param():
    try:
        if 'id' not in session:# Verification si l'utilisateur est connecte
            return redirect(url_for('login'))# Redirection vers la page de connexion si l'utilisateur n'est pas connecte
        id = session['id']# Recuperation de l'identifiant de l'utilisateur
        cur = cnx.cursor()# Connexion à la base de donnees
        txt = f"SELECT id FROM avatar WHERE id = {id};"# Requête SQL pour verifier si l'avatar existe en base de donnees
        cur.execute(txt)
        result = cur.fetchall()
        cur.close()
        if result:# Si l'avatar existe en base de donnees
            for f in os.listdir(dir):# Vidage du dossier avatar
                os.remove(os.path.join(dir, f))
            cur = cnx.cursor()# Recuperation du nom de l'image de l'avatar en base de donnees
            txt = f"SELECT file_name FROM avatar WHERE id = {id};"
            cur.execute(txt)
            resulta = cur.fetchall()
            session.pop('avatar', None)
            session['avatar'] = resulta[0][0]
            session['pp'] = True
            cur.close()
            cur = cnx.cursor()# Recuperation des donnees de l'image de l'avatar en base de donnees
            txt = f"SELECT image_data, file_name FROM avatar WHERE id = {id};"
            cur.execute(txt)
            image_data, file_name = cur.fetchone()
            with open(os.path.join(app.root_path, 'static', 'uploads', 'avatar', file_name), 'wb') as f:# Sauvegarde de l'avatar dans le dossier des uploads
                f.write(image_data)
            logger.info(f"Avatar recupere et sauvegarde : {file_name}")
            cur.close()
            return render_template('param.html', image_name=file_name)# Affichage de la page param.html avec le nom de l'image de l'avatar
        else:
            logger.warning("Avatar non trouve en base de donnees")# Affichage de la page param.html si l'avatar n'existe pas en base de donnees
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
        hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')
        if account:
            msg = 'Account already exists !'
            session['loggedin'] = True
            session['id'] = account[0]
            session['mail'] = account[1]
            session['pseudo'] = account[2]
            session['date'] = account[4]
        else:
            cur.execute('INSERT INTO user (mail, pseudo, password, date) VALUES (%s, %s, %s, %s)', (mail, pseudo, hashed_password, date))
            cnx.commit()
            msg = 'You have successfully registered !'
            cur.close()
    else:
        if 'pseudo' in session:
            return redirect(url_for('index'))
    return render_template('index.html', msg = msg)

@app.route('/delete')
def delete():
    mail = session['mail']
    sql = f"DELETE FROM user WHERE mail = '{mail}'"
    cur.execute(sql)
    msg = "suppression reussis"
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

@app.route("/upload_pp", methods=["POST", "GET"])
def upload_pp():
    UPLOAD_FOLDER = 'static/uploads/avatar'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER# Dossier dans lequel les fichiers téléchargés seront stockés
    id = session['id']# ID de session de l'utilisateur
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)# Obtenir la date et l'heure actuelles
    now = datetime.now()# Obtenir la date et l'heure actuelles
    if request.method == 'POST':# Vérifier si la méthode de demande est POST
        try:
            files = request.files.getlist('files[]') # Récupérer la liste de fichiers téléchargés
            for file in files:
                if file and allowed_file(file.filename): # Vérifier si le fichier est autorisé à être téléchargé
                    filename = secure_filename(file.filename) # Sécuriser le nom du fichier en utilisant la fonction secure_filename() de Flask
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename) # Créer le chemin d'accès complet du fichier
                    file.save(file_path) # Enregistrer le fichier dans le dossier UPLOAD_FOLDER
                    with open(file_path, 'rb') as f:
                        image_data = f.read() # Lire les données de l'image
                    query = "INSERT INTO avatar (id, file_name, uploaded_on, image_data, image_type) VALUES (%s, %s, %s, %s, %s)" # Requête MySQL pour insérer les données de l'image dans la table avatar
                    cur1.execute(query, (id, filename, now, image_data, file.content_type)) # Exécuter la requête MySQL avec les paramètres appropriés
                    mysql.connection.commit() # Soumettre les changements à la base de données
                    session['pp'] = True # Marquer la session de l'utilisateur comme ayant une photo de profil téléchargée
                    session['avatar'] = filename # Stocker le nom du fichier de la photo de profil dans la session
                    cur1.close() # Fermer le curseur de la base de données
                    logger.info(f"File {filename} uploaded by user {id}") # Journaliser le téléchargement réussi du fichier
                    flash('File(s) successfully uploaded') # Afficher un message de confirmation à l'utilisateur
        except Exception as e:
            logger.error(f"An error occurred while uploading file(s): {e}") # Journaliser l'erreur
            flash('An error occurred while uploading the file(s). Please try again later.') # Afficher un message d'erreur à l'utilisateur
    return redirect('param') # Rediriger l'utilisateur vers la page des paramètres

@app.route("/modif_pp", methods=["POST", "GET"])
def modif_pp():
    UPLOAD_FOLDER = 'static/uploads/avatar'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    id = session['id']# Récupération de l'id de l'utilisateur
    cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)# Obtention d'un objet curseur pour interagir avec la base de données
    now = datetime.now()# Récupération de la date et heure actuelle
    file_input_name = 'files[]'# Nom du champ de formulaire pour les fichiers
    if request.method == 'POST':# Traitement de la requête POST pour télécharger un nouveau fichier
        try:
            files = request.files.getlist(file_input_name)# Récupération de la liste des fichiers téléchargés
            for file in files:# Pour chaque fichier téléchargé
                if file and allowed_file(file.filename):# Vérification que le fichier est autorisé
                    for f in os.listdir(app.config['UPLOAD_FOLDER']):# Suppression de tous les fichiers dans le dossier de téléchargement
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
                    filename = secure_filename(file.filename)# Obtention du nom de fichier sécurisé et sauvegarde du fichier dans le dossier de téléchargement
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    with open(file_path, 'rb') as f:# Ouverture du fichier et lecture de son contenu binaire
                        image_data = f.read()
                    cur1.execute("UPDATE avatar SET file_name = %s, uploaded_on = %s, image_data = %s WHERE id = %s", [filename, now, image_data, id])# Mise à jour de l'enregistrement d'avatar de l'utilisateur correspondant dans la base de données
                    mysql.connection.commit()
                    session['pp'] = True# Stockage du nom du fichier dans la session utilisateur
                    session['avatar'] = filename
                    logger.info('Le fichier %s a ete telecharge avec succes')# Enregistrement d'un message de journalisation indiquant le succès du téléchargement
                    return render_template('param.html', image_name = filename)# Redirection vers la page des paramètres avec le nom de fichier téléchargé
            flash('No file selected')# Si aucun fichier n'a été sélectionné
        except Exception as e:# En cas d'erreur lors du téléchargement
            app.logger.error('Error uploading file(s): %s', e)
            flash('An error occurred while uploading the file(s). Please try again later.')
    else:# Si la requête n'est pas de type POST
        filename = session.get('avatar')# Récupération du nom de fichier dans la session utilisateur
    cur1.close()# Fermeture de l'objet curseur
    return render_template('param.html', image_name = filename )# Rendu de la page des paramètres avec le nom de fichier téléchargé ou précédemment téléchargé

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
        msg = f"table {table} bien vide !"
    return render_template('admin.html', msg = msg)

@app.route('/messages1', methods=['GET', 'POST'])
def messages1():
    return render_template('chat.html')

@app.route('/message', methods=['POST'])
def add_message():
    message = request.json['message']
    username = request.json['username']
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO messages (pseudo, message) VALUES (%s, %s)', (username, message))
    mysql.connection.commit()
    cursor.close()
    emit('message', {'username': username, 'message': message}, broadcast=True)
    return jsonify(success=True)

@socketio.on('connect')
def connect():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM messages')
    messages = cursor.fetchall()
    cursor.close()
    for message in messages:
        emit('message', {'username': message[1], 'message': message[2]})


@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        username = session['pseudo']
        message = request.form['message']
        cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur1.execute('INSERT INTO messages (pseudo, message) VALUES (%s, %s)', (username, message))
        mysql.connection.commit()
        cur1.close()
        logger.info(f"New message from user {username} has been added to the database")
        return jsonify({'status': 'OK'})
    else:
        cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur1.execute('SELECT pseudo, message, timestamp FROM messages ORDER BY id DESC LIMIT 10')
        results = cur.fetchall()
        messages = []
        for row in results:
            messages.append({'username': row[0], 'message': row[1], 'timestamp': row[2]})
        cur1.close()
        logger.info(f"Retrieved {len(messages)} messages from the database")
        return jsonify(messages)




#erreur : 

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


if __name__=='__main__':
    app.run(debug= True)
    socketio.run(app, debug=True)