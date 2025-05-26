from PIL import Image, ImageDraw

def create_icon():
    # 创建一个64x64的图像
    size = 64
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 绘制圆形背景
    draw.ellipse([4, 4, size-4, size-4], fill='#2196F3')
    
    # 绘制眼睛
    eye_color = 'white'
    draw.ellipse([20, 20, 30, 30], fill=eye_color)
    draw.ellipse([34, 20, 44, 30], fill=eye_color)
    
    # 绘制嘴巴
    draw.arc([20, 30, 44, 44], 0, 180, fill='white', width=2)
    
    # 保存PNG图标
    image.save('icon.png')
    
    # 保存ICO图标
    image.save('icon.ico', format='ICO')

if __name__ == '__main__':
    create_icon() 