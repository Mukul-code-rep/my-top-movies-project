from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get("api_key")
TMDB_URL = 'https://api.themoviedb.org/3/search/movie'
MOVIE_URL = 'https://api.themoviedb.org/3/movie/'
IMAGE_URL = 'https://image.tmdb.org/t/p/w500'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-10-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class EditMovie(FlaskForm):
    new_rating = StringField('Your Rating Out of 10')
    new_review = StringField('Your Review')
    submit = SubmitField('Update')


class AddMovie(FlaskForm):
    title = StringField("Name of movie", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = EditMovie()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if movie is None:
        response = requests.get(url=MOVIE_URL+f'{movie_id}?api_key={API_KEY}')
        response.raise_for_status()
        movie = response.json()
        if form.validate_on_submit():
            new_movie = Movie(
                title=movie["original_title"],
                description=movie["overview"],
                year=int(movie["release_date"][:4]),
                img_url=IMAGE_URL+movie["poster_path"],
                rating=float(form.new_rating.data),
                review=form.new_review.data
            )
            db.session.add(new_movie)
            db.session.commit()
            return redirect(url_for('home'))
    else:
        if form.validate_on_submit():
            movie.rating = float(form.new_rating.data)
            movie.review = form.new_review.data
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=movie)


@app.route('/delete')
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        movie_name = form.title.data
        response = requests.get(url=TMDB_URL+f'?api_key={API_KEY}&query={movie_name}')
        response.raise_for_status()
        data = response.json()
        return render_template('select.html', data=data)
    return render_template('add.html', form=form)


if __name__ == '__main__':
    app.run(debug=True, port=5003, use_reloader=False)
