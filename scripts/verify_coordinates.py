import json

data = json.load(open('data/alphanumeric_medians.json', 'r', encoding='utf-8'))

print('验证坐标范围:')
print('-' * 50)
for ch in ['1', '5', 'A', 'Z', 'a', 'z']:
    m = data[ch]['medians']
    pts = [p for s in m for p in s]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x_center = (min(xs) + max(xs)) // 2
    y_center = (min(ys) + max(ys)) // 2
    print(f'  {ch}: X({min(xs):3d}-{max(xs):3d}) 中心X:{x_center:3d}  |  Y({min(ys):3d}-{max(ys):3d}) 中心Y:{y_center:3d}')

print('-' * 50)
print('✅ 预期: X中心接近512, Y中心接近400')

