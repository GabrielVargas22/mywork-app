from PIL import Image, ImageDraw, ImageFont

def criar(tam):
    img = Image.new("RGB", (tam, tam), "#2563eb")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0,0,tam,tam], radius=tam//4, fill="#2563eb")
    try:
        font = ImageFont.truetype("arialbd.ttf", int(tam*0.6))
    except:
        font = ImageFont.load_default()
    txt = "M"
    bbox = d.textbbox((0,0), txt, font=font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]
    d.text(((tam-w)/2, (tam-h)/2 - 10), txt, fill="white", font=font)
    img.save(f"static/icon-{tam}.png")
    print(f"Criado static/icon-{tam}.png")

criar(192)
criar(512)