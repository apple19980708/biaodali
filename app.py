from flask import Flask, render_template, request, jsonify
import os
import json
import hashlib
import sqlite3
from datetime import datetime

from db import (
    init_db, seed_data, get_or_create_user, get_active_cycle,
    create_cycle, complete_cycle, get_or_create_daily_progress, update_daily_progress,
    update_user_state, reset_daily_progress,
    get_article_for_method, get_article_by_id,
    get_cycle_used_article_ids, add_cycle_used_article_id,
    increment_completed_articles_count, get_connection,
    save_drag_analysis, save_recording,
    checkin_today, get_checkin_dates, get_streak,
    reset_user_progress
)
from datetime import date, timedelta
from ai_service import format_feedback

app = Flask(__name__)
app.secret_key = 'expression-pro-secret-key'


def _static_version():
    """Generate a cache-busting version based on static file mtimes."""
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    pieces = []
    for filename in ['app.js', 'style.css']:
        filepath = os.path.join(static_dir, filename)
        if os.path.exists(filepath):
            pieces.append(f"{filename}:{os.path.getmtime(filepath):.0f}")
    return hashlib.md5('|'.join(pieces).encode()).hexdigest()[:8] if pieces else '1'


STATIC_VERSION = _static_version()


@app.context_processor
def inject_static_version():
    # Recompute per request so edits take effect without restarting the server
    return dict(static_version=_static_version())


@app.after_request
def add_no_cache_headers(response):
    """Prevent browsers and proxies from caching API responses."""
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


# Initialize database
init_db()
seed_data()


@app.route('/')
def index():
    return render_template('index.html')


# -------------------- API: User & State --------------------

@app.route('/api/user', methods=['GET'])
def api_user():
    user = get_or_create_user('U10086')
    cycle = get_active_cycle('U10086')
    return jsonify({'user': user, 'cycle': cycle})


@app.route('/api/home', methods=['GET'])
def api_home():
    user = get_or_create_user('U10086')
    cycle = get_active_cycle('U10086')

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    checkin_set = get_checkin_dates('U10086', week_start.isoformat(), week_end.isoformat())
    today_checked = today.isoformat() in checkin_set

    weekly = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        weekly.append({
            'date': d.isoformat(),
            'day_name': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
            'checked': d.isoformat() in checkin_set,
            'is_today': d == today
        })

    return jsonify({
        'user': user,
        'cycle': cycle,
        'streak': get_streak('U10086'),
        'weekly': weekly,
        'today_checked': today_checked,
        'week_progress': sum(1 for d in weekly if d['checked'])
    })


@app.route('/api/checkin', methods=['POST'])
def api_checkin():
    cycle = get_active_cycle('U10086')
    # Auto-create cycle if none exists
    if not cycle:
        cycle_id = create_cycle('U10086', 'STAR', 4)
        update_user_state('U10086', {
            'current_method': 'STAR',
            'cycle_day': 1,
            'cycle_total_days': 4,
            'state': 'method_learning'
        })
        get_or_create_daily_progress('U10086', cycle_id, 1)
        cycle = get_active_cycle('U10086')
    else:
        # Move from home to training state if needed
        user = get_or_create_user('U10086')
        if user['state'] == 'home':
            update_user_state('U10086', {'state': 'method_learning'})

    is_new = checkin_today('U10086')
    return jsonify({
        'success': True,
        'checked_in': True,
        'is_new': is_new,
        'state': 'method_learning'
    })


@app.route('/api/select-method', methods=['POST'])
def select_method():
    data = request.json
    method = data.get('method', 'STAR')
    total_days = data.get('total_days', 4)

    # Complete any existing active cycle
    existing = get_active_cycle('U10086')
    if existing:
        complete_cycle(existing['id'])

    cycle_id = create_cycle('U10086', method, total_days)
    update_user_state('U10086', {
        'current_method': method,
        'cycle_day': 1,
        'cycle_total_days': total_days,
        'state': 'method_learning'
    })

    # Create day 1 progress
    get_or_create_daily_progress('U10086', cycle_id, 1)

    return jsonify({'success': True, 'cycle_id': cycle_id})


@app.route('/api/method/learned', methods=['POST'])
def method_learned():
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])
    update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
        'method_learned': 1
    })

    # If day 1, after method learned, move to article reading
    if cycle['current_day'] == 1:
        update_user_state('U10086', {'state': 'article_reading'})
    else:
        update_user_state('U10086', {'state': 'article_reading'})

    return jsonify({'success': True})


# -------------------- API: Article & Drag --------------------

@app.route('/api/article', methods=['GET'])
def api_article():
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])

    # If no article assigned, pick one that hasn't been used in this cycle
    if not progress['article_id']:
        used_ids = get_cycle_used_article_ids(cycle['id'])
        article = get_article_for_method(cycle['method'], exclude_ids=used_ids)
        if not article and used_ids:
            # All articles used; reset used list for this cycle and pick again
            article = get_article_for_method(cycle['method'])
        if article:
            update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
                'article_id': article['id']
            })
            add_cycle_used_article_id(cycle['id'], article['id'])
        else:
            return jsonify({'error': 'No article found'}), 404
    else:
        article = get_article_by_id(progress['article_id'])

    # Return fresh progress so the response matches the persisted state
    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])

    return jsonify({'article': article, 'cycle': cycle, 'progress': progress})


@app.route('/api/article/swap', methods=['POST'])
def swap_article():
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])
    used_ids = get_cycle_used_article_ids(cycle['id'])
    current_id = progress['article_id']
    article = get_article_for_method(cycle['method'], exclude_ids=used_ids)
    if not article and current_id:
        # Fallback: allow any article except current one
        article = get_article_for_method(cycle['method'], exclude_ids=[current_id])
    if article:
        update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
            'article_id': article['id']
        })
        add_cycle_used_article_id(cycle['id'], article['id'])
        return jsonify({'article': article})
    return jsonify({'error': 'No alternative article'}), 404


@app.route('/api/drag/submit', methods=['POST'])
def submit_drag():
    data = request.json
    mappings = data.get('mappings', {})

    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])
    article = get_article_by_id(progress['article_id']) if progress['article_id'] else get_article_for_method(cycle['method'])

    from ai_service import evaluate_drag_analysis
    evaluation = evaluate_drag_analysis(mappings, article)

    save_drag_analysis('U10086', cycle['id'], cycle['current_day'], mappings)

    if evaluation['success']:
        update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
            'drag_completed': 1
        })
        update_user_state('U10086', {'state': 'qa'})

    return jsonify(evaluation)


@app.route('/api/drag/force-complete', methods=['POST'])
def force_complete_drag():
    """Allow the user to proceed after reviewing the correct structure hints."""
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
        'drag_completed': 1
    })
    update_user_state('U10086', {'state': 'qa'})
    return jsonify({'success': True})


# -------------------- API: Output Modules --------------------

@app.route('/api/qa/feedback', methods=['POST'])
def qa_feedback():
    data = request.json
    transcript = data.get('transcript', '')

    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    article = get_article_for_method(cycle['method'])
    llm_info = {}
    feedback = format_feedback('qa', transcript, {
        'topic': article['title'] if article else '',
        'method': cycle['method']
    }, out_info=llm_info)

    save_recording('U10086', cycle['id'], cycle['current_day'], 'output', 'qa', transcript, feedback,
                   llm_used=llm_info.get('llm_used', 0), llm_provider=llm_info.get('llm_provider'))
    update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
        'qa_completed': 1
    })
    update_user_state('U10086', {'state': 'retell'})

    return jsonify({'feedback': feedback})


@app.route('/api/retell/feedback', methods=['POST'])
def retell_feedback():
    data = request.json
    transcript = data.get('transcript', '')

    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])
    article = get_article_by_id(progress['article_id']) if progress['article_id'] else None
    original = article['content'] if article else ''

    llm_info = {}
    result = format_feedback('retell', transcript, {'original': original}, out_info=llm_info)

    if isinstance(result, dict):
        feedback_text = f"【建议】{result['suggestion']}\n【润色】{result['polish']}\n{result['comfort']}"
    else:
        feedback_text = f"【建议】{result}"

    save_recording('U10086', cycle['id'], cycle['current_day'], 'output', 'retell', transcript, feedback_text,
                   llm_used=llm_info.get('llm_used', 0), llm_provider=llm_info.get('llm_provider'))
    update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
        'retell_completed': 1
    })
    update_user_state('U10086', {'state': 'free_output'})

    return jsonify({'result': result if isinstance(result, dict) else {'suggestion': result}})


@app.route('/api/free/feedback', methods=['POST'])
def free_feedback():
    data = request.json
    transcript = data.get('transcript', '')
    topic = data.get('topic', '')

    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    llm_info = {}
    result = format_feedback('free', transcript, {
        'topic': topic,
        'method': cycle['method']
    }, out_info=llm_info)

    feedback_text = f"【建议】{result['suggestion']}\n【详细报告】{json.dumps(result, ensure_ascii=False)}"
    save_recording('U10086', cycle['id'], cycle['current_day'], 'output', 'free', transcript, feedback_text,
                   result.get('metrics_backend'), llm_used=llm_info.get('llm_used', 0),
                   llm_provider=llm_info.get('llm_provider'))
    update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
        'free_completed': 1,
        'completed': 1
    })

    # Count this article as completed
    increment_completed_articles_count(cycle['id'])

    # Auto check-in when daily training is completed
    checkin_today('U10086')

    # Return fresh cycle so the completion page shows the accurate article count
    return jsonify({'result': result, 'cycle': get_active_cycle('U10086')})


# -------------------- API: Daily Completion & Next Day --------------------

@app.route('/api/day/complete', methods=['POST'])
def complete_day():
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    # Check if cycle should complete
    if cycle['current_day'] >= cycle['total_days']:
        complete_cycle(cycle['id'])
        update_user_state('U10086', {
            'state': 'select_method',
            'current_method': None,
            'cycle_day': 0
        })
        return jsonify({'cycle_completed': True})

    # Move to next day
    next_day = cycle['current_day'] + 1
    # Update cycle current_day
    from db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cycles SET current_day = ? WHERE id = ?', (next_day, cycle['id']))
    conn.commit()
    conn.close()

    get_or_create_daily_progress('U10086', cycle['id'], next_day)

    # Pre-assign a new article for the next day, excluding articles already used in this cycle
    used_ids = get_cycle_used_article_ids(cycle['id'])
    article = get_article_for_method(cycle['method'], exclude_ids=used_ids)
    if article:
        update_daily_progress('U10086', cycle['id'], next_day, {
            'article_id': article['id']
        })
        add_cycle_used_article_id(cycle['id'], article['id'])

    update_user_state('U10086', {
        'cycle_day': next_day,
        'state': 'article_reading'
    })

    return jsonify({
        'cycle_completed': False,
        'next_day': next_day,
        'cycle': get_active_cycle('U10086')
    })


@app.route('/api/day/retry', methods=['POST'])
def retry_day():
    """Let the user practice another article on the same day."""
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    # Remember the article they just used so we can pick a different one
    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])
    old_article_id = progress.get('article_id')

    reset_daily_progress('U10086', cycle['id'], cycle['current_day'])

    # Pre-assign a different article for this retry, excluding all already used in this cycle
    used_ids = get_cycle_used_article_ids(cycle['id'])
    article = get_article_for_method(cycle['method'], exclude_ids=used_ids)
    if not article and old_article_id:
        # Fallback if there is only one article available
        article = get_article_for_method(cycle['method'], exclude_ids=[old_article_id])
    if article:
        update_daily_progress('U10086', cycle['id'], cycle['current_day'], {
            'article_id': article['id']
        })
        add_cycle_used_article_id(cycle['id'], article['id'])

    update_user_state('U10086', {'state': 'article_reading'})
    return jsonify({'success': True})


@app.route('/api/day/retry-method', methods=['POST'])
def retry_same_method():
    """Complete current cycle and start a fresh cycle with the same method."""
    cycle = get_active_cycle('U10086')
    if not cycle:
        return jsonify({'error': 'No active cycle'}), 400

    # Remember the last article so the new cycle starts with a different one
    progress = get_or_create_daily_progress('U10086', cycle['id'], cycle['current_day'])
    old_article_id = progress.get('article_id')

    complete_cycle(cycle['id'])
    cycle_id = create_cycle('U10086', cycle['method'], cycle['total_days'])
    get_or_create_daily_progress('U10086', cycle_id, 1)

    # New cycle has fresh used list; just exclude the last article if possible
    article = get_article_for_method(
        cycle['method'],
        exclude_ids=[old_article_id] if old_article_id else []
    )
    if not article and old_article_id:
        article = get_article_for_method(cycle['method'])
    if article:
        update_daily_progress('U10086', cycle_id, 1, {
            'article_id': article['id']
        })
        add_cycle_used_article_id(cycle_id, article['id'])

    update_user_state('U10086', {
        'current_method': cycle['method'],
        'cycle_day': 1,
        'cycle_total_days': cycle['total_days'],
        'state': 'article_reading'
    })
    return jsonify({'success': True, 'cycle_id': cycle_id})


# -------------------- API: Settings --------------------

@app.route('/api/settings/days', methods=['POST'])
def set_days():
    data = request.json
    days = data.get('days', 4)
    days = max(1, min(6, days))

    cycle = get_active_cycle('U10086')
    if cycle and cycle['current_day'] == 1:
        from db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE cycles SET total_days = ? WHERE id = ?', (days, cycle['id']))
        conn.commit()
        conn.close()
        update_user_state('U10086', {'cycle_total_days': days})
        return jsonify({'success': True, 'days': days})

    return jsonify({'error': 'Can only adjust days on day 1'}), 400


# -------------------- API: Reset --------------------

@app.route('/api/reset', methods=['POST'])
def reset_all():
    reset_user_progress('U10086')
    update_user_state('U10086', {
        'current_method': None,
        'cycle_day': 0,
        'cycle_total_days': 4,
        'state': 'home'
    })
    return jsonify({'success': True})




# -------------------- Admin: view users --------------------

@app.route('/admin')
def admin():
    """Simple admin page to view all users and their progress."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = [dict(row) for row in cursor.fetchall()]

    cycles = {}
    progress = {}
    checkins = {}
    for user in users:
        uid = user['user_id']
        cursor.execute('SELECT * FROM cycles WHERE user_id = ? ORDER BY created_at DESC', (uid,))
        cycles[uid] = [dict(row) for row in cursor.fetchall()]

        cursor.execute('''
            SELECT dp.*, a.title as article_title
            FROM daily_progress dp
            LEFT JOIN articles a ON dp.article_id = a.id
            WHERE dp.user_id = ?
            ORDER BY dp.cycle_id DESC, dp.day ASC
        ''', (uid,))
        progress[uid] = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM checkins WHERE user_id = ? ORDER BY checkin_date DESC', (uid,))
        checkins[uid] = [dict(row) for row in cursor.fetchall()]

    recordings_list = {}
    cursor.execute('SELECT * FROM recordings ORDER BY created_at DESC LIMIT 200')
    for row in cursor.fetchall():
        uid = row['user_id']
        recordings_list.setdefault(uid, []).append(dict(row))

    conn.close()

    def fmt_metrics(m):
        if not m:
            return '-'
        try:
            data = json.loads(m) if isinstance(m, str) else m
            if isinstance(data, dict):
                parts = []
                for k, v in data.items():
                    if isinstance(v, (int, float)):
                        parts.append(f"{k}={v}")
                return ', '.join(parts) if parts else '-'
        except Exception:
            pass
        return '-'

    recording_rows_list = []
    for r in sorted([rec for recs in recordings_list.values() for rec in recs], key=lambda x: x.get('created_at', ''), reverse=True):
        recording_rows_list.append(f"""
        <tr>
            <td class="border p-2">{r.get('created_at', '-')[:16]}</td>
            <td class="border p-2">{r.get('user_id', '-')}</td>
            <td class="border p-2">{r.get('module', '-')}</td>
            <td class="border p-2">{r.get('step', '-')}</td>
            <td class="border p-2">{r.get('llm_provider') or '未使用'}</td>
            <td class="border p-2">{'成功' if r.get('llm_used') else '规则回退'}</td>
            <td class="border p-2">{(r.get('transcript') or '无文字')[:80]}{'...' if (r.get('transcript') or '') and len(r.get('transcript', '')) > 80 else ''}</td>
            <td class="border p-2">{(r.get('ai_feedback') or '-')[:80]}{'...' if (r.get('ai_feedback') or '') and len(r.get('ai_feedback', '')) > 80 else ''}</td>
            <td class="border p-2">{fmt_metrics(r.get('metrics'))}</td>
        </tr>
        """)
    recording_rows = ''.join(recording_rows_list)

    rows = []
    for user in users:
        uid = user['user_id']
        row_html = f"""
        <tr>
            <td class="border p-2">{uid}</td>
            <td class="border p-2">{user['created_at']}</td>
            <td class="border p-2">{user['current_method'] or '-'}</td>
            <td class="border p-2">{user['cycle_day']}/{user['cycle_total_days']}</td>
            <td class="border p-2">{user['state']}</td>
            <td class="border p-2">{len(cycles[uid])}</td>
            <td class="border p-2">{len(checkins[uid])}</td>
            <td class="border p-2">
                <details>
                    <summary>周期 ({len(cycles[uid])})</summary>
                    <ul class="mt-1 text-sm">
                        {''.join(f"<li>#{c['id']} {c['method']} 第{c['current_day']}/{c['total_days']}天 完成{c['completed_articles_count']}篇 {'进行中' if c['status']=='active' else '已完成'}</li>" for c in cycles[uid])}
                    </ul>
                </details>
                <details class="mt-1">
                    <summary>进度 ({len(progress[uid])})</summary>
                    <ul class="mt-1 text-sm">
                        {''.join(f"<li>周期{p['cycle_id']}第{p['day']}天: {p['article_title'] or '无文章'} | 方法{p['method_learned']} 划线{p['drag_completed']} 问答{p['qa_completed']} 复述{p['retell_completed']} 输出{p['free_completed']} | {'已完成' if p['completed'] else '进行中'}</li>" for p in progress[uid])}
                    </ul>
                </details>
            </td>
        </tr>
        """
        rows.append(row_html)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理后台 - 使用者信息</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; padding: 20px; background: #f8fafc; }}
        h1 {{ color: #059669; }}
        table {{ width: 100%; border-collapse: collapse; background: white; margin-top: 16px; }}
        th {{ background: #059669; color: white; text-align: left; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 8px; }}
        details {{ cursor: pointer; }}
    </style>
</head>
<body>
    <h1>使用者信息（共 {len(users)} 人）</h1>
    <table>
        <thead>
            <tr>
                <th>使用者 ID</th>
                <th>创建时间</th>
                <th>当前方法</th>
                <th>周期天</th>
                <th>状态</th>
                <th>周期数</th>
                <th>打卡数</th>
                <th>详情</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>

    <h2 style="margin-top: 32px;">录音记录（最近 200 条）</h2>
    <table>
        <thead>
            <tr>
                <th>时间</th>
                <th>用户 ID</th>
                <th>模块</th>
                <th>步骤</th>
                <th>LLM Provider</th>
                <th>LLM 状态</th>
                <th>录音文字</th>
                <th>AI 反馈</th>
                <th>质量分</th>
            </tr>
        </thead>
        <tbody>
            {recording_rows}
        </tbody>
    </table>
</body>
</html>"""
    return html


@app.route('/api/admin/users')
def api_admin_users():
    """JSON API for user data."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'users': users, 'count': len(users)})
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
