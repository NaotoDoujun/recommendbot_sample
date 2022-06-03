import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from typing import Dict
import slackweb
from bert_serving.client import BertClient
import sentencepiece as spm
from elasticsearch import Elasticsearch

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
            timeout=10000)

    def status(self):
        return self.bc.status

    def sentence_piece_tokenizer(self, text):
        text = text.lower()
        return self.sp.EncodeAsPieces(text)
    
    def sentence2vec(self, sentences):
        parsed_texts = list(map(self.sentence_piece_tokenizer, sentences))
        return self.bc.encode(parsed_texts, is_tokenized=True)

app = FastAPI()
bsc = BertServingClient()
es = Elasticsearch("http://elasticsearch:9200", request_timeout=100)
recommendbot = slackweb.Slack(url="http://mattermost:8065/hooks/wnsihzjy8p8d78tub98fzqsa7c")

@app.get("/")
def read_root():
    return {"BertClinetStatus" : bsc.status(), "ElasticSearch": es.info()}

@app.post("/recommends/")
def propose_recommend(slackPost: Dict):
    data = jsonable_encoder(slackPost)
    query_vector = bsc.sentence2vec([data['text']])[0].tolist()
    script_query = {
      "script_score": {
          "query": {
              "multi_match": {
                  "fields": [ "title", "text" ],
                  "query": data['text']
              }
          },
          "script": {
              "source": "_score + (cosineSimilarity(params.query_vector, 'text_vector') + 1.0)/2",
              "params": {"query_vector": query_vector}
          }
      }
    }
    response = es.search(
        index="jawiki",
        size=2,
        query=script_query
    )

    result = [
        {
            'title': row['_source']['title'], 
            'text': row['_source']['text'], 
            'score': row['_score'],
        }
        for row in response['hits']['hits']
    ]

    if len(result) > 0:
        attachments = [
            {
            "mrkdwn_in": ["text"],
                "color": "#36a64f",
                "pretext": "",
                "author_name": "recommendbot",
                "title": "Recommends from Wikipedia",
                "text": "{} said [{}]".format(data['user_name'], data['text']),
                "fields": [
                    {
                        "title": "{} (score:{})".format(row['title'], row['score']),
                        "value": row['text'],
                        "short": "false"
                    }
                    for row in result
                ]
            }
        ]
        recommendbot.notify(attachments=attachments)

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)