import json
import random
import re
import os


# ---------------------------------------------------------------------------
# Optional real AI integration
# DeepSeek is used by default. Set DEEPSEEK_API_KEY in your environment to
# enable LLM-generated feedback. You can also override the base URL or model
# with DEEPSEEK_API_BASE and DEEPSEEK_MODEL.
# For any other OpenAI-compatible provider, set OPENAI_API_KEY / OPENAI_API_BASE
# / OPENAI_MODEL instead.
# If no API key is provided, the app falls back to the built-in heuristic
# feedback below so it still works offline.
# ---------------------------------------------------------------------------

def _call_llm(messages, temperature=0.7, max_tokens=600):
    """Call an OpenAI-compatible chat completion endpoint if configured."""
    # Prefer DeepSeek config, fall back to generic OpenAI-compatible config
    api_key = os.environ.get('DEEPSEEK_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None

    if os.environ.get('DEEPSEEK_API_KEY'):
        base_url = (os.environ.get('DEEPSEEK_API_BASE') or 'https://api.deepseek.com/v1').rstrip('/')
        model = os.environ.get('DEEPSEEK_MODEL') or 'deepseek-chat'
    else:
        base_url = (os.environ.get('OPENAI_API_BASE') or 'https://api.openai.com/v1').rstrip('/')
        model = os.environ.get('OPENAI_MODEL') or 'gpt-3.5-turbo'

    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens
    }

    try:
        import urllib.request
        req = urllib.request.Request(
            f'{base_url}/chat/completions',
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print('LLM call failed, falling back to heuristic feedback:', e)
        return None


def _try_parse_json(text):
    """Best-effort JSON extraction from an LLM response."""
    if not text:
        return None
    # First try the whole text as JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try to extract a JSON object from markdown fences
    match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Heuristic (mock) feedback - used when no LLM key is configured
# ---------------------------------------------------------------------------

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
        struct_feedback = f"下次试试{method or 'STAR'}框架，观点会更扎实"
        struct_score = random.randint(4, 7)

    if len(transcript) > 80:
        density_feedback = "观点密度高，很有说服力"
        density_score = random.randint(7, 10)
    else:
        density_feedback = "试试论点+案例结构，内容会更丰盈"
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


def _extract_best_span(content, summary, max_sentences=1):
    """Find the single original sentence in content that best matches the summary.

    We deliberately return only one sentence so the reference shown to the user is a
    complete, contiguous sentence from the article rather than a span that jumps over
    several sentences.
    """
    if not content or not summary:
        return summary

    # Build sentence spans with their original positions so we can return the
    # exact original text (preserving whitespace and punctuation).
    sentence_spans = []
    start = 0
    for m in re.finditer(r'[。！？]', content):
        end = m.end()
        sentence = content[start:end].strip()
        if sentence:
            sentence_spans.append((start, end, sentence))
        start = end
    if start < len(content):
        sentence = content[start:].strip()
        if sentence:
            sentence_spans.append((start, len(content), sentence))

    if not sentence_spans:
        return summary

    best_span = sentence_spans[0][2]
    best_score = 0.0

    for i in range(len(sentence_spans)):
        span = sentence_spans[i][2]
        score = similarity(span, summary)
        if score > best_score:
            best_score = score
            best_span = span

    # Always return the best original sentence; never fall back to the summary,
    # because the user needs a highlightable sentence from the article.
    return best_span


def evaluate_drag_analysis(user_mappings, article):
    """Compare user's highlighted text with the correct structure slots."""
    method = article.get('method', 'STAR')
    content = article.get('content', '')
    if method == 'STAR':
        keys = {
            'S': article.get('star_s', ''),
            'T': article.get('star_t', ''),
            'A': article.get('star_a', ''),
            'R': article.get('star_r', '')
        }
    else:
        keys = {
            'P': article.get('prep_p', ''),
            'R': article.get('prep_r', ''),
            'E': article.get('prep_e', ''),
            'P2': article.get('prep_p2', '')
        }

    # Use original article spans as references, not the condensed summaries
    correct_texts = {slot: _extract_best_span(content, summary) for slot, summary in keys.items()}

    threshold = 0.90
    slots = {}
    all_correct = True

    for slot, correct_text in correct_texts.items():
        user_texts = user_mappings.get(slot, [])
        if not user_texts or not correct_text:
            slots[slot] = {
                'correct': False,
                'user': '',
                'correct_text': correct_text
            }
            all_correct = False
            continue

        user_combined = '。'.join(user_texts)
        score = similarity(user_combined, correct_text)
        contains = correct_text in user_combined or user_combined in correct_text
        is_correct = score >= threshold or contains

        slots[slot] = {
            'correct': is_correct,
            'score': round(score, 2),
            'user': user_combined[:80],
            'correct_text': correct_text
        }
        if not is_correct:
            all_correct = False

    return {
        'success': all_correct,
        'slots': slots,
        'correct_texts': {slot: info['correct_text'] for slot, info in slots.items()},
        'message': '结构分析正确，进入下一环节' if all_correct else '部分结构划分与原文有出入，已标出正确结构供对照'
    }


# ---------------------------------------------------------------------------
# LLM-based feedback (used when OPENAI_API_KEY is set)
# ---------------------------------------------------------------------------

def llm_feedback_qa(transcript, article_title, method):
    prompt = f"""你是一位中文表达力教练。用户刚完成一道问答练习。
文章标题：{article_title}
使用方法：{method}
用户回答：{transcript}

请给出一段 30-60 字的简短反馈，先肯定优点，再给一条具体改进建议。只返回反馈文字，不要返回 JSON。"""
    return _call_llm([{'role': 'system', 'content': '你是中文表达力教练，语气鼓励、具体。'}, {'role': 'user', 'content': prompt}])


def llm_feedback_retell(transcript, original_text):
    prompt = f"""你是一位中文表达力教练。用户刚完成一篇文章复述。
原文：{original_text[:600]}
用户复述：{transcript}

请按 JSON 格式返回：
{{
  "suggestion": "30-60 字的改进建议",
  "polish": "润色后的复述版本，保留用户原意但让逻辑更顺畅",
  "comfort": "一句鼓励的话"
}}
只返回 JSON，不要加 markdown 标记。"""
    content = _call_llm([{'role': 'system', 'content': '你是中文表达力教练，擅长复述润色。'}, {'role': 'user', 'content': prompt}])
    parsed = _try_parse_json(content)
    if parsed and all(k in parsed for k in ('suggestion', 'polish', 'comfort')):
        parsed['overlap'] = round(similarity(transcript, original_text), 2)
        return parsed
    return None


def llm_feedback_free(transcript, topic, method):
    prompt = f"""你是一位中文表达力教练。用户刚完成一段主动即兴表达。
话题：{topic}
使用方法：{method}
用户表达：{transcript}

请按 JSON 格式返回：
{{
  "suggestion": "30-60 字的改进建议",
  "rewrite": "润色后的版本",
  "comfort_message": "一句鼓励的话",
  "metrics_display": {{
    "relevance_feedback": "主题相关度评价",
    "structure_feedback": "结构框架评价",
    "density_feedback": "观点密度评价",
    "habit_feedback": "语言习惯评价"
  }}
}}
只返回 JSON，不要加 markdown 标记。"""
    content = _call_llm([{'role': 'system', 'content': '你是中文表达力教练，擅长即兴表达分析。'}, {'role': 'user', 'content': prompt}])
    parsed = _try_parse_json(content)
    if parsed and all(k in parsed for k in ('suggestion', 'rewrite', 'comfort_message', 'metrics_display')):
        # Provide backend metrics so the app can still record them
        parsed['metrics_backend'] = {
            'relevance_score': random.randint(6, 10),
            'structure_score': random.randint(6, 10),
            'density_score': random.randint(6, 10),
            'habit_count': habit_count(transcript)
        }
        return parsed
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def format_feedback(module, transcript, context):
    if module == 'qa':
        # Try LLM first, fall back to heuristic
        llm = llm_feedback_qa(transcript, context.get('topic', ''), context.get('method', ''))
        if llm:
            return llm
        return feedback_qa(transcript, context.get('topic', ''), context.get('method', ''))
    elif module == 'retell':
        llm = llm_feedback_retell(transcript, context.get('original', ''))
        if llm:
            return llm
        return feedback_retell(transcript, context.get('original', ''))
    elif module == 'free':
        llm = llm_feedback_free(transcript, context.get('topic', ''), context.get('method', ''))
        if llm:
            return llm
        return feedback_free(transcript, context.get('topic', ''), context.get('method', ''))
    return "继续加油！"
