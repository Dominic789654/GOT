import re
import time
import numpy as np
import concurrent.futures
import requests as requests
from tqdm import tqdm
from datasets import load_dataset
import random
from api_pool import api_pool
key_pool = api_pool
print(f"Number of api keys {len(key_pool)}")     

OUTPUT_PATH = "./cot/gpt_3.5_turbo_0301_original_cot.txt"


gsm8k = load_dataset('gsm8k', 'main')
gsm8k_test = gsm8k['test']


from tenacity import (
    retry,
    stop_after_attempt,
    wait_chain,
    wait_fixed
) 

@retry(wait=wait_chain(*[wait_fixed(3) for i in range(3)] +
                       [wait_fixed(5) for i in range(2)] +
                       [wait_fixed(10)]))
def completion_with_backoff(**kwargs):
    api_key = random.choice(key_pool)
    headers = {
        "Authorization": 'Bearer ' + api_key,
    }
    result = requests.post(
        "https://api.ohmygpt.com//v1/chat/completions",
        headers=headers,
        json=params,
        stream=False
    )
    return result.json()

def test_answer(pred_str, ans_str):
    pattern = '\d*\.?\d+'
    # pattern = '-?\d+\.?\d*'
    pred_str = pred_str.replace(",","")
    pred = re.findall(pattern, pred_str)
    if(len(pred) >= 1):
        # print(pred_str)
        pred = pred[-1]
        gold = re.findall(pattern, ans_str)
        # print(ans_str)
        gold = gold[-1]
        return pred == gold
    else: return False

def parse_decomposed_step(filename):
    with open(filename) as fd: lines = fd.readlines()
    am, a = None, None
    num_q, acc = 0, 0
    current_mode = 'none'
    questions = []
    ans_pred = []
    ans_gold = []
    for l in lines:
        if(l.startswith('Q: ')):
            if(am is not None and a is not None):
                questions.append(q)
                ans_pred.append(am)
                ans_gold.append(a)
            current_mode = 'q'
            q = l
            num_q += 1
        elif(l.startswith('A_model:')):
            current_mode = 'am'
            am = l
        elif(l.startswith('A:')):
            current_mode = 'a'
            a = l
        else:
            if(current_mode == 'q'): q += l
            elif(current_mode == 'am'): am += l
            elif(current_mode == 'a'): a += l
            else:
                raise ValueError(current_mode)
                
    questions.append(q)
    ans_pred.append(am)
    ans_gold.append(a)
    decomposed_steps=[]
    for i in range(len(ans_pred)):
        # current_step = ans_pred[i].split('we need to know: ')[-1]
        # cur_step = ans_pred[i].split('\n')
        # if 'A_model' not in cur_step:
        decomposed_steps.append([ cur_step for cur_step in ans_pred[i].strip().split('\n') if 'A_model' not in cur_step])
    return questions, ans_pred, ans_gold, decomposed_steps


def parse_pred_ans(filename):
    with open(filename) as fd: lines = fd.readlines()
    am, a = None, None
    num_q, acc = 0, 0
    current_mode = 'none'
    questions = []
    ans_pred = []
    ans_gold = []
    for l in lines:
        if(l.startswith('Question:')):
            if(am is not None and a is not None):
                questions.append(q)
                ans_pred.append(am)
                ans_gold.append(a)
                if(test_answer(am, a)):
                    acc += 1
            current_mode = 'q'
            q = l
            num_q += 1
        elif(l.startswith('A_model:')):
            current_mode = 'am'
            am = l
        elif(l.startswith('A_gold:')):
            current_mode = 'a'
            a = l
        else:
            if(current_mode == 'q'): q += l
            elif(current_mode == 'am'): am += l
            elif(current_mode == 'a'): a += l
            else:
                raise ValueError(current_mode)
                
    questions.append(q)
    ans_pred.append(am)
    ans_gold.append(a)
    if(test_answer(am, a)):
        acc += 1
    print('num_q %d correct %d ratio %.4f' % (num_q, acc, float(acc / num_q)))
    return questions, ans_pred, ans_gold

def test_finished(ans_model):
    if('answer is' in ans_model): return True
    else: return False

def extract_ans(ans_model):
    ans_model = ans_model.split('\n')
    ans = []
    residual = []
    for li, al in enumerate(ans_model):
        ans.append(al)
        if('answer is' in al):
            break
    residual = list(ans_model[li + 1:])
    ans = '\n'.join(ans)
    residual = '\n'.join(residual)
    return ans, residual


def process_question(q, a, prompt_original):
    try:
        prompt_q = prompt_original + '\n\nQuestion: ' + q + '\n'
        response = completion_with_backoff(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Follow the given examples and answer the following question."},
                {"role": "user", "content": prompt_q},
            ],
            temperature=0,
            # stop='\n\n',
            top_p=0.9
        )
        ans_model = response['choices'][0]['message']['content']
        ans_, residual = extract_ans(ans_model)
        return f'Question:\n{q}\nA_model:\n{ans_}\nA_gold:\n{a}\n\n'
    except Exception as e:
        # Print the error message if an exception occurs
        error_message = str(e)
        return f'An error occurred: {error_message}'


def main():
    prompt_original = open('./prompt_lib/prompt_original.txt').read()

    test_questions =  gsm8k_test['question']
    test_ans_gold =  gsm8k_test['answer']

    # 使用 ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(tqdm(executor.map(process_question, test_questions, test_ans_gold, [prompt_original]*len(test_questions)), total=len(test_questions)))

    with open(OUTPUT_PATH, 'w') as fd:
        for result in results:
            fd.write(result)

if __name__ == '__main__':
    main()
_, _, _ = parse_pred_ans(OUTPUT_PATH)