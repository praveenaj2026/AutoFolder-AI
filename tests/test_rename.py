import re

name = 'desktop (1) (1) (1) (1) (1) (1) (1)'
cleaned = name

print(f'Original: {cleaned}')

# Apply the while loop from smart_renamer
while re.search(r'\s*\(\d+\)\s*', cleaned):
    cleaned = re.sub(r'\s*\(\d+\)\s*', ' ', cleaned)
    print(f'After iteration: {cleaned}')

# Clean up spaces
cleaned = re.sub(r'[\s_]+', '_', cleaned)
print(f'After space replacement: {cleaned}')

cleaned = cleaned.strip('_- ')
print(f'After strip: {cleaned}')
print(f'Final result: "{cleaned}.ini"')
