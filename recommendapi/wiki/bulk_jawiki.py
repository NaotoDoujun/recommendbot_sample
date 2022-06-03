# -*- coding: utf-8 -*-
import json, gzip, datetime, sys, math
from bert_serving.client import BertClient
import sentencepiece as spm
from elasticsearch import Elasticsearch, helpers
es = Elasticsearch("http://elasticsearch:9200", request_timeout=100)

target_file = "/app/wiki/jawiki-20220516-cirrussearch-content.json.gz"
target_index = "jawiki"
target_mapping = "/app/wiki/jawiki_mapping.json"
target_setting = "/app/wiki/jawiki_setting.json"

class BertServingClient:
    def __init__(self, sp_model='/app/wiki/wiki-ja.model', bert_server_ip='bertserving',bert_port=5555,bert_port_out=5556):
        self.sp = spm.SentencePieceProcessor()
        self.sp.Load(sp_model)
        self.bc = BertClient(
            ip=bert_server_ip, 
            port=bert_port,
            port_out=bert_port_out,
            check_version = False,
            check_length = False,
            timeout=60000)

    def status(self):
        return self.bc.status

    def sentence_piece_tokenizer(self, text):
        text = text.lower()
        return self.sp.EncodeAsPieces(text)
    
    def sentence2vec(self, sentences):
        parsed_texts = list(map(self.sentence_piece_tokenizer, sentences))
        return self.bc.encode(parsed_texts, is_tokenized=True)

bsc = BertServingClient()

def progress(current, pro_size):
    return print('\r making bulk data {0}% {1}/{2}'.format(
        math.floor(current / pro_size * 100.), 
        current, 
        pro_size), end='')

def convert_size(size, unit="B"):
    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB")
    i = units.index(unit.upper())
    size = round(size / 1024 ** i, 2)
    return f"{size} {units[i]}"

def create_docs(jsonlines, curids, texts, index_name, count):
    size = sys.getsizeof(jsonlines)
    print('\r ****** sentence2vec {} [{}] started at {} ******'.format(
        count, 
        convert_size(size, "KB"), 
        datetime.datetime.now()
    ))
    vectors = bsc.sentence2vec(texts)
    print('\r ****** sentence2vec {} [{}]    done at {} ******'.format(
        count, 
        convert_size(size, "KB"), 
        datetime.datetime.now()
    ))
    return [
        {
        '_index': index_name,
        'curid': curid,
        'title': jsonline['title'], 
        'text': jsonline['text'], 
        'text_vector': vector.tolist(), 
        'category': jsonline['category'],
        'outgoing_link': jsonline['outgoing_link'],
        'timestamp': jsonline['timestamp']
        } 
        for jsonline, curid, vector in zip(jsonlines, curids, vectors)
    ]

def do_bulk_import(jsonlines, curids, texts, index_name, count):
    if len(jsonlines) > 0:
        count += 1
        docs = create_docs(jsonlines, curids, texts, index_name, count)
        size = sys.getsizeof(docs)
        print('\r ****** bulk_import  {} [{}] started at {} ******'.format(
            count, 
            convert_size(size, "KB"),
            datetime.datetime.now()))
        helpers.bulk(es, docs)
        print('\r ****** bulk_import  {} [{}]    done at {} ******'.format(
            count, 
            convert_size(size, "KB"), 
            datetime.datetime.now()))
    return count

def open_cirrussearch_file(cirrussearch_file, index_name, bulk_articles_limit, import_limit):
    with gzip.open(cirrussearch_file) as f:
        jsonlines, curids, texts, count, import_count = [], [], [], 1, 0
        for line in f:
            if not line:
                import_count = do_bulk_import(jsonlines, curids, texts, index_name, import_count)
                jsonlines = []
                curids = []
                texts = []
                break
            else:
                json_line = json.loads(line)
                if "index" not in json_line:
                    progress(count, bulk_articles_limit)
                    jsonlines.append(json_line)
                    texts.append(json_line['text'])
                    if count % bulk_articles_limit == 0:
                        import_count = do_bulk_import(jsonlines, curids, texts, index_name, import_count)
                        jsonlines, curids, texts, count = [], [], [], 1
                        if import_limit > 0 and import_count >= import_limit:
                            break
                    else:
                        count += 1
                else:
                    curids.append(json_line['index']['_id'])

def bulk_import_wiki(bulk_articles_limit=1000, import_limit=0):
    open_cirrussearch_file(target_file, target_index, bulk_articles_limit, import_limit)

def make_index():
    if es.indices.exists(index=target_index):
        es.indices.delete(index=target_index)
    
    with open (target_setting) as fs:
        setting = json.load(fs)
        with open(target_mapping) as fm:
            mapping = json.load(fm)
            es.indices.create(index=target_index, mappings=mapping, settings=setting)

def check_recreate_index():
    while True:
        inp = input('Re-create index[{}] before bulk import? [Y]es/[N]o? >> '.format(target_index)).lower()
        if inp in ('y', 'yes', 'n', 'no'):
            inp = inp.startswith('y')
            break
        print('Error! Input again.')
    return inp

def main():
    if check_recreate_index():
        make_index()
    bulk_import_wiki(10, 100)
    
if __name__ == '__main__':
    main()
    es.close()
