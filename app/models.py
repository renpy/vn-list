from app import db
from sqlalchemy import Integer, String, Boolean, Date, Text, DateTime, SmallInteger #and_, or_, desc

ROLE_USER = 0
ROLE_ADMIN = 1
USER_STATUS_ACTIVE = 1
USER_STATUS_BANNED = 0
class UserAccount(db.Model):
    #__tablename__ = 'users_login'
    id = db.Column(Integer, primary_key=True)
    username = db.Column(db.String, index = True, unique = True)
    password = db.Column(db.String)
    email = db.Column(db.String, index = True, unique = True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    status = db.Column(db.SmallInteger, default=USER_STATUS_ACTIVE)
    password_reset_token = db.Column(db.String, unique = True)
    password_reset_expiration = db.Column(db.DateTime)
    def __init__(self, username, password, email, role=ROLE_USER, status=USER_STATUS_ACTIVE):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.status = status
    def __repr__(self):
        return "<Users('%s','%s','%s','%s','%s','%s')>" % (self.id, self.username, self.password, self.email, self.role, self.status)
    def is_authenticated(self): #This method should just return True. Used to check if the user is logged in.
        return True
    def is_active(self): #The is_active method should return True for users unless they are inactive / banned.
#TO DO: return False for banned users
        return True
    def is_anonymous(self): #The is_anonymous method should return True only for fake users that are not supposed to log in to the system.
        return False
    def get_id(self): #The get_id method should return a unique identifier for the user, in unicode format.
        return unicode(self.id)
		
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    category_group_id = db.Column(db.Integer, db.ForeignKey('category_group.id'))
    show_in_navigation = db.Column(db.Boolean)
    slug = db.Column(db.String)
	
    def __init__(self, name, category_group_id, show_in_navigation, slug):
        self.name = name
        self.category_group_id = category_group_id
        self.show_in_navigation = show_in_navigation
        self.slug = slug

    def __repr__(self):
        return "<Category('%s','%s','%s','%s','%s')>" % (self.id, self.name, self.category_group_id, self.show_in_navigation, self.slug)

class CategoryGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    show_in_navigation = db.Column(db.Boolean)
    categories_sql = db.relationship('Category', backref='category_group', lazy='dynamic')
    categories = None
    categories1 = db.relationship('Category', lazy='select')
    def __init__(self, name, show_in_navigation):
#        self.id = id
        self.name = name
        self.show_in_navigation = show_in_navigation
        #self.categories = categories
    def __repr__(self):
        return "<CategoryGroup('%s','%s','%s','%s','%s')>" % (self.id, self.name, self.show_in_navigation, self.categories, self.categories_sql)

class CategoryGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    categories = db.relationship('Category', lazy='select', uselist=False)
    def __init__(self, category_id, game_id):
        self.category_id = category_id
        self.game_id = game_id
    def __repr__(self):
        return "<Category_game('%s','%s','%s','%s')>" % (self.id, self.category_id, self.game_id, self.categories)

class Engine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return "<Engine('%s','%s')>" % (self.id, self.name)

class LinkType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_type = db.Column(db.String)
    def __init__(self, link_type):
        self.link_type = link_type
    def __repr__(self):
        return "<Link_types('%s','%s')>" % (self.id, self.link_type)

class LinkGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    name = db.Column(db.String)
    url = db.Column(db.String)
    link_type_id = db.Column(db.Integer)
	
    def __init__(self, game_id, name, url, link_type_id):
        self.game_id = game_id
        self.name = name
        self.url = url
        self.link_type_id = link_type_id
    def __repr__(self):
        return "<Link_game('%s','%s','%s','%s','%s')>" % (self.id, self.game_id, self.name, self.url, self.link_type_id) 

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String)
    def __init__(self, platform_name):
        self.platform_name = platform_name
    def __repr__(self):
        return "<Platforms('%s','%s')>" % (self.id, self.platform_name)

class PlatformRelease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'))
    platform_id = db.Column(db.Integer, db.ForeignKey('platform.id'))
    platform = db.relationship('Platform', lazy='select', uselist=False)
    def __init__(self, release_id, platform_id):
        self.release_id = release_id
        self.platform_id = platform_id
    def __repr__(self):
        return "<Platforms_releases('%s','%s','%s')>" % (self.id, self.release_id, self.platform_id) 

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    release_id = db.Column(db.Integer, db.ForeignKey('release.id'))
    size = db.Column(db.Integer)
    filename = db.Column(db.String)
    description = db.Column(db.String)
    approved  = db.Column(db.Boolean, default=False)

class Release(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    release_date = db.Column(db.Date)
    release_version = db.Column(db.String)
    engine_id = db.Column(db.Integer, db.ForeignKey('engine.id'))
    release_description = db.Column(db.Text)
    engine_version = db.Column(db.String)
    user_id = db.Column(db.Integer)
    approved  = db.Column(db.Boolean, default=False)
    engine = db.relationship('Engine', lazy='select', uselist=False)
    platforms_release_sql = db.relationship('PlatformRelease', lazy='dynamic')
    platforms = db.relationship('PlatformRelease', lazy='select')
    files = db.relationship('File', lazy='select')
    def __init__(self, game_id, release_date, release_version, engine_id, release_description, engine_version, user_id):
        self.game_id = game_id
        self.release_date = release_date
        self.release_version = release_version
        self.engine_id = engine_id
        self.release_description = release_description
        self.engine_version = engine_version
        self.user_id = user_id
    def __repr__(self):
        return "<Releases('%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.id, self.game_id, self.release_date, self.release_version, self.engine_id, self.release_description, self.engine_version, self.user_id) 
		
class Screenshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    filename = db.Column(db.String)
    caption = db.Column(db.Text)
    is_thumb = db.Column(db.Boolean)
    def __init__(self, game_id, filename, caption, is_thumb):
        self.game_id = game_id
        self.filename = filename
        self.caption = caption
        self.is_thumb = is_thumb
    def __repr__(self):
        return "<Screenshots('%s','%s','%s','%s','%s')>" % (self.id, self.game_id, self.filename, self.caption, self.is_thumb)

class AgeRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    is_adult = db.Column(db.Boolean)
    def __init__(self, name, description, is_adult):
        self.name = name
        self.description = description
        self.is_adult = is_adult
    
    
class Developer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.Integer) #group or person
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    
    group = db.relationship('Group', lazy='select', uselist=False)
    person = db.relationship('Person', lazy='select', uselist=False)
    
    def __init__(self, name, type, user_id, group_id=1, person_id=1):
        self.name = name
        self.type = type
        self.user_id = user_id
        self.group_id = group_id
        self.person_id = person_id
        
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String)
    
    def __init__(self, description):
        self.description = description

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String)
    
    def __init__(self, description):
        self.description = description

class Game(db.Model):
#    __tablename__ = 'game'
    id = db.Column(db.Integer, primary_key=True)
    game_title = db.Column(db.String)
    description = db.Column(db.Text)
    created = db.Column(db.DateTime)
    slug = db.Column(db.String)
    words = db.Column(db.Integer)
    playtime = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    age_rating_id = db.Column(db.Integer, db.ForeignKey('age_rating.id'))
    approved  = db.Column(db.Boolean, default=False)
    maker = db.Column(db.String)
    developer_id = db.Column(db.Integer, db.ForeignKey('developer.id'))
    listed_on = db.Column(db.Integer, default=0)
    words_estimate = db.Column(db.Integer)
    
    developer = db.relationship('Developer', lazy='select', uselist=False)
    
    age_rating = db.relationship('AgeRating', lazy='select', uselist=False)
    link = db.relationship('LinkGame', lazy='select', uselist=False)
    categories =  db.relationship('CategoryGame', lazy='select')
    screenshot = db.relationship('Screenshot', lazy='select', uselist=False, order_by=Screenshot.is_thumb)
    screenshots = db.relationship('Screenshot', lazy='select')
    releases = db.relationship('Release', lazy='select', order_by=Release.release_date.desc)
    release = db.relationship('Release', lazy='select', uselist=False, order_by=Release.release_date.desc)
    
    def __init__(self, game_title, slug, description, developer_id, words, words_estimate, playtime, user_id, maker, age_rating_id, listed_on, approved=False):
        self.game_title = game_title
        self.description = description
        self.developer_id = developer_id
        self.slug = slug
        self.words = words
        self.words_estimate = words_estimate
        self.playtime = playtime
        self.user_id = user_id
        self.maker = maker
        self.approved = approved
        self.listed_on = listed_on
        self.age_rating_id = age_rating_id

    def __repr__(self):
        return "<Game ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')>" % (self.id, self.game_title, self.created, self.developer_id, self.slug, self.words, self.playtime, self.user_id, self.age_rating, self.approved, self.maker, self.listed_on)