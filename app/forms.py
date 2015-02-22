from flask.ext.wtf import Form                                                                                                                                                
from wtforms import StringField, FloatField, IntegerField
from wtforms.validators import DataRequired 

class PoemForm(Form):
    seed_words = StringField('seed_words', validators=[DataRequired()], default="cat")  
    generations = IntegerField('generations', validators=[DataRequired()], default=4)
    mutation_probability = FloatField('m_probability', validators=[DataRequired()], default=0.05)
    breeding_fraction = FloatField('b_fraction', validators=[DataRequired()], default=0.25)
    starting_population_size = IntegerField('sp_size', validators=[DataRequired()], default=50)
    lines = IntegerField('lines', validators=[DataRequired()], default=6)
    phonetic_similarity_weight = FloatField('ps_weight', validators=[DataRequired()], default=1)
