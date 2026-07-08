# -*- coding: utf-8 -*-
"""Render detected arrow-tips as NUMBERED markers per slide + print fractions,
so labels can be assigned to tip numbers reliably (tips = teacher's exact marks)."""
import fitz, os, json, math
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\produ\Downloads\prelab 1 study"
PDFS = {"nervecells":"Lab 1-4 Nervous system (histology).pdf","sense":"Sense Organs histology-1 (1).pdf",
        "motor":"Motor end plate (histology).pdf","pns":"histology slides-1.pdf"}
OUT = r"C:\Users\produ\biol40b-practical\build\tips"; os.makedirs(OUT, exist_ok=True)
ext = json.load(open(r"C:\Users\produ\biol40b-practical\build\extracted.json",encoding="utf-8"))
docs = {k: fitz.open(os.path.join(SRC,v)) for k,v in PDFS.items()}

# (id, pdf, p0, panel)
SLIDES = [("nerve_v1","pns",1,0),("nerve_v2","pns",2,0),("nerve_v3","pns",3,0),
          ("sc27_over","pns",5,0),("sc27_cc","pns",6,0),("sc28_over","pns",7,0),
          ("sc28_cc","pns",9,0),("cbl_over","pns",10,0),("cbl_r2","pns",13,0),
          ("cerebrum","pns",14,0),("nmj","motor",5,1),("lip","motor",1,0),
          ("eye","sense",1,0),("motorneuron","nervecells",6,0)]

allframes={}
for sid,pdf,p0,panel in SLIDES:
    pg=ext[pdf][p0]; im=pg["images"][panel]
    rx0,ry0,rx1,ry1=im["rect"]; rw,rh=rx1-rx0,ry1-ry0
    doc=docs[pdf]; pix=fitz.Pixmap(doc,im["xref"])
    if pix.n>4: pix=fitz.Pixmap(fitz.csRGB,pix)
    IW,IH=pix.width,pix.height
    img=Image.frombytes("RGB",[IW,IH],pix.samples); dr=ImageDraw.Draw(img)
    try: font=ImageFont.truetype("arialbd.ttf",max(18,IW//30))
    except: font=ImageFont.load_default()
    frames=[]
    n=0
    for h in pg["heads"]:
        fx=(h[0]-rx0)/rw; fy=(h[1]-ry0)/rh
        if -0.03<=fx<=1.03 and -0.03<=fy<=1.03:
            n+=1; px,py=fx*IW,fy*IH; r=max(10,IW//55)
            dr.ellipse([px-r,py-r,px+r,py+r],outline=(255,0,0),width=4)
            dr.text((px+r,py-r),str(n),fill=(255,0,0),font=font,stroke_width=3,stroke_fill=(255,255,255))
            frames.append((n,round(max(0,min(1,fx)),4),round(max(0,min(1,fy)),4)))
    img.save(os.path.join(OUT,sid+"_tips.png"))
    allframes[sid]=frames
    print(f"{sid}: "+", ".join(f"#{n}=({fx},{fy})" for n,fx,fy in frames))

json.dump(allframes,open(r"C:\Users\produ\biol40b-practical\build\tips.json","w"),indent=1)
