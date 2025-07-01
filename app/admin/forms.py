from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired
 
class SwapForm(FlaskForm):
    replacement_user = SelectField('Replacement User', validators=[DataRequired()])
    submit = SubmitField('Swap User')

class EditUserForm(FlaskForm):
    is_admin = BooleanField('Is Admin')
    is_intern = BooleanField('Is Intern')
    submit = SubmitField('Update User') 