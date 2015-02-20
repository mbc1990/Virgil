from flask.ext.wtf import Form                                                                                                                                                
from wtforms import TextAreaField                                                                                                                  
from wtforms.validators import DataRequired 

class PoemForm(Form):
    seed_words = TextAreaField('seed_words', validators=[DataRequired()])  
