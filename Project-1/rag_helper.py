INSTRUCTIONS = '''
Your task is to recommend anime to users based on the provided context.

Use the context to find relevant information and provide accurate
recommendations. If no suitable recommendations are found in the context,
respond with "I don't have any recommendations based on the provided characteristics."
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
        boost_dict = {'synopsis': 3.0, 'title': 1.5, 'title_english': 1.5, 'studios': 1.0, 'genres': 1.0, 'source': 1.0}
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
