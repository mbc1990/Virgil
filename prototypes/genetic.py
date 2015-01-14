
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
parser = Parser()

# Constants 
generations = 7
breeding_fraction = .25 # Top fraction of candidates allowed to breed
mutation_prob = .05 # Probability that a child will be mutated
poem_length = 6 # Number of lines in a poem
starting_population_size = 50

# Generates an outline, against which the candidate poems are measured 
def generate_outline():
    return ['winter', 'owl', 'snow', 'sadness']
    #return ['heat', 'light', 'sun', 'happy', 'cat', 'soft', 'fur', 'love', 'sunrise']
    #return ['fur', 'soft', 'warm', 'snow', 'mountain', 'morning', 'sunrise', 'dense']
    #return ['sleep', 'warm', 'dream', 'tire', 'drift']
    #return ['stars', 'night', 'quiet', 'clear']
    #return ['cat', 'sun', 'sleep', 'field', 'tree']

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


height_memo = {} # tuple -> parse height  
def alliteration(poem):
    # Alliteration factor - poems where more of the words start with the same two letters are considered more fit
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

# Sum of parse height of each line
def line_parse_height(poem):
    global height_memo
    # Sum of parse height for each line
    total_parse_height = 0.1
    for line in poem:
        # Parse height
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

        return total_parse_height

# Like line_parse_height, but the sum of parse heights for each pair of adjacent lines
# This rewards grammatical continuity across lines
def line_pair_parse_height(poem):
    global height_memo
    # Sum of parse height for each pair of lines
    total_parse_height = 0.1
    for i in range(0,len(poem)-1):
        line = poem[i]
        next_line = poem[i+1]
        line_pair = line + next_line
        # Parse height
        parse_height = 0
        if tuple(line_pair) in height_memo:
            parse_height = height_memo[tuple(line_pair)]
            height_memo[tuple(line_pair)] = parse_height
        else:
            try:
                parse_tree = parser.parse(' '.join(line_pair))
                parse_height = parse_tree.height()
                height_memo[tuple(line_pair)] = parse_height
            except:
                height_memo[tuple(line_pair)] = 0.1
                return 0.1 # Return 0.1 if there's an error parsing a poem line
        total_parse_height += parse_height

        return total_parse_height


def phonetic_similarity(poem):
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


# Fitness function for an individual poem, the higher the return value the more fit an individual is 
def poem_fitness(poem):
    global min_alliteration 
    global max_alliteration
    global min_phon 
    global max_phon 
    
    alliteration_score = alliteration(poem)
    parse_height_score = line_pair_parse_height(poem)
    phonetic_similarity_score = phonetic_similarity(poem)

    if alliteration_score > max_alliteration:
        max_alliteration = alliteration_score 

    if alliteration_score < min_alliteration:
        min_alliteration = alliteration_score 

    if phonetic_similarity_score > max_phon:
        max_phon = phonetic_similarity_score

    if phonetic_similarity_score < min_phon:
        min_phon = phonetic_similarity_score

    print 'Alliteration: '+str(alliteration_score)
    print 'Parse height: '+str(parse_height_score)
    print 'Phon similar: '+str(phonetic_similarity_score)

    score = ((alliteration_score*2)+phonetic_similarity_score)/parse_height_score
    return score

# Randomly decided whether or not to mutate
def mutate(poem, probability):
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

# Load parse height cache
def load_parse_height_cache():
    global height_memo
    if os.path.isfile('parse_height_cache.json'):
        with open('parse_height_cache.json', 'r') as fp:
            height_cache_saved = json.load(fp)
            for key in height_cache_saved['key_map'].keys():
                tup_key = tuple(height_cache_saved['key_map'][key])
                height_value = height_cache_saved['saved_cache'][key]
                height_memo[tup_key] = height_value

# Save the updated height cache
def dump_parse_height_cache():
    with open('parse_height_cache.json', 'w') as fp:
        key_map_counter = 0
        key_map = {}
        saved_cache = {}
        for key in height_memo.keys():
            key_map[key_map_counter] = key 
            saved_cache[key_map_counter] = height_memo[key]
            key_map_counter += 1
        output = {'key_map': key_map, 'saved_cache': saved_cache}
        json.dump(output, fp)

min_phon = 1
max_phon = 0
min_alliteration = 1
max_alliteration = 0
def main():
    load_parse_height_cache()

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

    # Generate starting population
    for i in range(0, starting_population_size):
        next_poem = []
        for k in range(0, poem_length):
            outline_word = choice(outline)
            candidate_line = generate_candidate_line(outline_word, 2, 2, 10)
            next_poem.append(candidate_line)
        candidates.append(next_poem)
            
    print str(len(candidates))+" candidate poems"
    print str(time.time() - start_time)+" seconds"

    generation_counter = 1
    while generation_counter <= generations:
        # Get a fitness score for each poem 
        scored_candidates = []
        counter = 0
        for candidate in candidates:
            fitness = poem_fitness(candidate)
            counter += 1
            print str(counter)+'/'+str(len(candidates))+' candidates scored in generation '+str(generation_counter)+'/'+str(generations)+' with '+str(len(height_memo))+' cached line parse heights'
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
            for k in range(0,2+int(math.ceil(num_replacements/2))): # Parents replace themselves + at least their proportion of the culled generation 
                crossovers = crossover(parent[0], parent[1])
                children.append(mutate(crossovers[0], mutation_prob))
                children.append(mutate(crossovers[1], mutation_prob))

        # Repeat on the next generation 
        candidates = children
        generation_counter += 1

    # Results!
    scored_candidates = []
    for candidate in candidates:
        fitness = poem_fitness(candidate)
        scored_candidates.append((candidate, fitness))
        
    # Sort poems by fitness 
    scored_candidates.sort(key=operator.itemgetter(1))
    scored_candidates.reverse()
    candidates = scored_candidates[:5]
    candidates.reverse()

    # Save parse height cache
    dump_parse_height_cache()

    # Print top 5 members of final generation 
    for candidate in candidates:
        print "Score: "+str(candidate[1])+'\n-----'
        print_human_text(candidate[0])

    print 'min phon: '+str(min_phon)
    print 'max phon: '+str(max_phon)
    print 'min allit: '+str(min_alliteration)
    print 'max allit: '+str(max_alliteration)
        
if __name__ == "__main__":
    main()

