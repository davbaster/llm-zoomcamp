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

“I don't have any exact recommendations based on the provided characteristics.”

Do not provide unsupported alternatives.


'''


PROMPT_TEMPLATE = '''
QUESTION: {question}

CONTEXT:
{context}
'''.strip()


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

        return response.output_text

    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer, search_results
