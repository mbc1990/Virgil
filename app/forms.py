from flask.ext.wtf import Form                                                                                                                                                
from wtforms import StringField 
from wtforms.validators import DataRequired 

class PoemForm(Form):
    seed_words = StringField('seed_words', validators=[DataRequired()])  
