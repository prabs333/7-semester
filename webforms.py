from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,BooleanField,ValidationError
from wtforms.validators import DataRequired,EqualTo,Length,Email

# Login form
class LoginForm(FlaskForm):
    username=StringField("Username",validators=[DataRequired()])
    password=PasswordField("Password",validators=[DataRequired()])
    submit=SubmitField("Submit")

# Create a form class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username=StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(),Email()])
    password_hash=PasswordField('Password',validators=[DataRequired(),EqualTo('password_hash2',message="Password Must Match")])
    password_hash2=PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Submit")

# for the password
class PasswordForm(FlaskForm):
    email=StringField("What is your email",validators=[DataRequired()])
    password=PasswordField("What is your password",validators=[DataRequired()])
    submit=SubmitField("Submit")