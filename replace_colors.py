import re

path = r'C:\Users\12277\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a982af2d09b3824411c6fa6\static\app.js'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    # Grays -> black opacity
    ('text-gray-500', 'text-black/60'),
    ('text-gray-400', 'text-black/50'),
    ('text-gray-300', 'text-black/30'),
    ('text-gray-700', 'text-black/70'),
    ('text-gray-800', 'text-black/80'),
    ('text-gray-600', 'text-black/60'),
    ('text-gray-50', 'text-black/5'),
    ('bg-gray-50', 'bg-black/5'),
    ('bg-gray-100', 'bg-black/10'),
    ('border-gray-200', 'border-black/10'),

    # Blues -> greens
    ('bg-blue-100', 'bg-primary/10'),
    ('text-blue-600', 'text-primary'),
    ('badge-blue', 'badge-green'),
    ('bg-blue-50', 'bg-primary/5'),
    ('border-blue-100', 'border-primary/10'),
    ('text-blue-700', 'text-primary'),
    ('border-blue-200', 'border-primary/20'),
    ('from-blue-50', 'from-primary/5'),
    ('to-indigo-50', 'to-primary/10'),
    ('from-blue-400', 'from-primary'),
    ('via-purple-400', 'via-primary-light'),

    # Purples -> greens
    ('bg-purple-100', 'bg-primary/10'),
    ('text-purple-600', 'text-primary'),
    ('bg-purple-50', 'bg-primary/5'),
    ('text-purple-700', 'text-primary'),
    ('border-purple-200', 'border-primary/20'),

    # Reds -> greens
    ('bg-red-100', 'bg-primary/10'),
    ('text-red-600', 'text-primary'),
    ('text-red-700', 'text-primary'),
    ('border-red-200', 'border-primary/20'),
    ('to-red-400', 'to-primary-dark'),

    # Oranges -> greens
    ('bg-orange-100', 'bg-primary/10'),
    ('text-orange-600', 'text-primary'),

    # Greens -> keep as primary variants
    ('bg-green-100', 'bg-primary/10'),
    ('text-green-600', 'text-primary'),
    ('bg-green-50', 'bg-primary/5'),
    ('text-green-700', 'text-primary'),
    ('border-green-200', 'border-primary/20'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Replace color values in JS data
content = content.replace("color: 'blue'", "color: 'green'")
content = content.replace("color: 'purple'", "color: 'green-light'")
content = content.replace("color: 'red'", "color: 'green-dark'")
content = content.replace("color: 'green'", "color: 'green'")
content = content.replace("color: 'orange'", "color: 'green'")

# Update color class maps
content = content.replace("blue: 'bg-primary/10 text-primary',", "green: 'bg-primary/10 text-primary',")
content = content.replace("purple: 'bg-primary/10 text-primary',", "green-light: 'bg-primary/5 text-primary-light',")
content = content.replace("red: 'bg-primary/10 text-primary',", "green-dark: 'bg-primary/20 text-primary-dark',")

content = content.replace("blue: 'bg-primary',", "green: 'bg-primary',")
content = content.replace("purple: 'bg-primary-light',", "green-light: 'bg-primary-light',")
content = content.replace("red: 'bg-primary-dark',", "green-dark: 'bg-primary-dark',")

content = content.replace("blue: 'bg-primary/5 text-primary border-primary/20',", "green: 'bg-primary/5 text-primary border-primary/20',")
content = content.replace("purple: 'bg-primary/5 text-primary border-primary/20',", "green-light: 'bg-primary/5 text-primary border-primary/20',")
content = content.replace("red: 'bg-primary/5 text-primary border-primary/20',", "green-dark: 'bg-primary/5 text-primary border-primary/20',")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Color replacements done.')
