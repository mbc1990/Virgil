
import time
from random import randint
from random import choice
import random
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
import fuzzy # phonetic representation 
import Levenshtein as pylev
import bisect
import os.path
import sys
import json
import operator
import math
from random import shuffle
from stat_parser import Parser
parser = Parser()

# Generates an outline, against which the candidate poems are measured 
def generate_outline():
    #return ['winter', 'owl', 'snow', 'sadness']
    #return ['heat', 'light', 'sun', 'happy', 'cat', 'soft', 'fur', 'love', 'sunrise']
    return ['fur', 'soft', 'warm', 'snow', 'mountain', 'morning', 'sunrise', 'dense']

tmap = {}
token2ngrams = {}
def build_markov_model(tokens, n):
    global tmap
    global token2ngrams
    for i in range(0, len(tokens) - n):
        if 'SENTENCE_START' not in tokens[i:i+n+1]:
            if tuple(tokens[i:i+n]) not in tmap:
                tmap[tuple(tokens[i:i+n])] = []
            tmap[tuple(tokens[i:i+n])].append(tokens[i+n])

            # ngrams for generating starting "seeds"
            toks = tokens[i:i+n]
            for k in toks:
                if k not in token2ngrams:
                    token2ngrams[k] = []
                token2ngrams[k].append(toks)

def get_tokens():
    symbol_stopwords = ['(', ')', '&', '$', '%', '#', '@', '*', '^', '-', '+', '_', '[',']','/', '\\', '=', '|']
    if os.path.isfile('saved_tokens.json'):
        print "loading tokens"
        with open('saved_tokens.json') as toks:
            tokens = json.load(toks)
            return tokens
    else:
        print "making tokens"
        tokens = []
        for c in corpuses:
            with open(c) as fd:
                content = fd.read()
                sentences = sent_tokenize(content)
                for s in sentences:
                    tokens.append('SENTENCE_START')
                    tokens += [word for word in word_tokenize(s) if word not in symbol_stopwords]
        with open('saved_tokens.json', 'w') as outfile:
            json.dump(tokens, outfile)
        return tokens

# Generates a candidate 
def generate_candidate_line(keyword, n, min_length, max_length):
    rand = randint(0, len(token2ngrams[keyword])-1)
    starter_ngram = token2ngrams[keyword][rand]
    line_length = randint(min_length, max_length)
    line = list(starter_ngram)
    while len(line) < line_length:
        ngram = tuple(line[-n:]) 
        # Handle sentence ending tokens with no candidates by terminating the line
        if ngram not in tmap:
            return line
        candidates = tmap[ngram]
        nextToken = choice(candidates)
        line.append(nextToken)
    return line

# Fitness function for an individual poem, the higher the return value the more fit an individual is 
height_memo = {} # tuple -> parse depth
def poem_fitness(poem):
    global height_memo
    # Sum of parse depth for each pair of lines
    # Parse depth overall? Probably too slow 
    # Phonetic/levenshtein factor for positionally aligned (beginning, end) members of line 
    # Something involving wordnet? Comparison to outline? 
    
    # Alliteration factor - poems where more of the words start with the same two letters are considered more fit
    total_words = 0.0
    letters = {}

    # Sum of parse depth for each line
    total_parse_height = 0.1
    for line in poem:
        parse_height = 0
        if tuple(line) in height_memo:
            parse_height = height_memo[tuple(line)]
            height_memo[tuple(line)] = parse_height
        else:
            try:
                parse_tree = parser.parse(' '.join(line))
                parse_height = parse_tree.height()
                height_memo[tuple(line)] = parse_height
            except:
                height_memo[tuple(line)] = 0.1
                return 0.1 # Return 0 if there's an error parsing a poem line
        total_parse_height += parse_height
        
        # Populate letter counts for alliteration metric 
        for word in line:
            total_words += 1
            first_letter = word[0].lower()
            if first_letter not in letters:
                letters[first_letter] = 0
            letters[first_letter] += 1

    # Calculate alliteration value 
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    letter_freqs = []
    for letter in alphabet:
        if letter in letters:
            letter_freqs.append((letter,letters[letter]))
    letter_freqs.sort(key=operator.itemgetter(1))
    letter_freqs.reverse()

    # Just letter frequencies 
    score = (letter_freqs[0][1] + letter_freqs[1][1]) / total_words

    # High alliterative value per depth is rewarded 
    score = score/parse_height 
    print "score: "+str(score)
    return score

# Randomly decided whether or not to mutate
def mutate(poem, probability):
    rand = random.uniform(0,1)
    if rand <= probability:
        shuffle(poem) # Naive mutation, rearrange all the words in the line
    return poem
        
# 1 point crossover between two poems
def crossover(p1, p2):
    
    # Maximum crossover location (shortest of the two poems)
    max_point = len(p1)
    if max_point > len(p2):
        max_point = len(p2)

    crossover_point = randint(0, max_point)
    
    child1 = p1[:crossover_point]+p2[crossover_point:]
    child2 = p2[:crossover_point]+p1[crossover_point:]
    return (child1, child2)

def print_human_text(poem):
    outpt = "\n"
    for line in poem: 
        for t in line:
            if len(outpt) != 0 and t not in [',', '.', '!', '\n', ';','\'']:
                outpt += " "
            outpt += t
        outpt += '\n'
    print outpt

def main():
    # initialize corpus
    tokens = get_tokens()

    print("building model 1")
    build_markov_model(tokens, 1)
    print("building model 2")
    build_markov_model(tokens, 2)
    
    # This will eventually use WordNet to turn the 1-5 word outline into 10-50 words 
    outline = generate_outline()

    start_time = time.time()
    cur_poem = []
    candidates = []
    poem_length = 6 # Number of lines in a poem
    for i in range(0,1000):
        outline_word = choice(outline)
        candidate_line = generate_candidate_line(outline_word, 2, 2, 10)
        if len(cur_poem) < poem_length:
            cur_poem.append(candidate_line)
        else:
            candidates.append(cur_poem)
            cur_poem = []
    print str(len(candidates))+" candidate poems"
        
    print str(time.time() - start_time)+" seconds"

    generations = 2
    breeding_fraction = .25 # Top fraction of candidates allowed to breed
    mutation_prob = .1 # Probability that a child will be mutated
    while generations > 0:
        print "Generations remaining: "+str(generations)
        print "Saved lines: "+str(len(height_memo))
        # Get a fitness score for each poem 
        scored_candidates = []
        counter = 0
        for candidate in candidates:
            fitness = poem_fitness(candidate)
            counter += 1
            print str(counter)+'/'+str(len(candidates))+' candidates scored'
            scored_candidates.append((candidate, fitness))
            
        # Sort poems by fitness 
        scored_candidates.sort(key=operator.itemgetter(1))
        scored_candidates.reverse()

        # Select the top 1/n for some n for breeding
        parents = scored_candidates[0: int(math.ceil(len(scored_candidates) * breeding_fraction))]

        # Remove scores
        parents = [p[0] for p in parents] 

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
        num_replacements = math.ceil(1/breeding_fraction)
        for parent in parent_pairs:
            for k in range(0,int(num_replacements/2)):
                crossovers = crossover(parent[0], parent[1])
                children.append(mutate(crossovers[0], mutation_prob))
                children.append(mutate(crossovers[1], mutation_prob))

        # Repeat on the next generation 
        candidates = children
        generations -= 1

    scored_candidates = []
    for candidate in candidates:
        fitness = poem_fitness(candidate)
        scored_candidates.append((candidate, fitness))
        
    # Sort poems by fitness 
    scored_candidates.sort(key=operator.itemgetter(1))
    scored_candidates.reverse()
    candidates = scored_candidates[:5]
    candidates.reverse()

    #print top 5 members of final generation 
    for candidate in candidates:
        print "Score: "+str(candidate[1])+'\n-----'
        print_human_text(candidate[0])

        
if __name__ == "__main__":
    main()

