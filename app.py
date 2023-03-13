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


# Route vers page :
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    status = request.args.get('status')# Récupérer le statut de la requête
    cur = cnx.cursor()# Créer un curseur pour exécuter des requêtes SQL
    cur.execute('SELECT pseudo FROM user')# Exécuter une requête pour récupérer les pseudos des utilisateurs
    users_res = cur.fetchall()  # Récupérer tous les résultats de la requête
    users = users_res[0] # Récupérer le premier pseudo de la première ligne des résultats
    cur.execute('SELECT file_name FROM avatar')# Exécuter une requête pour récupérer le nom du fichier d'avatar
    file_res = cur.fetchall()# Récupérer tous les résultats de la requête
    file_name = file_res[0][0] # Récupérer le nom du fichier de la première ligne des résultats
    cur.close()# Fermer le curseur
    logger.info(f"Chat function called with status='{status}', users='{users}', image_name='{file_name}'")# Enregistrer un message de journalisation avec les informations de l'utilisateur et de l'avatar
    return render_template('chat.html', status=status, users=users, image_name=file_name)# Renvoyer le modèle HTML avec les informations de l'utilisateur et de l'avatar

@app.route("/uploadimage")
def uploadimage():
    return render_template('upload.html')

@app.route('/upload_avatar')
def upload_avatar():
    return render_template('upload_avatar.html')

@app.route('/update', methods =['GET', 'POST'])
def update():
    if request.method == 'POST' :
        cur = cnx.cursor()
        mail = session['mail']
        pseudo = request.form.get('pseudo')
        mdp = request.form.get('password')
        mail2 = request.form.get('mail')
        hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')
        val = mail2, pseudo, hashed_password, mail
        sql = "UPDATE user SET mail = %s, pseudo = %s, password = %s WHERE mail = %s"
        cur.execute(sql, val)
        cnx.commit()
        cur.close()
        session['mail'] = mail2
        session['pseudo'] = pseudo
        return render_template('index.html')
    else :
        return render_template('update.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST': # Si une requête POST est envoyée
        try:
            mail = request.form['mail']
            password = request.form['password']
            with cnx.cursor() as cur: # Requête pour récupérer le compte utilisateur associé à l'adresse e-mail fournie
                cur.execute("SELECT * FROM user WHERE mail = %s", (mail,))
                account = cur.fetchone()
            if account: # Si un compte utilisateur est trouvé
                hashed_password = account[3] 
                # Vérifier si le mot de passe fourni correspond au mot de passe haché stocké dans la base de données
                if bcrypt.checkpw(password.encode('utf8'), hashed_password.encode('utf8')):# Si le mot de passe est correct, connecter l'utilisateur en créant une session
                    session.permanent = True
                    session['loggedin'] = True
                    session['id'] = account[0]
                    session['mail'] = account[1]
                    session['pseudo'] = account[2]
                    session['date'] = account[4]
                    msg = 'Connecté avec succès !'
                    return render_template('index.html', msg=msg)
            msg = 'Adresse e-mail ou mot de passe incorrect !' # Si l'adresse e-mail ou le mot de passe est incorrect
            return render_template('login.html', msg=msg)
        except Exception as e:# En cas d'erreur lors de la connexion à la base de données
            app.logger.error(e)
            msg = 'Une erreur est survenue. Veuillez réessayer ultérieurement.'
            return render_template('login.html', msg=msg)
    else:
        return render_template('login.html') # Afficher la page de connexion


@app.route("/param")
def param():
    try:
        if 'id' not in session:# Vérifier si l'utilisateur est connecté
            return redirect(url_for('login'))        
        user_id = session['id']# Récupérer l'identifiant de l'utilisateur
        cursor = cnx.cursor()# Vérifier si l'avatar existe en base de données
        query = f"SELECT id FROM avatar WHERE id = {user_id};"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        if result:
            avatar_dir = os.path.join(app.root_path, 'static', 'uploads', 'avatar')# Supprimer les anciens avatars
            for filename in os.listdir(avatar_dir):
                file_path = os.path.join(avatar_dir, filename)
                os.remove(file_path)
            cursor = cnx.cursor()# Récupérer le nom de l'image de l'avatar et les données de l'image
            query = f"SELECT image_data, file_name FROM avatar WHERE id = {user_id};"
            cursor.execute(query)
            image_data, file_name = cursor.fetchone()
            cursor.close()
            file_path = os.path.join(avatar_dir, file_name)# Enregistrer l'image dans le dossier des uploads
            with open(file_path, 'wb') as f:
                f.write(image_data)
            session.pop('avatar', None)# Enregistrer le nom de l'image de l'avatar dans la session
            session['avatar'] = file_name
            session['pp'] = True
            return render_template('param.html', image_name=file_name)# Afficher la page param.html avec le nom de l'image de l'avatar
        else:
            logger.warning("Avatar non trouvé en base de données")# Afficher la page param.html si l'avatar n'existe pas en base de données
            return render_template('param.html')
    except mysql.connector.Error as err:
        logger.error(f"Erreur MySQL : {err}")# Afficher un message d'erreur si la requête SQL échoue
        return redirect('errorhandler')
    except IOError as err:
        logger.error(f"Erreur d'entrée/sortie : {err}")# Afficher un message d'erreur si l'enregistrement de l'image échoue
        return redirect('errorhandler')
    except Exception as e:
        logger.error(f"Erreur inattendue : {e}")# Afficher un message d'erreur générique en cas d'erreur
        return redirect('errorhandler')


@app.route("/admin")
def admin():
    return render_template('admin.html')

@app.route('/logout')
def logout():
    utilisateur = session['mail'] # Récupération du pseudo de l'utilisateur
    if 'loggedin' in session: # Vérification si l'utilisateur est connecté
        session.pop('loggedin', None) # Suppression de la clé 'loggedin' de la session
        session.pop('mail', None) # Suppression de la clé 'mail' de la session
        session.pop('id', None) # Suppression de la clé 'id' de la session
        session.pop('pseudo', None) # Suppression de la clé 'pseudo' de la session
        session.pop('date', None) # Suppression de la clé 'date' de la session
        session.pop('avatar', None) # Suppression de la clé 'avatar' de la session
        session.pop('pp', None) # Suppression de la clé 'pp' de la session
        flash('Vous êtes déconnecté.', 'success') # Affichage d'un message de confirmation de déconnexion
        logging.info('Utilisateur', {{utilisateur}}, 'déconnecté') # Enregistrement d'un message de log indiquant la déconnexion de l'utilisateur
    return redirect(url_for('index')) # Redirection vers la page d'accueil de l'application


# action : 

@app.route('/register', methods=['GET', 'POST']) 
def register():
    if request.method == 'POST':  # Si la méthode est POST
        pseudo = request.form.get('pseudo')  # Récupérer le pseudo de la requête
        mdp = request.form.get('password')  # Récupérer le mot de passe de la requête
        mail = request.form.get('mail')  # Récupérer le mail de la requête
        date = datetime.now()  # Récupérer la date actuelle
        cur = cnx.cursor()  # Créer un curseur pour exécuter des requêtes sur la base de données
        try:
            cur.execute('SELECT * FROM user WHERE mail = %s', (mail,))  # Vérifier si le compte existe déjà
            account = cur.fetchone()  # Récupérer les informations de l'utilisateur
            if account:  # Si le compte existe déjà
                msg = 'Ce compte existe déjà !'
                session['loggedin'] = True
                session['id'] = account[0]
                session['mail'] = account[1]
                session['pseudo'] = account[2]
                session['date'] = account[4]
                logging.info('Utilisateur connecté avec succès : %s', account[2])  # Enregistrer l'information dans les logs
            else:  # Si le compte n'existe pas encore
                hashed_password = bcrypt.generate_password_hash(mdp).decode('utf-8')  # Hasher le mot de passe
                cur.execute('INSERT INTO user (mail, pseudo, password, date) VALUES (%s, %s, %s, %s)', (mail, pseudo, hashed_password, date))  # Insérer les informations de l'utilisateur dans la base de données
                cnx.commit()  # Valider les modifications dans la base de données
                msg = 'Vous êtes inscrit avec succès !'
                logging.info('Utilisateur enregistré avec succès : %s', pseudo)  # Enregistrer l'information dans les logs
        except Exception as e:
            logging.error('Erreur lors de l\'enregistrement de l\'utilisateur : %s', str(e))  # Enregistrer l'erreur dans les logs
            msg = 'Une erreur est survenue lors de votre inscription.'
        finally:
            cur.close()  # Fermer le curseur pour libérer les ressources
    else:  # Si la méthode est GET
        if 'pseudo' in session:  # Si l'utilisateur est déjà connecté
            return redirect(url_for('index'))  # Rediriger vers la page d'accueil
        msg = ''  # Sinon, ne rien afficher
    logging.debug('Rendu du template index.html avec le message : %s', msg)  # Afficher le message de retour dans les logs
    return render_template('index.html', msg=msg)  # Renvoyer le template HTML avec le message de retour en paramètre

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

@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if request.method == 'POST':
        username = session['pseudo']# Récupérer le nom d'utilisateur de la session et le message soumis dans le formulaire
        message = request.form['message']
        cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur1.execute('INSERT INTO messages (pseudo, message) VALUES (%s, %s)', (username, message))# Insérer le message dans la base de données
        mysql.connection.commit()
        cur1.close()
        logger.info(f"New message from user {username} has been added to the database")# Enregistrer un message de log indiquant que le nouveau message a été ajouté à la base de données
        return redirect(url_for('messages1', messages=message))# Rediriger l'utilisateur vers la page de messages avec un message de statut
    else:
        cur1 = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur1.execute('SELECT pseudo, message, timestamp FROM messages ORDER BY id DESC LIMIT 10')# Récupérer les 10 derniers messages de la base de données
        results = cur.fetchall()
        messages = []
        for row in results:
            messages.append({'username': row[0], 'message': row[1], 'timestamp': row[2]})# Ajouter chaque message dans une liste
        cur1.close()
        logger.info(f"Retrieved {len(messages)} messages from the database")# Enregistrer un message de log indiquant que les messages ont été récupérés de la base de données
        return jsonify(messages)# Renvoyer les messages au format JSON

@app.route('/choixdecompte', methods=['GET', 'POST'])
def choixdecompte():
    if request.method == 'POST' :
        session['chat'] = request.form.get('user')
    return render_template('chat.html', userdis = session['chat'])


#erreur : 

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


if __name__=='__main__':
    app.run(debug= True)
    socketio.run(app, debug=True)