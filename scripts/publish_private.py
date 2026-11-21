#!/usr/bin/env python3
"""Publikuje przygotowany commit wyłącznie w prywatnym repo wskazanej organizacji."""
from pathlib import Path
import subprocess,json,sys
root=Path(__file__).resolve().parents[1];org='HackNation2026-dev';name=root.name;full=f'{org}/{name}'
def run(args,check=True):return subprocess.run(args,cwd=root,text=True,capture_output=True,check=check)
def fail(text):print(text,file=sys.stderr);sys.exit(1)
try:
 run(['gh','auth','status'])
 run(['gh','api',f'orgs/{org}'])
 info=run(['gh','api',f'repos/{full}'],False)
 if info.returncode:
  if 'HTTP 404' not in info.stderr:fail('Nie można sprawdzić repo: '+info.stderr.strip())
  run(['gh','repo','create',full,'--private','--description','HackNation 2026: wersjonowana dokumentacja i materiały zadania'])
  info=run(['gh','api',f'repos/{full}'])
 data=json.loads(info.stdout)
 if data.get('private') is not True or data.get('owner',{}).get('login','').lower()!=org.lower():fail('Przerwano: niewłaściwy właściciel lub repo nie jest prywatne.')
 target=f'https://github.com/{full}.git'
 origin=run(['git','remote','get-url','origin'],False)
 if origin.returncode:run(['git','remote','add','origin',target])
 elif origin.stdout.strip()!=target:fail('Przerwano: istniejący origin wskazuje inne miejsce.')
 remote=run(['git','ls-remote','origin','refs/heads/main'])
 local=run(['git','rev-parse','HEAD']).stdout.strip()
 if remote.stdout.strip() and remote.stdout.split()[0]!=local:fail('Repo ma już inną gałąź main. Nie nadpisano zdalnej historii.')
 run(['python3','scripts/verify_docs.py'])
 run(['git','push','-u','origin','main'])
 run(['git','push','origin','v'+(root/'VERSION').read_text().strip()])
 confirm=json.loads(run(['gh','api',f'repos/{full}']).stdout)
 if confirm.get('private') is not True:fail('Nie potwierdzono prywatności.')
 sha=run(['git','ls-remote','origin','refs/heads/main']).stdout.split()[0]
 if sha!=local:fail('Zdalny commit nie zgadza się z lokalnym.')
 print(f'OK: {confirm["html_url"]}, private=true, commit={sha}')
except subprocess.CalledProcessError as e:
 fail('Publikacja zatrzymana: '+(e.stderr or e.stdout or str(e)).strip())
