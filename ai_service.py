import json
import random
import re


def extract_keywords(text, max_words=5):
    """Very simple keyword extraction for demo purposes."""
    words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    stop = {'一个', '没有', '而是', '自己', '他们', '我们', '所有', '可以', '成为', '应该'}
    candidates = [w for w in sorted(freq, key=freq.get, reverse=True) if w not in stop]
    return candidates[:max_words]


def similarity(text1, text2):
    """Simple overlap score between two texts."""
    if not text1 or not text2:
        return 0.0
    set1 = set(re.findall(r'[\u4e00-\u9fff]{2,}', text1))
    set2 = set(re.findall(r'[\u4e00-\u9fff]{2,}', text2))
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / max(len(set1), len(set2))


def habit_count(text):
    """Count common filler words."""
    fillers = ['然后', '那个', '就是', '嗯', '啊', '呃', '我觉得', '怎么说呢']
    count = 0
    for f in fillers:
        count += len(re.findall(re.escape(f), text))
    return count


def feedback_qa(transcript, article_title, method):
    """System Prompt 1: 问答环节"""
    if not transcript or len(transcript.strip()) < 5:
        return "内容与主题略有偏离，建议扫读原文首段。"

    score = similarity(transcript, article_title)
    if score < 0.05:
        return "内容与主题略有偏离，建议扫读原文首段。"

    praises = [
        "结构清晰，保持这个节奏",
        "观点明确，表达很稳",
        "逻辑顺畅，继续练习",
        "回答聚焦，值得肯定"
    ]
    tweaks = [
        "试试把‘然后’换成停顿",
        "试着提炼三个关键词",
        "结尾可以再点一下题",
        "语速放慢一点更有力"
    ]
    return f"{random.choice(praises)}，{random.choice(tweaks)}。"


def feedback_retell(transcript, original_text):
    """System Prompt 2: 复述润色 + 简短建议"""
    if not transcript:
        return "内容与原文偏差较大，建议先梳理3个关键要素。"

    overlap = similarity(transcript, original_text)

    if overlap < 0.3:
        return "内容与原文偏差较大，建议先梳理3个关键要素。"

    praise = random.choice([
        "节奏稳当，试试把‘然后’换成停顿",
        "复述完整，建议增加一个逻辑连接词",
        "要点抓住了，下次注意语速",
        "逻辑通顺，结尾再回扣主题更好"
    ])

    # Simple polish: remove duplicates and add connectors
    sentences = re.split(r'[。！？]', transcript)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 1:
        polished = "首先，" + sentences[0] + "。其次，" + "。".join(sentences[1:-1])
        if sentences[-1]:
            polished += "。最后，" + sentences[-1] + "。"
    else:
        polished = transcript

    comfort = random.choice([
        "保留你的风格，只是帮你理顺了逻辑。",
        "核心意思很棒，稍微调整了连接词。"
    ])

    return {
        'suggestion': praise,
        'polish': polished,
        'comfort': comfort,
        'overlap': round(overlap, 2)
    }


def feedback_free(transcript, topic, method):
    """System Prompt 3: 主动输出深度分析"""
    if not transcript:
        transcript = ""

    relevance = similarity(transcript, topic)
    fillers = habit_count(transcript)

    if relevance < 0.05:
        suggestion = f"话题略有漂移，试试拉回关键词【{topic[:4]}】。"
    else:
        suggestion = random.choice([
            "观点很鲜明，下次试着加一个具体案例会更生动",
            "表达流畅，建议用一个金句收尾",
            "结构不错，试试把理由压缩成三点",
            "节奏很好，加入数字会更有说服力"
        ])

    if relevance >= 0.3:
        rel_feedback = "内容紧扣主题，聚焦感强"
        rel_score = random.randint(7, 10)
    else:
        rel_feedback = "检测到话题漂移，收得回来才是高手"
        rel_score = random.randint(3, 6)

    if method and method.upper() in transcript.upper():
        struct_feedback = "框架运用到位，骨架清晰"
        struct_score = random.randint(7, 10)
    else:
        struct_feedback = f"推荐训练：下次试试{method or 'STAR'}框架，观点会更扎实"
        struct_score = random.randint(4, 7)

    if len(transcript) > 80:
        density_feedback = "观点密度高，很有说服力"
        density_score = random.randint(7, 10)
    else:
        density_feedback = "推荐训练：试试论点+案例结构，内容会更丰盈"
        density_score = random.randint(4, 6)

    if fillers == 0:
        habit_feedback = "语言干净利落"
    else:
        habit_feedback = "捕捉到几次口头禅，下次试试用呼吸停顿代替它们"

    sentences = re.split(r'[。！？]', transcript)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > 1:
        rewrite = "首先，" + sentences[0] + "。其次，" + "。".join(sentences[1:-1])
        if sentences[-1]:
            rewrite += "。总之，" + sentences[-1] + "。"
    else:
        rewrite = transcript

    comfort = random.choice([
        "表达是肌肉，越练越稳。",
        "今天的尝试已经比昨天更进一步。",
        "敢说比说好更重要，继续。",
        "你的表达有自己的节奏，保持它。"
    ])

    metrics = {
        'relevance_score': rel_score,
        'structure_score': struct_score,
        'density_score': density_score,
        'habit_count': fillers
    }

    metrics_display = {
        'relevance_feedback': rel_feedback,
        'structure_feedback': struct_feedback,
        'density_feedback': density_feedback,
        'habit_feedback': habit_feedback
    }

    return {
        'suggestion': suggestion,
        'rewrite': rewrite,
        'comfort_message': comfort,
        'metrics_display': metrics_display,
        'metrics_backend': metrics
    }


def format_feedback(module, transcript, context):
    if module == 'qa':
        return feedback_qa(transcript, context.get('topic', ''), context.get('method', ''))
    elif module == 'retell':
        return feedback_retell(transcript, context.get('original', ''))
    elif module == 'free':
        return feedback_free(transcript, context.get('topic', ''), context.get('method', ''))
    return "继续加油！"
