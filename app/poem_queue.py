
from app import poem_generator
import thread

MAX_CONCURRENT_POEMS = 2
class Poem_Queue:

    def __init__(self):
        print "Init poem queue"
        # call static method on virgil code that runs preprocessing etc. with config options 
        poem_generator.Poem_Generator.initialize('testing')
        self.queue = [];
        self.running_count = 0

    def get_position(self, poem):
        pos = 0
        for queue_poem in self.queue:
            if poem.id == queue_poem.id:
                return pos
            pos += 1
        return -1 

    def add_poem(self, poem):
        self.queue.append(poem)
        self.advance()

    def advance(self):
        while self.running_count < MAX_CONCURRENT_POEMS and len(self.queue) > 0:
            poem = self.queue.pop(0)
            self.running_count += 1
            pg = poem_generator.Poem_Generator(poem, self)
            thread.start_new_thread(pg.start_poem, (poem,))

    def start_poem(self, poem):
        pg = poem_generator.Poem_Generator(poem)
        pg.start_poem(poem)

    def end_poem(self):
        self.running_count -= 1

