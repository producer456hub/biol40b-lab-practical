"""Render each PDF page to a reference PNG and save the clean embedded image(s)."""
import fitz, os
SRC = r"C:\Users\produ\Downloads\prelab 1 study"
PDFS = {
    "nervecells": "Lab 1-4 Nervous system (histology).pdf",
    "sense":      "Sense Organs histology-1 (1).pdf",
    "motor":      "Motor end plate (histology).pdf",
    "pns":        "histology slides-1.pdf",
}
PAGEDIR = r"C:\Users\produ\biol40b-practical\build\pages"
CLEANDIR = r"C:\Users\produ\biol40b-practical\build\clean"
os.makedirs(PAGEDIR, exist_ok=True)
os.makedirs(CLEANDIR, exist_ok=True)

for key, fname in PDFS.items():
    doc = fitz.open(os.path.join(SRC, fname))
    for pno in range(len(doc)):
        page = doc[pno]
        # reference render (with labels) at ~110 dpi
        pix = page.get_pixmap(matrix=fitz.Matrix(1.1, 1.1))
        pix.save(os.path.join(PAGEDIR, f"{key}_p{pno+1:02d}.png"))
        # save each sizeable embedded image, ordered L->R T->B
        infos = []
        for im in page.get_images(full=True):
            xref = im[0]
            for r in page.get_image_rects(xref):
                if r.width*r.height >= 5000:
                    infos.append((xref, r))
        infos.sort(key=lambda a: (round(a[1].y0/50), a[1].x0))
        for idx,(xref,r) in enumerate(infos):
            d = fitz.Pixmap(doc, xref)
            if d.n > 4:
                d = fitz.Pixmap(fitz.csRGB, d)
            d.save(os.path.join(CLEANDIR, f"{key}_p{pno+1:02d}_{idx}.png"))
    doc.close()
print("done")
