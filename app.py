
from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

 # config MySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask app'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app);

 
@app.route('/')
def home():
 return render_template('home.html')

@app.route('/records')
def records():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get records
    result = cur.execute("SELECT * FROM records")
    # Show articles only from the user logged in 
    # result = cur.execute("SELECT * FROM records WHERE author = %s", [session['username']])

    records = cur.fetchall()

    if result > 0:
        return render_template('records.html', records=  records)
    else:
        msg = 'No Records Found'
        return render_template('records.html', msg=msg)
    # Close connection
    cur.close()
    
class RegisterForm(Form):
    firstname =  StringField('Firstname',[validators.length(min =1, max = 50),validators.input_required()])
    lastname =  StringField('Lastname',[validators.length(min =1, max = 50),validators.optional()])
    username = StringField('Username',[validators.length(min =4, max = 25), validators.input_required()])
    email = StringField('Email',[validators.length(min =6, max = 50),validators.input_required()])
    password = PasswordField('Password',[
    validators.DataRequired(),
    validators.EqualTo('confirm',message = 'Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# user signup

@app.route('/signup',methods = ['GET','POST'])
def signup():
 form = RegisterForm(request.form);
 
 if request.method == 'POST'  and form.validate():
  firstname = form.firstname.data
  lastname = form.lastname.data
  email = form.email.data
  username = form.username.data
  password = sha256_crypt.encrypt(str(form.password.data))
  
  # create cursor
  cur = mysql.connection.cursor()
  
  # execute query
  
  
  cur.execute(''' INSERT INTO users VALUES(%s,%s,%s,%s,%s)''',(firstname, lastname,email, username, password))
  
  
  # commit to the db
  
  mysql.connection.commit()
  
  #close connection
  
  cur.close()
  
  return redirect(url_for('registered'))
  
   
  
 return render_template('signup.html',form = form)  


# User login
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now signed in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('signin.html', error=error)
            # Close connection
            
            cur.close()
        else:
            error = 'Username not found'
            return render_template('signin.html', error=error)

    return render_template('signin.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('signin'))
    return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get records
    result = cur.execute("SELECT * FROM records")
    # Show articles only from the user logged in 
    # result = cur.execute("SELECT * FROM records WHERE author = %s", [session['username']])

    records = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', records=  records)
    else:
        msg = 'No Records Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()
  


class RecordForm(Form):
    name =  StringField('Company Name',[validators.length(min =1, max = 50),validators.input_required()])
    email = StringField('Email',[validators.length(min =6, max = 50),validators.input_required()])
    number = StringField('Phone Number', [validators.input_required()])
    address =  StringField('Address',[validators.length(min =1, max = 100),validators.input_required()])
    about = TextAreaField('About', [validators.Length(min=30),validators.input_required()])
  
 
 

# Add Records
@app.route('/add_record', methods=['GET', 'POST'])
@is_logged_in
def add_record():
    form = RecordForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        number = form.number.data
        address = form.address.data
        about = form.about.data
        

        # Create Cursor
        cur = mysql.connection.cursor()
         
        # Execute
        cur.execute(''' INSERT INTO records VALUES(%s,%s,%s,%s,%s)''',(name, email,number, address, about))
        
         

        # Commit to DB
        mysql.connection.commit()
        

        #Close connection
        cur.close()

        flash('Record Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_record.html', form=form)

# Edit Record
@app.route('/edit_record/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def edit_record(name):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get record by name
    result = cur.execute("SELECT * FROM records WHERE name = %s", [name])

    record = cur.fetchone()
    cur.close()
    # Get form
    form = RecordForm(request.form) 

    # Populate record form fields
    
    form.name.data = record['name']
    form.email.data = record['email']
    form.number.data = record['number']
    form.address.data = record['address']
    form.about.data = record['about']

    if request.method == 'POST' and form.validate():
         
        
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        address = request.form['address']
        about = request.form['about']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(name)
       #Execute
       
        cur.execute ("UPDATE records SET name=%s, email=%s,number=%s,address=%s,about=%s WHERE name=%s",(name,email,number,address,about,name))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Record updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_record.html', form=form)

# Delete Record
@app.route('/delete_record/<string:name>', methods=['POST'])
@is_logged_in
def delete_record(name):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM records WHERE name = %s", [name])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Record Deleted', 'success')

    return redirect(url_for('dashboard'))


@app.route('/registered')
def registered():
    return render_template('thankYou.html')

# Logout
@app.route('/signout')
def signout():
    session.clear()
    flash('You are now signed out', 'success')
    return redirect(url_for('signin'))

if __name__ == '__main__':
 app.secret_key = 'secret123'
 app.run(debug = True) 