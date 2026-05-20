from openai import AzureOpenAI, OpenAI

from app.config import config


class TongGPT:
    def __init__(self, MODEL="gpt-35-turbo-0125", REGION="westus"):
        super().__init__()
        self.REGION = REGION
        self.MODEL = MODEL
        llm_config = config.llm["default"]
        self.api_type = llm_config.api_type.lower()
        self.api_key = llm_config.api_key
        self.base_url = llm_config.base_url
        self.api_version = llm_config.api_version
        self.init_client()

    def init_client(self):
        if self.api_type == "azure":
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.base_url,
            )
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self.client

    def send_request(self, kw):
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": kw}],
        )

        print(response.model_dump_json(indent=2))
        print(".....")
        print(response.choices[0].message.content)
        return response


class GPT4o(TongGPT):
    def __init__(self, MODEL="gpt-4-turbo-2024-04-09", REGION="westus"):
        super().__init__(MODEL, REGION)

    def send_request(self, payload):
        response = self.client.chat.completions.create(
            model=payload["model"],
            messages=payload["messages"],
            temperature=payload["temperature"],
            max_tokens=payload["max_tokens"],
        )
        return response


class GPT4V(GPT4o):
    def __init__(self, MODEL="gpt-4-vision-preview", REGION="australiaeast"):
        super().__init__(MODEL, REGION)
