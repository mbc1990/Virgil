from flask.ext.wtf import Form                                                                                                                                                
from wtforms import StringField, FloatField, IntegerField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from app import poem_generator 

def is_in_corpus(form, field):
    seed_words = field.data
    seed_words = seed_words.split(',')
    print "seed words: "+str(seed_words)
    not_allowed = poem_generator.Poem_Generator.validate_input(seed_words)
    if len(not_allowed) > 0:
        msg = "The following words are not allowed: "
        for word in not_allowed:
            msg += word+", "
        raise ValidationError(msg)
        
class PoemForm(Form):
    seed_words = StringField('seed_words', validators=[DataRequired(), is_in_corpus], default="cat")  
    generations = IntegerField('generations', validators=[DataRequired(), NumberRange(min=2, max=6, message="Must be between 2 and 6 inclusive")], default=2)
    mutation_probability = FloatField('m_probability', validators=[DataRequired(), NumberRange(min=0.0, max=1.0, message="Must be between 0.0 and 1.0 inclusive")], default=0.05)
    breeding_fraction = FloatField('b_fraction', validators=[DataRequired(), NumberRange(min=0.05, max=1.0, message="Must be between 0.05 and 1.0 inclusive")], default=0.25)
    starting_population_size = IntegerField('sp_size', validators=[DataRequired(), NumberRange(min=10, max=1000, message="Must be between 10 and 1000 inclusive")], default=20)
    lines = IntegerField('lines', validators=[DataRequired(), NumberRange(min=2, max=8, message="Must be between 2 and 8 inclusive")], default=6)
    phonetic_similarity_weight = FloatField('ps_weight', validators=[DataRequired()], default=1)

