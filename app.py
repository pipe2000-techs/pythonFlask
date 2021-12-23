import os
from flask import Flask, request, url_for, redirect, abort, render_template, session
import mysql.connector
from time import time 


app = Flask(__name__)

#creamos una ruta absoluta donde se gurdaran las imagenes
UPLOAD_FOLDER = os.path.abspath("./static/img/")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

#para crear la session se nesesita de una clave
app.secret_key = 'ejemplo-uno-flask'

miDB = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = '',
    database = 'prueva'
)

#funcion para consultas que no sesesitan una salida
def queryInput(query,data):
    cursor.execute(query,data)
    miDB.commit()
    return cursor

#funcion para consultas que si sesesitan una salida
def queryOutput(query,data):
    cursor.execute(query,data)
    result = cursor.fetchall()
    return result

cursor = miDB.cursor(dictionary=True) #con  dictionary podemos obtener el nombre de cada una de las columnas 



@app.route('/login', methods=['GET','POST'])
def login():
    messageAct = 'none'

    #se berifica si hay ya esta creada la cecion
    if 'username' in session and 'password' in session:
        return redirect(url_for('index'))

    #se berifica siel usuari y contraseña conciden con las registradas en la bd y se crea la sesion
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        usuario = queryOutput('select * from usuario where username = %s and password = %s',(username, password))

        if usuario:
            session['username'] = username
            session['password'] = password
            return redirect(url_for('index'))
        else:
            messageAct = ''

    return render_template('login.html', messageAct = messageAct)


#METODOS GET, POST, PUT, PATCH, DELETE
@app.route('/', methods=['GET','POST'])
def index():
    if 'username' in session and 'password' in session:
        button = ''
        msg = ''
        buttonAct = 'none'
        message = []

        if request.method == 'POST':
            username = request.form['user']
            email = request.form['email']
            password = request.form['password']
            f = request.files['image']

            existEmail = queryOutput('select * from usuario where email = %s',(email, ))
            existUser = queryOutput('select * from usuario where username = %s',(username, ))

            if existEmail:
                session['existEmail'] = ''
            elif existUser:
                session['existUser'] = ''
            else:
                #al nombre de la imagen se le agrega el tempo en milisegunos para que no se balla a reemplazar una imagen ya exixstente
                filename = str(time() * 1000)+'_'+str(f.filename)

                cursor = queryInput('insert into usuario (email, username, password, image) values (%s, %s, %s, %s)',(email, username, password, filename))

                if cursor:
                    buttonAct = ''
                    button = 'success'
                    msg = 'Se Guardo Correctamente'

                    #si se guarda en la bd se puede guardar la imagen en la carpeta img
                    f.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))
                else:
                    buttonAct = ''
                    button = 'danger'
                    msg = 'No Se Guardo Correctamente'

        message = [buttonAct,button,msg]

        return render_template('index.html', message = message)

    else:
        return redirect(url_for('login'))


@app.route('/datos', methods=['POST','GET'])
def datos():

    if 'username' in session and 'password' in session:
        
        session.pop('data',None)
        
        usuario = queryOutput('select * from usuario','')
        #abortamos la ejecuacion de nuestro codigo y devolbemos un error
        #abort(404)

        if request.method == 'POST':
            session['data'] = [request.form['id'],request.form['email'],request.form['username'],request.form['password'],request.form['image']]

        return render_template('datos.html', usuarios=usuario)

    else:
        return redirect(url_for('login'))


@app.route('/delete/<delete_id>/<delete_image>', methods=['POST','GET'])
def delete(delete_id,delete_image):
    #se berifica si hay ya esta creada la cecion
    if 'username' in session and 'password' in session:

        cursor = queryInput('delete from usuario where id = %s',(delete_id, ))

        if cursor.rowcount == 1:
            #se borra la secion de data
            session.pop('data',None)
            #se elimina la imagen del servidor
            os.remove("./static/img/"+delete_image)
            return redirect(url_for('datos'))
        else:
            return 'no se pudo eliminar'
    else:
        return redirect(url_for('login'))


@app.route('/update', methods=['POST','GET'])
def update():
    #se berifica si hay ya esta creada la cecion
    if 'username' in session and 'password' in session:
        if request.method == 'POST':
            id = request.form['id']
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']
            imageOld = request.form['image']

            f = request.files['image']
            filename = str(time() * 1000)+'_'+str(f.filename)

            #se berifica si se esta enviando una nueva imagen
            if f.filename == '':
                #se actualiza el registro sin la imagen
                cursor = queryInput('update usuario set email = %s, username = %s, password = %s where id = %s; ',(email,username,password,id))

            else:
                #se borra la imagen del servicor
                os.remove("./static/img/"+imageOld)
                #se guarda la nueva imagen el elservidor 
                f.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))
                #se actualiza el regidtro con la imagen
                cursor = queryInput('update usuario set email = %s, username = %s, password = %s, image = %s where id = %s; ',(email,username,password,filename,id))

            if cursor:
                session.pop('data',None)
                return redirect(url_for('datos'))
            else:
                session['errorUpdate'] = 'No se pudo actualizar el registro'
        else:
            return redirect(url_for('datos'))
    else:
        return redirect(url_for('login'))

@app.route('/cancelUpdate')
def cancelUpdate():
    if 'username' in session and 'password' in session:
        session.pop('data',None)
        return redirect(url_for('datos'))
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))