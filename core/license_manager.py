import json,os,base64,hashlib
from datetime import datetime,timedelta
from pathlib import Path
import getpass,sys

class LicenseManager:
 def __init__(self):
  self._a=self._b()
  self._c=self._d()
  self._e=self._f()
  self._g="MM_2026_ENZOC"
  self._h()
 def _b(self):
  u=getpass.getuser();h=str(Path.home())
  m=f"{u}@{h}@ImageOptimizer"
  return hashlib.sha256(m.encode()).hexdigest()[:10].upper()
 def _d(self):
  s="IMGOPT_LICENSE_DATA"
  k=hashlib.sha256(f"{self._a}{s}".encode()).digest()
  return k[:16]
 def _f(self):
  r=[]
  try:
   if getattr(sys,'frozen',False):p=Path(sys.executable).parent
   else:p=Path(__file__).parent.parent
   r.append(p/"user_settings.json")
  except:pass
  r.append(Path(os.getenv('APPDATA',Path.home()/"AppData"/"Roaming"))/"ImageOptimizer"/"settings.json")
  r.append(Path(os.getenv('LOCALAPPDATA',Path.home()/"AppData"/"Local"))/"ImageOptimizer"/"app_data.json")
  r.append(Path.home()/"Documents"/"ImageOptimizer"/"config.json")
  return r
 def _i(self,t):
  return base64.b64encode(t.encode()).decode()
 def _j(self,t):
  try:return base64.b64decode(t).decode()
  except:return None
 def _k(self,d):
  dc=d.copy()
  if'_checksum'in dc:del dc['_checksum']
  return hashlib.md5(json.dumps(dc,sort_keys=True).encode()).hexdigest()
 def _l(self):
  n=datetime.now().isoformat()
  return{"app_name":"ImageOptimizer Pro","version":"1.2","first_run":n,"last_run":n,"license_key":None,"license_active":False,"machine_id":self._a,"run_count":1,"trial_days":15,"created":n,"_checksum":""}
 def _h(self):
  existing_data=None
  for fp in self._e:
   try:
    if not fp.exists():continue
    with open(fp,'r',encoding='utf-8')as f:ed=f.read().strip()
    dd=self._j(ed)
    if not dd:continue
    d=json.loads(dd)
    if d.get('_checksum')!=self._k(d):continue
    if d.get('app_name')!="ImageOptimizer Pro":continue
    existing_data=d
    break
   except:continue
  if not existing_data:
   existing_data=self._l()
   existing_data["_checksum"]=self._k(existing_data)
  ed=self._i(json.dumps(existing_data,indent=2))
  for fp in self._e:
   try:
    fp.parent.mkdir(parents=True,exist_ok=True)
    with open(fp,'w',encoding='utf-8')as f:f.write(ed)
   except:continue
 def _m(self,fp):
  try:
   if not fp.exists():return None
   with open(fp,'r',encoding='utf-8')as f:ed=f.read().strip()
   dd=self._j(ed)
   if not dd:return None
   d=json.loads(dd)
   if d.get('_checksum')!=self._k(d):return None
   if d.get('app_name')!="ImageOptimizer Pro":return None
   return d
  except:return None
 def _n(self):
  al=[d for fp in self._e if(d:=self._m(fp))]
  if not al:return None
  for d in al:
   if d.get('license_active')and d.get('license_key'):
    if self._o(d['license_key']):return d
  best=None;best_date=None
  for d in al:
   lr=d.get('last_run')
   if lr and(not best_date or lr>best_date):best_date=lr;best=d
  return best or al[0]
 def _p(self,d):
  if not d:return
  n=datetime.now().isoformat()
  d['last_run']=n;d['run_count']=d.get('run_count',0)+1;d['machine_id']=self._a
  if'trial_days'not in d:d['trial_days']=15
  d['_checksum']=self._k(d)
  ed=self._i(json.dumps(d,indent=2))
  for fp in self._e:
   try:
    fp.parent.mkdir(parents=True,exist_ok=True)
    with open(fp,'w',encoding='utf-8')as f:f.write(ed)
   except:continue
 def _o(self,lk):
  if not lk or not isinstance(lk,str):return False
  if not lk.startswith("IMGOPT-"):return False
  ck=lk.replace("IMGOPT-","").replace("-","").upper()
  if len(ck)!=20 or not ck.isalnum():return False
  cp=ck[:16];cs=ck[16:]
  ecs=hashlib.md5(f"{cp}{self._g}".encode()).hexdigest()[:4].upper()
  return cs==ecs
 def activate_license(self,key):
  lk=key.upper().strip()
  if not self._o(lk):return False
  d=self._n()or self._l()
  d['license_key']=lk;d['license_active']=True
  d['license_activated']=datetime.now().isoformat()
  self._p(d);return True
 def days_remaining(self):
  d=self._n()
  if not d:
   self._h();d=self._n()or self._l();self._p(d)
   return d.get('trial_days',15)
  if d.get('license_active')and d.get('license_key'):
   if self._o(d['license_key']):return-1
   else:d['license_active']=False;d['license_key']=None;self._p(d)
  try:
   fr=datetime.fromisoformat(d["first_run"])
   dp=(datetime.now()-fr).days
   td=d.get('trial_days',15)
   rm=td-dp
   return max(0,rm)if rm>=0 else 0
  except:return d.get('trial_days',15)
 def get_license_info(self):
  dl=self.days_remaining()
  d=self._n()or self._l()
  hv=bool(d.get('license_key')and self._o(d['license_key']))
  return{"is_activated":hv,"days_remaining":dl,"machine_id":self._a,"license_key":d.get('license_key',"")if hv else""}
 def is_trial_expired(self):
  dl=self.days_remaining()
  if dl==-1:return False
  return dl<=0
 def should_force_activation(self):
  i=self.get_license_info()
  if i["is_activated"]:return False
  return i["days_remaining"]<=0
 def save_run_data(self):
  d=self._n()
  if d:self._p(d)