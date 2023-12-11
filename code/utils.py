import requests as requests
import re
from tenacity import retry, stop_after_attempt, wait_chain, wait_fixed
import random
from api_pool import api_pool
from tqdm import trange

key_pool = api_pool
print(f"Number of api keys {len(key_pool)}")
TEMPERATURE = 0.0

@retry(
    wait=wait_chain(
        *[wait_fixed(3) for i in range(3)]
        + [wait_fixed(5) for i in range(2)]
        + [wait_fixed(10)]
    )
)
def completion_with_backoff(params):
    api_key = random.choice(key_pool)
    headers = {
        "Authorization": "Bearer " + api_key,
    }
    result = requests.post(
        "https://aigptx.top/v1/chat/completions",
        headers=headers,
        json=params,
        stream=False,
    )
    return result.json()


def test_answer(pred_str, ans_str):
    pattern = "\d*\.?\d+"
    pred_str = pred_str.replace(",", "")
    pred = re.findall(pattern, pred_str)
    if len(pred) >= 1:
        pred = pred[-1]
        gold = re.findall(pattern, ans_str)
        gold = gold[-1]
        # print(pred, gold)
        return pred == gold
    else:
        return False


def parse_pred_ans_SC(filename):
    with open(filename) as fd:
        lines = fd.readlines()
    mf_ans, a = None, None  # mf_ans for Most Frequent Answer
    num_q, acc = 0, 0
    current_mode = "none"
    questions = []
    ans_most_freq = []
    ans_gold = []
    for l in lines:
        if l.startswith("Question:"):
            if mf_ans is not None and a is not None:
                questions.append(q)
                ans_most_freq.append(mf_ans)
                ans_gold.append(a)
                if test_answer(mf_ans, a):
                    acc += 1
            current_mode = "q"
            q = l
            num_q += 1
        elif l.startswith("Most Frequent Answer:"):
            current_mode = "mf_ans"
            mf_ans = l
        elif l.startswith("A_gold:"):
            current_mode = "a"
            a = l
        else:
            if current_mode == "q":
                q += l
            elif current_mode == "mf_ans":
                mf_ans += l
            elif current_mode == "a":
                a += l
            else:
                raise ValueError(current_mode)

    questions.append(q)
    ans_most_freq.append(mf_ans)
    ans_gold.append(a)
    if test_answer(mf_ans, a):
        acc += 1
    print("num_q %d correct %d ratio %.4f" % (num_q, acc, float(acc / num_q)))
    return questions, ans_most_freq, ans_gold


def parse_pred_ans(filename):
    with open(filename) as fd:
        lines = fd.readlines()
    am, a = None, None
    num_q, acc = 0, 0
    current_mode = "none"
    questions = []
    ans_pred = []
    ans_gold = []
    for l in lines:
        if l.startswith("Question:"):
            if am is not None and a is not None:
                questions.append(q)
                ans_pred.append(am)
                ans_gold.append(a)
                if test_answer(am, a):
                    acc += 1
            current_mode = "q"
            q = l
            num_q += 1
        elif l.startswith("A_model:"):
            current_mode = "am"
            am = l
        elif l.startswith("A_gold:"):
            current_mode = "a"
            a = l
        else:
            if current_mode == "q":
                q += l
            elif current_mode == "am":
                am += l
            elif current_mode == "a":
                a += l
            else:
                raise ValueError(current_mode)

    questions.append(q)
    ans_pred.append(am)
    ans_gold.append(a)
    if test_answer(am, a):
        acc += 1
    print("num_q %d correct %d ratio %.4f" % (num_q, acc, float(acc / num_q)))
    return questions, ans_pred, ans_gold


def test_finished(ans_model):
    if "answer is" in ans_model:
        return True
    else:
        return False


def extract_ans(ans_model):
    ans_model = ans_model.split("\n")
    ans = []
    residual = []
    for li, al in enumerate(ans_model):
        ans.append(al)
        if "answer is" in al:
            break
    residual = list(ans_model[li + 1 :])
    ans = "\n".join(ans)
    residual = "\n".join(residual)
    return ans, residual


def process_question_multiple_times(q, a, prompt_original, num_attempts=10):
    answers = []
    total_tokens_count = 0
    prompt_tokens_count = 0
    completion_tokens_count = 0
    for _ in trange(num_attempts):
        result, tokens_total, tokens_prompt, tokens_completion = process_question(q, a, prompt_original)
        # Extract the answer from the result
        ans = result.split("\nA_model:\n")[1].split("\nA_gold:\n")[0]
        pattern = "\d*\.?\d+"
        pred_ans = ans.replace(",", "")
        pred = re.findall(pattern, pred_ans)
        if len(pred) >= 1:
            pred = pred[-1]
        else:
            pred = '0'
        answers.append(pred)

        # Accumulate token counts
        total_tokens_count += tokens_total
        prompt_tokens_count += tokens_prompt
        completion_tokens_count += tokens_completion

    # Find the most frequent answer
    most_frequent_ans = max(set(answers), key=answers.count)
    return (
        f"Question:\n{q}\nMost Frequent Answer:\n{most_frequent_ans}\nA_gold:\n{a}\n\n",
        total_tokens_count,
        prompt_tokens_count,
        completion_tokens_count
    )


            
def process_question(q, a, prompt_original):
    try:
        prompt_q = prompt_original + "\n\nQuestion: " + q + "\n"
        # print(prompt_q)
        # print("Temperature: ", TEMPERATURE)
        response = completion_with_backoff(
            {
                "model": "gpt-3.5-turbo-0301",
                "messages": [
                    {
                        "role": "system",
                        "content": "Follow the given examples and answer the following question.",
                    },
                    {"role": "user", "content": prompt_q},
                ],
                "temperature": TEMPERATURE,
            }
        )
        # print(response)
        ans_model = response["choices"][0]["message"]["content"]
        total_token_tokens_count = response["usage"]["total_tokens"]
        prompt_tokens_count = response["usage"]["prompt_tokens"]
        completion_tokens_count = response["usage"]["completion_tokens"]
        ans_, residual = extract_ans(ans_model)
        return (
            f"Question:\n{q}\nA_model:\n{ans_}\nA_gold:\n{a}\n\n",
            total_token_tokens_count,
            prompt_tokens_count,
            completion_tokens_count,
        )
    except Exception as e:
        # Print the error message if an exception occurs
        error_message = str(e)
        print(error_message)
        return f"An error occurred: {error_message}"
