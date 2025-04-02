logic_decompose_domain = """
You are given a problem description and a claim. 
Remember you do not need to verify the claim, just identify the domain of the claim. 
The task is to:
1) define all the predicates in the claim.
2) parse the predicates into follow-up questions that form a logical chain of reasoning.
3) answer the follow-up questions.

your output should include following components:
1. **Predicates**: Logical representations of specific assertions in the claim, paired with verification instructions. Write each predicate in the format:
   Predicate ::: Verification Instructions
   
2. **Followup Questions**: A list of questions to further explore or verify the claim and its context.

Output your response strictly in the following format:
Claim: [The provided claim]
>>>>>>
Predicates:
[Predicate 1] ::: [Verification Instructions 1]
[Predicate 2] ::: [Verification Instructions 2]
...

Followup Question: [Question 1]
Followup Question: [Question 2]
...

### Example:
Claim: Howard University Hospital and Providence Hospital are both located in Washington, D.C.
>>>>>>
Predicates:
Location(Howard Hospital, Washington D.C.) ::: Verify Howard University Hospital is located in Washington, D.C.
Location(Providence Hospital, Washington D.C.) ::: Verify Providence Hospital is located in Washington, D.C.

Followup Question: Where is Howard Hospital located?
Followup Question: Is Howard University Hospital listed among major healthcare providers in Washington, D.C.?
Followup Question: Where is Providence Hospital located?
Followup Question: Is Providence Hospital listed among major healthcare providers in Washington, D.C.?
------
Claim: An IndyCar race driver drove a Formula 1 car designed by Peter McCool during the 2007 Formula One season.
>>>>>>
Predicates: 
Designed(Peter McCool, a Formula 1 car) ::: Verify a Formula 1 car was designed by Peter McCool during the 2007 Formula One season.
Drive(An IndyCar race driver, a Formula 1 car) ::: Verify an IndyCar driver drove a Formula 1 car.

Followup Question: Which Formula 1 car was designed by Peter McCool during the 2007 Formula One season?
Followup Question: What specific contributions did Peter McCool make to the design of Formula 1 cars during that season?
Followup Question: Did an IndyCar driver drive a Formula 1 car designed by Peter McCool during the 2007 Formula One season?
Followup Question: Are there any records of IndyCar drivers transitioning to Formula 1 during the 2007 season?
------
Claim: Thomas Loren Friedman has won more Pulitzer Prizes than Colson Whitehead.
>>>>>>
Predicates: 
Won(Thomas Loren Friedman, Pulitzer Prize) ::: Verify the number of Pulitzer Prizes Thomas Loren Friedman has won.
Won(Colson Whitehead, Pulitzer Prize) ::: Verify the number of Pulitzer Prizes Colson Whitehead has won.

Followup Question: How many Pulitzer Prizes did Thomas Loren Friedman win?
Followup Question: In which categories did Thomas Loren Friedman win his Pulitzer Prizes?
Followup Question: How many Pulitzer Prizes did Colson Whitehead win?
Followup Question: In which categories did Colson Whitehead win his Pulitzer Prizes?
Followup Question: Did Thomas Loren Friedman win more Pulitzer Prizes than Colson Whitehead?
------
Claim: SkyHigh Mount Dandenong (formerly Mount Dandenong Observatory) is a restaurant located on top of Mount Dandenong, Victoria, Australia.
>>>>>>
Predicates:
Location(SkyHigh Mount Dandenong, top of Mount Dandenong, Victoria, Australia) ::: Verify that SkyHigh Mount Dandenong is located on top of Mount Dandenong, Victoria, Australia.
Known(SkyHigh Mount Dandenong, Mount Dandenong Observatory) ::: Verify that SkyHigh Mount Dandenong is formerly known as Mount Dandenong Observatory.

Followup Question: Where is SkyHigh Mount Dandenong located?
Followup Question: What evidence confirms that SkyHigh Mount Dandenong is located on top of Mount Dandenong?
Followup Question: Was SkyHigh Mount Dandenong formerly known as Mount Dandenong Observatory?
Followup Question: Are there historical records documenting the transition from Mount Dandenong Observatory to SkyHigh Mount Dandenong?
------
"""

openai_google_search_tool_description = {
        "type": "function",
        "function": {
            "name": "google_search",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "The term or query string to search on Google."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "The number of top search results to return which should be less than 5."
                    }
                },
                "required": ["search_term", "num_results"],
                "additionalProperties": False
            }
        }
    }

GoogleSearchAgentSystemPrompt = """
You are an intelligent agent trained to answer factual questions step by step. 
For each question, determine the likely domain of the context (e.g., Sports, Science, Art, Computer Science, Actors, Performers, Singers, etc.) to guide your search. 
Then, use the identified domain to refine your reasoning and perform accurate information retrieval.

You need to get all the information that you need to answer the question. 
You can not simply give the link to user and let them search on their own. 
You need to specify "<**END**>" behind the final response that you provide.
You can use the following example steps to answer the question:

Question What is the elevation range for the area that the eastern sector of the
Colorado orogeny extends into?
Thought 1 I need to search Colorado orogeny, find the area that the eastern sector
of the Colorado orogeny extends into, then find the elevation range of the
area.
Action 1 Search[Colorado orogeny]
Observation 1 The Colorado orogeny was an episode of mountain building (an orogeny) in
Colorado and surrounding areas.
Thought 2 It does not mention the eastern sector. So I need to look up eastern
sector.
Action 2 Lookup[eastern sector]
Observation 2 (Result 1 / 1) The eastern sector extends into the High Plains and is called
the Central Plains orogeny.
Thought 3 The eastern sector of Colorado orogeny extends into the High Plains. So I
need to search High Plains and find its elevation range.
Action 3 Search[High Plains]
Observation 3 High Plains refers to one of two distinct land regions
Thought 4 I need to instead search High Plains (United States).
Action 4 Search[High Plains (United States)]
Observation 4 The High Plains are a subregion of the Great Plains. From east to west, the
High Plains rise in elevation from around 1,800 to 7,000 ft (550 to 2,130
m).[3]
Thought 5 High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer
is 1,800 to 7,000 ft.
Action 5 Finish[1,800 to 7,000 ft]
...
The elevation range for the area that the eastern sector of the Colorado orogeny extends into is 1,800 to 7,000 ft (550 to 2,130 m).<**END**>

**Your Task**:
For each question:
1. Follow the workflow to reason about the domain nad topic of the question.
2. Generate the thought process and action search based on the identified domain and topic.
3. Use the specified search query to retrieve information with keywords about the topic and domain.
4. Return the final result if you do not need extra informations anymore(do not use tool_calls anymore).
"""

logic_ask_question = """
You are given a Claim and a set of Predicates. 
Your final goal is to prove the Claim is correct or not with a confidense score.
And you need to verify the Predicates first before you can make a final judgment on the Claim.

**Claim**: 
{claim}

**Predicates**:
{predicates}

Let us begin with several questions to search for enough evidences.
You do not have to verify each predicate and the claim when answering these questions. 
Just focus on the quesion I give and then provide the answer and the reasoning behind it.

**Question**: {question}
"""

logic_verify_predicate = """
Now we collected some evidences from those questions as follows:
{QA_pairs}

let us verify each predicate one by one. 
You should clearly state whether the predicate is true or false and provide the reasoning behind it.
Provide a confidence score (out of 10) to indicate how strongly the evidence supports your conclusion. 
**Predicate**: {predicate}
"""


logic_prove_true = """
We have completed predicate verification and synthesized evidence-based arguments. 
Now, it is time to prove that the claim is true by analyzing all collected information holistically. 


**Questions and Evidence**: 
{QA_pairs}

**Predicate Verification**: 
{predicate_verifications}

**Claim**: 
{claim}

**Task:** 
1. Synthesize a comprehensive reasoning process to **prove that the claim is true**. Incorporate both supporting and refuting arguments, highlighting why the supporting arguments outweigh or negate the refuting ones. 
2. Use retrieved evidence and predicate verification results to substantiate your reasoning. 
3. Provide a confidence score (out of 10) to indicate how strongly the evidence supports the conclusion that the claim is true. 
"""

logic_prove_false = """
We have completed predicate verification and synthesized evidence-based arguments. 
Now, it is time to prove that the claim is false by analyzing all collected information holistically. 

**Questions and Evidence**: 
{QA_pairs}

**Predicate Verification**: 
{predicate_verifications}

**Claim**: 
{claim}

**Task:** 
1. Synthesize a comprehensive reasoning process to **prove that the claim is false**. Incorporate both supporting and refuting arguments, emphasizing why the refuting arguments outweigh or invalidate the supporting ones. 
2. Use retrieved evidence and predicate verification results to substantiate your reasoning. 
3. Provide a confidence score (out of 10) to indicate how strongly the evidence supports the conclusion that the claim is false. 
"""

logic_final_judgment = """
Now that we have completed the verification of all predicates and synthesized supporting and refuting arguments based on the evidence retrieved, it is time to evaluate the claim holistically. 

**Claim:** 
{claim}

**Supporting Arguments:** 
{supporting_arguments}

**Refuting Arguments:** 
{refuting_arguments}


**Task:** 
Your task is to evaluate the overall credibility of the claim by analyzing both the supporting and refuting arguments, as well as the predicate verification results. 
1. Synthesize a comprehensive explanation incorporating both perspectives (supporting and refuting). 
2. Based on the synthesized explanation, you MUST classify the claim as either "<**SUPPORTED**>", "<**NOT_SUPPORTED**>".
3. Provide a confidence score (out of 10) for your classification, indicating how strongly the evidence supports your conclusion. 
"""
