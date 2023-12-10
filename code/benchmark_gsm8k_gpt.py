import concurrent.futures
from tqdm import tqdm
from datasets import load_dataset
from utils import *

OUTPUT_PATH = "./outputs/gpt_3.5_turbo_0301_original_cot.txt"


gsm8k = load_dataset("gsm8k", "main")
gsm8k_test = gsm8k["test"]


def main():
    prompt_original = open("./prompt_lib/prompt_original.txt").read()

    test_questions = gsm8k_test["question"][:]
    test_ans_gold = gsm8k_test["answer"][:]

    total_token_tokens_count = 0
    prompt_tokens_count = 0
    completion_tokens_count = 0

    # 使用 ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(
            tqdm(
                executor.map(
                    process_question,
                    test_questions,
                    test_ans_gold,
                    [prompt_original] * len(test_questions),
                ),
                total=len(test_questions),
            )
        )

    # sum three token counts
    total_token_tokens_count = sum([result[1] for result in results])
    prompt_tokens_count = sum([result[2] for result in results])
    completion_tokens_count = sum([result[3] for result in results])
    print(f"total_token_tokens_count: {total_token_tokens_count}")
    print(f"prompt_tokens_count: {prompt_tokens_count}")
    print(f"completion_tokens_count: {completion_tokens_count}")

    with open(OUTPUT_PATH, "w") as fd:
        for result in results:
            fd.write(result[0])


if __name__ == "__main__":
    main()
_, _, _ = parse_pred_ans(OUTPUT_PATH)
