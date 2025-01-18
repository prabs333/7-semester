from flask import Flask, render_template, flash,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,BooleanField,ValidationError
from wtforms.validators import DataRequired,EqualTo,Length
from werkzeug.security import generate_password_hash,check_password_hash
from flask_migrate import Migrate
from flask_login import UserMixin,login_user,LoginManager,login_required,logout_user,current_user
# Create flask instance
app = Flask(__name__)

# Add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# Secret key
app.config['SECRET_KEY'] = "mysecretkey"
# Configuring the database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)
# Migrating the database
migrate=Migrate(app,db)

# Flask_Login Stuff
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Login form
class LoginForm(FlaskForm):
    username=StringField("Username",validators=[DataRequired()])
    password=PasswordField("Password",validators=[DataRequired()])
    submit=SubmitField("Submit")

# login page
@app.route('/login', methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=Users.query.filter_by(username=form.username.data).first()
        if user:
            #check the hash
            if check_password_hash(user.password_hash,form.password.data):
                login_user(user)
                flash("Login Successful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try again")
        else:
            flash("That User Doesnot Exist! Try Again!")
    return render_template('login.html',form=form)

# logout page
@app.route('/logout',methods=['GET','POSt'])
@login_required
def logout():
    logout_user()
    flash("You have been logout! Thank You")
    return redirect(url_for('login'))

# dashboard page
@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    form=LoginForm()
    return render_template('dashboard.html',form=form)


# Create model
class Users(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20),nullable=False,unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    # password stuff
    password_hash=db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')

    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    # Create a string
    def __repr__(self):
        return '<Name %r>' % self.name

# Create the database tables
with app.app_context():
    db.create_all()

# Create a form class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username=StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password_hash=PasswordField('Password',validators=[DataRequired(),EqualTo('password_hash2',message="Password Must Match")])
    password_hash2=PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Submit")

@app.route('/')
def index():
    return render_template("index.html")


# for adding the user
@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    name = None   
    form = UserForm()
    # Validating the user entered name and email are not present in the database
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            #Hash the password
            hashed_pw = generate_password_hash(form.password_hash.data,method= "pbkdf2:sha256")
            user = Users(username=form.username.data,name=form.name.data, email=form.email.data,password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()

        name = form.name.data
        form.name.data = ''
        form.username.data=''
        form.email.data = ''
        form.password_hash.data=''
        form.password_hash2.data=''
        flash("User Added Successfully!")
    # Retrieve all users from the database, ordered by date_added
    our_users = Users.query.order_by(Users.date_added).all()  # .all() to get list
    return render_template("add_user.html", form=form, name=name, our_users=our_users)

#for updating the user
@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):
    form= UserForm()
    name_to_update=Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name=request.form['name']
        name_to_update.email=request.form['email']
        name_to_update.username=request.form['username']
        try:
            db.session.commit()
            flash("User updated successfully")
            return render_template("update.html",
            form=form,
            name_to_update=name_to_update)
        except:
            flash("Error! Something went wrong... Try again")
            return render_template("update.html",
            form=form,
            name_to_update=name_to_update)
    else:
        flash("Error! Something went wrong... Try again")
        return render_template("update.html",
            form=form,
            name_to_update=name_to_update)

# for the delete
@app.route('/delete/<int:id>')
def delete(id):
    user_to_delete=Users.query.get_or_404(id)
    name = None   
    form = UserForm()
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully !!")

        our_users = Users.query.order_by(Users.date_added).all()  # .all() to get list
        return render_template("add_user.html", form=form, name=name, our_users=our_users)
    except:
        flash("Whoops! There was a problem using deleting the user, try again....")
        our_users = Users.query.order_by(Users.date_added).all()  # .all() to get list
        return render_template("add_user.html", form=form, name=name, our_users=our_users)

# for testing the password
class PasswordForm(FlaskForm):
    email=StringField("What is your email",validators=[DataRequired()])
    password=PasswordField("What is your password",validators=[DataRequired()])
    submit=SubmitField("Submit")

# for testing the password hashing
@app.route('/test_pw',methods=['GET','POST'])
def test_pw():
    email=None
    password=None
    pw_to_check=None
    passed=None
    form=PasswordForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password_hash.data
        
        # clear the form
        form.email.data=''
        form.password_hash.data=''

        pw_to_check=Users.query.filter_by(email=email).first()
        
    return render_template("testPW.html",email=email,password=password,form=form,pw_to_check=pw_to_check)

if __name__ == "__main__":
    app.run(debug=True)
