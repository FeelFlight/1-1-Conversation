import os
import json
import couchdb
import requests
from   flask                  import Flask, jsonify, request, make_response
from   flask_httpauth         import HTTPBasicAuth
from   watson_developer_cloud import ToneAnalyzerV3, ConversationV1

app           = Flask(__name__)
tone_analyzer = ToneAnalyzerV3(username=os.environ['TONE-USER'], password=os.environ['TONE-PASS'], version='2016-05-19')
conversation  = ConversationV1(username=os.environ['CONV-USER'], password=os.environ['CONV-PASS'], version='2017-04-21')
workspace_id  = os.environ['CONV-WOSP']
auth          = HTTPBasicAuth()
couch         = couchdb.Server('http://couchdb:5984/')

try:
    db = couch['feelflight']
except Exception as e:
    db = couch.create('feelflight')


@auth.get_password
def get_password(username):
    if username == 'ansi':
        return 'test'
    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.route('/api/v1.0/conversation/process', methods=['POST'])
@auth.login_required
def process_text():
    r = request.get_json(silent=True)
    if r is not None and 'text' in r and 'telegramid' in r:
        text = r['text']
        uid  = str(r['telegramid'])
        msg  = r['telegrammsg']
        user = json.loads(requests.get('http://passenger:8030/api/v1.0/passengers/%s' % uid,
                                       auth=('ansi', 'test')
                                       ).content
                          )
        #print("USER:")
        #print(json.dumps(user, indent=2, sort_keys= True))

        if uid in db:
            context = db[uid]
        else:
            context = {}

        context['user'] = user

        #print("CONTEXT:")
        #print(json.dumps(context, indent=2, sort_keys= True))

        answer = {}
        answer['tone'] = tone_analyzer.tone(text=text)
        answer['chat'] = conversation.message(context=context, workspace_id=workspace_id, message_input={'text': text})
        db[uid] = answer['chat']['context']
        return jsonify(answer)
    else:
        return make_response(jsonify({'error': 'Not a valid json'}), 401)


@app.route('/api/v1.0/conversation/clear', methods=['POST'])
@auth.login_required
def clear_conversation():
    r = request.get_json(silent=True)
    if r is not None and 'telegramid' in r:
        uid  = str(r['telegramid'])
        db[uid] = {}


if __name__ == '__main__':
    app.run(host="::", port=8011)
