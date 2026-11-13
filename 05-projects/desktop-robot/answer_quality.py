"""Conservative completed-answer checks; experimental, not a fact checker."""
import re


def normalize(text):
    return ''.join(c.casefold() for c in text if c.isalnum())


def check_answer(question, answer, language='zh'):
    normalized = normalize(answer)
    if not normalized:
        reason = 'empty'
    elif re.fullmatch(
        r'(?:好的|好|嗯|请稍等|稍等|让我想想|让我思考一下|我需要思考一下|我想一想|稍后回答你|我会稍后回答|正在思考|正在查询)+', normalized
    ) or normalized in {'letmethink', 'letmethinkaboutit', 'illthinkaboutit', 'pleasewait', 'illgetbacktoyou'}:
        reason = 'placeholder_only'
    elif normalized == normalize(question) and not any(
        marker in question.casefold() for marker in ('复述', '重复', '翻译', 'repeat', 'translate', 'say exactly')
    ):
        reason = 'exact_echo'
    else:
        return answer, None
    fallback = ('这次我没有生成有效回答，请把问题说得更具体一些。' if language == 'zh'
                else 'I could not produce a useful answer this time. Please make the question more specific.')
    return fallback, reason
