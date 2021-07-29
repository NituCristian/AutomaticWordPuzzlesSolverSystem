from flask import Flask, request
from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api
from json import dumps
from flask_jsonpify import jsonify
from nltk import *
from nltk.corpus import wordnet
from pattern.en import conjugate, pluralize, lemma, lexeme, PRESENT, SG, PL

import requests
import json
import spacy
import neuralcoref

nlp = spacy.load('en')
neuralcoref.add_to_pipe(nlp)

tag_dict = {"J": wordnet.ADJ,
            "N": wordnet.NOUN,
            "V": wordnet.VERB,
            "R": wordnet.ADV}

def find_persons(puzzle):
    trained_puzzle = nlp(puzzle)

    puzzle_persons = []

    for entity in trained_puzzle.ents:
        if entity.label_ == 'PERSON':
            puzzle_persons.append(entity.text)

    return puzzle_persons


def coref_resolution(puzzle):
    sentences = sent_tokenize(puzzle)

    for sent in sentences:
        if sent.endswith('?'):
            sentences.remove(sent)

    sentences_coref = []

    for sentence in sentences:
        sentence_trained = nlp(sentence)
        sentence = sentence_trained._.coref_resolved
        sentence = sentence.replace('.', '')

        sentences_coref.append(sentence)

    return sentences_coref


def create_mace_command(sentences_coref, parser, puzzle_id):
    puzzle_assumptions = []
    read_expr = Expression.fromstring

    for sentence in sentences_coref:
        tokens = sentence.split()

        updated_tokens = []
        word_count = -1
        sentence_can_be_parsed = True

        try:
            for tree in parser.parse(tokens):
                expr = tree.label()['SEM']
                expr_to_str = str(expr)
                assumption = read_expr(expr_to_str)

            puzzle_assumptions.append(assumption)

        except ValueError as e:
            sentence_can_be_parsed = False

        if not sentence_can_be_parsed:
            for t in tokens:
                word_count = word_count + 1
                synonyms = []

                word_can_be_parsed = True
                try:
                    for tree in parser.parse([t]):
                        expr = tree.label()['SEM']
                        expr_to_str = str(expr)
                        assumption = read_expr(expr_to_str)

                except ValueError as e:
                    exception_to_be_thrown = e
                    cannot_parse_synonym_flag = False
                    unfound_synonym = True
                    word_can_be_parsed = False

                if not word_can_be_parsed:
                    for syn in wordnet.synsets(t):
                        for lemma in syn.lemmas():
                            synonyms.append(lemma.name())

                    if len(synonyms) < 1:
                        # if no synonym for undefined word in lexicon, throw exception
                        raise Exception(exception_to_be_thrown)

                    for s in set(synonyms):
                        word_tag = pos_tag([tokens[word_count]])

                        try:
                            lexeme_test = lexeme('gave')
                        except:
                            pass

                        if word_tag[0][1] == 'NNS':
                            s = pluralize(s)
                        elif word_tag[0][1] == 'VBZ':
                            s = conjugate(verb=s, tense=PRESENT, number=SG)
                        elif word_tag[0][1] == 'VBP':
                            s = conjugate(verb=s, tense=PRESENT, number=PL)

                        synonym_can_be_parsed = True

                        try:
                            for tree in parser.parse([s]):
                                print("Check")

                        except ValueError as e:
                            if unfound_synonym:
                                cannot_parse_synonym_flag = True

                            synonym_can_be_parsed = False

                        if synonym_can_be_parsed:
                            cannot_parse_synonym_flag = False
                            unfound_synonym = False
                            tokens[word_count] = s
                            updated_tokens = tokens

            try:
                if cannot_parse_synonym_flag:
                    if not synonym_can_be_parsed:
                        raise Exception(exception_to_be_thrown)

                for tree in parser.parse(updated_tokens):
                    expr = tree.label()['SEM']
                    expr_to_str = str(expr)
                    assumption = read_expr(expr_to_str)

                puzzle_assumptions.append(assumption)

            except ValueError as e:
                raise ValueError(e)

    assumptions_file = 'puzzleAssumptions' + puzzle_id + '.fol'
    f = open(assumptions_file, "w+")

    index = 0
    for assumption in puzzle_assumptions:
        f.write("Sentence: ")
        f.write(sentences_coref[index])
        f.write('\n')
        f.write("FOL representation: ")
        f.write(str(assumption))
        f.write('\n \n')
        index = index + 1
    f.close()

    return MaceCommand(assumptions=puzzle_assumptions)


def solve_question(sentence, parser):
    read_expr = Expression.fromstring
    tokens = sentence.split()

    updated_tokens = []
    word_count = -1
    sentence_can_be_parsed = True

    try:
        for tree in parser.parse(tokens):
            expr = tree.label()['SEM']
            expr_to_str = str(expr)
            assumption = read_expr(expr_to_str)

        return assumption

    except ValueError as e:
        sentence_can_be_parsed = False

    if not sentence_can_be_parsed:
        for t in tokens:
            word_count = word_count + 1
            synonyms = []

            word_can_be_parsed = True
            try:
                for tree in parser.parse([t]):
                    expr = tree.label()['SEM']
                    expr_to_str = str(expr)
                    assumption = read_expr(expr_to_str)

            except ValueError as e:
                exception_to_be_thrown = e
                cannot_parse_synonym_flag = False
                unfound_synonym = True
                word_can_be_parsed = False

            if not word_can_be_parsed:
                for syn in wordnet.synsets(t):
                    for lemma in syn.lemmas():
                        synonyms.append(lemma.name())

                if len(synonyms) < 1:
                    # if no synonym for undefined word in lexicon, throw exception
                    raise Exception(exception_to_be_thrown)

                for s in set(synonyms):
                    word_tag = pos_tag([tokens[word_count]])

                    try:
                        lexeme_test = lexeme('gave')
                    except:
                        pass

                    if word_tag[0][1] == 'NNS':
                        s = pluralize(s)
                    elif word_tag[0][1] == 'VBZ':
                        s = conjugate(verb=s, tense=PRESENT, number=SG)
                    elif word_tag[0][1] == 'VBP':
                        s = conjugate(verb=s, tense=PRESENT, number=PL)

                    synonym_can_be_parsed = True

                    try:
                        for tree in parser.parse([s]):
                            print("Check")

                    except ValueError as e:
                        if unfound_synonym:
                            cannot_parse_synonym_flag = True

                        synonym_can_be_parsed = False

                    if synonym_can_be_parsed:
                        cannot_parse_synonym_flag = False
                        unfound_synonym = False
                        tokens[word_count] = s
                        updated_tokens = tokens

        try:
            if cannot_parse_synonym_flag:
                if not synonym_can_be_parsed:
                    raise Exception(exception_to_be_thrown)

            for tree in parser.parse(updated_tokens):
                expr = tree.label()['SEM']
                expr_to_str = str(expr)
                assumption = read_expr(expr_to_str)

            return assumption

        except ValueError as e:
            raise ValueError(e)


def write_person_assumptions(persons, puzzle_automatic_background):
    f = open(puzzle_automatic_background, "w+")
    i = 0

    for p in set(persons):
        i = i + 1
        j = 0

        for q in set(persons):
            j = j + 1

            if p != q and i < j:
                assumption = '' + p.lower() + ' != ' + q.lower() + ''
                f.write(assumption)
                f.write('\n')

    f.close()


def word_in_puzzle(word, puzzle, original_word_tag):
    sentences = sent_tokenize(puzzle)
    lemmatizer = WordNetLemmatizer()

    for sentence in sentences:
        token = word_tokenize(sentence)
        tag = (pos_tag(token))

        for t in set(tag):
            if word == lemmatizer.lemmatize(t[0], tag_dict.get(t[1][0].upper(), wordnet.NOUN)) \
                    and tag_dict.get(t[1][0].upper(), wordnet.NOUN) == original_word_tag:
                return True
    return False


def write_synonyms_assumptions(sentences_coref, puzzle, puzzle_automatic_background):
    assumptions_synonyms = []
    lemmatizer = WordNetLemmatizer()
    f = open(puzzle_automatic_background, "a+")

    for sentence in sentences_coref:
        word = word_tokenize(sentence)
        tag = (pos_tag(word))

        for t in set(tag):
            synonyms = []

            for syn in wordnet.synsets(t[0]):
                for lemma in syn.lemmas():
                    synonyms.append(lemma.name())

            for s in set(synonyms):
                if s != lemmatizer.lemmatize(t[0], tag_dict.get(t[1][0].upper(), wordnet.NOUN)):

                    assumption = 'all x.(' + s + '(x) <-> ' + lemmatizer.lemmatize(t[0], tag_dict.get(t[1][0].upper(), wordnet.NOUN)) + '(x))'

                    if s in puzzle and word_in_puzzle(s, puzzle, tag_dict.get(t[1][0].upper(), wordnet.NOUN)) == True\
                            and len(s) > 1 and len(lemmatizer.lemmatize(t[0], tag_dict.get(t[1][0].upper(), wordnet.NOUN))) > 1:

                        assumptions_synonyms.append(assumption)

    for assumption in set(assumptions_synonyms):
        f.write(assumption)
        f.write('\n')
    f.close()


app = Flask(__name__)
api = Api(app)
CORS(app)


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


@app.route('/puzzle/<puzzle_id>', methods=['POST'])
def resolve_puzzle(puzzle_id):

    data2 = json.loads(request.data.decode())
    puzzle = data2["puzzle"]
    path = data2["filepath"]
    background_path = data2["background"]

    puzzle_automatic_background = 'background' + puzzle_id + '.fol'

    parser = load_parser(path, trace=0)

    sentences_coref = coref_resolution(puzzle)

    mb = create_mace_command(sentences_coref, parser, puzzle_id)

    persons = find_persons(puzzle)
    write_person_assumptions(persons, puzzle_automatic_background)

    write_synonyms_assumptions(sentences_coref, puzzle, puzzle_automatic_background)

    background_info = data.load(background_path)
    mb.add_assumptions(background_info)

    background_info_deduced = data.load(puzzle_automatic_background)
    mb.add_assumptions(background_info_deduced)

    print("Assumptions are: ")
    print(mb.print_assumptions())

    print("Can mace4 build a model?: ", mb.build_model())
    print(mb.valuation)

    result = json.dumps(mb.valuation, default=set_default)

    print("Solution is")
    print(result)

    return jsonify(result)


@app.route('/question/<puzzle_id>', methods=['POST'])
def resolve_question(puzzle_id):

    data2 = json.loads(request.data.decode())
    puzzle = data2["puzzle"]
    path = data2["filepath"]
    background_path = data2["background"]
    question_file = data2["question"]

    puzzle_automatic_background = 'background' + puzzle_id + '.fol'

    parser = load_parser(path, trace=0)

    sentences_coref = coref_resolution(puzzle)

    mb = create_mace_command(sentences_coref, parser, puzzle_id)

    persons = find_persons(puzzle)
    write_person_assumptions(persons, puzzle_automatic_background)

    write_synonyms_assumptions(sentences_coref, puzzle, puzzle_automatic_background)

    background_info = data.load(background_path)
    mb.add_assumptions(background_info)

    background_info_deduced = data.load(puzzle_automatic_background)
    mb.add_assumptions(background_info_deduced)

    persons = find_persons(puzzle)

    read_expr = Expression.fromstring

    youngest = ""
    oldest = ""
    shortest = ""
    tallest = ""

    for person in set(persons):
        #used to obtain a bounded domain
        youngest += "youngest(" + person.lower() + ")" + " | "
        oldest += "oldest(" + person.lower() + ")" + " | "
        shortest += "shortest(" + person.lower() + ")" + " | "
        tallest += "tallest(" + person.lower() + ")" + " | "

    shortest = shortest[0:-3]

    if youngest != "":
        a1 = read_expr("" + youngest[0:-3] + "")
        a2 = read_expr("" + oldest[0:-3] + "")
        a3 = read_expr("" + shortest + "")
        a4 = read_expr("" + tallest[0:-3] + "")

        bounded_assumptions = [a1, a2, a3, a4]
        mb.add_assumptions(bounded_assumptions)

    print("Assumptions are: ")
    print(mb.print_assumptions())

    sentences = sent_tokenize(question_file)

    sentences_coref = []

    puzzle_question_proofs = "proof" + puzzle_id + ".txt"
    f = open(puzzle_question_proofs, "w+")

    for sentence in sentences:

        sentence = sentence.replace('.', '')
        question = solve_question(sentence, parser)
        sentences_coref.append(sentence)

        f.write("Statement is: ")
        f.write(sentence)
        f.write('\n')
        f.write("FOL representation: ")
        f.write(str(question))
        f.write('\n')
        f.write("Can the statement be proved? ")

        prover = Prover9Command(question, mb.assumptions())

        if prover.prove():
            f.write("Yes")
            f.write("\n")
            f.write(prover.proof())
        else:
            f.write("No")
        f.write("\n")
        f.write("\n")

    return jsonify(puzzle_question_proofs)


if __name__ == '__main__':
    app.run(port=5002)
