
from app import poem_generator, db
from models import Poem 
from config import ENVIRONMENT
import thread

MAX_CONCURRENT_POEMS = 1
class Poem_Queue:

    def __init__(self):
        print "Init poem queue"
        # call static method on virgil code that runs preprocessing etc. with config options 
        poem_generator.Poem_Generator.initialize()
        self.queue = [];
        self.running_count = 0
        self.running = []


    def get_position(self, poem):
        for p in self.running:
            if p.id == poem.id:
                return 0
        pos = 1
        for queue_poem in self.queue:
            if poem.id == queue_poem.id:
                return pos
            pos += 1
        return -1 

    def add_poem(self, poem):
        print "adding poem "+str(poem.id)+" with seed words: "+str(poem.seed_words.all())
        db.session.add(poem)
        db.session.commit()
        self.queue.append(poem)
        self.advance()

    def advance(self):
        while self.running_count < MAX_CONCURRENT_POEMS and len(self.queue) > 0:
            poem = self.queue.pop(0)
            print "poem: "+str(poem)
            poem = Poem.query.filter_by(id=poem.id).first()
            print "poem after: "+str(poem)
            self.running_count += 1
            self.running.append(poem)
            print "Starting poem "+str(poem.id)+" with seed words: "+str(poem.seed_words.all())
            pg = poem_generator.Poem_Generator(poem, self)

            if ENVIRONMENT == 'Development':
                thread.start_new_thread(pg.start_poem, (poem,))
            elif ENVIRONMENT == 'Production':
                # Throw away unexpected exceptions from the generator in produciton to prevent the queue from breaking 
                thread.start_new_thread(pg.start_poem_safe, (poem,))

    def end_poem(self, poem):
        print "Removing poem "+str(poem.id)+" from queue"
        self.running_count -= 1
        print self.running
        self.running = [s for s in self.running if s.id != poem.id] 
        print self.running
        self.advance()
