from flask import *
from datetime import datetime
import mysql.connector
import imghdr

app = Flask(__name__)

import urllib, hashlib


cnx = mysql.connector.connect(host = 'localhost',
                              user = 'root',
                              password = '',
                              database = 'bdmain')

app.secret_key = b'74$mo7iokz&qmhfgg35r+641a(vqw4pkfdp7bl4ogqimv2*9pj'

cur = cnx.cursor()

@app.route("/")
def index():
    return render_template('index.html')
@app.route('/update')
def update():
    return render_template('update.html')
@app.route("/login")
def login():
    return render_template('login.html')
@app.route('/signup')
def signup():
    return render_template('signup.html')
@app.route("/param")
def param():
    return render_template('param.html')
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('mail', None)
    session.pop('id', None)
    session.pop('pseudo', None)
    session.pop('date', None)
    return redirect(url_for('index'))
@app.route('/login2', methods =['GET', 'POST'])
def login2():
    msg = ''
    if request.method == 'POST' :
        mail = request.form['mail']
        password = request.form['password']
        cur.execute('SELECT * FROM user WHERE mail = %s AND password = %s', (mail, password))
        account = cur.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['mail'] = account[1]
            session['pseudo'] = account[2]
            session['date'] = account[4]
            msg = 'Logged in successfully !'
            print(msg)
            return render_template('index.html', msg = msg)
        else:
            msg = 'Incorrect pseudo / password !'
    return render_template('login.html', msg = msg)
@app.route('/register', methods =['GET', 'POST'])
def register():
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
            val = mail, pseudo, mdp, date
            sql = "INSERT INTO user (mail, pseudo, password, date) VALUES (%s, %s, %s, %s)"
            cur.execute(sql, val)
            cnx.commit()
            msg = 'You have successfully registered !'
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
    print("suppréssion réussis")
    logout()
    return render_template('index.html')

@app.route('/update2', methods =['GET', 'POST'])
def update2():
    mail = session['mail']
    pseudo = request.form.get('pseudo')
    mdp = request.form.get('password')
    mail2 = request.form.get('mail')
    val = mail2, pseudo, mdp, mail
    sql = "UPDATE user SET mail = %s, pseudo = %s, password = %s WHERE mail = %s"
    cur.execute(sql, val)
    cnx.commit()
    return render_template('index.html')

@app.route('/upload_img', methods = ['GET', 'POST'])
def upload_img():
    if request.method == 'POST':
        img = request.form.get('file')
        print(img)
        res = imghdr.what(img)
        print(res)
        mail = session['mail']
        cur.execute('SELECT * FROM img INNER JOIN user ON image.id_pp = user.id WHERE user.mail = %s', (mail))
        account = cur.fetchone()
        if res == 'png':
            if account:
                val =  img, mail
                sql = "UPDATE image FROM img INNER JOIN user ON image.id_pp = user.id SET img = %s, WHERE user.mail = %s"
                cur.execute(sql, val)
                cnx.commit()
            else:
                val = img
                sql = "INSERT INTO img (img) VALUES (%s)"
                cur.execute(sql, val)
                cnx.commit()
                msg = 'Bien enregistrer'
        else : 
            msg = 'Nous ne prennons compte que des fichier .png'
    return render_template('param.html', msg = msg)

if __name__=='__main__':
    app.run(debug= True)

cnx.close()




