# -*- coding: utf-8 -*-
"""
Assign each arrow-tip to its label for the chosen slides, export clean cropped
images, emit the question bank (pins with image-fraction coords + accepted
answers), and render QA overlays for visual verification.
"""
import fitz, os, json, math, re, unicodedata

SRC = r"C:\Users\produ\Downloads\prelab 1 study"
PDFS = {
    "nervecells": "Lab 1-4 Nervous system (histology).pdf",
    "sense":      "Sense Organs histology-1 (1).pdf",
    "motor":      "Motor end plate (histology).pdf",
    "pns":        "histology slides-1.pdf",
}
OUT_IMG = r"C:\Users\produ\biol40b-practical\images"
OUT_QA  = r"C:\Users\produ\biol40b-practical\build\qa"
os.makedirs(OUT_IMG, exist_ok=True)
os.makedirs(OUT_QA, exist_ok=True)

# ---- accepted-answer variants per canonical label (strict spelling, synonyms ok)
ACCEPTED = {
    "epineurium": ["epineurium"],
    "perineurium": ["perineurium"],
    "endoneurium": ["endoneurium"],
    "myelin sheath": ["myelin sheath", "myelin"],
    "axons": ["axon", "axons"],
    "fascicle": ["fascicle"],
    "posterior/dorsal root": ["posterior root", "dorsal root", "posterior/dorsal root"],
    "posterior/dorsal grey horn": ["posterior grey horn","dorsal grey horn","posterior gray horn","dorsal gray horn","posterior horn","dorsal horn"],
    "posterior/dorsal root ganglion": ["dorsal root ganglion","posterior root ganglion","drg","posterior/dorsal root ganglion"],
    "central canal": ["central canal"],
    "anterior median fissure": ["anterior median fissure"],
    "posterior median sulcus": ["posterior median sulcus"],
    "arachnoid membrane": ["arachnoid membrane","arachnoid","arachnoid mater"],
    "anterior grey horn": ["anterior grey horn","anterior gray horn","anterior horn","ventral grey horn","ventral horn"],
    "posterior grey horn": ["posterior grey horn","posterior gray horn","dorsal grey horn","posterior horn"],
    "ependymal cells": ["ependymal cell","ependymal cells","ependymal"],
    "grey matter": ["grey matter","gray matter"],
    "white matter": ["white matter"],
    "choroid plexus": ["choroid plexus"],
    "folia": ["folia","folium"],
    "molecular layer": ["molecular layer"],
    "granular layer": ["granular layer"],
    "purkinje cells": ["purkinje cell","purkinje cells","purkinje"],
    "sulcus": ["sulcus"],
    "gyrus": ["gyrus"],
    "motor nerve axon": ["motor nerve axon","motor nerve","motor axon"],
    "axon terminal": ["axon terminal"],
    "motor end plate": ["motor end plate","end plate","motor endplate"],
    "synaptic end bulb": ["synaptic end bulb","synaptic bulb","end bulb"],
    "myofiber": ["myofiber","muscle fiber","muscle cell","myofibre"],
    "exterior surface": ["exterior surface"],
    "interior surface": ["interior surface"],
    "orbicularis oris": ["orbicularis oris"],
    "ciliary body": ["ciliary body"],
    "retina": ["retina"],
    "pupil": ["pupil"],
    "cornea": ["cornea"],
    "anterior chamber": ["anterior chamber"],
    "iris": ["iris"],
    "sclera": ["sclera"],
    "posterior chamber": ["posterior chamber"],
    "optic nerve": ["optic nerve"],
    "ganglion cells": ["ganglion cell","ganglion cells"],
    "bipolar cells": ["bipolar cell","bipolar cells"],
    "rods and cones": ["rods and cones","rods & cones","rods","cones","photoreceptors"],
    "pigment epithelium": ["pigment epithelium"],
    "optic disc": ["optic disc","optic disk","blind spot"],
    "spiral organ": ["spiral organ","organ of corti","spiral organ of corti"],
    "scala tympani": ["scala tympani"],
    "scala vestibuli": ["scala vestibuli","scala vestibule"],
    "cochlear duct": ["cochlear duct","scala media"],
    "spiral ganglion": ["spiral ganglion"],
    "hair cells": ["hair cell","hair cells"],
    "tectorial membrane": ["tectorial membrane"],
    "basilar membrane": ["basilar membrane"],
    "olfactory epithelium": ["olfactory epithelium"],
    "hyaline cartilage": ["hyaline cartilage"],
    "papillae": ["papilla","papillae"],
    "skeletal muscle": ["skeletal muscle"],
    "taste buds": ["taste bud","taste buds"],
    "gustatory cell": ["gustatory cell","gustatory cells","taste cell"],
    "meissners corpuscle": ["meissner's corpuscle","meissners corpuscle","meissner corpuscle","tactile corpuscle","meissner's","meissners"],
    "epidermis": ["epidermis"],
    "dermis": ["dermis"],
    "pacinian corpuscle": ["pacinian corpuscle","lamellated corpuscle","pacinian","lamellar corpuscle"],
    "axon": ["axon"],
    "axon hillock": ["axon hillock"],
    "chromatophilic substance": ["chromatophilic substance","nissl body","nissl bodies","chromatophilic substances"],
    "nucleolus": ["nucleolus"],
    "nucleus": ["nucleus"],
    "dendrites": ["dendrite","dendrites"],
}

# ---- slides: (id, title, pdf, page0, panel_index, whole_answer_variants, [(canonical,label, anchor_token)...])
S = []
def slide(id,title,pdf,p0,panel,whole,pins,manual=None):
    S.append(dict(id=id,title=title,pdf=pdf,p0=p0,panel=panel,whole=whole,pins=pins,manual=manual or []))

slide("nerve_v1","Peripheral Nerve (osmium) — low power","pns",1,0,
      ["nerve","peripheral nerve"],
      [("epineurium","epineurium"),("perineurium","perineurium")])
slide("nerve_v2","Peripheral Nerve (osmium) — medium","pns",2,0,
      ["nerve","peripheral nerve"],
      [("perineurium","perineurium"),("endoneurium","endoneurium")])
slide("nerve_v3","Peripheral Nerve (osmium) — enlarged","pns",3,0,
      ["nerve","peripheral nerve"],
      [("myelin sheath","myelin"),("endoneurium","endoneurium"),("axons","axons")])
slide("sc27_over","Spinal Cord w/ Ganglion (#27)","pns",5,0,
      ["spinal cord","spinal cord ganglion"],
      [("posterior/dorsal root","root"),("posterior/dorsal grey horn","grey"),
       ("posterior/dorsal root ganglion","ganglion"),("central canal","central"),
       ("anterior median fissure","fissure"),("arachnoid membrane","arachnoid"),
       ("anterior grey horn","anterior")])
slide("sc27_cc","Spinal Cord (#27) — central canal","pns",6,0,
      ["spinal cord"],
      [("ependymal cells","ependymal")],
      manual=[("central canal",0.62,0.55)])
slide("sc28_over","Spinal Cord, Silver (#28)","pns",7,0,
      ["spinal cord"],
      [("posterior median sulcus","sulcus"),("posterior grey horn","grey"),
       ("central canal","central"),("anterior median fissure","fissure"),
       ("anterior grey horn","anterior")])
slide("sc28_cc","Spinal Cord, Silver (#28) — central canal","pns",9,0,
      ["spinal cord"],
      [("ependymal cells","ependymal")],
      manual=[("central canal",0.45,0.5)])
slide("cbl_over","Cerebellum (#30)","pns",10,0,
      ["cerebellum"],
      [("grey matter","grey"),("choroid plexus","choroid"),
       ("folia","folia"),("white matter","white")])
slide("cbl_r2","Cerebellum (#30) — cortex layers","pns",13,0,
      ["cerebellum"],
      [("white matter","white"),("molecular layer","molecular"),("granular layer","granular")])
slide("cerebrum","Cerebrum (#31)","pns",14,0,
      ["cerebrum"],
      [("grey matter","grey"),("sulcus","sulcus"),("gyrus","gyrus")],
      manual=[("white matter",0.35,0.3)])
slide("nmj","Neuromuscular Junction (#25) — 400x","motor",5,1,
      ["neuromuscular junction","motor end plate","nmj"],
      [("motor nerve axon","motor"),("axon terminal","terminal"),
       ("motor end plate","plate"),("synaptic end bulb","bulb"),("myofiber","myofiber")])
slide("lip","Lip (#53)","motor",1,0,
      ["lip"],
      [("exterior surface","exterior"),("interior surface","interior"),
       ("orbicularis oris","skeletal")])
slide("eye","Monkey Eye (#36)","sense",1,0,
      ["eye","eyeball"],
      [("ciliary body","ciliary"),("retina","retina"),("pupil","pupil"),
       ("cornea","cornea"),("anterior chamber","anterior"),("iris","iris"),
       ("sclera","sclera"),("posterior chamber","posterior"),("optic nerve","optic")])
slide("motorneuron","Motor Neuron — enhanced view","nervecells",6,0,
      ["motor neuron","neuron"],
      [("axon","axon"),("axon hillock","hillock"),
       ("chromatophilic substance","chromatophilic"),("nucleolus","nucleolus"),
       ("nucleus","nucleus"),("dendrites","dendrites")])

# ---------------------------------------------------------------
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9 ]"," ", s.lower()).strip()

ext = json.load(open(r"C:\Users\produ\biol40b-practical\build\extracted.json",encoding="utf-8"))
docs = {k: fitz.open(os.path.join(SRC,v)) for k,v in PDFS.items()}

bank = []
qa_report = []
for sl in S:
    pg = ext[sl["pdf"]][sl["p0"]]
    imgs = pg["images"]
    if sl["panel"] >= len(imgs):
        qa_report.append((sl["id"],"PANEL MISSING")); continue
    im = imgs[sl["panel"]]
    rx0,ry0,rx1,ry1 = im["rect"]; rw,rh = rx1-rx0, ry1-ry0
    words = pg["words"]; heads = pg["heads"]; shafts = pg["shafts"]

    # export clean image for this panel
    doc = docs[sl["pdf"]]
    pix = fitz.Pixmap(doc, im["xref"])
    if pix.n > 4: pix = fitz.Pixmap(fitz.csRGB, pix)
    img_path = os.path.join(OUT_IMG, sl["id"]+".png")
    pix.save(img_path)
    IW, IH = pix.width, pix.height

    # tail of a head = far endpoint of nearest shaft
    def tail_of(head):
        best=None;bd=1e9
        for s in shafts:
            for (ex,ey,ox,oy) in [(s[0],s[1],s[2],s[3]),(s[2],s[3],s[0],s[1])]:
                d=math.hypot(ex-head[0],ey-head[1])
                if d<bd: bd=d; best=(ox,oy)
        return best
    # anchor position for a token
    def anchor(tok):
        tok=norm(tok); cand=[]
        for w in words:
            if tok in norm(w["t"]):
                b=w["bbox"]; cand.append(((b[0]+b[2])/2,(b[1]+b[3])/2))
        return cand

    # candidate (label, head, dist) using tail-to-anchor
    heads_xy=[tuple(h) for h in heads]
    cand=[]
    for (canon,tok) in sl["pins"]:
        aset=anchor(tok)
        if not aset: continue
        for hi,h in enumerate(heads_xy):
            t=tail_of(h)
            if not t: continue
            d=min(math.hypot(t[0]-ax,t[1]-ay) for (ax,ay) in aset)
            cand.append((d,canon,hi))
    cand.sort()
    used_h=set(); used_l=set(); pins=[]
    for d,canon,hi in cand:
        if hi in used_h or canon in used_l: continue
        # tip must fall within/near this panel
        hx,hy=heads_xy[hi]
        fx=(hx-rx0)/rw; fy=(hy-ry0)/rh
        if -0.03<=fx<=1.03 and -0.03<=fy<=1.03:
            used_h.add(hi); used_l.add(canon)
            pins.append(dict(label=canon, accepted=ACCEPTED.get(canon,[canon]),
                             fx=round(max(0,min(1,fx)),4), fy=round(max(0,min(1,fy)),4)))
    # manual pins: (canonical, fx, fy) hand-placed for arrow-less labels
    for (canon,fx,fy) in sl["manual"]:
        pins.append(dict(label=canon, accepted=ACCEPTED.get(canon,[canon]),
                         fx=fx, fy=fy, manual=True))
        used_l.add(canon)
    missing=[c for (c,_) in sl["pins"] if c not in used_l]
    bank.append(dict(id=sl["id"],title=sl["title"],image=sl["id"]+".png",
                     whole=sl["whole"], pins=pins))
    qa_report.append((sl["id"], f"{len(pins)} pins" + (f"  MISSING={missing}" if missing else "")))

    # ---- QA overlay: draw pins + labels on the clean image
    from PIL import Image, ImageDraw, ImageFont
    qimg = Image.open(img_path).convert("RGB")
    dr = ImageDraw.Draw(qimg)
    try: font = ImageFont.truetype("arial.ttf", max(14,IW//45))
    except: font = ImageFont.load_default()
    for pn in pins:
        px,py = pn["fx"]*IW, pn["fy"]*IH
        r = max(6, IW//90)
        col = (0,180,0) if pn.get("manual") else (255,0,0)
        dr.ellipse([px-r,py-r,px+r,py+r], outline=col, width=3)
        dr.line([px,py-r*2,px,py+r*2],fill=col,width=1); dr.line([px-r*2,py,px+r*2,py],fill=col,width=1)
        dr.text((px+r+2,py-r-2), pn["label"], fill=(0,0,255), font=font,
                stroke_width=3, stroke_fill=(255,255,255))
    qimg.save(os.path.join(OUT_QA, sl["id"]+"_qa.png"))

json.dump(bank, open(r"C:\Users\produ\biol40b-practical\build\bank_raw.json","w",encoding="utf-8"), indent=1)
print("SLIDE ASSIGNMENT REPORT")
for sid,msg in qa_report: print(f"  {sid:14s} {msg}")
