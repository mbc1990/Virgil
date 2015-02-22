from app import db, app   

class Poem(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000))

    generations = db.Column(db.Integer)
    mutation_probability = db.Column(db.Float)
    phonetic_similarity_weight = db.Column(db.Float)
    breeding_fraction = db.Column(db.Float)
    starting_population_size = db.Column(db.Integer)
    lines = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    current_generation = db.Column(db.Integer)

    seed_words = db.relationship('Seed_Word', backref='poem', lazy='dynamic')

    def __repr__(self):
        return 'Poem: %r' % (self.seed_words)

class Seed_Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poem_id = db.Column(db.Integer, db.ForeignKey('poem.id'))
    word = db.Column(db.String(30))

    def __repr__(self):
        return self.word
