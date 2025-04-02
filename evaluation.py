import pandas as pd
import re
from args import *
from main import main
import os
import traceback
import pprint
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = f"HoVerDev/processed/{args.hover_num_hop}_hop_df_new.json"
STORE_PATH = f"EvalResults/{args.hover_num_hop}_hop_df_new_eval.json"

if __name__ == '__main__':
    DATA_PATH = os.path.join(os.getcwd(), DATA_PATH)
    STORE_PATH = os.path.join(os.getcwd(), STORE_PATH)

    data_df = pd.read_json(DATA_PATH)

    if not os.path.exists(STORE_PATH):
        print(f"Creating new store file at {STORE_PATH}")
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        store_df = data_df[['uid', 'claim', 'supporting_facts', 'label', 'hpqa_id']].copy()
        store_df['result'] = store_df['label']  
        store_df['status'] = 0 
    else:
        store_df = pd.read_json(STORE_PATH)

    try_count = 0
    while (store_df['status'] == 0).any():
        
        status_zero_df = store_df[store_df['status'] == 0]
        
        random_row = status_zero_df.sample(n=1)
        claim = random_row['claim'].values[0]
        try:
            result = main(claim, temperature=args.temperature, max_tokens=args.max_token)
            print(f"Working on claim: {claim}")
            pprint.pprint(result)

            if "NOT_SUPPORTED" in result:
                res = "NOT_SUPPORTED"
            elif "SUPPORTED" in result:
                res = "SUPPORTED"
            store_df.loc[random_row.index, 'result'] = res
            store_df.loc[random_row.index, 'status'] = 1  
            try_count = 0
        except Exception as e: # print error and its traceback

            print(f"Error: {e}")
            traceback.print_exc()
            if try_count >= 3:
                print("Maximum tries reached. Exiting...")
                break
            else:
                print(f"Retrying... ({try_count+1}/3)")
                try_count += 1
                continue
    store_df.to_json(STORE_PATH, index=False)

    if (store_df['status'] == 0).any():
        print ("Some claims are still not evaluated!")
    else: 
        print("All claims are evaluated!")

    # evaluaion
    result_path = os.path.join(os.getcwd(), "EvalResults/{hover_num_hop}_hop_df_new_eval.json")

    for num in ["two", "three", "four"]:
        if os.path.exists(result_path.format(hover_num_hop=num)):
            df = pd.read_json(result_path.format(hover_num_hop=num))
            tested_df = df[df['status'] == 1]

            print(f"For hop {num}: {len(tested_df)} line of data are tested")
            print(f"Accuracy: {tested_df['result'].eq(tested_df['label']).mean()}")
            print(classification_report(tested_df['label'], tested_df['result']))
            print(confusion_matrix(tested_df['label'], tested_df['result']))
        else:
            print(f"No data for hop {num}")

 

