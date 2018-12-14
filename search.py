from collections import defaultdict
import pickle
from elasticsearch import Elasticsearch
import nltk.data
from nltk.tag.stanford import StanfordNERTagger
import pandas as pd

def my_search(query, es):
    return es.search(index="test-index", body={"query":
                                                   {"match":
                                                        {"text":
                                                             {"query": query,
                                                              #"fuzziness": "AUTO",
                                                              "operator": "and"}}
                                                    }}
                     )


def my_search_easy(query, es):
    return es.search(index="test-index", doc_type='text', q=query)


def find_names(sentence, tagger):
    tokens = nltk.word_tokenize(sentence)
    tags = tagger.tag(tokens)
    i = 0
    names = set()
    while i < len(tags):
        token, cat = tags[i]
        if cat == "PERSON":
            full_name = token
            for j in range(i + 1, len(tags)):
                token_next, cat_next = tags[j]
                if cat_next == "PERSON":
                    full_name += " " + token_next
                    i += 1
                else:
                    break
            names.add(full_name)
        i += 1

    return names


def find_part_with_ceo(sentence):
    BEFORE_CEO = 10 # 10 words before
    AFTER_CEO = 10 # 10 words after
    sentence = sentence.lower()
    tokens = nltk.word_tokenize(sentence)
    i = 0
    ceo_pos = None
    while i < len(tokens):
        if tokens[i] == "ceo":
            ceo_pos = (i, i + 1)
            break
        elif tokens[i] == "chief" and tokens[i+1] == "executive" and tokens[i+2] == "officer":
            ceo_pos = (i, i + 3)
        i += 1
    if (ceo_pos is None):
        return ""
    ceo_start, ceo_end = ceo_pos
    return " ".join(tokens[ceo_start - BEFORE_CEO : ceo_end + AFTER_CEO])


def search_for(text, es, tagger, res):
    res = my_search_easy(text, es)
    print("Got %d Hits:" % res['hits']['total'])
    possible_ceo = defaultdict(int)
    for hit in res['hits']['hits']:
        sentence = hit["_source"]["text"]
        print(sentence)
        part_with_seo = find_part_with_ceo(sentence)
        names = find_names(sentence, tagger)
        for name in names:
            possible_ceo[name] += 1
    print("------------- Possible CEO -------------")
    for ceo, num in possible_ceo.items():
        print(ceo + " : " + str(num))
    return possible_ceo

def loadall(filename):
    with open(filename, "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

def check_ceo(company):
    df = pd.read_csv('sp-500.csv', sep=',', header=0)
    ciks = list(df['Symbol'])
    names = list(df['Name'])
    if (company not in ciks and company not in names):
        raise LookupError("Company not found")
    companies = list(loadall('companies.pkl'))
    try:
        ind = ciks.index(company)
    except ValueError:
        try:
            ind = names.index(company)
        except ValueError:
            raise LookupError("Company not in my list of 500")
    try:
        text = companies[ind]
    except:
        raise LookupError("Unexpected Error!")
    stanford_tagger = StanfordNERTagger('stanford-ner/english.all.3class.distsim.crf.ser.gz', 'stanford-ner/stanford-ner.jar')
    es = Elasticsearch()
    if es.indices.exists("test-index"): es.indices.delete("test-index")
    data = text.replace("\n", ".\n").replace("\n\n", "\n")
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(data)
    for i, sentence in enumerate(sentences):
        doc = {'text': sentence}
        res = es.index(index="test-index", doc_type='text', id=i, body=doc)
    es.indices.refresh(index="test-index")

    text = "ceo"
    ceos = search_for(text, es, stanford_tagger, res)
    return ceos.keys()

def check_ceo_in_file(company):
    ceos = list(loadall('ceos.pkl'))
    df = pd.read_csv('sp-500.csv', sep=',', header=0)
    ciks = list(df['Symbol'])
    names = list(df['Name'])
    if (company not in ciks and company not in names):
        raise LookupError("Company not found")
    ind = ciks.index(company) or names.index(company)
    ceo_list = ceos[ind]
    return ceo_list

if __name__ == '__main__':
    f = open('ceos.pkl', 'ab+')
    df = pd.read_csv('sp-500.csv', sep=',', header=0)
    ciks = list(df['Symbol'])
    names = list(df['Name'])
    ceo = []
    for i, cik in enumerate(ciks):
        print("Checking CEO for: {}".format(names[i]))
        try:
            ceo = check_ceo(cik)
            pickle.dump(list(ceo), f)
        except:
            pickle.dump(ceo, f)
            continue