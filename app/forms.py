from flask.ext.wtf import Form                                                                                                                                                
from wtforms import StringField, FloatField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class PoemForm(Form):
    seed_words = StringField('seed_words', validators=[DataRequired()], default="cat")  
    generations = IntegerField('generations', validators=[DataRequired(), NumberRange(min=2, max=6, message="Must be between 2 and 6 inclusive")], default=2)
    mutation_probability = FloatField('m_probability', validators=[DataRequired(), NumberRange(min=0.0, max=1.0, message="Must be between 0.0 and 1.0 inclusive")], default=0.05)
    breeding_fraction = FloatField('b_fraction', validators=[DataRequired(), NumberRange(min=0.05, max=1.0, message="Must be between 0.05 and 1.0 inclusive")], default=0.25)
    starting_population_size = IntegerField('sp_size', validators=[DataRequired(), NumberRange(min=10, max=1000, message="Must be between 10 and 1000 inclusive")], default=20)
    lines = IntegerField('lines', validators=[DataRequired(), NumberRange(min=2, max=8, message="Must be between 2 and 8 inclusive")], default=6)
    phonetic_similarity_weight = FloatField('ps_weight', validators=[DataRequired()], default=1)
