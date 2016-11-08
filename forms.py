from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, TextAreaField, DateField)
from wtforms.validators import (DataRequired, Regexp, ValidationError,
                                Length, EqualTo)

from models import User


def name_exists(form, field):
    """check if a user exists"""
    if User.select().where(User.username == field.data).exists():
        raise ValidationError('User with that name already exists.')


class RegisterForm(FlaskForm):
    """form for creating new users"""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Regexp(
                r'^[a-zA-Z0-9_]+$',
                message=("Username should be one word, letters, "
                         "numbers, and underscores only.")
            ),
            name_exists
        ])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=2),
            EqualTo('password2', message='Passwords must match')
        ])
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
    )


class LoginForm(FlaskForm):
    """form for login details"""
    username = StringField('Username', validators=[DataRequired(),
                           Regexp(r'^[a-zA-Z0-9_]+$',
                           message="Username should be one word, letters, numbers, and underscores only.")])

    password = PasswordField('Password', validators=[DataRequired()])


class EntryForm(FlaskForm):
    """form for journal entries"""
    title = StringField(validators=[DataRequired()])
    tags = StringField()
    date = DateField(validators=[DataRequired()])
    time_spent = StringField(validators=[DataRequired()])
    learning = TextAreaField(validators=[DataRequired()])
    resources = TextAreaField(validators=[DataRequired()])
