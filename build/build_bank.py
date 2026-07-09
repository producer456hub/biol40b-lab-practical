# -*- coding: utf-8 -*-
"""Final bank builder: uses verified tip#->label maps (teacher-exact tips) +
manual pins. Exports clean panel images and writes questions.js for the app."""
import fitz, os, json
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\produ\Downloads\prelab 1 study"
PDFS = {"nervecells":"Lab 1-4 Nervous system (histology).pdf","sense":"Sense Organs histology-1 (1).pdf",
        "motor":"Motor end plate (histology).pdf","pns":"histology slides-1.pdf"}
OUT_IMG = r"C:\Users\produ\biol40b-practical\images"
OUT_QA  = r"C:\Users\produ\biol40b-practical\build\finalqa"
os.makedirs(OUT_IMG, exist_ok=True); os.makedirs(OUT_QA, exist_ok=True)

# accepted-answer variants (strict spelling, legit synonyms accepted)
A = {
 "epineurium":["epineurium"],"perineurium":["perineurium"],"endoneurium":["endoneurium"],
 "myelin sheath":["myelin sheath","myelin"],"axons":["axon","axons"],
 "posterior/dorsal root":["posterior root","dorsal root","posterior/dorsal root"],
 "posterior/dorsal grey horn":["posterior grey horn","dorsal grey horn","posterior gray horn","dorsal gray horn"],
 "posterior/dorsal root ganglion":["dorsal root ganglion","posterior root ganglion","drg","posterior/dorsal root ganglion"],
 "central canal":["central canal"],"anterior median fissure":["anterior median fissure"],
 "posterior median sulcus":["posterior median sulcus"],"arachnoid membrane":["arachnoid membrane","arachnoid","arachnoid mater"],
 "anterior grey horn":["anterior grey horn","anterior gray horn","ventral grey horn","ventral horn"],
 "posterior grey horn":["posterior grey horn","posterior gray horn","dorsal grey horn"],
 "ependymal cells":["ependymal cell","ependymal cells","ependymal"],
 "grey matter":["grey matter","gray matter"],"white matter":["white matter"],
 "choroid plexus":["choroid plexus"],"folia":["folia","folium"],
 "molecular layer":["molecular layer"],"granular layer":["granular layer"],"purkinje cells":["purkinje cell","purkinje cells","purkinje"],
 "sulcus":["sulcus"],"gyrus":["gyrus"],
 "motor nerve axon":["motor nerve axon","motor nerve","motor axon"],"axon terminal":["axon terminal"],
 "motor end plate":["motor end plate","end plate","motor endplate"],"synaptic end bulb":["synaptic end bulb","synaptic bulb","end bulb"],
 "myofiber":["myofiber","muscle fiber","muscle cell","myofibre"],
 "exterior surface":["exterior surface"],"interior surface":["interior surface"],"orbicularis oris":["orbicularis oris"],
 "ciliary body":["ciliary body"],"retina":["retina"],"pupil":["pupil"],"cornea":["cornea"],
 "anterior chamber":["anterior chamber"],"iris":["iris"],"sclera":["sclera"],"optic nerve":["optic nerve"],
 "axon":["axon"],"axon hillock":["axon hillock"],
 "chromatophilic substance":["chromatophilic substance","nissl body","nissl bodies","chromatophilic substances"],
 "nucleolus":["nucleolus"],"nucleus":["nucleus"],"dendrites":["dendrite","dendrites"],
}
# whole-slide answers
def wholeacc(v): return v

# panel source per slide
PANEL = {"nerve_v1":("pns",1,0),"nerve_v2":("pns",2,0),"nerve_v3":("pns",3,0),
 "sc27_over":("pns",5,0),"sc27_cc":("pns",6,0),"sc28_over":("pns",7,0),"sc28_cc":("pns",9,0),
 "cbl_over":("pns",10,0),"cbl_r2":("pns",13,0),"cerebrum":("pns",14,0),
 "nmj":("motor",5,1),"lip":("motor",1,0),"eye":("sense",1,0),"motorneuron":("nervecells",6,0)}

TITLE = {"nerve_v1":"Peripheral Nerve, osmium stain (low power)","nerve_v2":"Peripheral Nerve, osmium stain (medium)",
 "nerve_v3":"Peripheral Nerve, osmium stain (enlarged)","sc27_over":"Spinal Cord with Dorsal Root Ganglion (slide #27)",
 "sc27_cc":"Spinal Cord #27 — central canal (enlarged)","sc28_over":"Spinal Cord, silver stain (slide #28)",
 "sc28_cc":"Spinal Cord, silver #28 — central canal","cbl_over":"Cerebellum (slide #30)",
 "cbl_r2":"Cerebellum #30 — cortex layers","cerebrum":"Cerebrum (slide #31)",
 "nmj":"Neuromuscular Junction (slide #25, 400x)","lip":"Lip (slide #53)","eye":"Monkey Eye (slide #36)",
 "motorneuron":"Motor Neuron — enhanced view"}
WHOLE = {"nerve_v1":["nerve","peripheral nerve"],"nerve_v2":["nerve","peripheral nerve"],"nerve_v3":["nerve","peripheral nerve"],
 "sc27_over":["spinal cord","spinal cord ganglion"],"sc27_cc":["spinal cord"],"sc28_over":["spinal cord"],"sc28_cc":["spinal cord"],
 "cbl_over":["cerebellum"],"cbl_r2":["cerebellum"],"cerebrum":["cerebrum"],
 "nmj":["neuromuscular junction","nmj"],"lip":["lip"],"eye":["eye","eyeball"],"motorneuron":["motor neuron","neuron"]}

# verified tip#->label maps; ("m",fx,fy) = manual pin
MAP = {
 "nerve_v1":{"epineurium":1,"perineurium":2},
 "nerve_v2":{"perineurium":2,"endoneurium":1},
 "nerve_v3":{"myelin sheath":3,"endoneurium":2,"axons":5},
 "sc27_over":{"anterior median fissure":1,"posterior/dorsal root ganglion":2,"arachnoid membrane":3,
   "posterior/dorsal root":4,"anterior grey horn":5,"posterior/dorsal grey horn":6,"central canal":7},
 "sc27_cc":{"ependymal cells":1,"central canal":("m",0.62,0.55)},
 "sc28_over":{"posterior median sulcus":1,"posterior grey horn":4,"central canal":2,"anterior grey horn":3,"anterior median fissure":5},
 "sc28_cc":{"ependymal cells":1,"central canal":("m",0.45,0.5)},
 "cbl_over":{"choroid plexus":7,"white matter":4,"grey matter":3,"folia":5},
 "cbl_r2":{"white matter":4,"molecular layer":2,"granular layer":3},
 "cerebrum":{"grey matter":1,"sulcus":3,"gyrus":2,"white matter":("m",0.35,0.30)},
 "nmj":{"motor nerve axon":1,"axon terminal":5,"motor end plate":2,"synaptic end bulb":3,"myofiber":4},
 "lip":{"exterior surface":3,"orbicularis oris":1,"interior surface":2},
 "eye":{"ciliary body":5,"retina":7,"cornea":3,"anterior chamber":2,"pupil":4,"iris":6,"sclera":9,"optic nerve":8},
 "motorneuron":{"axon":3,"axon hillock":4,"nucleus":1,"nucleolus":8,"chromatophilic substance":5,"dendrites":6},
}

tips = json.load(open(r"C:\Users\produ\biol40b-practical\build\tips.json"))
docs = {k: fitz.open(os.path.join(SRC,v)) for k,v in PDFS.items()}
ext = json.load(open(r"C:\Users\produ\biol40b-practical\build\extracted.json",encoding="utf-8"))

bank=[]
for sid,(pdf,p0,panel) in PANEL.items():
    im = ext[pdf][p0]["images"][panel]
    doc = docs[pdf]; pix = fitz.Pixmap(doc, im["xref"])
    if pix.n>4: pix = fitz.Pixmap(fitz.csRGB, pix)
    pix.save(os.path.join(OUT_IMG, sid+".png")); IW,IH=pix.width,pix.height
    tipmap = {t[0]:(t[1],t[2]) for t in tips[sid]}
    pins=[]
    for label,ref in MAP[sid].items():
        if isinstance(ref,tuple) and ref[0]=="m": fx,fy=ref[1],ref[2]
        else: fx,fy=tipmap[ref]
        acc=list(A.get(label,[label]))
        if label not in acc: acc=[label]+acc          # the shown answer must always grade correct
        pins.append({"label":label,"accepted":acc,"x":round(fx,4),"y":round(fy,4)})
    bank.append({"id":sid,"title":TITLE[sid],"image":sid+".png","whole":WHOLE[sid],"pins":pins})

    # final QA overlay
    img=Image.open(os.path.join(OUT_IMG,sid+".png")).convert("RGB"); d=ImageDraw.Draw(img)
    try: f=ImageFont.truetype("arialbd.ttf",max(14,IW//38))
    except: f=ImageFont.load_default()
    for p in pins:
        px,py=p["x"]*IW,p["y"]*IH; r=max(7,IW//80)
        d.ellipse([px-r,py-r,px+r,py+r],outline=(255,30,30),width=3)
        d.text((px+r+2,py-r),p["label"],fill=(0,0,220),font=f,stroke_width=3,stroke_fill=(255,255,255))
    img.save(os.path.join(OUT_QA,sid+"_fqa.png"))

json.dump(bank, open(r"C:\Users\produ\biol40b-practical\build\bank.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
# emit questions.js for the app
with open(r"C:\Users\produ\biol40b-practical\questions.js","w",encoding="utf-8") as f:
    f.write("// Auto-generated question bank. Do not edit by hand.\n")
    f.write("const SLIDES = "+json.dumps(bank, ensure_ascii=False, indent=1)+";\n")
print(f"built {len(bank)} slides, {sum(len(s['pins']) for s in bank)} pins ->",
      "images/, questions.js")
for s in bank: print(f"  {s['id']:13s} {len(s['pins'])} pins")
