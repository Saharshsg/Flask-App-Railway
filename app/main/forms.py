from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, ValidationError, TextAreaField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional

class AttendanceForm(FlaskForm):
    status = SelectField('Your Status', choices=[('Yes', 'Coming'), ('No', 'Not Coming')], validators=[DataRequired()])
    meal_preference = SelectField('Meal', choices=[('Veg', 'Veg'), ('Non-Veg', 'Non-Veg'), ('No Meal', 'No Meal')], validators=[Optional()])
    submit = SubmitField('Save')

    def validate_meal_preference(self, meal_preference):
        if self.status.data == 'Yes' and not meal_preference.data:
            raise ValidationError('Please select a meal preference if you are attending.')

class ReassignmentForm(FlaskForm):
    reason = TextAreaField('Reason for Reassignment', validators=[DataRequired()])
    submit = SubmitField('Submit Request to Admin') 