import cv2
import mediapipe as mp
import random, time, math, os, threading, queue, subprocess, winsound
import numpy as np

# ============================================================
# MAGIC MIRROR 5.0 - POWER RUSH
# Python 3.13 + MediaPipe 1.0.0 + OpenCV 5.x
# Keep hand_landmarker.task beside this file.
# Q = quit, R = reset
# ============================================================

CAMERA_INDEX = 0
HAND_MODEL = "hand_landmarker.task"
SCAN_TIME = 3.5
ROUND_TIME = 30
TARGETS_TO_WIN = 10
MAX_HANDS = 6
FACE_MATCH_DISTANCE = 170
PERSON_TIMEOUT = 1.8
PALM_COOLDOWN = 0.55
PROJECTILE_SPEED = 850.0
TARGET_RADIUS = 28
WINDOW = "MAGIC MIRROR - POWER RUSH"

WHITE=(245,245,255); BLACK=(5,5,15); CYAN=(255,230,60)
PURPLE=(255,70,210); BLUE=(255,150,50); GREEN=(80,255,150)
YELLOW=(0,240,255); RED=(70,70,255); ORANGE=(0,130,255)
ICE=(255,245,200); GRAY=(110,110,120)

POWERS=[
    ("FIRE MASTER",ORANGE),
    ("WATER MASTER",BLUE),
    ("WEB MASTER",WHITE),
    ("LIGHTNING POWER",YELLOW),
    ("ENERGY BLAST",PURPLE),
    ("LASER POWER",RED),
    ("ICE MASTER",ICE),
    ("COSMIC POWER",CYAN),
]

# ---------------- voice ----------------
voice_q=queue.Queue(); voice_running=True
def speak_windows(s):
    try:
        s=s.replace("'","''")
        cmd=("Add-Type -AssemblyName System.Speech; "
             "$x=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
             "$x.Rate=0;$x.Volume=100;"+f"$x.Speak('{s}');$x.Dispose();")
        subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass",
                        "-Command",cmd],stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception: pass
def voice_worker():
    while voice_running:
        try: s=voice_q.get(timeout=.2)
        except queue.Empty: continue
        if s is None: break
        speak_windows(s); voice_q.task_done()
threading.Thread(target=voice_worker,daemon=True).start()
def speak(s): voice_q.put(s)

# ---------------- sound ----------------
sound_q=queue.Queue(); sound_running=True
def tones(kind):
    notes={
        "scan":[(500,70),(650,70),(800,70),(1000,110)],
        "complete":[(700,70),(900,70),(1150,80),(1450,170)],
        "power":[(850,45),(1100,55),(1450,100)],
        "hit":[(1000,40),(1350,50),(1700,80)],
        "win":[(800,70),(1000,70),(1250,70),(1500,80),(1800,160)],
    }.get(kind,[])
    for f,d in notes:
        try: winsound.Beep(f,d)
        except Exception: pass
def sound_worker():
    while sound_running:
        try: s=sound_q.get(timeout=.2)
        except queue.Empty: continue
        if s is None: break
        tones(s); sound_q.task_done()
threading.Thread(target=sound_worker,daemon=True).start()
def sound(s): sound_q.put(s)

# ---------------- camera / face ----------------
cap=cv2.VideoCapture(CAMERA_INDEX,cv2.CAP_DSHOW)
if not cap.isOpened(): raise SystemExit("Camera could not be opened. Try CAMERA_INDEX = 1.")
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280); cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
face_detector=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
if face_detector.empty(): raise SystemExit("Face detector could not be loaded.")

# ---------------- MediaPipe 1.0.0 Tasks API ----------------
if not os.path.exists(HAND_MODEL):
    cap.release()
    raise SystemExit("Missing hand_landmarker.task. Put it beside main.py.")

try:
    BaseOptions=mp.tasks.BaseOptions
    RunningMode=mp.tasks.vision.RunningMode
    HandLandmarker=mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions=mp.tasks.vision.HandLandmarkerOptions
    opts=HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL),
        running_mode=RunningMode.VIDEO,
        num_hands=MAX_HANDS,
        min_hand_detection_confidence=.35,
        min_hand_presence_confidence=.35,
        min_tracking_confidence=.35)
    landmarker=HandLandmarker.create_from_options(opts)
except Exception as e:
    cap.release()
    raise SystemExit("Could not initialize MediaPipe HandLandmarker.\n"+str(e))

people={}; next_id=1; timestamp=0

def center(face):
    x,y,w,h=face; return (x+w//2,y+h//2)
def distance(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def power():
    n,c=random.choice(POWERS); return {"name":n,"color":c}
def target(w,h,face):
    fx,fy,fw,fh=face
    for _ in range(30):
        x=random.randint(70,max(71,w-70)); y=random.randint(125,max(126,h-100))
        if distance((x,y),(fx+fw//2,fy+fh//2))>170:
            return {"x":x,"y":y,"r":TARGET_RADIUS}
    return {"x":w//2,"y":h//2,"r":TARGET_RADIUS}

def new_person(face,w,h):
    global next_id
    p={"id":next_id,"face":face,"center":center(face),"last_seen":time.time(),
       "power":None,"scanned":False,"scan_start":time.time(),"voice_done":False,
       "started":False,"finished":False,"game_start":0,"score":0,"hits":0,"combo":0,
       "target":None,"shots":[],"particles":[],"last_palm":None,"last_fire":0,
       "flash":0}
    people[next_id]=p; next_id+=1; return p

def get_person(face,w,h):
    c=center(face); best=None; bd=1e9
    for p in people.values():
        d=distance(c,p["center"])
        if d<FACE_MATCH_DISTANCE and d<bd: best,bd=p,d
    if best is None: return new_person(face,w,h)
    best["face"]=face; best["center"]=(int(best["center"][0]*.65+c[0]*.35),
                                       int(best["center"][1]*.65+c[1]*.35))
    best["last_seen"]=time.time(); return best

def cleanup():
    now=time.time()
    for pid in [i for i,p in people.items() if now-p["last_seen"]>PERSON_TIMEOUT]:
        del people[pid]

# ---------------- drawing ----------------
def put(f,s,pos,size=.6,color=WHITE,th=2,centered=False):
    font=cv2.FONT_HERSHEY_SIMPLEX
    if centered:
        (tw,thh),_=cv2.getTextSize(s,font,size,th); pos=(pos[0]-tw//2,pos[1])
    cv2.putText(f,s,pos,font,size,color,th,cv2.LINE_AA)

def corners(f,x,y,w,h,c):
    L=20
    for a,b in [((x,y),(x+L,y)),((x,y),(x,y+L)),
                ((x+w,y),(x+w-L,y)),((x+w,y),(x+w,y+L)),
                ((x,y+h),(x+L,y+h)),((x,y+h),(x,y+h-L)),
                ((x+w,y+h),(x+w-L,y+h)),((x+w,y+h),(x+w,y+h-L))]:
        cv2.line(f,a,b,c,2,cv2.LINE_AA)

def draw_face(f,p):
    x,y,w,h=p["face"]; c=CYAN if not p["scanned"] else GREEN
    cv2.rectangle(f,(x,y),(x+w,y+h),c,2); corners(f,x,y,w,h,c)
    put(f,f'SUBJECT {p["id"]:02d}',(x,max(28,y-9)),.5,c,2)
    if p["power"]: put(f,p["power"]["name"],(x,y+h+23),.5,p["power"]["color"],2)

def draw_scan(f,p):
    x,y,w,h=p["face"]; t=time.time()-p["scan_start"]
    sy=int(y+(t*190)%max(h,1))
    cv2.line(f,(x,sy),(x+w,sy),CYAN,3); cv2.rectangle(f,(x,y),(x+w,y+h),CYAN,2)
    put(f,"SCANNING AURA...",(x,max(30,y-12)),.48,CYAN,2)

def draw_target(f,t):
    if not t:return
    x,y,r=t["x"],t["y"],t["r"]; pulse=int(5*math.sin(time.time()*7))
    cv2.circle(f,(x,y),r+13+pulse,RED,2); cv2.circle(f,(x,y),r,RED,3)
    cv2.circle(f,(x,y),7,WHITE,-1)
    cv2.line(f,(x-r-10,y),(x+r+10,y),RED,1); cv2.line(f,(x,y-r-10),(x,y+r+10),RED,1)
    put(f,"TARGET",(x-32,y+r+24),.4,RED,1)

def draw_hud(f,active):
    h,w=f.shape[:2]
    overlay=f.copy(); cv2.rectangle(overlay,(0,0),(w,90),(5,8,18),-1)
    cv2.rectangle(overlay,(0,h-75),(w,h),(5,8,18),-1)
    cv2.addWeighted(overlay,.84,f,.16,0,f)
    cv2.line(f,(0,89),(w,89),CYAN,2); cv2.line(f,(0,h-75),(w,h-75),CYAN,2)
    put(f,"MAGIC MIRROR",(28,37),.85,CYAN,2); put(f,"POWER RUSH",(30,66),.46,WHITE,1)
    put(f,f"SUBJECTS // {len(people)}",(w-190,35),.43,GREEN,1)
    put(f,"AURA-X // ONLINE",(w-190,61),.43,CYAN,1)
    if active and active["scanned"]:
        put(f,f"P{active['id']:02d}  {active['power']['name']}",(25,h-43),.55,active["power"]["color"],2)
        put(f,f"SCORE {active['score']}",(410,h-43),.55,YELLOW,2)
        put(f,f"HITS {active['hits']}/{TARGETS_TO_WIN}",(590,h-43),.55,WHITE,2)
        left=max(0,int(ROUND_TIME-(time.time()-active["game_start"])))
        put(f,f"TIME {left}",(790,h-43),.55,GREEN,2)
        put(f,"OPEN PALM = ATTACK",(930,h-43),.45,CYAN,2)
    else: put(f,"STEP INTO THE MIRROR",(25,h-43),.55,CYAN,2)

# ---------------- hand ----------------
CONNECTIONS=[(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
             (5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
             (13,17),(17,18),(18,19),(19,20),(0,17)]

def points(landmarks,w,h):
    return [(max(0,min(w-1,int(a.x*w))),max(0,min(h-1,int(a.y*h)))) for a in landmarks]

def palm_center(pts):
    ids=(0,5,9,13,17); return (int(sum(pts[i][0] for i in ids)/5),int(sum(pts[i][1] for i in ids)/5))

def open_palm(pts):
    wrist=np.array(pts[0],dtype=float); n=0
    for tip,pip in ((8,6),(12,10),(16,14),(20,18)):
        if np.linalg.norm(np.array(pts[tip])-wrist)>np.linalg.norm(np.array(pts[pip])-wrist)*1.10: n+=1
    return n>=3

def draw_hand(f,pts,on):
    c=GREEN if on else CYAN
    for a,b in CONNECTIONS: cv2.line(f,pts[a],pts[b],c,2,cv2.LINE_AA)
    for q in pts: cv2.circle(f,q,3,c,-1)

def owner_for(palm):
    best=None; score=1e9
    for p in people.values():
        x,y,w,h=p["face"]; d=distance(palm,p["center"])
        inside=(x-int(w*1.2)<=palm[0]<=x+int(w*2.2) and
                y+int(h*.2)<=palm[1]<=y+int(h*4))
        s=d*.35 if inside else d
        if d<520 and s<score: best,score=p,s
    return best

def aim(pts):
    v=np.array(pts[12],dtype=float)-np.array(pts[0],dtype=float); n=np.linalg.norm(v)
    return v/n if n>1 else np.array([1.,0.])

# ---------------- effects ----------------
def particles(p,x,y,c,n=28):
    for _ in range(n):
        a=random.random()*math.tau; sp=random.uniform(50,260)
        p["particles"].append([x,y,math.cos(a)*sp,math.sin(a)*sp,time.time(),random.uniform(.35,.8),c])

def draw_shot(f,s):
    x,y=int(s["x"]),int(s["y"]); dx,dy=s["dx"],s["dy"]; end=(int(x+dx*230),int(y+dy*230))
    name=s["power"]
    if name=="FIRE MASTER":
        for i in range(12):
            t=i/12; bx=int(x+(end[0]-x)*t); by=int(y+(end[1]-y)*t)
            wob=math.sin(time.time()*15+i)*10; bx+=int(-dy*wob); by+=int(dx*wob)
            r=random.randint(5,12); cv2.circle(f,(bx,by),r,ORANGE,-1); cv2.circle(f,(bx,by),max(2,r//2),YELLOW,-1)
    elif name=="WATER MASTER":
        for i in range(20):
            t=i/20; bx=int(x+(end[0]-x)*t); by=int(y+(end[1]-y)*t)
            wob=math.sin(time.time()*12+i)*9; bx+=int(-dy*wob); by+=int(dx*wob)
            cv2.circle(f,(bx,by),random.randint(3,7),BLUE,-1)
    elif name=="WEB MASTER":
        cv2.line(f,(x,y),end,WHITE,2)
        ang=math.atan2(dy,dx)
        for r in (35,70,110,150,190): cv2.ellipse(f,(x,y),(r,max(8,int(r*.22))),math.degrees(ang),0,360,WHITE,1)
    elif name=="LIGHTNING POWER":
        pts=[(x,y)]
        for i in range(1,10):
            t=i/9; pts.append((int(x+(end[0]-x)*t+random.randint(-18,18)),int(y+(end[1]-y)*t+random.randint(-18,18))))
        for a,b in zip(pts,pts[1:]): cv2.line(f,a,b,YELLOW,5); cv2.line(f,a,b,WHITE,1)
    elif name=="LASER POWER":
        cv2.line(f,(x,y),end,RED,10); cv2.line(f,(x,y),end,WHITE,2)
    elif name=="ENERGY BLAST":
        cv2.line(f,(x,y),end,PURPLE,9); cv2.line(f,(x,y),end,WHITE,2)
        cv2.circle(f,(x,y),25+int(8*math.sin(time.time()*9)),PURPLE,3)
    elif name=="ICE MASTER":
        cv2.line(f,(x,y),end,ICE,5)
        for i in range(8):
            t=i/8; cv2.circle(f,(int(x+(end[0]-x)*t),int(y+(end[1]-y)*t)),random.randint(4,9),ICE,2)
    else:
        cv2.line(f,(x,y),end,CYAN,5); cv2.line(f,(x,y),end,PURPLE,2)
        cv2.ellipse(f,(x,y),(55,22),time.time()*60,0,360,CYAN,2)

def fire_shot(p,palm,d):
    p["shots"].append({"x":float(palm[0]),"y":float(palm[1]),"dx":float(d[0]),"dy":float(d[1]),
                       "born":time.time(),"power":p["power"]["name"]})

def update_game(f,p,dt):
    now=time.time()
    if p["started"] and not p["finished"] and now-p["game_start"]>=ROUND_TIME:
        p["finished"]=True; p["target"]=None
        speak(f"Player {p['id']}. Time is up. Your score is {p['score']}.")
    if p["started"] and not p["finished"] and p["target"]: draw_target(f,p["target"])

    keep=[]
    for s in p["shots"]:
        s["x"]+=s["dx"]*PROJECTILE_SPEED*dt; s["y"]+=s["dy"]*PROJECTILE_SPEED*dt
        draw_shot(f,s)
        hit=False
        if p["target"]:
            t=p["target"]
            hit=distance((s["x"],s["y"]),(t["x"],t["y"]))<t["r"]+25
        if hit:
            p["score"]+=100+min(p["combo"],9)*20; p["hits"]+=1; p["combo"]+=1; p["flash"]=now+.18
            sound("hit"); t=p["target"]; particles(p,t["x"],t["y"],p["power"]["color"],35)
            if p["hits"]>=TARGETS_TO_WIN:
                p["finished"]=True; p["target"]=None; sound("win")
                speak(f"Player {p['id']}. Power Rush complete. Your score is {p['score']}.")
            else: p["target"]=target(f.shape[1],f.shape[0],p["face"])
        elif now-s["born"]<1.7 and -100<s["x"]<f.shape[1]+100 and -100<s["y"]<f.shape[0]+100:
            keep.append(s)
    p["shots"]=keep

    pk=[]
    for q in p["particles"]:
        age=now-q[4]
        if age<q[5]:
            q[0]+=q[2]*dt; q[1]+=q[3]*dt; q[3]+=80*dt
            cv2.circle(f,(int(q[0]),int(q[1])),max(1,int(7*(1-age/q[5]))),q[6],-1)
            pk.append(q)
    p["particles"]=pk

    if p["flash"]>now: cv2.rectangle(f,(0,0),(f.shape[1]-1,f.shape[0]-1),WHITE,5)

    if p["finished"]:
        bw,bh=420,165; bx=(f.shape[1]-bw)//2; by=f.shape[0]//2-bh//2
        ov=f.copy(); cv2.rectangle(ov,(bx,by),(bx+bw,by+bh),BLACK,-1); cv2.addWeighted(ov,.9,f,.1,0,f)
        cv2.rectangle(f,(bx,by),(bx+bw,by+bh),CYAN,2)
        put(f,"ROUND COMPLETE" if p["hits"]>=TARGETS_TO_WIN else "TIME UP",(f.shape[1]//2,by+48),.9,GREEN if p["hits"]>=TARGETS_TO_WIN else RED,3,True)
        put(f,f"SCORE  {p['score']}",(f.shape[1]//2,by+92),.72,YELLOW,2,True)
        put(f,"STEP AWAY FOR NEXT PLAYER",(f.shape[1]//2,by+132),.48,WHITE,1,True)

# ============================================================
# MAIN
# ============================================================

print("==========================================")
print("          MAGIC MIRROR 5.0")
print("             POWER RUSH")
print("==========================================")
print("MediaPipe Tasks API ACTIVE")
print("Q = quit | R = reset")
print()

cv2.namedWindow(WINDOW,cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WINDOW,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

last=time.time()
try:
    while True:
        ok,frame=cap.read()
        if not ok: continue
        frame=cv2.flip(frame,1); h,w=frame.shape[:2]
        now=time.time(); dt=min(.05,now-last); last=now

        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        faces=face_detector.detectMultiScale(gray,1.08,6,minSize=(80,80))
        current=[get_person(fc,w,h) for fc in faces]
        cleanup()

        for p in current:
            draw_face(frame,p)
            if not p["scanned"]:
                draw_scan(frame,p)
                if now-p["scan_start"]>=SCAN_TIME:
                    p["power"]=power(); p["scanned"]=True; p["started"]=True
                    p["game_start"]=now; p["target"]=target(w,h,p["face"])
                    sound("complete")
                    if not p["voice_done"]:
                        p["voice_done"]=True
                        speak(f"Subject {p['id']}. Your superpower is {p['power']['name']}.")

        # NEW MediaPipe Tasks API -- no mp.solutions
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image=mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
        timestamp=max(timestamp+1,int(now*1000))
        try: result=landmarker.detect_for_video(image,timestamp)
        except Exception as e:
            print("Hand detection error:",e); result=None

        if result:
            for lm in result.hand_landmarks:
                pts=points(lm,w,h); palm=palm_center(pts); p=owner_for(palm)
                if p is None:
                    draw_hand(frame,pts,False); continue
                if not p["scanned"] or p["finished"]:
                    draw_hand(frame,pts,False); continue

                if p["last_palm"] is None: p["last_palm"]=palm
                else: p["last_palm"]=(int(.65*p["last_palm"][0]+.35*palm[0]),
                                      int(.65*p["last_palm"][1]+.35*palm[1]))
                palm=p["last_palm"]
                op=open_palm(pts); draw_hand(frame,pts,op)
                cv2.circle(frame,palm,18+int(4*math.sin(now*8)),GREEN if op else CYAN,2)

                if op:
                    put(frame,"OPEN PALM",(palm[0]-42,palm[1]-28),.4,GREEN,2)
                    if now-p["last_fire"]>=PALM_COOLDOWN:
                        fire_shot(p,palm,aim(pts)); p["last_fire"]=now; sound("power")
                else:
                    put(frame,"RAISE PALM",(palm[0]-42,palm[1]-28),.4,GRAY,1)

        for p in current:
            if p["scanned"]: update_game(frame,p,dt)

        active=next((p for p in sorted(current,key=lambda x:x["id"]) if p["scanned"] and not p["finished"]),None)
        if active is None and current: active=current[0]
        draw_hud(frame,active)

        if not current:
            put(frame,"STEP INTO THE MIRROR",(w//2,h//2),1.05,CYAN,3,True)
            put(frame,"SCAN  •  DISCOVER  •  USE YOUR POWER",(w//2,h//2+48),.58,WHITE,2,True)

        put(frame,"Q QUIT",(18,120),.4,WHITE,1)
        put(frame,"R RESET",(18,144),.4,WHITE,1)
        cv2.imshow(WINDOW,frame)

        key=cv2.waitKey(1)&0xFF
        if key==ord("q"): break
        if key==ord("r"):
            for p in people.values():
                if p["scanned"]:
                    p["started"]=True; p["finished"]=False; p["game_start"]=time.time()
                    p["score"]=p["hits"]=p["combo"]=0; p["shots"].clear(); p["particles"].clear()
                    p["target"]=target(w,h,p["face"])
finally:
    try: landmarker.close()
    except Exception: pass
    cap.release(); cv2.destroyAllWindows()
    voice_running=False; sound_running=False
    voice_q.put(None); sound_q.put(None)
    print("Magic Mirror closed.")
