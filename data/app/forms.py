from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, Form
from wtforms.validators import DataRequired

# Create a non-CSRF form base class
class NoCSRFForm(Form):
    """A base form that doesn't use CSRF protection."""
    pass

class GuestRegistrationForm(NoCSRFForm):
    name = StringField('Name', validators=[DataRequired()])
    company = StringField('Company')
    host = StringField('Host/Meeting', validators=[DataRequired()])
    additional_guests = TextAreaField('Additional Guests (One per line)')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In') 