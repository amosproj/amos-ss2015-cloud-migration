"""
Routes and views for the flask application.
"""
import hashlib
import uuid

from flask import render_template, send_from_directory, redirect, url_for, session, g, request
from FlaskWebProject import app, db, lm, facebook, google
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug.routing import BaseConverter
import os
from .forms import LoginForm, RegisterForm
from .models import User
from FlaskWebProject import storageinterface

# Global constants
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_STATIC = os.path.join(APP_ROOT, 'static')


# Regex Handling for URLs
class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

app.url_map.converters['regex'] = RegexConverter


# Function for LoginManager to get a user with specific id
@lm.user_loader
def load_user(id):
    user = User.query.get(int(id))
    if user:
        return user


@app.before_request
def before_request():
    g.user = current_user


@app.route('/create_bucket')
def create_bucket():
    storageinterface.create_container('test1')
    return redirect(url_for('home'))

@app.route('/upload_from_text')
def upload_from_text():
    storageinterface.upload_from_text('test1', 'filename.txt', 'content')
    return redirect(url_for('home'))

@app.route('/delete_bucket')
def delete_bucket():
    storageinterface.delete_container('test1')
    return redirect(url_for('home'))


@app.route('/')
@app.route('/index')
@login_required
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """UserName Password Login"""
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    error = None
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(
                username=request.form['username']).first()
            if user is not None and user.sso == "none":
                password, salt = user.password.split(':')
                if password == hashlib.sha256(salt.encode() + request.form['password'].encode()).hexdigest():
                    session['remember_me'] = form.remember_me.data
                    login_user(user)
                    return redirect(request.args.get('next') or url_for('home'))
                else:
                    error = 'Invalid passowrd'
            else:
                error = 'Invalid username'
    return render_template('login.html', form=form, error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """UserName Password Register"""
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        # generate randomness
        salt = uuid.uuid4().hex
        # hashing password
        user = User.query.filter_by(username=request.form['username']).first()
        email = User.query.filter_by(email=request.form['email']).first()
        if user is None and email is None:
            password = hashlib.sha256(
                salt.encode() + form.password.data.encode()).hexdigest() + ':' + salt
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=password,
                sso="none"
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
    return render_template('register.html', form=form)


@login_required
@app.route('/<path:filepath1>/<path:filepath2>')
def static_files(filepath1, filepath2):
    return send_from_directory(os.path.join(APP_STATIC, 'scripts', filepath1, os.path.dirname(filepath2)),  os.path.basename(filepath2))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


'''
OAuth2 Facebook Login
'''


@app.route('/login_fb', methods=['GET', 'POST'])
def login_fb():
    callback_url = url_for('facebook_authorized', _external=True)
    return facebook.authorize(callback=callback_url)


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.route('/login_fb/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_for('home')
    if resp is None:
        # The user likely denied the request
        # TODO: excalate error to user: 'There was a problem logging in with
        # Google.'
        return redirect(next_url)
    session['oauth_token'] = (resp['access_token'], '')
    user_data = facebook.get('/me').data
    user = User.query.filter(User.email == user_data['email']).first()
    # TODO: Security Issue, Disable Login from different SSO's with same mail
    # to same user
    if user is None:
        new_user = User(email=user_data['email'], username=user_data[
                        'id'], password=" ", sso="facebook")
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
    else:
        login_user(user)
    return redirect(next_url)


'''
OAuth2 Google Login
'''


@app.route('/login_google', methods=['GET', 'POST'])
def login_google():
    # next_url = request.args.get('next') or url_for('home')
    callback_url = url_for('google_authorized', _external=True)
    return google.authorize(callback=callback_url)


@google.tokengetter
def get_google_oauth_token():
    return session.get('oauth_token')


@app.route('/login_google/authorized')
@google.authorized_handler
def google_authorized(resp):
    next_url = request.args.get('next') or url_for('home')
    if resp is None:
        # The user likely denied the request
        # TODO: excalate error to user: 'There was a problem logging in with
        # Google.'
        return redirect(next_url)
    session['oauth_token'] = (resp['access_token'], '')
    user_data = google.get('/userinfo/v2/me').data
    user = User.query.filter(User.email == user_data['email']).first()
    # TODO: Security Issue, Disable Login from different SSO's with same mail
    # to same user
    if user is None:
        new_user = User(
            email=user_data['email'], username=user_data['id'], password=" ", sso="google")
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
    else:
        login_user(user)
    return redirect(next_url)


'''
REST API
'''


@app.route('/storage/api/v1.0/<int:bucket_id>', methods=['GET'])
def rest_list_files(bucket_id):
    """ Lists files in container """
    storageinterface.list_files(bucket_id)
    return None


@app.route('/storage/api/v1.0/<int:bucket_id>', methods=['DELETE'])
def rest_delete_container(bucket_id):
    """ Deletes specified container """
    storageinterface.delete_container(bucket_id)
    return None


@app.route('/storage/api/v1.0/<int:bucket_id>/<string:file_id>', methods=['GET'])
def rest_download_file_to_text(bucket_id, file_id):
    """ Returns specified file in container as text """
    storageinterface.download_file_to_text(bucket_id, file_id)
    return None


@app.route('/storage/api/v1.0/<int:bucket_id>/<string:file_id>', methods=['POST'])
def rest_upload_from_text(bucket_id, file_id):
    """ Uploads text to new file in container """
    return None


@app.route('/storage/api/v1.0/<int:bucket_id>/<string:file_id>', methods=['PUT'])
def rest_overwrite_file_from_text(bucket_id, file_id):
    """ Uploads text to file in container """
    return None


@app.route('/storage/api/v1.0/<int:bucket_id>/<string:file_id>', methods=['DELETE'])
def rest_delete_file(bucket_id, file_id):
    """ Deletes file in container """
    storageinterface.delete_file(bucket_id, file_id)
    return None
