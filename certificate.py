from PIL import Image, ImageDraw
from datetime import datetime

def create_certificate(name, location):
    """സർട്ടിഫിക്കറ്റ് ഉണ്ടാക്കി സേവ് ചെയ്യുന്നു"""
    width, height = 800, 600
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # ബോർഡർ
    draw.rectangle([20, 20, 780, 580], outline="navy", width=5)

    # ടെക്സ്റ്റ്
    draw.text((280, 100), "CERTIFICATE OF CONTRIBUTION", fill="darkblue")
    
    content = f"\n\nThis certifies that\n{name.upper()}\nhas contributed marine data for\n{location}."
    draw.multiline_text((250, 200), content, fill="black", align="center", spacing=10)

    # സേവ് ചെയ്യുന്നു
    filename = f"Cert_{name}_{datetime.now().strftime('%M%S')}.png"
    image.save(filename)
    return filename