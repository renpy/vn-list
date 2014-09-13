#from flask.ext.wtf import Form, StringField, BooleanField, PasswordField, RadioField, FileField, SubmitField, TextAreaField, SelectMultipleField, HiddenField, DateField, Required, Length, Email, ValidationError, URL, Optional, widgets

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, RadioField, FileField, SubmitField, TextAreaField, SelectMultipleField, HiddenField, DateField, widgets
from wtforms.validators import Required, Length, Email, ValidationError, URL, Optional

import re
from models import Game, AgeRating, CategoryGroup, Engine, Platform




#class MyTextInput(TextInput):
#    def __init__(self, error_class=u'has_errors'):
#        super(MyTextInput, self).__init__()
#        self.error_class = error_class
#    def __call__(self, field, **kwargs):
#        if field.errors:
#            c = kwargs.pop('class', '') or kwargs.pop('class_', '')
#            kwargs['class'] = u'%s %s' % (self.error_class, c)
#        return super(MyTextInput, self).__call__(field, **kwargs)

class LoginFormOid(Form):
    openid = StringField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)

class LoginForm(Form):
    username = StringField('username', validators = [Required()])
    password = PasswordField('Password', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)

class SignupForm(Form):
    username = StringField('username', validators = [Required()])
    password = PasswordField('password', validators = [Required()])
    email = StringField('email')
    
class PassResetForm(Form):
    email = StringField('email', validators = [Required()])
    
class NewPasswordForm(Form):
    password = PasswordField('password', validators = [Required()])

class AdminGameApproveForm(Form):
    approved = RadioField('Approved on', choices=[("0", "Rejected"), ("1", "Ren'Ai Archive"), ("2", "Ren'Py Games List"), ("3", "Both"), ])
    
class UploadForm(Form):
    uploaded_file = FileField(u'File')
    description = StringField(u'Description')
    edit = HiddenField(u'Edit')
    
#class UploadFormEdit(UploadForm):
#    edit = HiddenField(u'Edit')
    
class AccountForm(Form):
    username = StringField(u'Username')
    email = StringField(u'Email')
    submit_basic = SubmitField(u'Save Settings', validators = [Required()])
    
class ChangePasswordForm(Form):
    password = PasswordField('Current Password', validators = [Required()])
    newpassword = PasswordField('New Password', validators = [Required()])
    submit_pass = SubmitField(u'Change Password', validators = [Required()])

def valid_short_name(form, field):
    word = field.data
    if not re.match(r'^[a-z0-9/-]+$', word):
        raise ValidationError('Lower-case letters, numbers and dashes only.')    
    if not (Game.query.filter(Game.slug==word).first() == None):
        raise ValidationError('A game with short name "'+field.data+'" already exists.')

def valid_game_name(form, field):
    if not (Game.query.filter(Game.game_title==field.data).first() == None):
        raise ValidationError('A game with a title "'+field.data+'" already exists.')

def playtime_or_words(form, field):
#    if (not playtime.data) and (not words.data):
#        raise ValidationError('Enter either "' + words.label + '" or "' + playtime.label + '"')
    pass

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class ReleaseFormBase(Form):
    release_date  = DateField('Release Date', format='%m/%d/%Y', validators = [Required(u'Enter month, day and year separated with / (MM/DD/YYYY).')], description=u'The date when this release occured.')
    release_version = StringField(u'Release Version', default="1.0", validators = [Required()], description=u'The version of the game. If no more specific version is given, use 1.0 for the first release.')

    engine_id = RadioField(u'Engine', validators = [Required()], choices=[(engine.id, engine.name) for engine in Engine.query], coerce=int, default="1", description=u'The engine that was used to create this release.')

    platforms = MultiCheckboxField(u'Platforms', validators = [Required(u'Select at least one platform.')], choices=[(platform.id, platform.platform_name) for platform in Platform.query], coerce=int, description=u'Select the platforms this release is supported on.', default=[1,2,3])

    engine_version = StringField(u'Engine Version', description=u'The version of the engine that was used to create this game. Leave blank if unknown.')
    
class ReleaseForm(ReleaseFormBase):
    release_description = TextAreaField(u'Release Description', default="", description=u'An optional description of this release.')

    #ReleaseForm
class GameFormBase(Form):
    homepage_link_url = StringField(u'Home Page', validators = [Optional(), URL(require_tld=True, message="Invalid URL.")], description=u"A link to the game's home page. This should not be games.renpy.org - you need a website where people can get the game from.", default="")
    creator = StringField(u'Developer', validators = [Required()], description=u"The name of the person or group/studio that made this game.", default="")
    creator_type = RadioField(u'Creator Type', validators = [Required()], choices=[('person', 'Person'), ('group', 'Group')], default="group")
    description_ = TextAreaField(u'Description', validators = [Required()], description=u"A description of this game.")
    #age_ratings = [('1', 'All'), ('2', '13+'), ('3', '16+'), ('4', '18+')]
    description = r'All: All ages, no sexual content<br />13+: perhaps some sexual themes, no nudity<br />16+: Nonexplicit nudity, off-camera sex<br />18+: adult, anything goes'
    description='<dl class="dl-horizontal">'
    for age in AgeRating.query:
        description += '<dt>%(age)s</dt><dd>%(desc)s</dd>' % {'age': age.name, 'desc': age.description}
    description += '</dl>'
    age_rating_id = RadioField(u'Age Rating', validators = [Required()], choices=[(age.id, age.name) for age in AgeRating.query], coerce=int, default=1, description=description)
    groups=[(group.categories1) for group in CategoryGroup.query]
    cat_choices=[]
    for group in groups:
        for cat in group:
            cat_choices.append((cat.id, cat.name))
    categories = MultiCheckboxField(u'Categories', validators = [Required(u'Select at least one category.')], choices=cat_choices, coerce=int, description=u'Select all the categories this games should be classified in')
    words = StringField(u'Number of Words', validators = [playtime_or_words], description=u"The number of words in the game.", default="")
    playtime = StringField(u'Playtime', validators = [playtime_or_words], description=u"Leave this blank if the number of words in the game is known.", default="")
    playtime_unit = RadioField(u'playtime_unit', validators = [Required()], choices=[('minutes', 'Minutes'), ('hours', 'Hours')], default='minutes', description='')

class GameForm(GameFormBase, ReleaseForm):    
    game_title = StringField(u'Title', validators = [Required(), valid_game_name], description=u"The game's title.", default="")
    slug = StringField(u'Short Title', validators = [Required(), valid_short_name],
        description=u'A short name for the game, used in URLs. This should be made up of lower-case letters, numbers and dashes (-) only.', default="")
    release_description = HiddenField(u'Release Description', default="", description=u'An optional description of this release.')
    listed_on = BooleanField(u'List on renai.us', description=u"Check this to list this game on renai.us. To be listed, the game must have been created in English, must be a visual novel or dating sim, and must be free for us to re-distribute.", default=False)
    
class GameFormEdit(GameFormBase):    
    game_title = StringField(u'Title', validators = [Required()], description=u"The game's title.", default="")