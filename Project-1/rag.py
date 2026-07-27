import json
from time import time


#INSTRUCTIONS = '''
#Your task is to recommend anime to users based on the provided context.

#Use the context to find relevant information and provide accurate
#recommendations. If no suitable recommendations are found in the context,
#respond with "I don't have any recommendations based on the provided characteristics."
#'''
INSTRUCTIONS = '''

You are a recommendation assistant for anime, manga, light novels, and webtoons.

Your task is to recommend titles that match the user's request using only the information contained in the provided context.

Follow these rules:

Understand the user's preferences
Identify the important characteristics in the request, including:
Requested medium: anime, manga, light novel, or webtoon
Genres and subgenres
Story premise
Setting or world
Protagonist characteristics
Fantasy races or creatures
Powers, technology, magic systems, or game mechanics
Themes, tone, relationships, and types of conflict

Correctly interpret informal wording, spelling mistakes, and synonymous expressions. For example, “VR game,” “virtual reality world,” and “trapped inside an online game” may describe related concepts.

Use only the provided context
Recommend only titles explicitly found in the provided context.

Do not:

Invent titles, seasons, formats, plots, characters, or availability
Add information based on outside knowledge
Claim that a title matches a characteristic that is not supported by the context
Recommend a title only because its name sounds relevant
Respect the requested medium
Prioritize titles available in the medium requested by the user.

For example:

If the user asks for manga, prioritize manga records.
If the user asks for anime, prioritize anime records.
If the user accepts multiple formats, recommendations may include any matching anime, manga, light novels, or webtoons.

Do not recommend an adaptation in another medium unless the context confirms that the requested version exists. Clearly label the medium of every recommendation.

Rank recommendations by relevance
Recommend the strongest matches first.

A strong match should satisfy several important characteristics from the request. Do not rank a weak thematic similarity above a title that directly matches the requested premise, setting, and genre.

When no title matches every characteristic but some titles match most of them, introduce them as “Closest matches” and briefly explain the differences.

Handle franchises and seasons carefully
Avoid presenting duplicate records as different recommendations.

When several records belong to the same franchise:

Combine them into one recommendation when they represent the same main work in different formats.
List seasons separately only when the context treats them as separate entries and season-level recommendations are useful.
When listing multiple seasons, place them in the correct viewing order according to the context.
Do not recommend a later season without also making it clear that the user should begin with the earlier season.
Keep recommendations concise and useful
Return up to five recommendations unless the user requests a different number.

Use this format:

Title — Medium
Briefly explain which requested characteristics it matches.
Title — Medium
Briefly explain which requested characteristics it matches.

Do not mention retrieval, embeddings, documents, records, or the provided context in the response.

Handle missing results
If no title in the context reasonably matches the user's requested characteristics, respond exactly with:

“I don't have any recommendations based on the provided characteristics.”

Do not provide unsupported alternatives.


'''


PROMPT_TEMPLATE = '''
QUESTION: {question}

CONTEXT:
{context}
'''.strip()


evaluation_prompt_template = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it
as 'NON_RELEVANT', 'PARTLY_RELEVANT', or 'RELEVANT'.

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  'Relevance': 'NON_RELEVANT' | 'PARTLY_RELEVANT' | 'RELEVANT',
  'Explanation': '[Provide a brief explanation for your evaluation]'
}}
""".strip()


class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        genre='',
        model='gpt-5.4-mini'
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.genre = genre
        self.prompt_template = prompt_template
        self.model = model

    def search(self, query, num_results=5):
        boost_dict = {'synopsis': 10.0, 'title': 0.5, 'title_english': 0.5, 'studios': 0, 'genres': 1.0, 'source': 1.0}
        filter_dict = {'genres': self.genre} if self.genre else {}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict,
            filter_dict=filter_dict
        )

    def build_context(self, search_results):
        lines = []

        for doc in search_results:
            lines.append('MAL ID: ' + str(doc['mal_id']))
            lines.append('Type: ' + doc['title_english']) 
            lines.append('Title: ' + doc['title'])
            lines.append('Synopsis: ' + doc['synopsis'])
            lines.append('Genres: ' + doc['genres'])
            lines.append('Studios: ' + doc['studios'])
            lines.append('')

        return '\n'.join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )

    def llm(self, prompt):
        input_messages = [
            {'role': 'developer', 'content': self.instructions},
            {'role': 'user', 'content': prompt}
        ]

        response = self.llm_client.responses.create(
            model=self.model,
            input=input_messages
        )

        return response.output_text, response.token_stats

    def rag(self, query):
        t0 = time()
        
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer, token_stats = self.llm(prompt)

        relevance, rel_token_stats = self.evaluate_relevance(query, answer)

        t1 = time()
        took = t1 - t0

        input_cost, output_cost, total_cost = self.calc_price(token_stats)

        
        return answer, search_results

        return {
            "answer": answer,
            "response_time": took,
            "relevance": relevance.get("Relevance", "UNKNOWN"),
            "relevance_explanation": relevance.get("Explanation", "Failed to parse"),
            "prompt_tokens": token_stats["prompt_tokens"],
            "completion_tokens": token_stats["completion_tokens"],
            "total_tokens": token_stats["total_tokens"],
            "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
            "eval_completion_tokens": rel_token_stats["completion_tokens"],
            "eval_total_tokens": rel_token_stats["total_tokens"],
            "openai_cost": openai_cost,
            "search_results": search_results
        }

    #evaluation functions
    def evaluate_relevance(self, question, answer):
        prompt = evaluation_prompt_template.format(question=question, answer=answer)
        evaluation, tokens = self.llm(prompt)

        try:
            json_eval = json.loads(evaluation)
            return json_eval, tokens
        except json.JSONDecodeError:
            result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
            return result, tokens

    #price calculation functions    
    def calc_price(usage):
        input_price_per_million = 0.20
        output_price_per_million = 1.25

        input_cost = (usage.input_tokens / 1_000_000) * input_price_per_million
        output_cost = (usage.output_tokens / 1_000_000) * output_price_per_million
        total_cost = input_cost + output_cost

        return  {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }


    def calc_total_price(usages):
        total_cost = 0.0

        for usage in usages:
            cost = calc_price(usage)
            total_cost = total_cost + cost["total_cost"]

        return total_cost