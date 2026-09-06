import json,pathlib,re,hashlib,datetime,difflib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
read=lambda f:json.loads((ROOT/f).read_text(encoding='utf-8-sig'))
inputs=[read('research/'+n+'.json') for n in ['root','assets','agencies','portals']]
allrows=[x for d in inputs for x in d['listings']]
raw={('forsale-'+str(x['id'])):x.get('descriptionEn','') for x in read('research/forsale-all-raw.json')}
excluded=[dict(x) for d in inputs for x in d.get('exclusions',[])]
# Exact physical matches to originals explicitly withdrawn/sold: area PLUS verified description/ref.
removed_areas={846:'Altamira PR33491: η αρχική σελίδα δηλώνει μη διαθέσιμο.',4534:'Altamira PR37557: η αρχική σελίδα δηλώνει μη διαθέσιμο.',2174:'Altamira PR37706: η αρχική σελίδα δηλώνει μη διαθέσιμο.',1924:'Mayfair251160: SOLD στην αρχική σελίδα· ίδιο H4/45μ. πρόσβαση.',1868:'BuySell944535: πωλημένο. Η ενεργή αναδημοσίευση δεν επιβεβαιώθηκε.'}
rows=[]
for original in allrows:
 x=dict(original);a=x.get('area');rid=x['id']
 if a in removed_areas or rid=='buysellcyprus-1312464':
  excluded.append({'url':x['url'],'source':x['source'],'checkedAt':x['checkedAt'],'reason':removed_areas.get(a,'Βιομηχανική γη 6.439 τ.μ. εκτός οικιστικού σκοπού.'),'area':a});continue
 if x.get('type') in ['agricultural','industrial']:excluded.append({'url':x['url'],'reason':'Μη οικιστική γη','area':a});continue
 x['zone']=', '.join(dict.fromkeys(re.findall(r'[HΗΓΒΖA][0-9][α-ωa-z]?',str(x.get('zone') or '').replace('Η','H')))) or None
 x['titleOriginal']=x.get('title');x['title']=True if x.get('title') in [True,'stated','separate','Δηλώνεται διαθέσιμος τίτλος'] else (False if x.get('title') is False else None)
 x['vat']={'+ ΦΠΑ':'plus','Δεν εφαρμόζεται σύμφωνα με την αγγελία':'not_applicable','subject_unspecified':'Ενδέχεται να υπόκειται σε ΦΠΑ'}.get(x.get('vat'),x.get('vat'))
 x['availability']='appears_available' if x.get('availability') in ['appears_available','appears-listed'] else 'unconfirmed'
 own=x.get('ownership');x['ownershipOriginal']=own
 if isinstance(own,dict):
  isshare=(own.get('whole') is False or own.get('type') in ['undivided_share','share'] or (own.get('sharePercent') is not None and own['sharePercent']<100) or (own.get('share') not in [None,'1/1','100%']))
  whole=own.get('whole') is True or own.get('type')=='whole'
  x['ownership']='share' if isshare else 'whole' if whole else None
 else:x['ownership']=own if own in ['share','whole'] else None
 road=x.get('road')
 if isinstance(road,str):
  desc={'registered':'Εγγεγραμμένος δρόμος','right-of-way':'Δικαίωμα διάβασης','landlocked':'Περίκλειστο','asphalt':'Ασφαλτοστρωμένος δρόμος· εγγραφή ανεπιβεβαίωτη','access-stated':'Πρόσβαση κατά την αγγελία· εγγραφή ανεπιβεβαίωτη'}.get(road,road)
  road={'description':desc,'registered':True if road=='registered' or (rid.startswith('remu') and rid!='remu-16963' and 'Εγγεγραμμένος' in road) else None,'landlocked':True if road=='landlocked' or 'Περίκλειστο' in road else None,'rightOfWay':True if road=='right-of-way' else None,'asphalt':True if road=='asphalt' else None}
 x['road']=road or {}
 c=x.get('coordinates')
 if isinstance(c,dict):
  lat=c.get('lat',c.get('latitude'));lng=c.get('lng',c.get('longitude',c.get('lon')))
  x['coordinates']={'lat':lat,'lng':lng,'accuracy':'exact' if c.get('accuracy') in ['exact','published_exact'] else 'approximate','note':c.get('note') or 'Δημοσιευμένη πινέζα αγγελίας· δεν επιβεβαιώθηκε κτηματολογικά.'} if lat and lng else None
 else:x['coordinates']=None
 if rid.startswith('altamira-') and x['coordinates']: x['coordinates']['accuracy']='published'
 if rid.startswith('altia-') and x['coordinates']:x['coordinates']['accuracy']='published'
 # Source claims remain available; sale-area conversion is explicit and independently recorded.
 extra=x.get('extraFacts') or {};x['extraFacts']=extra
 sharearea=(own.get('shareArea') if isinstance(own,dict) else None) or extra.get('Εμβαδό μεριδίου όπως αναφέρεται')
 x['advertisedArea']=a
 if x['ownership']=='share' and isinstance(sharearea,(int,float)) and sharearea>10:x['area']=sharearea
 if a==6299 and x['ownership']=='share':x['area']=1049;x['extraFacts']['Εμβαδό μεριδίου όπως αναφέρεται']=1049
 if a in [15004,7502]:x['ownership']='share';x['area']=7502
 if a in [3950,1975]:x['ownership']='share';x['area']=1975
 if a==5779:x['ownership']='share';x['area']=3302
 if a in [1933,11605]:x['type']='field'
 x['rawDescription']=raw.get(rid) or x.get('sourceDescription') or x.get('rawEvidence') or ''
 if not isinstance(x['rawDescription'],str):x['rawDescription']=' '.join(map(str,x['rawDescription']))
 if a==3679:x['availability']='unconfirmed';x.setdefault('conflicts',[]).append('Αντίστοιχη αγγελία INDEX.cy αποσύρθηκε. Άλλες πηγές εξακολουθούν να το διαφημίζουν· απαιτείται επιβεβαίωση.')
 # Preserve explicit absence of access even when the text discusses a possible future easement.
 if re.search(r'\bno access\b|without (?:direct )?access|no direct access',x['rawDescription'],re.I):
  x['road']['landlocked']=True;x['road']['registered']=False;x['road']['description']='Χωρίς άμεση πρόσβαση. Τυχόν μελλοντικό δικαίωμα διάβασης χρειάζεται εξασφάλιση.'
 if rid in ['forsale-423532','buysellcyprus-9147531']:x['road']['description']='Δηλώνεται άμεση οδική πρόσβαση. Η εγγραφή του δρόμου δεν επιβεβαιώνεται.'
 if rid=='forsale-245472':x['floors']=2
 if x.get('areaBasis')=='ambiguous_share_or_whole':x['pricePerSquareMetre']=None
 rows.append(x)
# Deduplication uses explicit physical signatures and source text. Area alone never joins records.
parent={x['id']:x['id'] for x in rows};byid={x['id']:x for x in rows};decisions=[]
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
def join(a,b,why):
 if a not in parent or b not in parent:return
 ra,rb=find(a),find(b)
 if ra!=rb:parent[rb]=ra;decisions.append({'a':a,'b':b,'reason':why})
def norm(t):return re.sub(r'\W+',' ',t.casefold()).strip()
for i,a in enumerate(rows):
 for b in rows[i+1:]:
  if a['area']!=b['area']:continue
  aa,bb=norm(a['rawDescription']),norm(b['rawDescription'])
  if len(aa)>100 and len(bb)>100 and (aa==bb or difflib.SequenceMatcher(None,aa,bb).ratio()>.77):join(a['id'],b['id'],'Ίδιο εμβαδό και ουσιαστικά ίδια λεπτομερής περιγραφή αρχικής αγγελίας.')
  fp=a.get('descriptionFingerprint')
  if fp and fp==b.get('descriptionFingerprint'):join(a['id'],b['id'],'Ίδια πλήρης περιγραφή, ίδιο εμβαδό.')
  ref=a.get('providerReference')
  if ref and ref==b.get('providerReference'):join(a['id'],b['id'],'Ίδιος δημοσιευμένος κωδικός πωλητή και εμβαδό: '+ref)
# Reviewed distinctive signatures, not generic equal-area rules.
signatures={521:('32','Γωνιακό οικόπεδο H3, δύο συγκεκριμένοι δρόμοι, συνολική πρόσοψη32μ.'),537:('22','H2,22μ. πρόσοψη σε αδιέξοδο,240μ. δυτικά δημοτικού,PR42579.'),11605:('165','Δύο χωράφια11420+185τμ.,προσόψεις165+38μ.,REMU17014.'),1933:('100','Περίκλειστο H4,100μ. από δρόμο,95μ. ανατολικά Ανάγειας–Εργατών,6/152.'),1975:('57','Μερίδιο1/2 του3950τμ.,πρόσοψη57μ.,παλαιές μεταλλικές κατασκευές,PR36973.'),7502:('75','Μερίδιο1/2 του15004τμ.,πρόσοψη75μ.,620μ. βόρεια του κέντρου.'),3830:('98','3830τμ. οικιστική γη με98μ. πρόσοψη.'),2277:('5','Ίδια περιγραφή21finder45400,2277τμ.H3,πρόσοψη5μ.,υπηρεσίες και τίτλος.')}
for area,(token,why) in signatures.items():
 matches=[x for x in rows if x['area']==area and (token in x['rawDescription'] or x['road'].get('frontage')==int(token))]
 for x in matches[1:]:join(matches[0]['id'],x['id'],why)
# Same provider's syndication for very distinctive canonical records whose abbreviated versions omit a measurement.
for area,why in [(521,'H3 γωνιακό οικόπεδο521τμ.,ίδιος τίτλος και περιγραφή δύο δρόμων/Altia.'),(537,'ΠρωτότυποPR42579 και αναδημοσιεύσεις ίδιου τεμαχίου537τμ./αδιέξοδο/22μ.'),(1933,'Ίδια περιγραφή περίκλειστου H4 τεμαχίου1933τμ.100μ. από δρόμο.'),(11605,'Ίδιο πακέτο δύο τεμαχίων REMU17014 συνολικού εμβαδού11605τμ.')]:
 m=[x for x in rows if x['area']==area]
 for x in m[1:]:join(m[0]['id'],x['id'],why)
# Additional explicit researcher-reviewed joins.
for d in inputs:
 for h in d.get('deduplicationHints',[]):
  if h.get('confidence') in ['same-reference','strong']:
   for x in h['ids'][1:]:join(h['ids'][0],x,h['reason'])
for evidence_file in ['photo-dedupe.json','text-dedupe.json']:
 photo=ROOT/('research/'+evidence_file)
 if photo.exists():
  pdata=read('research/'+evidence_file)
 else:continue
 if pdata:
  for h in pdata.get('merges',[]):
   ids=h.get('ids',h.get('sourceIds',[]))
   for x in ids[1:]:join(ids[0],x,h.get('reason','Ταύτιση φωτογραφιών και χαρακτηριστικών.'))
   for f in h.get('facts',[]):
    if f['sourceID'] in byid:byid[f['sourceID']]['extraFacts'][f['field']]=f['value']
   for c in h.get('conflicts',[]):
    for sid in ids:
     if sid in byid:byid[sid].setdefault('conflicts',[]).append(c.get('noteGreek',str(c)))
    if c.get('field')=='ownership':
     for sid in ids:
      if sid in byid:byid[sid]['ownershipConflict']=True;byid[sid]['pricePerSquareMetre']=None;byid[sid]['areaBasis']='ambiguous_share_or_whole'
groups=collections.defaultdict(list)
for x in rows:groups[find(x['id'])].append(x)
properties=[]
for rid,ss in groups.items():
 # Deterministic source preference governs descriptive summary only; conflicting facts retain ALL values.
 ss.sort(key=lambda x:(0 if x['id'].startswith(('altamira','altia','remu')) else 1 if x['source'] not in ['ForSale.com.cy','BuySellCyprus','INDEX.cy'] else 2,x['id']))
 p={'id':'erg-'+hashlib.sha256(min(x['id'] for x in ss).encode()).hexdigest()[:9],'sources':[],'facts':{},'images':[],'duplicateEvidence':[d for d in decisions if find(d['a'])==find(rid)]}
 def fact(k,v,sid):
  if v is None or v=='' or v==[]:return
  v=v.replace('H','Η') if k=='zone' and isinstance(v,str) else v
  arr=p['facts'].setdefault(k,[]);existing=next((a for a in arr if a['value']==v),None)
  if existing:existing['sourceIds'].append(sid)
  else:arr.append({'value':v,'sourceIds':[sid]})
 for s in ss:
  clean={k:v for k,v in s.items() if k not in ['rawDescription','rawEvidence','sourceDescription','descriptionFingerprint']}
  p['sources'].append(clean)
  for k in ['price','area','type','zone','density','coverage','floors','height','title','vat','ownership','location','descriptionGreek']:
   fact(k,s.get(k),s['id'])
  for k,v in s['road'].items():fact('road.'+k,v,s['id'])
  for k,v in s['extraFacts'].items():fact('extra.'+k,v,s['id'])
  for u in s.get('images',[]):
   if isinstance(u,dict):u=u.get('url')
   if isinstance(u,str) and u.startswith('https://') and u not in [q['url'] for q in p['images']]:p['images'].append({'url':u,'sourceId':s['id']})
 p['type']='field' if any(s['type']=='field' for s in ss) else 'plot'
 p['isShare']=any(s['ownership']=='share' or s.get('ownershipConflict') for s in ss)
 p['landlocked']=any(s['road'].get('landlocked') is True for s in ss)
 p['registeredRoad']=any(s['road'].get('registered') is True for s in ss) and not p['landlocked']
 p['titleStated']=any(s['title'] is True for s in ss)
 p['availability']='appears_available' if any(s['availability']=='appears_available' for s in ss) else 'unconfirmed'
 p['warnings']=[]
 if p['isShare']:p['warnings'].append('Μερίδιο ακινήτου — δεν πωλείται ολόκληρο το τεμάχιο')
 if p['landlocked']:p['warnings'].append('Περίκλειστο — δεν δηλώνεται άμεση πρόσβαση σε δημόσιο δρόμο')
 elif not p['registeredRoad']:p['warnings'].append('Η εγγραφή / πρόσβαση του δρόμου χρειάζεται επιβεβαίωση')
 if any('Γ' in str(s.get('zone')) for s in ss):p['warnings'].append('Μικτή οικιστική και γεωργική ζώνη')
 if any(s['id']=='bazaraki-5980282' for s in ss):p['warnings'].append('Οικιστική ζώνη / οικοδομησιμότητα δεν επιβεβαιώνονται· η περιγραφή αναφέρει γεωργική χρήση και ελιές.')
 p['conflictFields']=[k for k in ['price','area','zone','density','coverage','floors','height','vat','road.registered','road.frontage','title','ownership','type'] if len(p['facts'].get(k,[]))>1]
 coords=[s['coordinates'] for s in ss if s.get('coordinates')]
 p['coordinateConflict']=any(abs(a['lat']-b['lat'])>.0003 or abs(a['lng']-b['lng'])>.0003 for a in coords for b in coords)
 p['exactCoordinates']=any(c['accuracy']=='exact' for c in coords)
 p['normalPlot']=p['type']=='plot' and p['registeredRoad'] and not p['isShare'] and not any('Γ' in str(s.get('zone')) for s in ss)
 p['needsReview']=bool(p['warnings'])
 properties.append(p)
cachepath=ROOT/'research/image-cache.json'
cache=read('research/image-cache.json') if cachepath.exists() else {}
for p in properties:
 verified=[];seen={}
 for im in p['images']:
  c=cache.get(im['url'],{})
  if c.get('error'):continue
  key=c.get('path',im['url'])
  if key in seen:seen[key]['sourceIds']=list(dict.fromkeys(seen[key]['sourceIds']+[im['sourceId']]));continue
  im['sourceIds']=[im['sourceId']]
  if c.get('path'):im.update({'localPath':c['path'],'width':c['width'],'height':c['height']})
  verified.append(im);seen[key]=im
 p['images']=verified
properties.sort(key=lambda p:p['id'])
coverage=[x for d in inputs for x in d.get('coverage',[])]
# Aggregate discovery counts count distinct ORIGINAL URLs, not inflated portal headline totals.
urls=set(s['url'] for s in allrows)|set(x['url'] for x in excluded if x.get('url'))
meta={'checkedAt':max(s['checkedAt'] for s in allrows),'timezone':'Asia/Nicosia','discoveredListings':len(urls),'includedSourceListings':sum(len(p['sources']) for p in properties),'uniqueProperties':len(properties),'normalResidentialPlots':sum(p['normalPlot'] for p in properties),'allPlots':sum(p['type']=='plot' for p in properties),'residentialFields':sum(p['type']=='field' for p in properties),'landlocked':sum(p['landlocked'] for p in properties),'shares':sum(p['isShare'] for p in properties),'exactCoordinates':sum(p['exactCoordinates'] for p in properties),'titleDeedsStated':sum(p['titleStated'] for p in properties),'coverage':coverage,'scopeNote':'Ερευνητικό στιγμιότυπο δημόσιων αγγελιών, όχι εγγύηση διαθεσιμότητας ή οικοδομησιμότητας. Οι περιορισμοί πρόσβασης σε πηγές δεν επιτρέπουν βεβαίωση ότι καλύφθηκαν ΟΛΑ τα διαθέσιμα ακίνητα. Δεν έγινε τηλεφωνική επιβεβαίωση ή επίσκεψη.','excluded':excluded,'provenance':'Κάθε facts[field] περιέχει value και sourceIds. Κάθε source περιέχει πρωτότυπο URL, website και checkedAt. Derived flags/€/m² προκύπτουν από αυτά, όχι ανεξάρτητη πιστοποίηση.'}
(ROOT/'data/properties.json').write_text(json.dumps({'meta':meta,'properties':properties},ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'research/group-review.json').write_text(json.dumps([{'id':p['id'],'area':[v['value'] for v in p['facts'].get('area',[])],'prices':[v['value'] for v in p['facts'].get('price',[])],'type':p['type'],'ids':[s['id'] for s in p['sources']]} for p in properties],ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in meta.items() if k not in ['coverage','excluded','scopeNote','provenance']},ensure_ascii=False))
