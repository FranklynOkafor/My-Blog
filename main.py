from typing import Any
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, sessionmaker
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, CreateLoginForm, CreateRegisterForm, CreateCommentForm
from flask_gravatar import Gravatar
from sqlalchemy import create_engine, ForeignKey, Integer, Column, Text, Float, String, CHAR, Boolean
from functools import wraps
from sqlalchemy.ext.declarative import declarative_base

login_manager = LoginManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager.init_app(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/hp/Desktop/My_projects/Blog/blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# class Base(DeclarativeBase):
#     pass
Base = declarative_base()

##CONFIGURE TABLES
class User_data(UserMixin, Base):
    __tablename__ = 'users'

    id = Column('id', Integer, primary_key=True)
    name = Column('name', String, nullable=False)
    password = Column('password', String, nullable=False)
    email = Column('email', String, nullable=False, unique=True)
    posts = relationship('BlogPost', back_populates='author')
    user_comments = relationship('Comments', back_populates='writer')

    def __init__(self, id, name, password, email):
        self.id = id
        self.email = email
        self.name = name
        self.password = password

    def __repr__(self):
        return f'Name: {self.name}\nEmail:{self.email}'
    

class BlogPost(UserMixin, Base):
    __tablename__ = 'blog_post'

    id = Column(name='id', type_=Integer, primary_key=True)
    author_id = Column('author_id', Integer, ForeignKey('users.id'))
    title = Column('title', String, unique=True, nullable=False)
    subtitle = Column('subtitle', String, nullable=False)
    body = Column('body', String, nullable=False)
    # author = Column('author', String, nullable=False)
    date = Column('date', String, nullable=False)
    img_url = Column('img_url', String, nullable=False)
    author = relationship('User_data', back_populates='posts')
    comments_under_post = relationship('Comments', back_populates='comment_post')

    def __init__(self, id, author_id, title, subtitle, body, author, date, img_url):
        self.id = id
        self.author_id = author_id
        self.title = title
        self.subtitle = subtitle
        self.body = body
        self.author = author
        self.date = date
        self.img_url = img_url

    def __repr__(self):
        return f'{self.title} by {self.author}'

    
class Comments(UserMixin, Base):
    __tablename__ = 'comments'

    id = Column('id', Integer, primary_key=True)
    comment = Column('comment', String, nullable = False)
    commenter_id = Column('commenter_id', Integer, ForeignKey('users.id'))
    post_title = Column('post_title', String, ForeignKey('blog_post.title'))
    writer = relationship('User_data', back_populates='user_comments')
    comment_post = relationship('BlogPost', back_populates='comments_under_post')

    def __init__(self, id, comment, commenter_id, post_title):
        self.id = id
        self.comment = comment
        self.commenter_id = commenter_id
        self.post_title = post_title

engine = create_engine('sqlite:///C:/Users/hp/Desktop/My_projects/Blog/blog.db', echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
session = Session()

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return function(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    user = session.query(User_data).filter(User_data.id == user_id)
    for _ in user:
        return _


@app.route('/', methods=['GET', 'POST'])
# @login_required
def get_all_posts():
    login_manager.login_view = 'login'
    admin = False
    user_is_anonymos = False
    posts = session.query(BlogPost).all()
    num = 0
    for post in posts:
        num += 1
    if num < 1:
        posts=[]
    users = session.query(User_data).all()
    if current_user not in users:
        admin = False
        user_is_anonymos = True
    if not user_is_anonymos:
        if current_user.id == 1:
            admin = True
    return render_template("index.html", all_posts=posts, logged_in =True, current_user = current_user, admin = admin)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = CreateRegisterForm()
    if form.validate_on_submit():
        num = 1
        all_users = session.query(User_data).all()
        for _ in all_users:
            if _.email == request.form['email']:
                flash('Email already registered')
                return render_template("register.html", form=form, logged_in = False)
            num += 1
        new_user = User_data(
            id=num,
            name=request.form['name'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=10)
        )
        session.add(new_user)
        session.commit()
        return redirect(url_for('login'))
    return render_template("register.html", form=form, logged_in = False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = CreateLoginForm()
    if form.validate_on_submit():
        email_registered = False
        num = 0
        user = session.query(User_data).filter(User_data.email == request.form['email'])
        for _ in user:
            num = 1
        if num > 0:
            email_registered = True
        if email_registered:
            for current in user:
                if check_password_hash(current.password, request.form['password']):
                    login_user(current)
                    return redirect(url_for('get_all_posts'))
                else:
                    flash('Wrong password')
                    return redirect(url_for('login'))
        else:
            flash('Email not registered')
            return redirect(url_for('login'))
    return render_template("login.html", form = form, logged_in = False)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
# @login_required
def show_post(post_id):
    # login_manager.login_view = 'login'
    form = CreateCommentForm()
    requested_post = session.query(BlogPost).filter(BlogPost.id == post_id)
    for post in requested_post:
        if request.method == 'POST':
            
            if not current_user.is_authenticated:
                flash('You need to login or register to comment')
                return redirect(url_for('login'))
            num = 1
            all_comments = session.query(Comments).all()
            for _ in all_comments:
                num += 1
            new_comment = Comments(
                id=num,
                comment=request.form['body'],
                commenter_id=current_user.id,
                post_title=post.title
            )
            session.add(new_comment)
            session.commit()
            return redirect(url_for('show_post', post_id=post_id))
    
    for _ in requested_post:
        all_comments = session.query(Comments).filter(Comments.post_title == _.title)
        all_users = session.query(User_data).all()
        return render_template("post.html", post=_, logged_in = True, form = form, comments = all_comments)


@app.route("/about", methods=['GET', 'POST'])
def about():
    return render_template("about.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        all_post = session.query(BlogPost).all()
        num = 1
        for _ in all_post:
            num += 1
        new_post = BlogPost(
            id=num,
            author_id=current_user.id,
            title=request.form['title'],
            subtitle=request.form['subtitle'],
            body=request.form['body'],
            img_url=request.form['img_url'],
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        session.add(new_post)
        session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    pick_post = session.query(BlogPost).filter(BlogPost.id == post_id)
    for post in pick_post:
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
    if edit_form.validate_on_submit():
        for post in pick_post:
            post.title = request.form['title']
            post.subtitle = request.form['subtitle']
            post.img_url = request.form['img_url']
            post.author = request.form['author']
            post.body = request.form['body']
            session.commit()
            return redirect(url_for("show_post", post_id=post.id))

        return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>", methods=['GET', 'POST'])
@admin_only
def delete_post(post_id):
    post_to_delete = session.query(BlogPost).filter(BlogPost.id == post_id)
    for _ in post_to_delete:
        session.delete(_)
        session.commit()
        return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
