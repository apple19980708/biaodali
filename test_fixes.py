import os
import sys

# Point to a temp database so tests don't touch user data
os.environ['DATABASE_PATH'] = os.path.join(os.path.dirname(__file__), 'test_expression_pro.db')

from db import (
    init_db, seed_data, get_or_create_user, get_active_cycle,
    create_cycle, get_or_create_daily_progress, update_daily_progress,
    update_user_state, reset_daily_progress, reset_user_progress,
    get_article_for_method, add_cycle_used_article_id
)
from ai_service import evaluate_drag_analysis, _extract_best_span


def setup():
    if os.path.exists(os.environ['DATABASE_PATH']):
        os.remove(os.environ['DATABASE_PATH'])
    init_db()
    seed_data()
    reset_user_progress('U10086')


def test_count_accuracy():
    print('--- Test: completed_articles_count accuracy ---')
    setup()
    user_id = 'U10086'
    get_or_create_user(user_id)

    cycle_id = create_cycle(user_id, 'STAR', 4)
    update_user_state(user_id, {'current_method': 'STAR', 'cycle_day': 1, 'state': 'article_reading'})

    # Day 1: mark complete
    get_or_create_daily_progress(user_id, cycle_id, 1)
    update_daily_progress(user_id, cycle_id, 1, {
        'article_id': 1, 'method_learned': 1, 'drag_completed': 1,
        'qa_completed': 1, 'retell_completed': 1, 'free_completed': 1, 'completed': 1
    })

    cycle = get_active_cycle(user_id)
    assert cycle['completed_articles_count'] == 1, f"Expected 1, got {cycle['completed_articles_count']}"
    print(f"  After day 1 complete: count={cycle['completed_articles_count']} (current_day={cycle['current_day']})")

    # Simulate moving to day 2
    import sqlite3
    from db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cycles SET current_day = 2 WHERE id = ?', (cycle_id,))
    conn.commit()
    conn.close()
    update_user_state(user_id, {'cycle_day': 2})

    # Day 2: complete
    get_or_create_daily_progress(user_id, cycle_id, 2)
    update_daily_progress(user_id, cycle_id, 2, {
        'article_id': 2, 'method_learned': 1, 'drag_completed': 1,
        'qa_completed': 1, 'retell_completed': 1, 'free_completed': 1, 'completed': 1
    })

    cycle = get_active_cycle(user_id)
    assert cycle['completed_articles_count'] == 2, f"Expected 2, got {cycle['completed_articles_count']}"
    print(f"  After day 2 complete: count={cycle['completed_articles_count']} (current_day={cycle['current_day']})")

    # Retry day 2: reset progress
    reset_daily_progress(user_id, cycle_id, 2)

    cycle = get_active_cycle(user_id)
    assert cycle['completed_articles_count'] == 1, f"Expected 1 after retry, got {cycle['completed_articles_count']}"
    print(f"  After day 2 retry: count={cycle['completed_articles_count']} (current_day={cycle['current_day']})")

    # Complete day 2 again
    get_or_create_daily_progress(user_id, cycle_id, 2)
    update_daily_progress(user_id, cycle_id, 2, {
        'article_id': 2, 'method_learned': 1, 'drag_completed': 1,
        'qa_completed': 1, 'retell_completed': 1, 'free_completed': 1, 'completed': 1
    })

    cycle = get_active_cycle(user_id)
    assert cycle['completed_articles_count'] == 2, f"Expected 2, got {cycle['completed_articles_count']}"
    print(f"  After day 2 re-complete: count={cycle['completed_articles_count']} (current_day={cycle['current_day']})")
    print('  PASSED\n')


def test_footer_article_number():
    print('--- Test: article number display consistency ---')
    setup()
    user_id = 'U10086'
    get_or_create_user(user_id)

    cycle_id = create_cycle(user_id, 'STAR', 4)
    update_user_state(user_id, {'current_method': 'STAR', 'cycle_day': 1, 'state': 'article_reading'})

    # On day 1, no article completed
    cycle = get_active_cycle(user_id)
    footer_number = cycle['completed_articles_count'] + 1
    assert footer_number == cycle['current_day'], f"Footer shows {footer_number}, current_day is {cycle['current_day']}"
    print(f"  Day 1 before complete: footer={footer_number}, current_day={cycle['current_day']}")

    # Complete day 1 and move to day 2
    get_or_create_daily_progress(user_id, cycle_id, 1)
    update_daily_progress(user_id, cycle_id, 1, {
        'article_id': 1, 'free_completed': 1, 'completed': 1
    })
    from db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cycles SET current_day = 2 WHERE id = ?', (cycle_id,))
    conn.commit()
    conn.close()

    cycle = get_active_cycle(user_id)
    footer_number = cycle['completed_articles_count'] + 1
    assert footer_number == cycle['current_day'], f"Footer shows {footer_number}, current_day is {cycle['current_day']}"
    print(f"  Day 2 after day 1 complete: footer={footer_number}, current_day={cycle['current_day']}")
    print('  PASSED\n')


def test_drag_reference_is_original_span():
    print('--- Test: drag reference uses original article text ---')
    setup()

    article = {
        'method': 'STAR',
        'content': '二战期间，盟军对德国本土发动大规模战略轰炸，但轰炸机损失率高得惊人。为了提高生存率，军方决定对返航飞机进行弹孔统计，把有限的装甲加到中弹最密集的部位。统计学家亚伯拉罕·沃尔德坚决反对。',
        'star_s': '二战期间，盟军轰炸机损失惨重，军方希望通过统计返航飞机弹孔来优化装甲配置。',
        'star_t': '',
        'star_a': '',
        'star_r': ''
    }

    result = evaluate_drag_analysis({'S': ['二战期间，盟军对德国本土发动大规模战略轰炸，但轰炸机损失率高得惊人。']}, article)
    s_slot = result['slots']['S']
    assert s_slot['correct'], f"Expected correct, got score={s_slot.get('score')}, correct={s_slot['correct']}"
    print(f"  Correct selection: score={s_slot.get('score')}, correct={s_slot['correct']}")

    result = evaluate_drag_analysis({'S': ['统计学家亚伯拉罕·沃尔德坚决反对。']}, article)
    s_slot = result['slots']['S']
    assert not s_slot['correct'], f"Expected incorrect, got score={s_slot.get('score')}, correct={s_slot['correct']}"
    assert '二战期间' in s_slot['correct_text'], f"Reference should be original text, got: {s_slot['correct_text']}"
    print(f"  Wrong selection: score={s_slot.get('score')}, reference starts with: {s_slot['correct_text'][:20]}...")
    print('  PASSED\n')


def test_extract_best_span():
    print('--- Test: extract best original span ---')
    content = '第一段关于背景。第二段关于任务。第三段关于行动。第四段关于结果。'
    summary = '第二段关于任务'
    span = _extract_best_span(content, summary)
    assert span == '第二段关于任务。', f"Expected '第二段关于任务。', got '{span}'"
    print(f"  Summary '{summary}' -> span '{span}'")
    print('  PASSED\n')


def test_extract_best_span_multi_sentence():
    print('--- Test: multi-sentence span preserves original text ---')
    content = '第一段关于背景。第二段关于任务。第三段关于行动。第四段关于结果。'
    summary = '第二段关于任务。第三段关于行动。'
    span = _extract_best_span(content, summary)
    assert span == '第二段关于任务。第三段关于行动。', f"Expected '第二段关于任务。第三段关于行动。', got '{span}'"
    assert '。。' not in span, f"Span should not contain duplicated punctuation, got '{span}'"
    print(f"  Summary '{summary}' -> span '{span}'")
    print('  PASSED\n')


def test_current_article_number():
    print('--- Test: current_article_number field ---')
    setup()
    user_id = 'U10086'
    get_or_create_user(user_id)

    cycle_id = create_cycle(user_id, 'STAR', 4)
    cycle = get_active_cycle(user_id)
    assert cycle['current_article_number'] == 1, f"Expected 1, got {cycle['current_article_number']}"
    print(f"  Before any completion: current_article_number={cycle['current_article_number']}")

    get_or_create_daily_progress(user_id, cycle_id, 1)
    update_daily_progress(user_id, cycle_id, 1, {
        'article_id': 1, 'free_completed': 1, 'completed': 1
    })

    cycle = get_active_cycle(user_id)
    assert cycle['current_article_number'] == 2, f"Expected 2, got {cycle['current_article_number']}"
    print(f"  After day 1 complete: current_article_number={cycle['current_article_number']}")
    print('  PASSED\n')


if __name__ == '__main__':
    test_count_accuracy()
    test_footer_article_number()
    test_extract_best_span()
    test_extract_best_span_multi_sentence()
    test_drag_reference_is_original_span()
    test_current_article_number()
    print('All tests passed!')
