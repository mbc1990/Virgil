from flask.ext.wtf import Form                                                                                                                                                
from wtforms import StringField, FloatField, IntegerField
from wtforms.validators import DataRequired 

class PoemForm(Form):
    seed_words = StringField('seed_words', validators=[DataRequired()], default="cat")  
    
    generations = IntegerField('generations', validators=[DataRequired()], default=1)
    mutation_probability = FloatField('m_probability', validators=[DataRequired()], default=1)
    phonetic_similarity_weight = FloatField('ps_weight', validators=[DataRequired()], default=1)
    breeding_fraction = FloatField('b_fraction', validators=[DataRequired()], default=1)
    starting_population_size = IntegerField('sp_size', validators=[DataRequired()], default=1)
    lines = IntegerField('lines', validators=[DataRequired()], default=1)
