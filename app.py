from flask import Flask, render_template, flash,request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from flask_migrate import Migrate
from flask_login import UserMixin,login_user,LoginManager,login_required,logout_user,current_user
from webforms import LoginForm, UserForm, PasswordForm
import pickle
import pandas as pd

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

# load the model and scaler
with open('crop_recommendation_model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('robust_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/')
def index():
    return render_template("index.html")

# recommend crop page
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    try:
        if request.method == 'POST':
            # Get input data from the form
            N = float(request.form['N'])
            P = float(request.form['P'])
            K = float(request.form['K'])
            temperature = float(request.form['temperature'])
            humidity = float(request.form['humidity'])
            ph = float(request.form['ph'])
            rainfall = float(request.form['rainfall'])

            # Validation rules
            if N <= 0 or N > 150:
                raise ValueError("Nitrogen (N) value must be between 1 and 150.")
            if P <= 0 or P > 150:
                raise ValueError("Phosphorus (P) value must be between 1 and 150.")
            if K <= 0 or K > 200:
                raise ValueError("Potassium (K) value must be between 1 and 200.")
            if temperature <= 0 or temperature > 45:
                raise ValueError("Temperature must be between 1 and 45°C.")
            if humidity < 10 or humidity > 100:
                raise ValueError("Humidity must be between 10% and 100%.")
            if ph < 0 or ph > 9:
                raise ValueError("pH value must be between 0 and 9.")
            if rainfall < 100 or rainfall > 300:
                raise ValueError("Rainfall must be between 100mm and 300mm.")

            # Prepare the input for the model
            input_data = pd.DataFrame([[N, P, K, temperature, humidity, ph, rainfall]],
                                       columns=['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall'])

            # Scale the input data using the scaler
            input_data_scaled = scaler.transform(input_data)

            # Make prediction
            prediction = model.predict(input_data_scaled)

            # Get the recommended crop
            recommended_crop = prediction[0]

            # Render the template with the result and input values
            return render_template('predict.html', recommended_crop=recommended_crop,
                                   N=N, P=P, K=K, temperature=temperature, humidity=humidity,
                                   ph=ph, rainfall=rainfall)

        return render_template('predict.html')

    except Exception as e:
        # Render the template with the error message
        return render_template('predict.html', error=str(e),
                               N=request.form.get('N', ''),
                               P=request.form.get('P', ''),
                               K=request.form.get('K', ''),
                               temperature=request.form.get('temperature', ''),
                               humidity=request.form.get('humidity', ''),
                               ph=request.form.get('ph', ''),
                               rainfall=request.form.get('rainfall', ''))

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

# admin page
@app.route('/admin')
@login_required
def admin():
    id=current_user.id
    if id==1:
        name = None   
        form = UserForm()
        # Retrieve all users from the database, ordered by date_added
        our_users = Users.query.order_by(Users.date_added).all()  # .all() to get list
        return render_template("admin.html", form=form, name=name, our_users=our_users)
    else:
        flash("Sorry... Only Admin can access this page")
        return redirect(url_for('dashboard'))

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


# for adding the user
@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        # Check if the username already exists
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for('add_user'))

        # Add the user if they don't exist
        hashed_pw = generate_password_hash(form.password_hash.data, method="pbkdf2:sha256")
        user = Users(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        flash("User added successfully!", "success")
        return redirect(url_for('add_user'))

    return render_template('add_user.html', form=form)
#for updating the user
@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):

    if id!=current_user.id and current_user.id!=1:
        flash("You are not authorized to update others information","warning")
        return redirect(url_for('dashboard'))
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
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if current_user.id != 1:  # Ensure only the admin can delete
        flash("Unauthorized access.")
        return redirect(url_for('admin'))

    user_to_delete = Users.query.get_or_404(id)
    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User deleted successfully!")
    except:
        flash("There was a problem deleting the user, try again.")

    return redirect(url_for('admin'))

# for the contact
@app.route('/contact', methods=['POST'])
def contact():
    # Get form data
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']

    flash("Your message has been sent! Thank you for contacting us.")
    return redirect(url_for('index'))  # Redirect to the homepage or another page


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
