with open('src/mlt_python/project.py', 'r') as f:
    content = f.read()

# Find to_xml method boundaries
start_marker = '    def to_xml('
start = content.find(start_marker)
if start == -1:
    print('Method not found')
    exit()

# Find end of method (next method or class at same indent level)
lines = content[start:].split('\n')
end_pos = len(content)
for i, line in enumerate(lines):
    if i > 0:
        stripped = line.lstrip()
        if stripped and not line.startswith('        ') and (stripped.startswith('def ') or stripped.startswith('class ')):
            end_pos = start + sum(len(l) + 1 for l in lines[:i])
            break

print(f'Start: {start}, End: {end_pos}')

# Extract method
method = content[start:end_pos]

# Fix indentation
lines = method.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    if i == 0:
        fixed_lines.append(line)  # def line
        continue
    
    stripped = line.lstrip()
    if not stripped:  # Empty line
        fixed_lines.append('')
        continue
    
    # Method body should be indented by 8 spaces
    if not line.startswith('        '):
        fixed_lines.append('        ' + stripped)
    else:
        fixed_lines.append(line)

fixed_method = '\n'.join(fixed_lines)

# Replace in content
new_content = content[:start] + fixed_method + content[end_pos:]

with open('src/mlt_python/project.py', 'w') as f:
    f.write(new_content)

print('Fixed indentation')
