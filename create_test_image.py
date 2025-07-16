from PIL import Image, ImageDraw
import os

# Create a simple test user image (person silhouette)
def create_test_user_image():
    img = Image.new('RGB', (400, 600), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple person silhouette
    # Head
    draw.ellipse([150, 50, 250, 150], fill='black')
    # Body
    draw.rectangle([175, 150, 225, 350], fill='black')
    # Arms
    draw.rectangle([125, 180, 175, 280], fill='black')
    draw.rectangle([225, 180, 275, 280], fill='black')
    # Legs
    draw.rectangle([175, 350, 200, 550], fill='black')
    draw.rectangle([200, 350, 225, 550], fill='black')
    
    img.save('static/test_user.jpg', 'JPEG')
    print("Created test user image: static/test_user.jpg")

# Create a simple test product image (shirt)
def create_test_product_image():
    img = Image.new('RGB', (300, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple shirt
    # Main body
    draw.rectangle([50, 100, 250, 350], fill='blue')
    # Sleeves
    draw.rectangle([20, 120, 80, 200], fill='blue')
    draw.rectangle([220, 120, 280, 200], fill='blue')
    # Collar
    draw.polygon([(120, 100), (180, 100), (160, 80), (140, 80)], fill='darkblue')
    
    img.save('static/test_product.jpg', 'JPEG')
    print("Created test product image: static/test_product.jpg")

if __name__ == "__main__":
    os.makedirs('static', exist_ok=True)
    create_test_user_image()
    create_test_product_image()
    print("Test images created successfully!")