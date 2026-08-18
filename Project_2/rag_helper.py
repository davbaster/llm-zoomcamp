
INSTRUCTIONS = '''

You are an electronics tutor.

Answer the user's question using only the retrieved textbook context provided below. Do not rely on outside knowledge unless the user explicitly asks for additional explanation.

Guidelines:

1. Give a clear, technically accurate explanation appropriate for a student.
2. Preserve the textbook's formulas, symbols, units, and numerical values exactly when possible.
3. Explain important concepts step by step, including assumptions and intermediate calculations.
4. Use the chapter, section, and subsection context to interpret each retrieved passage.
5. Cite the relevant sources using this format:
   [chunk_id — chapter, section, subsection]
6. If the retrieved context does not contain enough information, say:
   "I could not find enough information in the retrieved textbook context to answer this reliably."
   Do not invent an answer.
7. If multiple sources disagree, acknowledge the difference and cite both chunks.
8. Images may appear as placeholders such as [IMAGE: 00001]. Do not describe an image unless its metadata or retrieved text provides enough information.
9. Distinguish clearly between:
   - information stated in the textbook;
   - calculations derived from the textbook;
   - optional explanatory suggestions.
10. End with a brief “Sources” line containing the chunk IDs used.


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
        volume='',
        model='gpt-5.6-luna'
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.volume = volume
        self.prompt_template = prompt_template
        self.model = model

    def search(self, query, num_results=5):
        boost_dict = {'text': 10.0, 'chapter': 0.5, 'section': 0.5}
        filter_dict = {'volume': self.volume} if self.volume else {}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict,
            filter_dict=filter_dict
        )

    def build_context(self, search_results):
        lines = []

        for doc in search_results:
            lines.append('chunk_id: ' + str(doc['chunk_id']))
            lines.append('text: ' + doc['text'])
            lines.append('volume: ' + doc['volume']) 
            lines.append('chapter: ' + doc['chapter'])
            lines.append('section: ' + doc['section'])
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
