from datetime import datetime
import os
from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.format import pronounce_number, nice_date, nice_number
from mycroft.util.log import LOG

import tmdbv3api

__author__ = "builderjer@github.com"
__version__ = "0.2.0"
__api__= "6b064259b900f7d4fd32f3c74ac35207"

LOGGER = LOG(__name__)

TMDB = tmdbv3api.TMDb()
MOVIE = tmdbv3api.Movie()

class MovieMaster(MycroftSkill):
	def __init__(self):
		"""A Mycroft skill to access the free TMDb api from https://www.themoviedb.org/"""
		super(MovieMaster, self).__init__(name="MovieMaster")
		self._api = None
		self._searchDepth = None
	
	def initialize(self):
		""" This sets some variables that do not change during the execution of the script"""
		
		# Try and get the settings from https://account.mycroft.ai/skills
		api = self.settings.get("apiv3")
		if api == "Default" or api == "":
			TMDB.api_key = __api__
		else:
			try:
				TMDB.api_key = api
				# Do a quick search to verify the api_key
				p = MOVIE.popular()
			except Exception:
				self.speak_dialog("no.valid.api", {})
				self.speak("Falling back to the default A P I")
				TMDB.api_key = __api__
			
		# Get search depth
		self.searchDepth = self.settings.get("searchDepth")
		
		# Set the language from the default in settings
		TMDB.language = self.lang
			
		self.settings.set_changed_callback(self.on_web_settings_change)
		
	def on_web_settings_change(self):
		api = self.settings.get("apiv3")
		if api == "Default" or api == "":
			TMDB.api_key = __api__
		else:
			try:
				TMDB.api_key = api
				# Do a quick search to verify the api_key
				p = MOVIE.popular()
			except Exception:
				self.speak_dialog("no.valid.api", {})
				self.speak("Falling back to the default A P I")
			
		# Get search depth
		self.searchDepth = self.settings.get("searchDepth")
			
	@property
	def api(self):
		return self._api

	@api.setter
	def api(self, apiNum):
		self._api = apiNum
	
	@property
	def searchDepth(self):
		return self._searchDepth
	
	@searchDepth.setter
	def searchDepth(self, depth):
		self._searchDepth = depth
		
	@intent_file_handler("movie.description.intent")
	def handle_movie_description(self, message):
		""" Gets the long version of the requested movie.
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			if movieDetails.overview is not "":
				self.speak_dialog("movie.description", {"movie": movie})
				for sentence in movieDetails.overview.split(". "):
					self.speak(sentence)
			else:
				self.speak_dialog("no.info", {"movie": movie})
				
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})
		
	@intent_file_handler("movie.information.intent")
	def handle_movie_information(self, message):
		""" Gets the short version and adds the TagLine for good measure.
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			self.speak_dialog("movie.info.response", {"movie": movieDetails.title, "year": nice_date(datetime.strptime(movieDetails.release_date.replace("-", " "), "%Y %m %d")), "budget": nice_number(movieDetails.budget)})
			self.speak(movieDetails.tagline)
				
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})
	
	@intent_file_handler("movie.year.intent")
	def handle_movie_year(self, message):
		""" Gets the year the movie was released.
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			self.speak_dialog("movie.year", {"movie": movieDetails.title, "year": nice_date(datetime.strptime(movieDetails.release_date.replace("-", " "), "%Y %m %d"))})
				
		## If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})
		
	@intent_file_handler("movie.cast.intent")
	def handle_movie_cast(self, message):
		""" Gets the cast of the requested movie.
		
		The search_depth setting is avaliable at home.mycroft.ai
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			cast = movieDetails.casts["cast"][:self.searchDepth]
			
			# Create a list to store the cast to be included in the dialog
			actorList = ""
			# Get the last actor in the list so that the dialog can say it properly
			lastInList = cast.pop()
			lastActor = " {} as {}".format(lastInList["name"], lastInList["character"])
			# Format the rest of the list for the dialog
			for person in cast:
				actor = " {} as {},".format(person["name"], person["character"])
				# Add the formated sentence to the actor list
				actorList = actorList + actor
			self.speak_dialog("movie.cast", {"movie": movie, "actorlist": actorList, "lastactor": lastActor})
				
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})

	@intent_file_handler("movie.production.intent")
	def handle_movie_production(self, message):
		""" Gets the production companies that made the movie.
		
		The search_depth setting is avaliable at home.mycroft.ai
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			companyList = movieDetails.production_companies[:self.searchDepth]
			
			# If there is only one production company, say the dialog differently
			if len(companyList) == 1:
				self.speak_dialog("movie.production.single", {"movie": movie, "company": companyList[0]["name"]})
			# If there is more, get the last in the list and set up the dialog
			if len(companyList) > 1:
				companies = ""
				lastCompany = companyList.pop()["name"]
				for company in companyList:
					companies = companies + company["name"] + ", "
				self.speak_dialog("movie.production.multiple", {"companies": companies, "movie": movie, "lastcompany": lastCompany})
				
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})

	@intent_file_handler("movie.genres.intent")
	def handle_movie_genre(self, message):
		""" Gets the genres the movie belongs to.
		
		The search_depth setting is avaliable at home.mycroft.ai
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			genreList = movieDetails.genres[:self.searchDepth]
			# Set up dialog AGAIN just like above.  Is there a better way?
			if len(genreList) == 1:
				self.speak_dialog("movie.genre.single", {"movie": movie, "genre": genreList[0]["name"]})
			if len(genreList) > 1:
				genreDialog = ""
				lastGenre = genreList.pop()["name"]
				for genre in genreList:
					genreDialog = genreDialog + genre["name"] + ", "
				self.speak_dialog("movie.genre.multiple", {"genrelist": genreDialog, "genrelistlast": lastGenre})
				
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})

	@intent_file_handler("movie.runtime.intent")
	def handle_movie_length(self, message):
		""" Gets the runtime of the searched movie.
		"""
		movie = message.data.get("movie")
		try:
			movieDetails = MOVIE.details(MOVIE.search(movie)[:1][0].id)
			self.speak_dialog("movie.runtime", {"movie": movie, "runtime": movieDetails.runtime})
				
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie})
	
	@intent_file_handler("movie.recommendations.intent")
	def handle_movie_recommendations(self, message):
		""" Gets the top movies that are similar to the suggested movie.
		"""
		try:
			movie = message.data.get("movie")
			# Create a list to store the dialog
			movieDialog = ""
			movieRecommendations = MOVIE.recommendations(MOVIE.search(movie)[:1][0].id)[:self.searchDepth]
			# Get the last movie
			lastMovie = movieRecommendations.pop()
			for film in movieRecommendations:
				if movieDialog == "":
					movieDialog = film.title
				else:
					movieDialog = movieDialog + ", " + film.title
			movieDialog = movieDialog + " and {}".format(lastMovie.title)
			self.speak_dialog("movie.recommendations", {"movielist": movieDialog, "movie": movie})
			
		# If the title can not be found, it creates an IndexError
		except IndexError:
			self.speak_dialog("no.info", {"movie": movie.title})
			
	@intent_file_handler("movie.popular.intent")
	def handle_popular_movies(self, message):
		""" Gets the daily popular movies.
		
		The list changes daily, and are not just recent movies.
		
		The search_depth setting is avaliable at home.mycroft.ai
		"""
		try:
			popularMovies = MOVIE.popular()[:self.searchDepth]
			# Lets see...I think we will set up the dialog again.
			lastMovie = popularMovies.pop()
			popularDialog = ""
			for movie in popularMovies:
				if popularDialog == "":
					popularDialog = movie.title
				else:
					popularDialog = popularDialog + ", " + movie.title
			popularDialog = popularDialog + " and {}".format(lastMovie.title)
			self.speak_dialog("movie.popular", {"popularlist": popularDialog})
		except:
			# Keep this for future use
			pass

	@intent_file_handler("movie.top.intent")
	def handle_top_movies(self, message):
		""" Gets the top rated movies of the day.
		The list changes daily, and are not just recent movies.
		
		The search_depth setting is avaliable at home.mycroft.ai
		"""
		try:
			topMovies = MOVIE.top_rated()[:self.searchDepth]
			# Set up the dialog
			lastMovie = topMovies.pop()
			topDialog = ""
			for movie in topMovies:
				if topDialog == "":
					topDialog = movie.title
				else:
					topDialog = topDialog + ", {}".format(movie.title)
			topDialog = topDialog + " and {}".format(lastMovie.title)
			self.speak_dialog("movie.top", {"toplist": topDialog})
		except:
			# Keep this here for future use
			pass
		
def create_skill():
	return MovieMaster()
