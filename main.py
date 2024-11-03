from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
bootstrap = Bootstrap5(app)


class MyForm(FlaskForm):
    get_rating = StringField('rating out of 10', validators=[DataRequired()])
    get_review = StringField('your review', validators=[DataRequired()])
    done = SubmitField('Done')


@app.route("/edit,<int:id>", methods=['GET', 'POST'])
def edit(id):
    form = MyForm()
    if form.validate_on_submit():
        update_rating = form.get_rating.data
        updated_review = form.get_review.data
        #update in database
        movie_to_edit = db.get_or_404(Movie, id)
        movie_to_edit.rating = update_rating
        movie_to_edit.review = updated_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form)


@app.route("/delete,<int:id>")
def delete(id):
    movie_to_delete = db.get_or_404(Movie,id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


class Form(FlaskForm):
    movie_name = StringField('Movie Title', validators=[DataRequired()])
    add_movie = SubmitField('Add Movie')


@app.route("/add",methods=['GET', 'POST'])
def add_movie():
    add_form = Form()
    if add_form.validate_on_submit():
        movie_title = add_form.movie_name.data
        return redirect(url_for('search', movie_title=movie_title))
    return render_template('add.html', form=add_form)


@app.route("/search/<string:movie_title>")
def search(movie_title):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "query": movie_title,
        "include_adult": "true",
        "language": "en-US",
    }
    headers = {
        "accept": "application/json",
        "Authorization": os.environ.get('AUTH')
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an error for bad responses
        results = response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        return render_template('error.html', error=str(e))

    return render_template('select.html', dict=results)


@app.route("/details,<int:movie_id>")
def get_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    headers = {
        "accept": "application/json",
        "Authorization": os.environ.get('AUTH')
    }
    params = {
            "include_adult": "true",
            "language": "en-US",
        }
    response = requests.get(url, headers=headers, params=params)
    result = response.json()
    title = result['original_title']
    img_url = f"https://image.tmdb.org/t/p/w500/{result['poster_path']}"
    year = result['release_date'].split('-')[0]
    description = result['overview']
    new_movie = Movie(
        id=movie_id,
        title=title,
        year=year,
        description=description,
        rating=5.8,
        ranking=4,
        review="something",
        img_url=img_url
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=movie_id))


# CREATE DB


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy(app)
# CREATE TABLE


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String,unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=False)
    img_url: Mapped[str] = mapped_column(String, nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


if __name__ == '__main__':
    app.run(debug=True)






