from openai import OpenAI
from boutiques.bosh import search, pull
import json
import os
import jsonschema
import sys


class TellMe:

    def __init__(self, model="gpt-4o-mini"):

        self.prompt_template = """
                You are here to help Boutiques users find relevant tools. You must reply to user questions with a list of JSON objects formatted as follows:
                [
                    {
                        "tool_id": "Boutiques tool id (zenodo id) matching the user query",
                        "tool_name": "Boutiques tool name matching the user query",
                        "explanation": "1-2 sentences explaining why you returned this tool"
                    },
                    {...}
                ]
                 
                
                Here is the set of Boutiques descriptors that you can search from:

        """

        # Initialize OpenAI client
        self.model = model
        self.client = OpenAI()
        MAX_PROMPT_SIZE = 200000

        # Watch out, this may take time
        # Pull has a cache but search does not
        self.descriptors = [
            { "tool_id": tool["ID"],
            "descriptor": json.loads(open(pull(tool["ID"])[0], "r").read())
            }
            for tool in search("-m 500")
        ]

        # Format the prompt
        max_chars_per_tool = (MAX_PROMPT_SIZE - 600) // len(self.descriptors)
        descriptors_string = (
            os.linesep
            + os.linesep
            + "### BEGIN DESCRIPTOR ###"
            + os.linesep
            + os.linesep
        ).join([json.dumps(d, indent=4)[:max_chars_per_tool] for d in self.descriptors])
        self.prompt = self.prompt_template + descriptors_string

    def ask(self, question):
        completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"{self.prompt}"},
                {"role": "user", "content": f"{question}"},
            ],
            model=self.model,
            temperature=0,
        )
        answer = completion.choices[0].message.content
        return answer

tellme = TellMe()
answer = tellme.ask(sys.argv[1])
print(answer)
