#!/usr/bin/env python

from gevent import monkey;monkey.patch_all()
from bottle import route, request,run, default_app
from trello import Cards, Lists
import re
import json

TRELLO_CONFIG = {
    'api_key': '41397e66e001c782d111a951c60644fe',
    'oauth_token': 'd21facf0145d2361f3a2a81243ecd993ee94b3a585da70fdee8d782cbf2e8427',
    'board_id': '4i8dVRWd',
    'list_id_to_do': '52f1cd2524067dc47edb6c99',
    'list_id_in_progress': '52f1cd2524067dc47edb6c9a',
    'list_id_done': '52f1cd2524067dc47edb6c9b',
}

WEBHOOK_CONFIG = {
    'host': '0.0.0.0',
    'port': 7343
}

TRELLO_LIST = Lists(TRELLO_CONFIG['api_key'], TRELLO_CONFIG['oauth_token'])
TRELLO_CARDS = Cards(TRELLO_CONFIG['api_key'], TRELLO_CONFIG['oauth_token'])


@route("/")
def index():
    return 'git webhook for move trello cards'


@route("/webhook", method='POST')
def handle_payload():
    json_payload = None
    from_gitlab = False
    if request.get_header('Content-Type', None) == 'application/json':
        json_payload = request.json
        from_gitlab = True
    else:
        body = request.forms['payload']
        json_payload = json.loads(body)
    print(json_payload)
    commits = json_payload['commits']
    cards_in_commit = []
    cards_url_dict = {}
    card_pattern = '(card #)([0-9]+)'

    for commit in commits:
        results = re.findall(
            card_pattern, commit['message'], flags=re.IGNORECASE)
        for result in results:
            cards_in_commit.append(result[2])
            cards_url_dict[result[2]] = commit['url']

    print(cards_in_commit)
    print(cards_url_dict)
    if cards_in_commit:
        from_cards = TRELLO_LIST.get_card(
            TRELLO_CONFIG['list_id_to_do'])

        for card in from_cards:
            print(card)
            if str(card['idShort']) in cards_in_commit:
                desc_with_commit = '{0}\n{1}'.format(
                    card['desc'], cards_url_dict[str(card['idShort'])])

                TRELLO_CARDS.update(
                    card['id'], desc=desc_with_commit, idList=TRELLO_CONFIG['list_id_in_progress'])
                
        from_cards = TRELLO_LIST.get_card(
            TRELLO_CONFIG['list_id_in_progress'])

        for card in from_cards:
            print(card)
            if str(card['idShort']) in cards_in_commit:
                desc_with_commit = '{0}\n{1}'.format(
                    card['desc'], cards_url_dict[str(card['idShort'])])

                TRELLO_CARDS.update(
                    card['id'], desc=desc_with_commit, idList=TRELLO_CONFIG['list_id_done'])

    return "done"

if __name__ == '__main__':
    run(host=WEBHOOK_CONFIG['host'],
               port=WEBHOOK_CONFIG['port'], server='gevent', debug=True)

app = default_app()
