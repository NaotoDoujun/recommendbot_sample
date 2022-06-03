# recommendbot_sample
recommendbot sample

## Usage
```bash
docker-compose up -d --build
```

## Use wikipedia cirrussearch dump
Download latest wikipedia cirrussearch dump file and place it in the 'recommendapi/wiki' folder.  
https://dumps.wikimedia.org/other/cirrussearch/  
I used 'jawiki-20220516-cirrussearch-content.json.gz'  

## Create index with mapping and bulk import jawiki
Run below command in 'recommendapi' container.
```bash
python3 /app/wiki/bulk_jawiki.py
```
If you wanna re-create index, enter y
```bash
python3 /app/wiki/bulk_jawiki.py
Re-create index[jawiki] before bulk import? [Y]es/[N]o? >> y
 ****** sentence2vec 1 [0.18 KB] started at 2022-06-03 10:11:11.012952 ******
 ****** sentence2vec 1 [0.18 KB]    done at 2022-06-03 10:11:35.988036 ******
 ****** bulk_import  1 [0.18 KB] started at 2022-06-03 10:11:35.989075 ******
 ****** bulk_import  1 [0.18 KB]    done at 2022-06-03 10:11:36.217358 ******
 ****** sentence2vec 2 [0.18 KB] started at 2022-06-03 10:11:36.232551 ******
```

## recommendbot Sample
Download model files from below link and place them in the 'bertserving/model'   
[BERT-wiki-ja](https://drive.google.com/drive/folders/1aR9kA8gRN9cT_tXO36E-y33tC-qb5-SH)  
Also, place "wiki-ja.model" in the 'recommendapi/wiki'.  
bertserving container will take time from activation to start of service. so, if recommendapi container is down due to a communication timeout with bertserving, restart it.  
And plz change the token for mattermost's incoming webhook to your one.  
```python
#main.py line 36
recommendbot = slackweb.Slack(url="http://mattermost:8065/hooks/[YOUR TOKEN]")
```
