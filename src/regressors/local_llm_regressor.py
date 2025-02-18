"""
For a locally deployed model (i.e., `AutoModelForCausalLM`)
"""


import numpy as np
from src.regressors.prompts import construct_few_shot_prompt
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch



def llm_regression(llm, tokenizer, x_train, x_test, y_train, y_test, encoding_type, model_name, add_instr_prefix=False, instr_prefix='The task is to provide your best estimate for "Output". Please provide that and only that, without any additional text.\n\n\n\n\n'):
    examples_test = []
    for x1 in x_test.to_dict('records'):
        examples_test.append(x1)

    fspt = construct_few_shot_prompt(x_train, y_train, x_test, encoding_type=encoding_type)
    full_outputs = []
    outputs = []
    gold    = []
    for x, y in zip(examples_test, y_test):
        gold.append(y)
        if add_instr_prefix:
            inpt = instr_prefix + fspt.format(**x)
        else:
            inpt = fspt.format(**x)
        inputs = tokenizer(inpt, return_tensors="pt").to(llm.device)
        output = llm.generate(inputs["input_ids"], max_new_tokens=12)
        output = tokenizer.decode(output[0].tolist()[inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        output = output.strip().split('\n')[0].strip() 
        full_outputs.append(output)
        # output = llm(inpt, stop=['\n'], max_tokens=12).strip().split('\n')[0].strip() # For davinci

        try:
            output = float(output)
        except Exception as e:
            print(e)
            print(output)
            output = 0.0
        outputs.append(output)

    y_predict = np.array(outputs)
    y_test    = np.array(gold)

    return {
        'model_name': model_name,
        'full_outputs': full_outputs,
        'x_train'   : x_train,
        'x_test'    : x_test,
        'y_train'   : y_train,
        'y_test'    : y_test,
        'y_predict' : y_predict,
    }

