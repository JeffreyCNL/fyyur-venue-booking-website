# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['SQLALCHEMY_DATABASE_URL'] = 'postgres://postgres@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    show = db.relationship('Show', backref='venue', lazy=True)

    # : implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    show = db.relationship('Show', backref='artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'Show'

    show_id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # get all the areas
    areas = Venue.query.with_entities(Venue.city, Venue.state)\
                .group_by(Venue.city, Venue.state).all()
    data = []
    for area in areas:
        # get all the venues in this area
        area_venues = Venue.query.filter_by(city=area.city).filter_by(state=area.state).all()
        venues = []
        for venue in area_venues:
            venues.append({
                "id": venue.id,
                "name": venue.name
            })
        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venues
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term')
    results = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
    response = {}
    response["count"] = len(results)
    response["data"] = results
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    if not venue:
        not_found_error(True)
    past_shows = Show.query.join(Artist).filter(Show.venue_id == venue_id)\
        .filter(Show.start_time < datetime.now()).all()

    upcoming_shows = Show.query.join(Artist).filter(Show.venue_id == venue_id)\
        .filter(Show.start_time > datetime.now()).all()
    old_shows = []
    new_shows = []
    for past_show in past_shows:
        old_shows.append({
            "artist_id": past_show.artist.id,
            "artist_name": past_show.artist.name,
            "artist_image_link": past_show.artist.image_link,
            "start_time": past_show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    for upcoming_show in upcoming_shows:
        new_shows.append({
            "artist_id": upcoming_show.artist.id,
            "artist_name": upcoming_show.artist.name,
            "artist_image_link": upcoming_show.artist.image_link,
            "start_time": upcoming_show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": old_shows,
        "upcoming_shows": new_shows,
        "past_shows_count": len(old_shows),
        "upcoming_shows_count": len(new_shows)
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html',form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        genres = request.form.getlist('genres')
        address = request.form.get('address')
        phone = request.form.get('phone')
        image_link = request.form.get('image_link')
        website = request.form.get('website')
        facebook_link = request.form.get('facebook_link')
        seeking_talent = True if 'seeking_talent' in request.form else False
        seeking_description = request.form.get('seeking_description')
        venue = Venue(name=name, city=city, state=state,
                      genres=genres, address=address,
                      phone=phone, image_link=image_link,
                      website=website,facebook_link=facebook_link,
                      seeking_talent=seeking_talent, seeking_description=seeking_description)
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        # unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    if error:
        flash('Venue' + request.form['name'] + ' could not be listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.sessoin.delete(venue)
        db.session.commit()
        flash("Venue " + request.form['name'] + " was deleted successfully!")
    except:
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash("Venue " + request.form['name'] + " could not be deleted!")

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.all()
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term')
    # ilike for case insensitive
    results = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
    response = {}
    response["count"] = len(results)
    response["data"] = results
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    artist = Artist.query.get(artist_id)
    if not artist:
        not_found_error(True)
    old_shows = []
    new_shows = []
    # query for past or upcoming shows
    past_shows = Show.query.join(Venue).filter(Show.artist_id == artist_id)\
        .filter(Show.start_time < datetime.now()).all()
    upcoming_shows = Show.query.join(Venue).filter(Show.artist_id == artist_id) \
        .filter(Show.start_time > datetime.now()).all()


    for past_show in past_shows:
        old_shows.append({
            "venue_id": past_show.venue.id,
            "venue_name": past_show.venue.name,
            "venue_image_link": past_show.venue.image_link,
            "start_time": past_show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    for upcoming_show in upcoming_shows:
        new_shows.append({
            "venue_id": upcoming_show.venue.id,
            "venue_name": upcoming_show.venue.name,
            "venue_image_link": upcoming_show.venue.image_link,
            "start_time": upcoming_show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    data = {
        "id": artist.id,
        "name": artist.name,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "genres": artist.genres,
        "image_link": artist.image_link,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": old_shows,
        "upcoming_shows": new_shows,
        "past_shows_count": len(old_shows),
        "upcoming_shows_count": len(new_shows)
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    if artist:
        return render_template('forms/edit_artist.html', form=form, artist=artist)
    else:
        return not_found_error(True)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    # artist = Artist.query.get(artist_id)
    edit_artist(artist_id)
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form.get("name")
        artist.genres = request.form.getlist("genres")
        artist.city = request.form.get("city")
        artist.state = request.form.get("state")
        artist.phone = request.form.get("phone")
        artist.website = request.form.get("website")
        artist.facebook_link = request.form.get("facebook_link")
        artist.seeking_venue = True if "seeking_venue" in request.form else False
        artist.seeking_description = request.form.get("seeking_description")
        artist.image_link = request.form.get("image_link")
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    if venue:
        return render_template('forms/edit_venue.html', form=form, venue=venue)
    else:
        not_found_error(True)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    edit_venue(venue_id)
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form.get("name")
        venue.genres = request.form.getlist("genres")
        venue.city = request.form.get("city")
        venue.state = request.form.get("state")
        venue.phone = request.form.get("phone")
        venue.website = request.form.get("website")
        venue.facebook_link = request.form.get("facebook_link")
        venue.seeking_talent = True if "seeking_talent" in request.form else False
        venue.seeking_description = request.form.get("seeking_description")
        venue.image_link = request.form.get("image_link")
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    error = False
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        phone = request.form.get('phone')
        genres = request.form.getlist('genres')
        image_link = request.form.get('image_link')
        website = request.form.get('website')
        facebook_link = request.form.get('facebook_link')
        seeking_venue = True if "seeking_venue" in request.form else False
        seeking_description = request.form.get('seeking_description')
        artist = Artist(name=name, city=city, state=state, phone=phone,
                        genres=genres, image_link=image_link,website=website,
                        facebook_link=facebook_link,
                        seeking_venue=seeking_venue, seeking_description=seeking_description)
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        # unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    finally:
        db.session.close()
    if error:
        flash('Artist ' + request.form['name'] + ' could not be listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    data = []
    shows = Show.query.join(Artist).join(Venue).all()
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
    # called to create new shows in the db, upon submitting new show listing form
        artist_id = request.form.get('artist_id')
        venue_id = request.form.get('venue_id')
        start_time = request.form.get('start_time')
        show = Show(artist_id=artist_id,
                    venue_id=venue_id,
                    start_time=start_time)
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        # unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show could not be listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


def myPrint(what):
    print(what, file=sys.stderr)
# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
