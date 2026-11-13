"""Opt-in spoken-answer policy; heuristics do not check factual correctness."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ReplyPolicy:
    intent: str
    prompt: str
    max_tokens: int


def requested_transform(text):
    """Preserve explicit repetition/translation instead of calling it echo."""
    value = text.strip().casefold()
    return bool(re.match(r'^(?:请(?:你|帮我)?|帮我|麻烦你)?(?:重复|复述|翻译)', value)
                or re.match(r'^(?:(?:please|can you|could you|would you)\s+)?(?:repeat|translate|say exactly)\b', value))


def reply_policy(text, language='zh', history=()):
    if language not in ('zh', 'en'):
        raise ValueError('language must be zh or en')
    value = ' '.join(text.strip().casefold().split())
    if not value:
        raise ValueError('text must not be empty')
    if requested_transform(value):
        intent = 'transform'
    elif history and (re.match(r'^(?:那|那么|所以|然后|为什么|具体|怎么|怎样|能不能|再|举个|举一个|举例)', value)
                      or re.match(r'^(?:why|how|what about|then|so|can you (?:elaborate|give|explain|show)|give (?:me )?(?:an?|one) (?:concrete |simple )?example)\b', value)):
        intent = 'followup'
    elif (re.search(r'什么是|是什么|为什么|为何|区别|原理|解释|相比|一样吗|有什么|有哪些|含义|特点', value)
          or re.match(r'^(?:what (?:is|are)|why|explain|how (?:does|do)|what.s the difference)\b', value)):
        intent = 'knowledge'
    elif (re.search(r'怎么做|怎样做|如何|步骤|建议|怎么开始', value)
          or re.match(r'^(?:how (?:can|should)|give (?:me )?(?:some |a )?(?:advice|suggestion)|suggest)\b', value)):
        intent = 'procedure'
    else:
        intent = 'chat'
    base = {
        'zh': '你是离线语音助手。直接回答当前问题，沿用对话中的姓名。不知道就说不知道。不承诺稍后回答，没执行操作不能说已完成。',
        'en': "Answer the current question directly. Preserve names from this conversation. Say when you do not know. Do not promise a later answer or claim an unperformed operation.",
    }[language]
    style = {
        'zh': {
            'chat': '用一句简短、完整的口语回答。',
            'knowledge': '用两句简短口语，不超过60字：先讲核心事实，再给一个例子。只说确定的内容。',
            'followup': '用两句简短口语，不超过60字，补充一个新解释或具体做法，不重复上一回答。',
            'procedure': '用两句简短口语，不超过60字：先给直接建议，再给一个可执行步骤。',
            'transform': '按用户要求翻译或复述，保留所需原文，不另加解释。',
        },
        'en': {
            'chat': 'Use one short, complete spoken sentence.',
            'knowledge': 'Use two short spoken sentences, at most 35 words: a key fact and one simple example.',
            'followup': 'Answer the follow-up in two short spoken sentences, at most 35 words, adding a new explanation or step instead of repeating the last answer.',
            'procedure': 'Give a direct suggestion and one actionable step in two short spoken sentences, at most 35 words.',
            'transform': 'Translate or repeat exactly as requested, preserving the required text without extra explanation.',
        },
    }[language][intent]
    budget = {'chat': 48, 'knowledge': 80, 'followup': 80, 'procedure': 80, 'transform': 96}[intent]
    return ReplyPolicy(intent, base + ' ' + style, budget)


_ENGLISH_PLACEHOLDERS = frozenset({
    'ok', 'okay', 'hmm', 'pleasewait', 'onemoment', 'holdon',
    'letmethink', 'letmethinkaboutit', 'illthinkaboutit', 'iwillthinkaboutit',
    'letmecheck', 'illgetbacktoyou', 'iwillgetbacktoyou',
    'illanswerlater', 'iwillanswerlater', 'ineedamomenttothink',
    'thatsagoodquestion', 'thatisagoodquestion', 'thisisaninterestingquestion',
    'greatquestion', 'goodquestion',
})
# Every Chinese atom in the finite regex below starts with one of these.
# Its outer repetition cannot change the first atom's initial. Review this
# set and its generated-grammar tests whenever extending that regex.
_PLACEHOLDER_INITIALS = frozenset('好嗯这关对我让先思想考查稍一等然请正') | frozenset(
    phrase[0] for phrase in _ENGLISH_PLACEHOLDERS)


def _placeholder(text):
    from answer_quality import normalize
    value = normalize(text)
    chinese = re.fullmatch(
        r'(?:好的|好|嗯|这个问题很有趣|这是个好问题|这是一个好问题|这个问题很重要|'
        r'(?:(?:这个问题|关于这个问题|对于这个问题)?(?:我(?:需要|要|会)?|让我)?(?:先)?'
        r'(?:思考一下|想一想|想想|考虑一下|查一下|查询一下|查一查))|'
        r'(?:(?:我会|我将|稍后|一会儿|等会儿|然后)(?:再)?(?:回答你|答复你|告诉你|给你答复))|'
        r'请稍等|稍等|等一下|正在思考|正在查询|我需要一点时间思考|'
        r'我会(?:认真)?(?:思考|考虑)(?:一下)?(?:后|之后)(?:再)?(?:告诉|回答|答复)你)+', value)
    english = value in _ENGLISH_PLACEHOLDERS
    return bool(chinese or english)


def guard_first_content(deltas, question, language='zh', issues=None, max_prefix_chars=512):
    """Opt-in streaming gate for finite placeholder patterns and exact echo.

    The prefix is held until a non-placeholder clause is available, or until
    its normalized initial excludes every finite placeholder atom and its
    text has diverged from the question. Subsequent deltas remain streamed.
    This is not a factual checker and does
    not prove that an arbitrary non-placeholder clause contains useful facts.
    Explicit translation/repetition is exempt from the placeholder/echo rule.
    Prefix work is bounded; cancellation closes the upstream generator.
    """
    from answer_quality import normalize
    if language not in ('zh', 'en'):
        raise ValueError('language must be zh or en')
    if not isinstance(max_prefix_chars, int) or max_prefix_chars < 1:
        raise ValueError('max_prefix_chars must be a positive integer')
    fallback = ('这次没有给出有效回答，请换一种问法。' if language == 'zh'
                else 'I did not produce a useful answer. Please rephrase the question.')
    problems = issues if issues is not None else []

    def mark(reason):
        if reason not in problems:
            problems.append(reason)

    def boundary(text, final=False):
        for index, char in enumerate(text):
            if char not in '。！？；，,.!?;\n':
                continue
            if char == '.':
                if index == len(text) - 1 and not final:
                    continue
                if index and index + 1 < len(text) and text[index - 1].isdigit() and text[index + 1].isdigit():
                    continue
            return index + 1
        return None

    source = iter(deltas)
    try:
        phatic = normalize(question) in {
            '谢谢', '谢谢你', '好的', '好', '明白了', '知道了', '嗯', '收到', '再见',
            '你好', '是', '是的', '对', '对的',
            'thanks', 'thankyou', 'okay', 'ok', 'gotit', 'understood', 'hello', 'hi',
            'goodmorning', 'goodnight', 'bye', 'yes', 'thatsright',
        }
        acknowledgements = {'好的', '好', '嗯', '收到', 'ok', 'okay', 'hmm'}
        if requested_transform(question):
            nonempty = False
            for delta in source:
                nonempty = nonempty or bool(delta.strip())
                yield delta
            if not nonempty:
                mark('empty')
                yield fallback
            return
        buffer, held = '', ''
        released = False
        seen = 0
        question_key = normalize(question)
        for delta in source:
            if released:
                yield delta
                continue
            buffer += delta
            while True:
                cut = boundary(buffer)
                if cut is None:
                    if seen + len(buffer) > max_prefix_chars:
                        mark('prefix_limit')
                        yield fallback
                        return
                    key = normalize(buffer)
                    if (not held and key and not question_key.startswith(key)
                            and key[0] not in _PLACEHOLDER_INITIALS):
                        # Appending text cannot change this initial or undo
                        # divergence from the question. This proves only
                        # exclusion from the current finite predicates; it
                        # does not establish semantic usefulness or truth.
                        yield buffer
                        released = True
                        buffer = ''
                    break
                seen += cut
                if seen > max_prefix_chars:
                    mark('prefix_limit')
                    yield fallback
                    return
                unit, buffer = buffer[:cut], buffer[cut:]
                candidate = held + unit
                key = normalize(candidate)
                if not key:
                    held = ''
                    continue
                if key == question_key and not phatic:
                    mark('exact_echo')
                    held = ''
                    continue
                if question_key.startswith(key) and not phatic:
                    held = candidate
                    continue
                if _placeholder(candidate) and not (phatic and key in acknowledgements):
                    mark('placeholder_prefix')
                    held = ''
                    continue
                yield candidate
                if buffer:
                    yield buffer
                released = True
                buffer, held = '', ''
                break
        if released:
            return
        tail = held + buffer
        if not normalize(tail):
            mark('placeholder_only' if 'placeholder_prefix' in problems else 'empty')
            yield fallback
        elif normalize(tail) == question_key and not phatic:
            mark('exact_echo')
            yield fallback
        elif _placeholder(tail) and not (phatic and normalize(tail) in acknowledgements):
            mark('placeholder_only')
            yield fallback
        else:
            yield tail
    finally:
        close = getattr(source, 'close', None)
        if close is not None:
            close()
