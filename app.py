#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql import func

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')


db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True, cascade="all,delete")

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True, cascade="all,delete")

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
  start_time = db.Column(db.DateTime)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # display all venues
  num_upcoming_shows = db.session.query(Venue).join(Show).filter(Show.start_time > func.now()).with_entities(Venue.id, Venue.name, Show.start_time)
  num_upcoming_shows_dict = dict()
  for row in num_upcoming_shows:
    if row.id in num_upcoming_shows_dict:
      num_upcoming_shows_dict[row.id] = num_upcoming_shows_dict[row.id] + 1
    else:
      num_upcoming_shows_dict[row.id] = 1

  result = db.session.query(Venue).with_entities(Venue.id, Venue.name, Venue.city, Venue.state)
  result_dict = dict()
  for row in result:
    if((row.city, row.state) not in result_dict):
      result_dict[(row.city, row.state)] = []
      result_dict[(row.city, row.state)].append({"id" :row.id, "name" : row.name, "num_upcoming_shows" : num_upcoming_shows_dict.get(row.id, 0)})
    else:
      result_dict[(row.city, row.state)].append({"id" :row.id, "name" : row.name, "num_upcoming_shows" : num_upcoming_shows_dict.get(row.id, 0)})
  
  data = []
  for key in result_dict:
    city_state_dict = {}
    city_state_dict["city"] = key[0]
    city_state_dict["state"] = key[1]
    city_state_dict["venues"] = result_dict[key]
    data.append(city_state_dict)
  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # search for venues using partial string matching and is case-insensitive
  # example - search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  name = request.form.get('search_term', '')
  num_upcoming_shows = db.session.query(Venue).join(Show).filter(Show.start_time > func.now()).with_entities(Venue.id, Venue.name, Show.start_time)
  
  num_upcoming_shows_dict = dict()
  for row in num_upcoming_shows:
    if row.id in num_upcoming_shows_dict:
      num_upcoming_shows_dict[row.id] = num_upcoming_shows_dict[row.id] + 1
    else:
      num_upcoming_shows_dict[row.id] = 1
  print(num_upcoming_shows_dict)
  
  result = db.session.query(Venue).filter(Venue.name.ilike("%" + name + "%")).with_entities(Venue.id, Venue.name)
  data = []
  for row in result:
    single_data = {}
    single_data["id"] = row.id
    single_data["name"] = row.name
    single_data["num_upcoming_shows_dict"] = num_upcoming_shows_dict.get(id, 0)
    data.append(single_data)
  response = {}
  response["count"] = len(data)
  response["data"] = (data) 

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  result = db.session.query(Venue).filter_by(id = venue_id).all()
  print(type(result), len(result))
  if(len(result) == 0):
    return not_found_error("Venue does not exist")
  print(result[0].genres)
  data = dict()
  data["id"] = result[0].id
  data["name"] = result[0].name
  data["genres"] = result[0].genres
  data["address"] = result[0].address
  data["city"] = result[0].city
  data["state"] = result[0].state
  data["phone"] = result[0].phone
  data["website"] = result[0].website
  data["facebook_link"] = result[0].facebook_link
  data["seeking_talent"] = result[0].seeking_talent
  data["seeking_description"] = result[0].seeking_description
  data["image_link"] = result[0].image_link

  upcoming_shows = db.session.query(Artist).join(Show).filter(Show.venue_id == venue_id, Show.start_time > func.now()).with_entities(Artist.id, Artist.name, Artist.image_link, Show.start_time)
  
  upcoming_shows_list = []
  for row in upcoming_shows:
    upcoming_shows_dict = dict()
    upcoming_shows_dict["artist_id"] = row.id
    upcoming_shows_dict["artist_name"] = row.name
    upcoming_shows_dict["artist_image_link"] = row.image_link
    upcoming_shows_dict["start_time"] = format_datetime(str(row.start_time))
    upcoming_shows_list.append(upcoming_shows_dict)

  data["upcoming_shows"] = upcoming_shows_list
  data["upcoming_shows_count"] = len(upcoming_shows_list)

  past_shows = db.session.query(Artist).join(Show).filter(Show.venue_id == venue_id, Show.start_time < func.now()).with_entities(Artist.id, Artist.name, Artist.image_link, Show.start_time)
  
  past_shows_list = []
  for row in past_shows:
    past_shows_dict = dict()
    past_shows_dict["artist_id"] = row.id
    past_shows_dict["artist_name"] = row.name
    past_shows_dict["artist_image_link"] = row.image_link
    past_shows_dict["start_time"] = format_datetime(str(row.start_time))
    past_shows_list.append(past_shows_dict)

  data["past_shows"] = past_shows_list
  data["past_shows_count"] = len(past_shows_list)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # create new venue	
  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  address = request.form['address']
  phone = request.form['phone']
  image_link = request.form['image_link']
  genres = request.form.getlist('genres')
  website = request.form['website']
  facebook_link = request.form['facebook_link']
  seeking_talent = request.form['seeking_talent']
  if seeking_talent == 'Yes':
    seeking_description = request.form['seeking_description']
    seeking_talent = True
  else:
    seeking_description = ''
    seeking_talent = False
  try:
    venue = Venue(name = name, city = city, state = state, address = address, phone = phone,  \
      genres = genres, image_link = image_link, facebook_link = facebook_link, \
        seeking_talent = seeking_talent, seeking_description = seeking_description, website = website)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('Venue ' + request.form['name'] + ' could not be listed!')  
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # delete a record based on venue id
  success = True
  try:
    Venue.query.filter_by(id = venue_id).delete()
    db.session.commit()
  except:
    success = False
    db.session.rollback()
  finally:
    db.session.close()
  if success:
    return jsonify({ 'success': True })
  else:
    return jsonify({ 'success': False })
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # retrive all artists 	
  result = db.session.query(Artist).with_entities(Artist.id, Artist.name)
  data = []
  
  for row in result:
    result_dict = dict()
    result_dict["id"] = row.id
    result_dict["name"] = row.name
    data.append(result_dict)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # search for artists using partial string matching and is case-insensitive 	
  # example seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  name = request.form.get('search_term', '')
  num_upcoming_shows = db.session.query(Artist).join(Show).filter(Show.start_time > func.now()).with_entities(Artist.id, Artist.name, Show.start_time)
  
  num_upcoming_shows_dict = dict()
  for row in num_upcoming_shows:
    if row.id in num_upcoming_shows_dict:
      num_upcoming_shows_dict[row.id] = num_upcoming_shows_dict[row.id] + 1
    else:
      num_upcoming_shows_dict[row.id] = 1
  
  result = db.session.query(Artist).filter(Artist.name.ilike("%" + name + "%")).with_entities(Artist.id, Artist.name)
  data = []
  for row in result:
    single_data = {}
    single_data["id"] = row.id
    single_data["name"] = row.name
    single_data["num_upcoming_shows"] = num_upcoming_shows_dict.get(id, 0)
    data.append(single_data)
  response = {}
  response["count"] = len(data)
  response["data"] = (data) 

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  result = db.session.query(Artist).filter_by(id = artist_id).all()
  if(len(result) == 0):
    return not_found_error("Artist does not exist")
  
  data = dict()
  data["id"] = result[0].id
  data["name"] = result[0].name
  data["genres"] = result[0].genres
  data["city"] = result[0].city
  data["state"] = result[0].state
  data["phone"] = result[0].phone
  data["website"] = result[0].website
  data["facebook_link"] = result[0].facebook_link
  data["seeking_venue"] = result[0].seeking_venue
  data["seeking_description"] = result[0].seeking_description
  data["image_link"] = result[0].image_link
  
  print(data["genres"])
  upcoming_shows = db.session.query(Venue).join(Show).filter(Show.artist_id == artist_id, Show.start_time > func.now()).with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time)
  
  upcoming_shows_list = []
  for row in upcoming_shows:
    upcoming_shows_dict = dict()
    upcoming_shows_dict["venue_id"] = row.id
    upcoming_shows_dict["venue_name"] = row.name
    upcoming_shows_dict["venue_image_link"] = row.image_link
    upcoming_shows_dict["start_time"] = format_datetime(str(row.start_time))
    upcoming_shows_list.append(upcoming_shows_dict)

  data["upcoming_shows"] = upcoming_shows_list
  data["upcoming_shows_count"] = len(upcoming_shows_list)

  past_shows = db.session.query(Venue).join(Show).filter(Show.artist_id == artist_id, Show.start_time < func.now()).with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time)
  
  past_shows_list = []
  for row in past_shows:
    past_shows_dict = dict()
    past_shows_dict["venue_id"] = row.id
    past_shows_dict["venue_name"] = row.name
    past_shows_dict["venue_image_link"] = row.image_link
    past_shows_dict["start_time"] = format_datetime(str(row.start_time))
    past_shows_list.append(past_shows_dict)

  data["past_shows"] = past_shows_list
  data["past_shows_count"] = len(past_shows_list)
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # update artists based on artist id	
  artist_obj = Artist.query.get(artist_id)
  if artist_obj is None:
    return not_found_error("Artist does not exist")
    
  form = ArtistForm()
  artist={
    "id": artist_obj.id,
    "name": artist_obj.name,
    "genres": artist_obj.genres,
    "city": artist_obj.city,
    "state": artist_obj.state,
    "phone": artist_obj.phone,
    "website": artist_obj.website,
    "facebook_link": artist_obj.facebook_link,
    "seeking_venue": artist_obj.seeking_venue,
    "seeking_description": artist_obj.seeking_description,
    "image_link": artist_obj.image_link
  }

  form.name.default = artist["name"]
  form.genres.default = artist["genres"]
  form.city.default = artist["city"]
  form.state.default = artist["state"]
  form.phone.default = artist["phone"]
  form.website.default = artist["website"]
  form.facebook_link.default = artist["facebook_link"]
  if artist["seeking_venue"] == True:
    form.seeking_venue.default = "Yes"
  else:  
    form.seeking_venue.default = "No"
    form.seeking_description.render_kw = {'disabled': 'disabled'}
  form.seeking_description.default = artist["seeking_description"]
  form.image_link.default = artist["image_link"]
  
  form.process()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # update artist with artist id 
  artist_obj = Artist.query.get(artist_id)
  if artist_obj is None:
    return not_found_error("Artist does not exist")

  artist_obj.name = request.form['name']
  artist_obj.city = request.form['city']
  artist_obj.state = request.form['state']
  artist_obj.phone = request.form['phone']
  artist_obj.image_link = request.form['image_link']
  artist_obj.genres = request.form.getlist('genres')
  artist_obj.website = request.form['website']
  artist_obj.facebook_link = request.form['facebook_link']
  artist_obj.seeking_venue = request.form['seeking_venue']
  if artist_obj.seeking_venue == 'Yes':
    artist_obj.seeking_venue = True
    artist_obj.seeking_description = request.form['seeking_description']
  else:
    artist_obj.seeking_venue = False
    artist_obj.seeking_description = ''
  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue_obj = Venue.query.get(venue_id)
  if venue_obj is None:
    return not_found_error("Venue does not exist")
  form = VenueForm()

  venue={
    "id": venue_obj.id,
    "name": venue_obj.name,
    "genres": venue_obj.genres,
    "address": venue_obj.address,
    "city": venue_obj.city,
    "state": venue_obj.state,
    "phone": venue_obj.phone,
    "website": venue_obj.website,
    "facebook_link": venue_obj.facebook_link,
    "seeking_talent": venue_obj.seeking_talent,
    "seeking_description": venue_obj.seeking_description,
    "image_link": venue_obj.image_link
  }
  
  form.name.default = venue["name"]
  form.genres.default = venue["genres"]
  form.city.default = venue["city"]
  form.address.default = venue["address"]
  form.state.default = venue["state"]
  form.phone.default = venue["phone"]
  form.website.default = venue["website"]
  form.facebook_link.default = venue["facebook_link"]
  if venue["seeking_talent"] == True:
    form.seeking_talent.default = "Yes"
  else:  
    form.seeking_talent.default = "No"
    form.seeking_description.render_kw = {'disabled': 'disabled'}
  form.seeking_description.default = venue["seeking_description"]
  form.image_link.default = venue["image_link"]
  
  form.process()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue_obj = Venue.query.get(venue_id)
  if venue_obj is None:
    return not_found_error("Venue does not exist")

  venue_obj.name = request.form['name']
  venue_obj.city = request.form['city']
  venue_obj.state = request.form['state']
  venue_obj.address = request.form['address']
  venue_obj.phone = request.form['phone']
  venue_obj.image_link = request.form['image_link']
  venue_obj.genres = request.form.getlist('genres')
  venue_obj.website = request.form['website']
  venue_obj.facebook_link = request.form['facebook_link']
  venue_obj.seeking_talent = request.form['seeking_talent']
  if venue_obj.seeking_talent == 'Yes':
    venue_obj.seeking_talent = True
    venue_obj.seeking_description = request.form['seeking_description']
  else:
    venue_obj.seeking_talent = False
    venue_obj.seeking_description = ''
  db.session.commit()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # create new artist	
  name = request.form['name']
  city = request.form['city']
  state = request.form['state']
  phone = request.form['phone']
  image_link = request.form['image_link']
  genres = request.form.getlist('genres')
  website = request.form['website']
  facebook_link = request.form['facebook_link']
  seeking_venue = request.form['seeking_venue']
  if seeking_venue == 'Yes':
    seeking_description = request.form['seeking_description']
    seeking_venue = True
  else:
    seeking_description = ''
    seeking_venue = False

  try:
    artist = Artist(name = name, city = city, state = state, phone = phone,  \
      genres = genres, image_link = image_link, facebook_link = facebook_link, \
        seeking_venue = seeking_venue, seeking_description = seeking_description, website = website)
    db.session.add(artist)
    db.session.commit()
    flash('artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    flash('artist ' + request.form['name'] + ' could not be listed!')  
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  # delete artist based on id	
  success = True
  print(artist_id)
  try:
    Artist.query.filter_by(id = artist_id).delete()
    db.session.commit()
  except Exception as e:
    print(e)
    success = False
    db.session.rollback()
  finally:
    db.session.close()
  if success:
    return jsonify({ 'success': True })
  else:
    return jsonify({ 'success': False })

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # retrive all shows	
  result = db.session.query(Show).join(Artist).join(Venue).with_entities(Venue.id.label("venue_id"), \
     Venue.name.label("venue_name"), Artist.id.label("artist_id"), Artist.name.label("artist_name"),  \
       Artist.image_link, Show.start_time)
  data = []
  for row in result:
    data_dict = dict()
    data_dict["venue_id"] = row.venue_id
    data_dict["venue_name"] = row.venue_name
    data_dict["artist_id"] = row.artist_id
    data_dict["artist_name"] = row.artist_name
    data_dict["artist_image_link"] = row.image_link
    data_dict["start_time"] = str(row.start_time)
    data.append(data_dict)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # Add new show	
  artist_id = request.form['artist_id']
  venue_id = request.form['venue_id']
  start_time = request.form['start_time']
  try:
    show = Show(venue_id = venue_id, artist_id = artist_id, start_time = start_time)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e: 
    print(e)
    flash('Show could not be listed check whether Artist id and Venue id is correct!')  
  finally:
    db.session.close()
  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


#----------------------------------------------------------------------------#
# Error handler.
#----------------------------------------------------------------------------#
if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
