import json

d = json.load(open('data/punctuation_medians.json', 'r', encoding='utf-8'))
chars = ['。', '，', '！', '？', '—', '.', ',']

print('标点符号坐标范围:')
print('-' * 60)
for ch in chars:
    if ch in d:
        m = d[ch]['medians']
        pts = [p for s in m for p in s]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x_center = (min(xs) + max(xs)) // 2
        y_center = (min(ys) + max(ys)) // 2
        print(f'  {ch}: X({min(xs):3d}-{max(xs):3d}) 中心{x_center:3d}  |  Y({min(ys):3d}-{max(ys):3d}) 中心{y_center:3d}')

print('-' * 60)
print('✅ 预期: X中心≈512, Y中心≈388')

