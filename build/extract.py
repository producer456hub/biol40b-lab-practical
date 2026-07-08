"""
Extract clean histology images + arrow(tip,label) pairs from the lab PDFs.
Each PDF page = a titled microscope slide with a clean embedded bitmap and
vector arrows+text labels on top. We pull the bitmap label-free and recover
each arrow tip (the arrowhead vector cluster) paired to its nearest label word.
Outputs: images/*.png (clean) + build/extracted.json + build/qa/*.png (overlays).
"""
import fitz, os, json, math
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\produ\Downloads\prelab 1 study"
PDFS = {
    "nervecells": "Lab 1-4 Nervous system (histology).pdf",
    "sense":      "Sense Organs histology-1 (1).pdf",
    "motor":      "Motor end plate (histology).pdf",
    "pns":        "histology slides-1.pdf",
}
IMGDIR = r"C:\Users\produ\biol40b-practical\images"
QADIR  = r"C:\Users\produ\biol40b-practical\build\qa"
os.makedirs(IMGDIR, exist_ok=True)
os.makedirs(QADIR, exist_ok=True)

def is_arrowhead(d):
    # small closed filled path, ~4 short segments, bbox small
    items = d.get("items", [])
    if len(items) < 3 or len(items) > 6:
        return False
    r = d.get("rect")
    if r is None:
        return False
    return r.width < 20 and r.height < 20

def path_points(d):
    pts = []
    for it in d.get("items", []):
        if it[0] == "l":
            pts.append(it[1]); pts.append(it[2])
        elif it[0] == "c":
            pts.append(it[1]); pts.append(it[-1])
        elif it[0] == "re":
            r = it[1]; pts.append(r.tl); pts.append(r.br)
    return pts

def centroid(pts):
    if not pts: return None
    return (sum(p.x for p in pts)/len(pts), sum(p.y for p in pts)/len(pts))

results = {}
for key, fname in PDFS.items():
    doc = fitz.open(os.path.join(SRC, fname))
    pages = []
    for pno in range(len(doc)):
        page = doc[pno]
        words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wno
        # title = words on the largest-font top lines; approximate by first line block
        # image rects
        img_infos = []
        for im in page.get_images(full=True):
            xref = im[0]
            rects = page.get_image_rects(xref)
            for r in rects:
                if r.width*r.height < 5000:  # skip tiny logos
                    continue
                img_infos.append({"xref": xref, "rect": r})
        # sort images left-to-right, top-to-bottom
        img_infos.sort(key=lambda a: (round(a["rect"].y0/50), a["rect"].x0))
        # drawings: separate arrowheads (tips) from shaft lines
        heads, shafts = [], []
        for d in page.get_drawings():
            if is_arrowhead(d):
                c = centroid(path_points(d))
                if c: heads.append(c)
            else:
                for it in d.get("items", []):
                    if it[0] == "l":
                        shafts.append((it[1], it[2]))
        pages.append({
            "pno": pno,
            "words": [{"t": w[4], "bbox": [w[0],w[1],w[2],w[3]]} for w in words],
            "images": [{"xref": a["xref"], "rect": [a["rect"].x0,a["rect"].y0,a["rect"].x1,a["rect"].y1]} for a in img_infos],
            "heads": [[c[0],c[1]] for c in heads],
            "shafts": [[s[0].x,s[0].y,s[1].x,s[1].y] for s in shafts],
        })
    results[key] = pages
    doc.close()

with open(r"C:\Users\produ\biol40b-practical\build\extracted.json","w",encoding="utf-8") as f:
    json.dump(results, f, indent=1)

# quick summary
for key, pages in results.items():
    print(f"\n===== {key} : {len(pages)} pages =====")
    for p in pages:
        print(f" p{p['pno']+1}: imgs={len(p['images'])} heads={len(p['heads'])} shafts={len(p['shafts'])}")
