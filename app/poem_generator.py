import sys
import time
from random import randint
from random import choice
import random
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
import fuzzy
import Levenshtein as pylev
import os.path
import json
import operator
import math
from random import shuffle
from stat_parser import Parser
from models import Poem 
from app import db
from config import ENVIRONMENT
parser = Parser()

class Poem_Generator:

    ngram2following_tokens = {} # tuple of ngram -> list of tokens that follow it in the corpus (used in markov chain) 
    token2ngrams = {} # token -> ngrams it is a member of
    height_memo = {} # tuple -> parse height  

    # Load parse height cache
    @staticmethod 
    def load_parse_height_cache():
        try:
            if os.path.isfile('parse_height_cache.json'):
                with open('parse_height_cache.json', 'r') as fp:
                    height_cache_saved = json.load(fp)
                    for key in height_cache_saved['key_map'].keys():
                        tup_key = tuple(height_cache_saved['key_map'][key])
                        height_value = height_cache_saved['saved_cache'][key]
                        Poem_Generator.height_memo[tup_key] = height_value
        except: #TODO: Rewrite the parse height cache to use a database table 
            pass 

    # Save the updated height cache
    @staticmethod
    def dump_parse_height_cache():
        with open('parse_height_cache.json', 'w') as fp:
            key_map_counter = 0
            key_map = {}
            saved_cache = {}
            for key in Poem_Generator.height_memo.keys():
                key_map[key_map_counter] = key 
                saved_cache[key_map_counter] = Poem_Generator.height_memo[key]
                key_map_counter += 1
            output = {'key_map': key_map, 'saved_cache': saved_cache}
            json.dump(output, fp)

    @staticmethod
    def get_tokens():
        symbol_stopwords = ['(', ')', '&', '$', '%', '#', '@', '*', '^', '-', '+', '_', '[',']','/', '\\', '=', '|']
        if os.path.isfile('saved_tokens.json'):
            print "loading tokens"
            with open('saved_tokens.json') as toks:
                tokens = json.load(toks)
                return tokens
        else:
            corpuses = ['god_and_the_state.txt', 'domestic_animals.txt', 'treatise_of_human_nature.txt', 'heart_of_darkness.txt', 'walden.txt','the_prince.txt', 'grimm_fairy_tails.txt', 'kama_sutra.txt', 'tail_of_two_cities.txt', 'ulysses.txt', 'metamorphosis.txt', 'dorian_gray.txt', 'treasure_island.txt', 'the_republic.txt', 'the_time_machine.txt']
            print "making tokens"
            tokens = []
            corpus_counter = 1
            for c in corpuses:
                print 'corpus '+str(corpus_counter)+'/'+str(len(corpuses))
                corpus_counter += 1
                with open('../corpus/'+c) as fd:
                    content = fd.read()
                    sentences = sent_tokenize(content)
                    for s in sentences:
                        tokens.append('SENTENCE_START')
                        tokens += [word for word in word_tokenize(s) if word not in symbol_stopwords]
            with open('saved_tokens.json', 'w') as outfile:
                json.dump(tokens, outfile)
            return tokens

    @staticmethod
    def build_markov_model(tokens, n):
        for i in range(0, len(tokens) - n):
            if 'SENTENCE_START' not in tokens[i:i+n+1]:
                if tuple(tokens[i:i+n]) not in Poem_Generator.ngram2following_tokens:
                    Poem_Generator.ngram2following_tokens[tuple(tokens[i:i+n])] = []
                Poem_Generator.ngram2following_tokens[tuple(tokens[i:i+n])].append(tokens[i+n])

                # ngrams for generating starting "seeds"
                toks = tokens[i:i+n]
                for k in toks:
                    if k not in Poem_Generator.token2ngrams:
                        Poem_Generator.token2ngrams[k] = []
                    Poem_Generator.token2ngrams[k].append(toks)


    @staticmethod
    def initialize():
        print "Static generator methods initialized!"
        Poem_Generator.load_parse_height_cache()
        tokens = Poem_Generator.get_tokens()
        print("building model 1")
        Poem_Generator.build_markov_model(tokens, 1)
        print("building model 2")
        Poem_Generator.build_markov_model(tokens, 2)

    # Checks that the input seed words are in the corpus 
    @staticmethod
    def validate_input(seed_words):
        not_allowed = []
        for word in seed_words:
            if word not in Poem_Generator.token2ngrams:
                not_allowed.append(word)
        return not_allowed

   
    def __init__(self, poem, poem_queue):
        print "Poem generator init"

        self.generations = poem.generations # Number of selection-breeding processes
        self.breeding_fraction = poem.breeding_fraction # .35 # Top fraction of candidates selected to breed
        self.mutation_prob = poem.mutation_probability #.05 # Probability that a child will be mutated
        self.poem_length = poem.lines #6 # Number of lines in a poem
        self.starting_population_size = poem.starting_population_size #50 # Number of poems the algorithm begins with 
        self.phonetic_similarity_weight = poem.phonetic_similarity_weight
        self.seed_words = [w.word for w in poem.seed_words.all()] #['cat', 'winter'] # Input "idea"
        print "Generator initialized with: "+str(self.seed_words)
        self.poem_queue = poem_queue 
        

    # Generates a set of synonyms from the input words 
    def generate_outline(self):

        starting_words = self.seed_words
        print "Starting words: "+str(starting_words)

        # Get synonyms for every input word 
        expanded_outline = []
        for keyword in starting_words:
            synsets = wordnet.synsets(keyword)
            if ENVIRONMENT == 'Development':
                syn_strings = [x.name.split('.')[0] for x in synsets] # get english token from synset
            elif ENVIRONMENT == 'Production':
                syn_strings = [x.name().split('.')[0] for x in synsets] # get english token from synset
            expanded_outline += syn_strings

        print "Expanded outline: "+str(expanded_outline)

        # Clean the expanded outline 
        pruned_outline = []
        for word in expanded_outline: 
            # Deduplicate expanded outline
            # Remove anything with an underscore (two-word synonyms such as "big cat" as in big cat vs. house cat)
            # Throw out any words that aren't in the markov model 
            if word in Poem_Generator.token2ngrams and word not in pruned_outline and '_' not in word:
                pruned_outline.append(word)

        print "Pruned outline: "+str(pruned_outline)

        return pruned_outline
        

    # Generates a candidate 
    def generate_candidate_line(self, keyword, n, min_length, max_length):
        starter_ngram = choice(Poem_Generator.token2ngrams[keyword])
        line_length = randint(min_length, max_length)
        line = list(starter_ngram)
        while len(line) < line_length:
            ngram = tuple(line[-n:]) 
            # Handle sentence ending tokens with no candidates by terminating the line
            if ngram not in Poem_Generator.ngram2following_tokens:
                return line
            candidates = Poem_Generator.ngram2following_tokens[ngram]
            nextToken = choice(candidates)
            line.append(nextToken)
        return line

    # Alliteration factor - poems where more of the words start with the same two letters are considered more fit
    def alliteration(self, poem):
        total_words = 0.0
        letters = {}
        for line in poem:
            for word in line:
                # Populate letter counts for alliteration metric 
                total_words += 1
                first_letter = word[0].lower()
                if first_letter not in letters:
                    letters[first_letter] = 0
                letters[first_letter] += 1

        # Calculate alliteration value 
        letter_freqs = []
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        for letter in alphabet:
            if letter in letters:
                letter_freqs.append((letter,letters[letter]))
        letter_freqs.sort(key=operator.itemgetter(1))
        letter_freqs.reverse()
        
        # sum of two most frequent letters divided by total number of words
        return (letter_freqs[0][1]+letter_freqs[1][1])/total_words

    # Sanity checks that, if failed, deem a poem completely unfit 
    def default_unfit(self, poem):
        # A line should never start with punctuation
        punctuation = [',','.','\'', '"', '(', ')', '!', '?', ';']
        for line in poem:
            if line[0] in punctuation:
                return True 
        return False 


    # Like line_parse_height, but the sum of parse heights for each pair of adjacent lines
    # This rewards grammatical continuity across lines
    def line_pair_parse_height(self, poem):
        # Sum of parse height for each pair of lines
        total_parse_height = 0.1
        for i in range(0,len(poem)-1):
            line = poem[i]
            next_line = poem[i+1]
            line_pair = line + next_line
            # Parse height
            parse_height = 0
            if tuple(line_pair) in Poem_Generator.height_memo:
                parse_height = Poem_Generator.height_memo[tuple(line_pair)]
                Poem_Generator.height_memo[tuple(line_pair)] = parse_height
            else:
                try:
                    parse_tree = parser.parse(' '.join(line_pair))
                    parse_height = parse_tree.height()
                    Poem_Generator.height_memo[tuple(line_pair)] = parse_height
                except:
                    Poem_Generator.height_memo[tuple(line_pair)] = 0.1
                    return 0.1 # Return 0.1 if there's an error parsing a poem line
            total_parse_height += parse_height

            return total_parse_height

    def phonetic_similarity(self, poem):
        # Phonetic representation of each line
        phonetic_lines = []
        for line in poem:
            phon_line = []
            for word in line:
                phon_line.append(fuzzy.nysiis(word))
            phonetic_lines.append(phon_line)

        # Calculate phonetic value
        phon_value = 0.1
        for i in range(0, len(phonetic_lines)-1):
            last_word = str(phonetic_lines[i][-1])
            next_last_word = str(phonetic_lines[i+1][-1])

            # Throw out identical sounding words (TODO: Check their original words, not phonetic representations)
            if last_word != next_last_word and len(last_word) > 0 and len(next_last_word) > 0:
                lev_dist = pylev.distance(last_word, next_last_word)

                # Divide distance by word length since eg morning - mourning is a way better similarity than hat - had 
                lev_dist = lev_dist/float((len(last_word) + len(next_last_word)))
                phon_value += lev_dist
                #print 'Potential rhyme pair: '+last_word +' '+next_last_word+' with dist: '+str(lev_dist)
            else:
                phon_value += 1 # very unsimilar for two words that are too short

        # Normalize by poem length (in case variable length poems are allowed)
        phon_value /= len(phonetic_lines)
        return phon_value

    # 1 point crossover between two poems
    def crossover(self, p1, p2):
        
        # Maximum crossover location (shortest of the two poems)
        max_point = len(p1)
        if max_point > len(p2):
            max_point = len(p2)

        crossover_point = randint(0, max_point)
        
        child1 = p1[:crossover_point]+p2[crossover_point:]
        child2 = p2[:crossover_point]+p1[crossover_point:]
        return (child1, child2)

    # Randomly decided whether or not to mutate
    def mutate(self, poem, probability):
        rand = random.uniform(0,1)

        # randomly switch two adjacent words 
        if rand <= probability:
            line_index = random.randint(0,len(poem)-1)
            word_index = random.randint(0,len(poem[line_index])-2)
            line = poem[line_index]
            first_part = line[:word_index]
            switch = [line[word_index+1]] + [line[word_index]]
            second_part = line[word_index+2:]
            poem[line_index] = first_part + switch + second_part
        return poem


    # Fitness function for an individual poem, the higher the return value the more fit an individual is 
    def poem_fitness(self, poem):

        # Don't both computing anything if this poem has something inherently wrong with it 
        if self.default_unfit(poem):
            return -1

        alliteration_score = self.alliteration(poem)
        parse_height_score = self.line_pair_parse_height(poem)
        phonetic_similarity_score = self.phonetic_similarity(poem)
        
        #print 'Alliteration: '+str(alliteration_score)
        #print 'Parse height: '+str(parse_height_score)
        #print 'Phon similar: '+str(phonetic_similarity_score)

        score = ((alliteration_score*2)+phonetic_similarity_score)/parse_height_score
        return score

    # Returns a string with <br> line breaks 
    def poem_to_html(self, poem):
        output = ""
        for line in poem: 
            for t in line:
                if len(output) != 0 and t not in [',', '.', '!', '\n', ';','\'', ':']:
                    output += " "
                output += t
            output += '<br>'
        return output


    def start_poem_safe(self, poem):
        try:
            self.start_poem(poem)
        except Exception as e:
            print "Exception in poem generator, throwing away poem"
            print e
            self.poem_queue.end_poem(poem.id)

    def start_poem(self, poemid):
        print "DB Poem at top of start_poem: "+str(Poem.query.filter_by(id=poemid).first())
        print "start_poem called with"+str(poemid)
        # This will eventually use WordNet to turn the 1-5 word outline into 10-50 words 
        outline = self.generate_outline()
        print "outline: "+str(outline)

        # Generate starting population
        candidates = []
        for i in range(0, self.starting_population_size):
            next_poem = []
            for k in range(0, self.poem_length):
                outline_word = choice(outline)
                candidate_line = self.generate_candidate_line(outline_word, 2, 2, 10)
                next_poem.append(candidate_line)
            candidates.append(next_poem)

        generation_counter = 1
        poem = Poem.query.filter_by(id=poemid).first()
        print "Poem ID: "+str(poemid)
        print "Poem: "+str(poem)
        print "DB Poem: "+str(Poem.query.filter_by(id=poemid).first())
        while generation_counter <= self.generations:
            # Get a fitness score for each poem 
            scored_candidates = []
            counter = 0
            for candidate in candidates:
                fitness = self.poem_fitness(candidate)
                counter += 1
                if counter % 5 == 0:
                    try:
                        poem = Poem.query.filter_by(id=poemid).first()
                        poems = Poem.query.all();
                        for p in poems:
                            print "query all poem: "+str(p.id) 

                        print "Counter: "+str(counter)
                        print "Poem ID: "+str(poemid)
                        print "Poem: "+str(poem)
                        print "DB Poem: "+str(Poem.query.filter_by(id=poemid).first())
                        poem.progress = float(counter)/float(len(candidates)) * 100
                        db.session.add(poem) # Without this line, the error occurs on the db.session.add() line below
                        db.session.commit()
                        print "Poem "+str(poem.id)+": "+str(counter)+'/'+str(len(candidates))+' candidates scored in generation '+str(generation_counter)+'/'+str(self.generations)+' with '+str(len(Poem_Generator.height_memo))+' cached line parse heights'
                    except:
                        pass
                scored_candidates.append((candidate, fitness))
                
            # Sort poems by fitness 
            scored_candidates.sort(key=operator.itemgetter(1))
            scored_candidates.reverse()

            # Select the top 1/n for some n for breeding
            # TODO: Different selection methods (tournament, roulette wheel)
            parents = scored_candidates[0: int(math.ceil(len(scored_candidates) * self.breeding_fraction))]

            # Remove scores
            parents = [p[0] for p in parents] 

            poem = Poem.query.filter_by(id=poemid).first()
            # Update database
            poem.text = self.poem_to_html(parents[0]) 
            poem.progress = 100
            poem.current_generation += 1
            # With both of these lines, it crashes here and does not write to the database
            
            db.session.add(poem) # Without this line, the error occurs on the db.session.add() line below
            db.session.commit()
            print "Poem text updated to "+str(poem.text)

            # Shuffle parents
            shuffle(parents)

            # Separate the selected parents into pairs
            parent_pairs = []
            for i in range(0, len(parents)):
                if i+1 < len(parents):
                    parent_pairs.append((parents[i], parents[i+1]))
                    i += 1

            # Each parent pair should replace their proportion of the truncated population
            children = []
            num_replacements = math.ceil(1/self.breeding_fraction)
            for parent in parent_pairs:
                for k in range(0,2+int(math.ceil(num_replacements/2))): # Parents replace themselves + at least their proportion of the culled generation 
                    crossovers = self.crossover(parent[0], parent[1])
                    children.append(self.mutate(crossovers[0], self.mutation_prob))
                    children.append(self.mutate(crossovers[1], self.mutation_prob))

            # Repeat on the next generation 
            candidates = children
            generation_counter += 1

        poem = Poem.query.filter_by(id=poemid).first()
        poem.progress = 0
        db.session.add(poem)
        db.session.commit()

        # Results
        scored_candidates = []
        scored_count = 0
        for candidate in candidates:
            if scored_count % 5 == 0:
                poem = Poem.query.filter_by(id=poemid).first()
                poem.progress = float(scored_count) / float(len(candidates)) * 100
                db.session.add(poem)
                db.session.commit()
            fitness = self.poem_fitness(candidate)
            scored_candidates.append((candidate, fitness))
            scored_count += 1
            
        # Sort poems by fitness 
        scored_candidates.sort(key=operator.itemgetter(1))
        scored_candidates.reverse()
        
        # Take the fittest candidate and format it for the web app
        best_candidate = scored_candidates[0]
        html_line_breaks = self.poem_to_html(best_candidate[0])
        poem = Poem.query.filter_by(id=poemid).first()
        poem.text = html_line_breaks 
        poem.current_generation += 1
        db.session.add(poem)
        db.session.commit()

        # Tell the queue that a poem is complete
        self.poem_queue.end_poem(poem.id)

        # Save parse height cache
        self.dump_parse_height_cache()

