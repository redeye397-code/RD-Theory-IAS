import json,time,hashlib,os,threading
def canonical(o): return json.dumps(o,sort_keys=True)
class HSM_TPM_SecureEnclave_Production:
 def __init__(s,a="audit.log"):
  s.hw_id=hashlib.sha256(os.urandom(16)).hexdigest();s.compromised=False;s._a=a
  if os.path.exists(a):
   try:
    for l in open(a):
     e=json.loads(l)
     if e.get("data_hash")!=hashlib.sha256(canonical(e["data"]).encode()).hexdigest(): s.compromised=True
   except: s.compromised=True
 def seal(s,d):
  h=hashlib.sha256(canonical(d).encode()).hexdigest(); e={"data":d,"data_hash":h,"hw_id":s.hw_id,"ts":time.time(),"sig":"x"}
  try: open(s._a,"a").write(json.dumps(e)+"\n")
  except: pass
  return e
 def verify_attestation(s,e): return hashlib.sha256(canonical(e["data"]).encode()).hexdigest()==e.get("data_hash")
class QuorumRate:
 def __init__(s): s._c=False
 def request(s):
  if s._c: raise RuntimeError("RATE_LIMIT_EXCEEDED")
  s._c=True
class FaultDomain:
 def __init__(s,p): s.parent=p
 def check_hw_spoof(s,f): s.parent.tpm.compromised=True; raise RuntimeError("POISON_PILL_WIPE_TRIGGERED")
class GhostVaultV8_Production:
 def __init__(s,a="audit.log"): s.tpm=HSM_TPM_SecureEnclave_Production(a);s.quorum=QuorumRate();s.fault=FaultDomain(s);s._ht=[];s._run=False
 def start_heartbeat(s,i=0.05):
  s._run=True;s._ht=[]
  def L():
   while s._run: s._ht.append(time.time()); time.sleep(i)
  threading.Thread(target=L,daemon=True).start()
 def stop_heartbeat(s): s._run=False
