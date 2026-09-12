"""查看所有使用者信息（本地调试工具）"""
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expression_pro.db')


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def main():
    if not os.path.exists(DB_PATH):
        print(f'数据库不存在: {DB_PATH}')
        return

    users = query('SELECT * FROM users ORDER BY created_at DESC')
    if not users:
        print('暂无使用者')
        return

    print(f'数据库: {DB_PATH}')
    print(f'使用者数量: {len(users)}')
    print('=' * 80)

    for user in users:
        uid = user['user_id']
        print(f"\n使用者 ID: {uid}")
        print(f"  创建时间: {user['created_at']}")
        print(f"  当前方法: {user['current_method'] or '无'}")
        print(f"  当前周期天: {user['cycle_day']}/{user['cycle_total_days']}")
        print(f"  当前状态: {user['state']}")

        # 周期信息
        cycles = query('SELECT * FROM cycles WHERE user_id = ? ORDER BY created_at DESC', (uid,))
        for cycle in cycles:
            status_zh = '进行中' if cycle['status'] == 'active' else '已完成'
            print(f"  周期 #{cycle['id']}: {cycle['method']} | "
                  f"第 {cycle['current_day']}/{cycle['total_days']} 天 | "
                  f"已完成 {cycle['completed_articles_count']} 篇 | {status_zh}")

        # 每日进度
        progresses = query('''
            SELECT dp.*, a.title as article_title
            FROM daily_progress dp
            LEFT JOIN articles a ON dp.article_id = a.id
            WHERE dp.user_id = ?
            ORDER BY dp.cycle_id DESC, dp.day ASC
        ''', (uid,))
        for p in progresses:
            modules = []
            if p['method_learned']: modules.append('方法')
            if p['drag_completed']: modules.append('划线')
            if p['qa_completed']: modules.append('问答')
            if p['retell_completed']: modules.append('复述')
            if p['free_completed']: modules.append('输出')
            completed = '已完成' if p['completed'] else '进行中'
            print(f"    周期#{p['cycle_id']} 第{p['day']}天: "
                  f"{p['article_title'] or '未分配文章'} | "
                  f"进度: {', '.join(modules) or '无'} | {completed}")

        # 打卡记录
        checkins = query('SELECT * FROM checkins WHERE user_id = ? ORDER BY checkin_date DESC', (uid,))
        if checkins:
            dates = [c['checkin_date'] for c in checkins]
            print(f"  打卡记录 ({len(checkins)} 天): {', '.join(dates[:7])}")

    print('\n' + '=' * 80)


if __name__ == '__main__':
    main()
