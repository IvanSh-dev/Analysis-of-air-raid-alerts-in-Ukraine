"""Reply-only Telegram bot for the frozen archive forecast; stdlib networking."""
import argparse
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen
from .pipeline import ROOT

URL='https://ivan-alert-atlas-2026.mapledrum8.chatgpt.site'
HELP='''Alert Atlas — архівний дослідницький приклад.
Дані: 15.10.2026. Початок прогнозу: 16.10.2026, 00:00 Europe/Kyiv.

/regions — обрати регіон кнопкою
/forecast Київ 1 — прогноз на добу
/forecast Львівська 3 — прогноз на три дні
/forecast Харківська 7 — прогноз на сім днів
/help — пояснення

Відсоток означає ймовірність хоча б одного запису за весь період. Це не ймовірність офіційної тривоги чи небезпеки. Керуйтеся офіційними сповіщеннями.
Бот не отримує живі тривоги й не надсилає автоматичних попереджень.'''

def percent(value):
    if value is None:return 'немає даних'
    if value>.999:return '>99,9%'
    if value<.001:return '<0,1%'
    return f'{value*100:.1f}%'.replace('.',',')

def normalize(text):
    return re.sub(r'\s+',' ',text.casefold().replace('область','').strip()).strip()

def find_region(data,text):
    key=normalize(text)
    if key in {'київ','киев','kyiv'}:return next(r for r in data['regions'] if r['id']=='Kyiv City')
    matches=[r for r in data['regions'] if key in {normalize(r['name']),normalize(r['id']),normalize(r['iso'])}]
    if len(matches)!=1:raise ValueError('Регіон не розпізнано. Скористайтеся /regions.')
    return matches[0]

def region_keyboard(data):
    buttons=[{'text':r['name'],'callback_data':'f:'+r['iso']+':1'} for r in data['regions']]
    return {'inline_keyboard':[buttons[i:i+2] for i in range(0,len(buttons),2)]}

def render_forecast(region,horizon,data):
    p=region['periods'][str(horizon)]
    start=data['forecastDate'];end=p['end']
    title=f"{region['name']} · {start} — {end}\nПеріод: {horizon} дн. · Europe/Kyiv"
    if p['probability'] is None:
        body=f"Прогноз недоступний: {region['reason']}.\nНевідоме значення не дорівнює нулю тривог."
    else:
        count=f'{p["count"]:.1f}'.replace('.',',')
        baseline=f'{p["countBaseline"]:.1f}'.replace('.',',')
        body=(f"Хоча б один запис за весь період: {percent(p['probability'])}\n"
              f"Базова ймовірність: {percent(p['baselineProbability'])}\n"
              f"Прогнозована кількість: {count} записів\n"
              f"Базова кількість: {baseline} записів")
    text=(title+'\n\n'+body+f"\n\nВерсія даних: {data['dataVersion']}. Зафіксований приклад, не живий сервіс."
          '\nЦе ймовірність запису архіву, не офіційної тривоги чи небезпеки. Керуйтеся офіційними сповіщеннями.'
          '\nКарта: '+URL+' (приватний сайт власника)')
    keyboard={'inline_keyboard':[[{'text':str(h)+' дн.','callback_data':f"f:{region['iso']}:{h}"} for h in [1,3,7]]]}
    return text,keyboard

def command(text,data):
    pieces=text.strip().split(maxsplit=1)
    cmd=pieces[0].split('@')[0].lower() if pieces else ''
    arg=pieces[1] if len(pieces)>1 else ''
    if cmd in {'/start','/help'}:return HELP,region_keyboard(data)
    if cmd=='/regions':return 'Оберіть територію. За замовчуванням — 1 день.',region_keyboard(data)
    if cmd=='/forecast':
        fields=arg.rsplit(maxsplit=1)
        horizon=1
        if len(fields)>1 and fields[-1].isdigit():
            horizon=int(fields[-1]);arg=fields[0]
        if horizon not in (1,3,7):raise ValueError('Доступні періоди: 1, 3 або 7 днів.')
        return render_forecast(find_region(data,arg),horizon,data)
    return 'Невідома команда. Скористайтеся /regions або /help.',None

class ApiFailure(RuntimeError):
    """Sanitized error; never include URL, token, chat or response body."""

class TelegramAPI:
    def __init__(self,token):
        if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+',token):
            raise ApiFailure('Invalid token format; value suppressed')
        self._token=token

    def call(self,method,payload):
        request=Request(f'https://api.telegram.org/bot{self._token}/{method}',
            data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(request,timeout=45) as r:result=json.loads(r.read())
        except HTTPError as err:
            if err.code==429:
                try:delay=min(60,max(1,int(json.loads(err.read()).get('parameters',{}).get('retry_after',5))))
                except Exception:delay=5
                time.sleep(delay)
            raise ApiFailure('Telegram HTTP error '+str(err.code)) from None
        except (URLError,TimeoutError,OSError,json.JSONDecodeError):
            raise ApiFailure('Telegram connection or response error') from None
        if not result.get('ok'):raise ApiFailure('Telegram rejected the request')
        return result['result']

def handle_update(update,data,api):
    if 'callback_query' in update:
        query=update['callback_query'];message=query.get('message')
        if not message or message.get('chat',{}).get('type')!='private':return
        api.call('answerCallbackQuery',{'callback_query_id':query['id']})
        parts=query.get('data','').split(':')
        if len(parts)!=3 or parts[0]!='f' or parts[2] not in {'1','3','7'}:return
        try:region=find_region(data,parts[1]);text,keyboard=render_forecast(region,int(parts[2]),data)
        except ValueError:return
    else:
        message=update.get('message',{})
        # Only respond to user-initiated private requests; no groups/broadcasts.
        if message.get('chat',{}).get('type')!='private' or not message.get('text','').startswith('/'):return
        try:text,keyboard=command(message['text'],data)
        except ValueError as err:text,keyboard=str(err),None
    payload={'chat_id':message['chat']['id'],'text':text,'link_preview_options':{'is_disabled':True}}
    if keyboard:payload['reply_markup']=keyboard
    api.call('sendMessage',payload)

def poll(api,data,state):
    api.call('getMe',{})
    if api.call('getWebhookInfo',{}).get('url'):
        raise ApiFailure('An active webhook exists; use a dedicated polling bot or remove it yourself')
    offset=json.loads(state.read_text()).get('offset',0) if state.exists() else 0
    print('Bot started: frozen research data; private replies only. Ctrl+C stops it.')
    while True:
        try:
            updates=api.call('getUpdates',{'offset':offset,'timeout':30,'allowed_updates':['message','callback_query']})
            for update in updates:
                handle_update(update,data,api)
                offset=max(offset,int(update['update_id'])+1)
                state.parent.mkdir(parents=True,exist_ok=True)
                temporary=state.with_suffix('.tmp');temporary.write_text(json.dumps({'offset':offset}));temporary.replace(state)
        except ApiFailure as err:
            print(str(err));time.sleep(5)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'site/data.json')
    parser.add_argument('--state',type=Path,default=ROOT/'.tmp/telegram_offset.json')
    parser.add_argument('--dry-run',help='Render a command without token, network or messages')
    args=parser.parse_args();data=json.loads(args.data.read_text(encoding='utf-8'))
    if args.dry_run:
        try:text,_=command(args.dry_run,data)
        except ValueError as err:parser.error(str(err))
        print(text);return
    token=os.environ.get('TELEGRAM_BOT_TOKEN','').strip()
    if not token:parser.error('Set TELEGRAM_BOT_TOKEN in the process environment; do not pass it as a command argument')
    try:poll(TelegramAPI(token),data,args.state)
    except KeyboardInterrupt:print('\nBot stopped.')
    except ApiFailure as err:parser.exit(1,str(err)+'\n')

if __name__=='__main__':main()
