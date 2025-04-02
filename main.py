from decompose import decompose_single
from answering import GoogleChatAgent
from prompts_library import logic_ask_question, logic_verify_predicate, logic_prove_true, logic_prove_false, logic_final_judgment
from args import *
from dotenv import load_dotenv
load_dotenv()

def main(claim, temperature=0.7, max_tokens = 1024):
    decompse_result = decompose_single(claim)
    agent = GoogleChatAgent(temperature=temperature, max_tokens=max_tokens)

    predicates = [p['predicate'] + ":::" + p['verification_instructions'] for p in decompse_result['predicates']]
    question_count = 1
    question = decompse_result['followup_questions']
    pre= '\n'.join(predicates)
    # print(f"[DEBUG] generat predicates{pre}")
    # print(f"[DEBUG] followup question: {question}")

    # stage 1: answering the questions
    # print(f"[DEBUG] ENTER STAGE 1")
    QA_pairs = {}
    for question in decompse_result['followup_questions']:
        prompt = logic_ask_question.format(
            claim=claim,
            predicates = "\n".join(predicates),
            question = question
        )
        # print(f"[DEBUG] asking question: {question}")
        QA_pairs[question] = agent(prompt)
        agent.reset_messages()

    # while question_count <= len(question):
    #     question_count += 1
    #     prompt = f"**Question {question_count}**: {question}"
    #     print(f"[DEBUG] asking question: {question[question_count-1]}")
    #     QA_pairs[question[question_count-1]] = agent(prompt)

    # stage 2: verify the predicates
    verify_pairs = {}
    QA = "\n".join([f"**Question: {k}\n**Answer**: {v}" for k, v in QA_pairs.items()])
    for predicate in predicates:
        prompt = logic_verify_predicate.format(
            predicate = predicate,
            QA_pairs = QA
        )
        # print(f"[DEBUG] verifying predicate: {predicate}")
        verify_pairs[predicate] = agent(prompt)
        agent.reset_messages()

    # for predicate in predicates:
    #     promtpt = f"**Predicate**: {predicate}"
    #     print(f"[DEBUG] verifying predicate: {predicate}")
    #     verify_pairs[predicate] = agent(promtpt)

    # stage 3: generate 
    current_state = agent.memory_length()
    verify = "\n".join([f"**Predicate**: {k}\n**Verification**: {v}" for k, v in verify_pairs.items()])

    # FALSE PROVE
    prompt = logic_prove_false.format(
        claim=claim,
        QA_pairs=QA,
        predicate_verifications=verify
    )
    false_response = agent(prompt)
    # print(f"[DEBUG] false response: {false_response}")

    false_cuts = agent.cut_messages(current_state)

    # TRUE PROVE
    prompt = logic_prove_true.format(
        claim=claim,
        QA_pairs=QA,
        predicate_verifications=verify
    )
    true_response = agent(prompt)
    # print(f"[DEBUG] true response: {true_response}")

    agent.extend_messages(false_cuts)

    # final synthesis
    prompt = logic_final_judgment.format(
        claim=claim,
        refuting_arguments=false_response,
        supporting_arguments=true_response
    )
    result = agent(prompt)  

    # agent.show_messages()
    return result

    



if __name__ == '__main__':
    input_claim = input("Enter a claim: ")
    print(main(input_claim, temperature=args.temperature, max_tokens=args.max_token))