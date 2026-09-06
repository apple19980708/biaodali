import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expression_pro.db'))


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            current_method TEXT,
            cycle_day INTEGER DEFAULT 0,
            cycle_total_days INTEGER DEFAULT 4,
            state TEXT DEFAULT 'select_method'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            method TEXT NOT NULL,
            total_days INTEGER DEFAULT 4,
            current_day INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            article_id INTEGER,
            method_learned INTEGER DEFAULT 0,
            drag_completed INTEGER DEFAULT 0,
            qa_completed INTEGER DEFAULT 0,
            retell_completed INTEGER DEFAULT 0,
            free_completed INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, cycle_id, day)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drag_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            mappings TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            day INTEGER NOT NULL,
            module TEXT NOT NULL,
            step TEXT NOT NULL,
            transcript TEXT,
            ai_feedback TEXT,
            metrics TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            checkin_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, checkin_date)
        )
    ''')

    conn.commit()
    conn.close()


def seed_data():
    """Seed articles and methods if not present."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            difficulty INTEGER DEFAULT 1,
            star_s TEXT,
            star_t TEXT,
            star_a TEXT,
            star_r TEXT,
            prep_p TEXT,
            prep_r TEXT,
            prep_e TEXT,
            prep_p2 TEXT,
            keywords TEXT
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM articles')
    if cursor.fetchone()[0] == 0:
        articles = [
            {
                'method': 'STAR',
                'title': '幸存者偏差：二战统计学家如何拯救轰炸机编队',
                'content': '1943 年，二战进入白热化阶段。美国空军对德国本土发动大规模轰炸，但轰炸机编队损失惨重。军方高层希望通过加装装甲来提高飞机生存率，但装甲过重会影响航程和载弹量，因此只能优先保护最脆弱的部位。军械师们检查了返航飞机身上的弹孔分布，发现机翼和机尾中弹最多，发动机和驾驶舱中弹最少。于是有人提议：应该在机翼和机尾加厚装甲。这个方案看似符合数据，却遭到统计学家亚伯拉罕·沃尔德的坚决反对。沃尔德敏锐地指出：我们现在能看到的弹孔数据，全部来自成功返航的飞机。那些没能返航的飞机，恰恰是因为发动机和驾驶舱中弹才坠毁的。换句话说，机翼中弹多反而说明它更耐打，真正需要保护的是数据缺失的部位。军方采纳了他的建议，把装甲集中在发动机、驾驶舱和燃油系统周围。随后几个月，轰炸机损失率显著下降，更多飞行员得以返航。这个故事后来被称为"幸存者偏差"的经典案例，它提醒我们：看不到的数据往往比看到的数据更重要。在做决策时，如果只研究成功案例而忽略失败案例，很容易得出完全相反的结论。无论是创业、投资还是个人成长，幸存者偏差都在悄悄影响我们的判断。学会追问"那些没有成功的人在哪里"，是避免这一陷阱的第一步。这一思维也解释了为什么我们看到那么多一夜暴富的故事，却很少听到无数沉默失败者的经历。',
                'difficulty': 2,
                'star_s': '1943 年，二战进入白热化阶段。美国空军对德国本土发动大规模轰炸，但轰炸机编队损失惨重。',
                'star_t': '军方希望通过加装装甲提高生存率，但装甲过重影响航程，只能优先保护最脆弱部位。',
                'star_a': '统计学家沃尔德指出返航飞机弹孔数据存在幸存者偏差，主张把装甲集中在发动机和驾驶舱等数据缺失部位。',
                'star_r': '轰炸机损失率显著下降，更多飞行员返航，这一案例也成为幸存者偏差的经典教材。',
                'keywords': '二战轰炸, 弹孔分布, 幸存者偏差, 装甲配置'
            },
            {
                'method': 'STAR',
                'title': '一个 SaaS 团队如何用"最小可行演示"拿下首单',
                'content': '2022 年春天，一家刚成立半年的 SaaS 创业团队遇到了生死关头的挑战：他们开发了一款帮助企业自动化客服工单的产品，但连续三个月没有成交，账上现金只够支撑六周。创始人李明意识到，问题不是产品不够好，而是潜在客户无法在短时间内理解产品的价值。当时团队只有四名工程师，没有专职销售，也没有任何大客户背书。李明的任务是：在两周内拿下第一个付费客户，否则公司将面临融资失败。他决定改变策略，不再给客户看功能清单和 PPT，而是直接为每家目标企业免费搭建一个"最小可行演示"——用真实数据展示如果部署他们的系统，客服响应时间能减少多少、积压工单能下降多少。为此，他让工程师开发了一个一键接入客户历史工单数据的沙盒环境，并亲自上门为五家目标客户分别演示。面对一家电商客户时，他甚至熬夜把对方过去一个月的真实投诉数据跑了进去，现场展示出平均响应时间从 6 小时压缩到 45 分钟的效果。客户当场决定先签一年合同。两周内，李明团队拿下三家付费客户，总合同金额超过八十万元，公司顺利渡过难关。这个案例后来被写入他们的销售手册：客户买的不是功能，而是可量化的业务结果。最小可行演示的核心价值，在于把抽象的承诺转化为客户能亲眼看见、亲手验证的具体场景。',
                'difficulty': 2,
                'star_s': '2022 年春天，一家 SaaS 创业团队连续三个月没有成交，账上现金只够支撑六周。',
                'star_t': '创始人李明需要在两周内拿下第一个付费客户，否则公司将融资失败。',
                'star_a': '他放弃功能清单，改为给目标客户免费搭建基于真实数据的"最小可行演示"，上门展示可量化的业务结果。',
                'star_r': '两周内拿下三家付费客户，总金额超八十万元，公司顺利渡过难关。',
                'keywords': 'SaaS创业, 最小可行演示, 真实数据, 付费客户'
            },
            {
                'method': 'PREP',
                'title': '复利思维：人生最重要的数学公式',
                'content': '我认为复利思维是普通人实现长期成长最重要的认知工具之一。复利的核心公式很简单：最终收益等于本金乘以一加收益率的年数次方。真正惊人的不是收益率本身，而是时间维度上的指数级累积。为什么复利如此重要？首先，它揭示了努力的非线性回报。在最初很长一段时间里，增长看起来微不足道，但一旦突破临界点，回报会呈现爆发式增长。其次，复利不仅适用于金钱，也适用于知识、健康和人际关系。一个人每天多读十页书、多锻炼半小时、多维护一段关系，短期几乎看不到差别，但五年十年后，这些微小的正反馈会拉开巨大的差距。巴菲特 99% 的财富是在 50 岁以后赚到的，这并非因为他 50 岁后更努力，而是因为他从年轻时就持续让资本复利滚动了半个世纪。当然，复利的前提是持续投入和避免重大回撤。一次大的健康危机、一段错误的人际关系、一笔冲动的投资，都可能让多年积累归零。因此，真正践行复利思维的人，不是追求短期爆发，而是日复一日做正确的小事，并保护好自己的本金——无论是金钱、身体还是信用。人生是一场长跑，而复利就是普通人最可靠的加速器。越早开始，越能享受时间赠予的指数红利，让平凡的努力在岁月的催化下绽放出惊人的力量。我们不必羡慕他人的一夜成名，只需专注于每天那一丁点可持续的进步。',
                'difficulty': 2,
                'prep_p': '我认为复利思维是普通人实现长期成长最重要的认知工具之一。',
                'prep_r': '复利揭示努力的非线性回报，适用于金钱、知识、健康和人际关系，时间维度上的指数累积会产生巨大差距。',
                'prep_e': '巴菲特 99% 的财富在 50 岁后获得，这源于他从年轻时就让资本复利滚动了半个世纪。',
                'prep_p2': '因此，真正践行复利思维的人应日复一日做正确的小事，并保护好本金，让人生在长跑中持续加速。',
                'keywords': '复利, 指数增长, 非线性回报, 长期主义'
            },
            {
                'method': 'PREP',
                'title': '延迟满足不是天赋，而是可以训练的能力',
                'content': '我的观点是：延迟满足能力并不是少数幸运儿与生俱来的天赋，而是每个人都可以后天训练的心理肌肉。为什么这样说？首先，心理学研究已经证明，大脑的前额叶皮层负责冲动控制和长远规划，而这一区域会随着年龄、训练和习惯养成而不断发育和强化。其次，神经科学家发现，当一个人反复经历"先忍耐、后获得更大回报"的循环时，大脑会逐步建立新的神经通路，让延迟满足变得越来越自然。棉花糖实验中被广泛引用的结论是"能等待的孩子更成功"，但后续研究真正有价值的发现在于：那些原本忍不住的孩子，在学会了一些简单策略后，等待时间可以显著延长。这意味着延迟满足是可教的。例如，把诱惑物移出视线、给自己设定明确的等待规则、把大目标拆成阶段性奖励，都能有效提升延迟满足能力。当然，这不意味着我们要压抑所有即时快乐。健康的延迟满足是有选择地放弃小诱惑，以换取更重要的长期收益。因此，与其羡慕那些天生自律的人，不如从今天开始，设计一个属于自己的"延迟满足训练计划"，从每天一次小忍耐开始，逐步重建大脑对奖励的反应模式。这种能力一旦形成，会在学习、理财和健康等多个领域持续产生复利效应，帮助我们做出更符合长远利益的决策。每一次主动选择延迟满足，都是在为未来的自己积累一笔宝贵的认知资本。',
                'difficulty': 2,
                'prep_p': '我的观点是：延迟满足能力并不是少数幸运儿与生俱来的天赋，而是每个人都可以后天训练的心理肌肉。',
                'prep_r': '前额叶皮层会随训练和习惯养成而强化，反复经历忍耐-回报循环能建立新的神经通路，棉花糖实验后续研究也证明延迟满足是可教的。',
                'prep_e': '例如，把诱惑物移出视线、设定明确等待规则、拆分阶段性奖励，都能显著提升延迟满足能力。',
                'prep_p2': '因此，与其羡慕天生自律的人，不如从今天开始设计自己的延迟满足训练计划，逐步重建大脑对奖励的反应模式。',
                'keywords': '延迟满足, 前额叶皮层, 神经可塑性, 棉花糖实验'
            }
        ]
        for article in articles:
            cursor.execute('''
                INSERT INTO articles (method, title, content, difficulty, star_s, star_t, star_a, star_r, prep_p, prep_r, prep_e, prep_p2, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['method'], article['title'], article['content'], article['difficulty'],
                article.get('star_s', ''), article.get('star_t', ''), article.get('star_a', ''), article.get('star_r', ''),
                article.get('prep_p', ''), article.get('prep_r', ''), article.get('prep_e', ''), article.get('prep_p2', ''),
                article.get('keywords', '')
            ))

    conn.commit()
    conn.close()


def get_or_create_user(user_id='U10086'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO users (user_id, created_at, state)
            VALUES (?, ?, ?)
        ''', (user_id, now, 'home'))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    conn.close()
    return dict(user)


def update_user_state(user_id, updates):
    conn = get_connection()
    cursor = conn.cursor()
    fields = ', '.join([f'{k} = ?' for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    cursor.execute(f'UPDATE users SET {fields} WHERE user_id = ?', values)
    conn.commit()
    conn.close()


def reset_user_progress(user_id):
    """Clear all progress for a user while keeping articles and methods."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM checkins WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM recordings WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM drag_analysis WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM daily_progress WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM cycles WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_active_cycle(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cycles WHERE user_id = ? AND status = ? ORDER BY id DESC LIMIT 1', (user_id, 'active'))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_cycle(user_id, method, total_days=4):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO cycles (user_id, method, total_days, current_day, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, method, total_days, 1, now))
    conn.commit()
    cycle_id = cursor.lastrowid
    conn.close()
    return cycle_id


def complete_cycle(cycle_id):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('UPDATE cycles SET status = ?, completed_at = ? WHERE id = ?', ('completed', now, cycle_id))
    conn.commit()
    conn.close()


def get_or_create_daily_progress(user_id, cycle_id, day):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM daily_progress WHERE user_id = ? AND cycle_id = ? AND day = ?', (user_id, cycle_id, day))
    row = cursor.fetchone()
    if not row:
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO daily_progress (user_id, cycle_id, day, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, cycle_id, day, now))
        conn.commit()
        cursor.execute('SELECT * FROM daily_progress WHERE user_id = ? AND cycle_id = ? AND day = ?', (user_id, cycle_id, day))
        row = cursor.fetchone()
    conn.close()
    return dict(row)


def update_daily_progress(user_id, cycle_id, day, updates):
    conn = get_connection()
    cursor = conn.cursor()
    fields = ', '.join([f'{k} = ?' for k in updates.keys()])
    values = list(updates.values()) + [user_id, cycle_id, day]
    cursor.execute(f'UPDATE daily_progress SET {fields} WHERE user_id = ? AND cycle_id = ? AND day = ?', values)
    conn.commit()
    conn.close()


def get_article_for_method(method, exclude_ids=None):
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_ids:
        placeholders = ','.join(['?'] * len(exclude_ids))
        cursor.execute(f'SELECT * FROM articles WHERE method = ? AND id NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT 1', (method, *exclude_ids))
    else:
        cursor.execute('SELECT * FROM articles WHERE method = ? ORDER BY RANDOM() LIMIT 1', (method,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_article_by_id(article_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_drag_analysis(user_id, cycle_id, day, mappings):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO drag_analysis (user_id, cycle_id, day, mappings, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, cycle_id, day, json.dumps(mappings, ensure_ascii=False), now))
    conn.commit()
    conn.close()


def save_recording(user_id, cycle_id, day, module, step, transcript, ai_feedback, metrics=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO recordings (user_id, cycle_id, day, module, step, transcript, ai_feedback, metrics, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, cycle_id, day, module, step, transcript, ai_feedback, json.dumps(metrics, ensure_ascii=False) if metrics else None, now))
    conn.commit()
    conn.close()


def checkin_today(user_id='U10086'):
    """Record today's check-in. Returns True if new, False if already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date().isoformat()
    now = datetime.now().isoformat()
    try:
        cursor.execute('''
            INSERT INTO checkins (user_id, checkin_date, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, today, now))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_checkin_dates(user_id='U10086', start_date=None, end_date=None):
    """Get set of check-in dates in range."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute('''
            SELECT checkin_date FROM checkins
            WHERE user_id = ? AND checkin_date >= ? AND checkin_date <= ?
        ''', (user_id, start_date, end_date))
    else:
        cursor.execute('SELECT checkin_date FROM checkins WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {row['checkin_date'] for row in rows}


def get_streak(user_id='U10086'):
    """Calculate current consecutive check-in streak."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT checkin_date FROM checkins WHERE user_id = ? ORDER BY checkin_date DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0

    dates = sorted([row['checkin_date'] for row in rows], reverse=True)
    from datetime import date, timedelta
    streak = 0
    check_date = date.today()

    # If no check-in today, start from yesterday
    if dates[0] != check_date.isoformat():
        check_date = date.today() - timedelta(days=1)

    for d in dates:
        if d == check_date.isoformat():
            streak += 1
            check_date -= timedelta(days=1)
        elif d > check_date.isoformat():
            continue
        else:
            break

    return streak


if __name__ == '__main__':
    init_db()
    seed_data()
    print('Database initialized and seeded.')
