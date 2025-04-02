import openai
from prompts_library import logic_decompose_domain
import re


from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI()


def extract_claim_data(llm_output):
    """
    Extracts claim, predicates, and follow-up questions from the LLM's structured output.
    
    Parameters:
        llm_output (str): The text output from the LLM.

    Returns:
        dict: A dictionary containing the claim, predicates, and follow-up questions.
    """
    # Extract predicates
    predicates_section = re.search(r"Predicates:\n(.+?)(?:\nFollowup Question|$)", llm_output, re.DOTALL)
    predicates_text = predicates_section.group(1).strip() if predicates_section else ""
    predicates = re.findall(r"(.+?) ::: (.+)", predicates_text)

    # Extract follow-up questions
    followup_questions = re.findall(r"Followup Question: (.+)", llm_output)

    return {
        "predicates": [{"predicate": p[0].strip(), "verification_instructions": p[1].strip()} for p in predicates],
        "followup_questions": [q.strip() for q in followup_questions],
    }

def decompose_single(claim, temperature=0.7, max_tokens=1024):
    user_prompt = """Claim: %s\n>>>>>>"""
    prompt = user_prompt % claim

    # Call the OpenAI API
    try:
        response = client.chat.completions.create(
        # response = client.beta.chat.completions.parse(
            model="gpt-3.5-turbo",  # Replace with the engine/model you're using
            messages=[
                {"role": "system", "content": logic_decompose_domain},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,  # Adjust this as needed
            temperature=temperature,  # Lower temperature for deterministic results
        )

        output = response.choices[0].message.content
        # output = response.choices[0].message.parsed
        return extract_claim_data(output)

    except Exception as e:
        return f"Error during API call: {e}"

if __name__ == '__main__':
    claim = """
Scientists have recently discovered that the moon is actually a giant, ancient spaceship built by an advanced alien civilization over 10,000 years ago. The discovery was made after studying the unusual geometric patterns found in the moon’s craters using high-powered telescopes. These findings are being kept secret by world governments, and the real purpose of the moon, which is believed to be a monitoring station for extraterrestrial life forms, is still under investigation. In fact, recent analysis of moon rocks has revealed traces of a previously unknown metal that is believed to be part of the alien technology. Researchers from MIT and Harvard are collaborating on the project, but no official publication has been released yet.
    """
    result = decompose_single(claim)

    print(result)
