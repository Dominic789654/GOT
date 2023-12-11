# Repository for Project of DSAA6000D

![HKUSTgz](./figs/hkust-logo.png)  
This repo is the code implementation of the **HKUSTgz DSAA6000D Graph Processing and Analytics**.  
The course is taught by Prof. [Luo Qiong](https://www.cse.ust.hk/~luo/).

## Setup Instructions

1. Install the required dependencies using the command: `pip install -r requirements.txt`

2. Insert your ChatGPT API key into the `./code/api_pool.py` file. If you need an API key to test the code, please contact LIU Xiang.

3. Modify the `run.sh` script to select the experiment you wish to test.



# Mini Survey introduction
## Title 
**Mini Survey on Graph of Thought**
## Abstrct
With the success of Large Language Models (LLMs) in various tasks, enhancing their reasoning capabilities has become a focal point of research. Chain-of-Thought (CoT)[1] is one such approach that significantly boosts the reasoning abilities of LLMs by generating a series of intermediate reasoning steps. The core idea behind the CoT prompting method is to provide a few chained thought examples in the prompts, thereby aiding the model in understanding and learning multi-step reasoning. Remarkably, this enhancement is achieved without the need for fine-tuning or pre-training, positioning CoT as a cost-effective technology for LLMs. However, while the CoT method has achieved some success in reasoning tasks, its performance still leaves room for improvement when dealing with complex problems involving multiple reasoning steps. To address this, researchers introduced graph-based reasoning methods, such as Graph-of-Thought, which represent the reasoning process as a graph, capturing the non-sequential nature of human thought more effectively. This mini survey first introduces the basic concepts and applications of CoT and then delves into how graph-based CoT[2], [3] methods further enhance the reasoning capabilities of models.
## Reference
[1]	J. Wei et al., “Chain-of-Thought Prompting Elicits Reasoning in Large Language Models,” Adv. Neural Inf. Process. Syst., vol. 35, pp. 24824–24837, Dec. 2022.  
[2]	M. Besta et al., “Graph of Thoughts: Solving Elaborate Problems with Large Language df_layers_trace_lion_ftModels.” arXiv, Aug. 21, 2023. Accessed: Oct. 20, 2023. [Online]. Available: http://arxiv.org/abs/2308.09687  
[3]	S. Jiang et al., “Resprompt: Residual Connection Prompting Advances Multi-Step Reasoning in Large Language Models.” arXiv, Oct. 07, 2023. Accessed: Oct. 20, 2023. [Online]. Available: http://arxiv.org/abs/2310.04743  