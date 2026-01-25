"""
Generate custom icons for AutoFolder AI
Creates professional icons matching the blue theme
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon_directory():
    """Create icons directory if it doesn't exist."""
    icon_dir = os.path.join(os.path.dirname(__file__), 'resources', 'icons')
    os.makedirs(icon_dir, exist_ok=True)
    return icon_dir

def create_app_icon(size=256):
    """Create main application icon - folder with AI symbol."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Folder shape (blue gradient)
    folder_color = (59, 130, 246)  # #3B82F6
    folder_dark = (37, 99, 235)    # #2563EB
    
    # Draw folder tab
    tab_points = [(size*0.1, size*0.3), (size*0.4, size*0.3), 
                  (size*0.45, size*0.2), (size*0.1, size*0.2)]
    draw.polygon(tab_points, fill=folder_color)
    
    # Draw folder body
    body_points = [(size*0.1, size*0.3), (size*0.9, size*0.3),
                   (size*0.9, size*0.8), (size*0.1, size*0.8)]
    draw.polygon(body_points, fill=folder_dark)
    
    # Add AI symbol (lightning bolt/sparkle)
    ai_color = (240, 249, 255)  # #F0F9FF
    center_x, center_y = size * 0.5, size * 0.55
    
    # Draw "AI" text
    try:
        font_size = int(size * 0.3)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = center_x - text_width / 2
    text_y = center_y - text_height / 2
    
    draw.text((text_x, text_y), text, fill=ai_color, font=font)
    
    return img

def create_info_icon(size=64):
    """Create info icon - blue circle with 'i'."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue circle
    circle_color = (59, 130, 246)  # #3B82F6
    padding = size * 0.1
    draw.ellipse([padding, padding, size-padding, size-padding], 
                 fill=circle_color)
    
    # White 'i'
    white = (255, 255, 255)
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.6))
    except:
        font = ImageFont.load_default()
    
    text = "i"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) / 2
    text_y = (size - text_height) / 2 - size * 0.05
    
    draw.text((text_x, text_y), text, fill=white, font=font)
    
    return img

def create_warning_icon(size=64):
    """Create warning icon - orange triangle with '!'."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Orange triangle
    warning_color = (249, 115, 22)  # #F97316
    padding = size * 0.1
    triangle = [
        (size/2, padding),  # Top
        (size - padding, size - padding),  # Bottom right
        (padding, size - padding)  # Bottom left
    ]
    draw.polygon(triangle, fill=warning_color)
    
    # White '!'
    white = (255, 255, 255)
    try:
        font = ImageFont.truetype("arialbd.ttf", int(size * 0.5))
    except:
        try:
            font = ImageFont.truetype("arial.ttf", int(size * 0.5))
        except:
            font = ImageFont.load_default()
    
    text = "!"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) / 2
    text_y = (size - text_height) / 2
    
    draw.text((text_x, text_y), text, fill=white, font=font)
    
    return img

def create_error_icon(size=64):
    """Create error icon - red circle with 'X'."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Red circle
    error_color = (239, 68, 68)  # #EF4444
    padding = size * 0.1
    draw.ellipse([padding, padding, size-padding, size-padding], 
                 fill=error_color)
    
    # White 'X'
    white = (255, 255, 255)
    line_width = int(size * 0.12)
    offset = size * 0.25
    
    # Draw X as two lines
    draw.line([(offset, offset), (size-offset, size-offset)], 
              fill=white, width=line_width)
    draw.line([(size-offset, offset), (offset, size-offset)], 
              fill=white, width=line_width)
    
    return img

def create_question_icon(size=64):
    """Create question icon - blue circle with '?'."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Blue circle
    question_color = (59, 130, 246)  # #3B82F6
    padding = size * 0.1
    draw.ellipse([padding, padding, size-padding, size-padding], 
                 fill=question_color)
    
    # White '?'
    white = (255, 255, 255)
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.6))
    except:
        font = ImageFont.load_default()
    
    text = "?"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) / 2
    text_y = (size - text_height) / 2 - size * 0.05
    
    draw.text((text_x, text_y), text, fill=white, font=font)
    
    return img

def create_success_icon(size=64):
    """Create success icon - green circle with checkmark."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Green circle
    success_color = (34, 197, 94)  # #22C55E
    padding = size * 0.1
    draw.ellipse([padding, padding, size-padding, size-padding], 
                 fill=success_color)
    
    # White checkmark
    white = (255, 255, 255)
    line_width = int(size * 0.12)
    
    # Draw checkmark as two lines
    check_start = (size * 0.25, size * 0.5)
    check_middle = (size * 0.45, size * 0.7)
    check_end = (size * 0.75, size * 0.3)
    
    draw.line([check_start, check_middle], fill=white, width=line_width)
    draw.line([check_middle, check_end], fill=white, width=line_width)
    
    return img

def main():
    """Generate all icons."""
    print("🎨 Generating custom icons for AutoFolder AI...")
    
    # Create icons directory
    icon_dir = create_icon_directory()
    print(f"📁 Icon directory: {icon_dir}")
    
    # Generate icons
    icons = {
        'app_icon.png': (create_app_icon(256), 256),
        'app_icon_small.png': (create_app_icon(64), 64),
        'info.png': (create_info_icon(64), 64),
        'warning.png': (create_warning_icon(64), 64),
        'error.png': (create_error_icon(64), 64),
        'question.png': (create_question_icon(64), 64),
        'success.png': (create_success_icon(64), 64),
    }
    
    for filename, (img, size) in icons.items():
        filepath = os.path.join(icon_dir, filename)
        img.save(filepath, 'PNG')
        print(f"  ✓ Created {filename} ({size}x{size})")
    
    # Create .ico file for Windows
    app_icon = create_app_icon(256)
    ico_path = os.path.join(icon_dir, 'app_icon.ico')
    app_icon.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"  ✓ Created app_icon.ico (multi-size)")
    
    print("\n✅ All icons generated successfully!")
    print(f"📂 Location: {icon_dir}")

if __name__ == '__main__':
    main()
