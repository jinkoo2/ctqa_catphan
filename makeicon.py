from PIL import Image

# Open the image file
img = Image.open("app.png")

# Convert it to an icon (ICO) file
img.save("app.ico", format="ICO", sizes=[(256, 256)])  # Set the size to 256x256 or other sizes you prefer
