from flask import (Flask, g, render_template, flash, redirect, url_for, abort,
                   request)
from flask_login import (LoginManager, login_user, logout_user, login_required,
                         current_user)
from flask_bcrypt import check_password_hash
import re
import forms
import models


DEBUG = True
PORT = 5000
HOST = '127.0.0.1'

app = Flask(__name__)

app.secret_key = 'aGetdfsergokajeraijFGedmr3#><?94j0934jsjmg0d,321,-,-32s,4395'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    """user_loader does the user login process"""
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request."""
    g.db.close()
    return response


@app.route('/', methods=('GET', 'POST'))
def index():
    """main view displays users logs if they are logged in or a welcome page"""
    if current_user in models.User.select():
        user = current_user
        journal = user.get_journal()
        list_tags = re.findall('#[a-zA-Z0-9\-_]+\w', user.tags)
        try:  # check for no entrys in journal
            journal[0]
        except IndexError:
            journal = None
        return render_template('journal.html', journal=journal, user=user, tags=list_tags)
    else:
        return render_template('welcome.html')


@app.route('/tags/<string:tag>')
@login_required
def tags(tag):
    """displays a version of the main page with only entries with a specific tag"""
    tag_list = [tag]
    user = current_user
    journal = user.get_tagged_journals(tag)
    return render_template('journal.html', journal=journal, user=user, tags=tag_list)


@app.route('/detail/<string:entry_id>')
@login_required
def detail(entry_id):
    """shows a detailed view of a journal entry with all fields and options for editing and deleting"""
    entry = models.Journal.get(models.Journal.entry_id == entry_id)
    list_tags = re.findall('#[a-zA-Z0-9\-_]+', entry.tags)
    if current_user.owner(entry):  # prevent unautherised users from accessing
        return render_template('detail.html', entry=entry, tags=list_tags)
    else:
        abort(404)


@app.route('/delete/<string:entry_id>')
@login_required
def delete(entry_id):
    """removes an entry from database then returns to index"""
    entry = models.Journal.get(models.Journal.entry_id == entry_id)
    user = current_user
    if user.owner(entry):  # prevent unautherised users from accessing
        entry.delete_instance()
        models.tags_persist(user)
        return redirect(url_for('index'))
    else:
        abort(404)


@app.route('/edit/<string:entry_id>', methods=('GET', 'POST'))
@login_required
def edit(entry_id):
    """opens view to edit existing entry filling fields with existing entry for ease of use checks tags still exist"""
    user = current_user
    entry = models.Journal.get(models.Journal.entry_id == entry_id)
    date = entry.date
    if user.owner(entry):
        form = forms.EntryForm(obj=entry)
        if form.validate_on_submit():

            list_tags = re.findall('#[a-zA-Z0-9\-_]+', form.tags.data)
            new_tags = ""
            for tag in list_tags:
                new_tags += tag + " "

            entry.user = g.user._get_current_object()
            entry.title = form.title.data
            entry.tags = new_tags
            entry.date = form.date.data
            entry.time_spent = form.time_spent.data
            entry.learning = form.learning.data
            entry.resources = form.resources.data
            entry.save()

            models.tags_persist(user)
            models.add_tags(user, entry.tags)

            flash("Journal Entry added! Thanks!")
            return redirect(url_for("index"))
        return render_template('edit.html', form=form, date=date)
    else:
        abort(404)


@app.route('/new', methods=('GET', 'POST'))
@login_required
def new():
    """creates as new entry from Entryform adds any new tags to the users tag list"""
    form = forms.EntryForm()
    if form.validate_on_submit():
        models.Journal.create_entry(user=g.user._get_current_object(),
                                    title=form.title.data,
                                    tags=form.tags.data,
                                    date=form.date.data,
                                    time_spent=form.time_spent.data,
                                    learning=form.learning.data,
                                    resources=form.resources.data)

        list_tags = re.findall('#[a-zA-Z0-9\-_]+', form.tags.data)
        user = current_user
        for tag in list_tags:
            tag += " "
            if tag not in user.tags:
                user.tags += tag + " "
                user.save()

        flash("Journal Entry added! Thanks!")
        return redirect(url_for("index"))
    return render_template('new.html', form=form)


@app.route('/register', methods=('GET', 'POST'))
def register():
    """allows new users to get a login"""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("yay, you registered", "success")
        models.User.create_user(username=form.username.data,
                                password=form.password.data)
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            pass
        else:
            login_user(user)

        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route("/login", methods=('GET', 'POST'))
def login():
    """presents a login form if correct username and password login_user is called"""
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            flash("Your username or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("you've been logged in!", "success")
                return redirect(url_for('index'))
            else:
                flash("Your username or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    """logs out user"""
    logout_user()
    flash("you have been logged out. bye!", "success")
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found():
    """presents 404 page with link back to index"""
    return render_template('404.html'), 404


if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(
            username='josh',
            password='123',
        )
    except ValueError:
        pass
    app.run(debug=DEBUG, host=HOST, port=PORT)
