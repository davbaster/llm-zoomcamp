#https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-agentic-rag/lessons/08-rag-helper.md

INSTRUCTIONS = """
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
"""

PROMPT_TEMPLATE = """
QUESTION: {question}

CONTEXT:
{context}
""".strip()

class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        model="gpt-5.4-mini"
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.model = model

    #The index parameter is anything with a search method, whether minsearch, sqlitesearch, or something else. 
    # The other four parameters all have defaults. You only pass course, instructions, prompt_template, or model when you want to override the default behavior. 
    # We swap the index later without touching any of the RAG code.
    #The search method delegates to the index:
    #question: 3.0 puts more weight on matches in the question field, while section: 0.5 puts less weight on matches in the section field.
    #filter_dict={"course": self.course} ensures that we only get results from the specified course, which is important if the index contains documents from multiple courses.
    #commented out filter_dict for now, since we are only loading data from one course. We can re-enable it later when we load data from multiple courses.
    def search(self, query, num_results=5):
        boost_dict = {"content": 3.0, "filename": 0.5}


        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict
        )

 
    #The build_context and build_prompt methods format the search results:
    #customized to use content/filename
    def build_context(self, search_results):
        lines = []

        for doc in search_results:
            lines.append(doc["content"] + "/" + doc["filename"])
            lines.append("")

        return "\n".join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )
        
   #The llm method sends the prompt to the LLM:
    def llm(self, prompt):
        input_messages = [
            {"role": "developer", "content": self.instructions},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_client.responses.create(
            model=self.model,
            input=input_messages
        )

        return response.output_text + " Input tokens: " + str(response.usage.input_tokens) + " Output tokens: " + str(response.usage.output_tokens)
    
    #And the rag method wires it all together:
    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer