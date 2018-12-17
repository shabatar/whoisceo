from collections import defaultdict
import pickle
from elasticsearch import Elasticsearch
import nltk.data
from nltk.tag.stanford import StanfordNERTagger
import csv


def load_columns(filename):
    with open(filename) as f:
        columns = defaultdict(list)
        reader = csv.DictReader(f)
        for row in reader:
            for (k, v) in row.items():
                columns[k].append(v)
    return columns


def load_all(filename):
    with open(filename, "rb") as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break


SP500 = load_columns('./data/sp-500.csv')
CEO_pkl = list(load_all('./data/ceos.pkl'))
REPORTS_pkl = list(load_all('./data/companies.pkl'))
CIKs = SP500['Symbol']
Names = SP500['Name']


def query_es(query, es):
    return es.search(index="test-index", doc_type='text', q=query)


def retrieve_names(sentence, tagger):
    tokens = nltk.word_tokenize(sentence)
    tags = tagger.tag(tokens)
    i = 0
    names = set()
    while i < len(tags):
        token, category = tags[i]
        if category == "PERSON":
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
    BEFORE_CEO = 10
    AFTER_CEO = 10
    # sentence = sentence.lower()
    tokens = nltk.word_tokenize(sentence)
    i = 0
    ceo_pos = None
    while i < len(tokens):
        if tokens[i].lower() == "ceo":
            ceo_pos = (i, i + 1)
            break
        elif tokens[i].lower() == "chief" and \
                tokens[i + 1].lower() == "executive" and \
                tokens[i + 2].lower() == "officer":
            ceo_pos = (i, i + 3)
        i += 1
    if ceo_pos is None:
        return ""
    ceo_start, ceo_end = ceo_pos
    start = max(ceo_start - BEFORE_CEO, 0)
    end = min(ceo_end + AFTER_CEO, len(tokens))
    return " ".join(tokens[start: end])


def search_for(text, es, tagger):
    res = query_es(text, es)
    # print("Got %d Hits:" % res['hits']['total'])
    possible_ceo = defaultdict(int)
    for hit in res['hits']['hits']:
        sentence = hit["_source"]["text"]
        if len(sentence) < 10:
            continue
        print(sentence)
        part_with_seo = find_part_with_ceo(sentence)
        names = retrieve_names(part_with_seo, tagger)
        for name in names:
            possible_ceo[name] += 1
    # print("------------- Possible CEO -------------")
    # for ceo, num in possible_ceo.items():
        # print(ceo + " : " + str(num))
    return possible_ceo


def company_exists(company):
    if company in CIKs:
        return 1
    if company in Names:
        return 2
    return 0


def check_ceo(company):
    global REPORTS_pkl, CIKs, Names
    report = get_company_report(company)
    stanford_tagger = StanfordNERTagger('stanford-ner/english.all.3class.distsim.crf.ser.gz',
                                        'stanford-ner/stanford-ner.jar')
    es = Elasticsearch()

    es.indices.delete("test-index")

    if not es.indices.exists("test-index"):
        data = report.replace("\n", ".\n").replace("\n\n", "\n")
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        sentences = tokenizer.tokenize(data)
        for i, sentence in enumerate(sentences):
            doc = {'text': sentence}
            res = es.index(index="test-index", doc_type='text', id=i, body=doc)
    es.indices.refresh(index="test-index")

    text = "ceo"
    ceos = search_for(text, es, stanford_tagger)
    text = "chief executive officer"
    chiefs = search_for(text, es, stanford_tagger)
    ceos = {**ceos, **chiefs}
    ceos = full_names(ceos)
    for (ceo, v) in ceos.items():
        print("{}: {}".format(ceo, v))
    print()
    return ceos.keys()


def get_company_report(company):
    company_exist = company_exists(company)
    if not company_exist:
        raise LookupError("Company not found")
    if company_exist is 1:
        ind = CIKs.index(company)
    if company_exist is 2:
        ind = Names.index(company)
    try:
        text = REPORTS_pkl[ind]
    except IndexError:
        raise LookupError("Unexpected Error!")
    return text


def return_dumped_ceo(company):
    global CEO_pkl, CIKs, Names
    if company not in CIKs and company not in Names:
        raise LookupError("Company not found")
    ind = CIKs.index(company) or Names.index(company)
    ceo_list = CEO_pkl[ind]
    return ceo_list


def get_lastname(st):
    return st.split()[-1]


def full_names(names):
    tmp_result = defaultdict(int)
    first_names = {}
    for (k, v) in names.items():
        first_name, last_name = k.split()[0], k.split()[-1]
        if first_name != last_name and "." not in first_name:
            first_names[last_name] = first_name
        tmp_result[last_name] += v
    result = {}
    for (last_name, v) in tmp_result.items():
        if last_name in first_names:
            result[first_names[last_name] + " " + last_name] = v
        else:
            result[last_name] = v
    return result


if __name__ == '__main__':
    f = open('./data/ceos.pkl', 'ab+')
    ceo = []
    for i, cik in enumerate(CIKs):
        print("Checking CEO for: {}".format(Names[i]))
        ceo = check_ceo(cik)
        pickle.dump(list(ceo), f)
    # except:
    #     pickle.dump(ceo, f)
        # continue

