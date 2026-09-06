import urllib.request
import urllib.error
import json

BASE = 'http://127.0.0.1:5000'

def request(path, data=None, method='GET'):
    url = BASE + path
    if data is not None:
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f'Error {path}: {e.code} {e.read().decode()}')
        return None

# Reset
print('Reset:', request('/api/reset', method='POST'))

# Select method
print('Select STAR:', request('/api/select-method', {'method': 'STAR', 'total_days': 4}, 'POST'))

# Method learned
print('Method learned:', request('/api/method/learned', method='POST'))

# Get article
article_data = request('/api/article')
print('Article:', article_data['article']['title'])

# Submit drag
mappings = {'S': ['sentence1'], 'T': ['sentence2'], 'A': ['sentence3'], 'R': ['sentence4']}
print('Drag submit:', request('/api/drag/submit', {'mappings': mappings}, 'POST'))

# QA feedback
print('QA:', request('/api/qa/feedback', {'transcript': '主人公面临药品不足的问题，采取了协调资源的行动。'}, 'POST'))

# Retell feedback
print('Retell:', request('/api/retell/feedback', {'transcript': article_data['article']['content'][:100]}, 'POST'))

# Free feedback
print('Free:', request('/api/free/feedback', {'transcript': '我想分享一次团队协作经历，当时我负责协调大家完成任务。', 'topic': '团队协作'}, 'POST'))

# Complete day
print('Complete day:', request('/api/day/complete', method='POST'))

print('Flow test completed successfully!')
