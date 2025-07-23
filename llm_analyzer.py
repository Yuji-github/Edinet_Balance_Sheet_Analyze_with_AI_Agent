import torch
import transformers
from transformers import (
    pipeline,
    AutoTokenizer,
    BitsAndBytesConfig,
    AutoModelForCausalLM,
)
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFacePipeline
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool


class LLMAnalyzer:
    def __init__(self, HF_API: str, model_id: str = 'tarun7r/Finance-Llama-8B') -> None:
        self.api = HF_API
        self.model_id = model_id

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,  # 4bitのQuantizationの有効化
            bnb_4bit_quant_type="nf4",  # 4bitのQuantizationのタイプ (fp4 or nf4)
            bnb_4bit_compute_dtype=torch.bfloat16,  # 4bitのQuantizationのdtype (float16 or bfloat16)
            bnb_4bit_use_double_quant=True,  # 4bitのDouble-Quantizationの有効化
        )

        # モデルのロード
        self.model_config = transformers.AutoConfig.from_pretrained(
            model_id,
            token=self.api
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            config=self.model_config,
            quantization_config = quantization_config,
            device_map='auto',
            token=self.api,
            low_cpu_mem_usage=True,
            weights_only=True
        )

        # Set device
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,  # モデル名
            add_eos_token=True,  # データへのEOSの追加を指示
            trust_remote_code=True,
            token=self.api,
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

        self.llm = HuggingFacePipeline(pipeline=self.generator)


    def agent_analyze(self, df_list: list) -> None:
        def search_web_news(query: str) -> str:
            """Performs a DuckDuckGo news search for the given query in Japanese, daily results, max 2."""
            wrapper = DuckDuckGoSearchAPIWrapper(region="jp-jp", time="d", max_results=2)
            engine = DuckDuckGoSearchResults(api_wrapper=wrapper, backend="news")
            return engine.invoke(f"{query}")

        def calculate_debt_to_equity_ratio(total_debt: float, total_equity: float) -> str:
            """
            Calculates the Debt-to-Equity (D/E) ratio.
            The D/E ratio is a financial ratio indicating the relative proportion of shareholders' equity and debt used to finance a company's assets.
            A higher ratio indicates more debt financing, which can imply higher risk.
            Input: total_debt (float), total_equity (float)
            Returns: The Debt-to-Equity ratio as a string, or an error message if total_equity is zero.
            """
            if total_equity == 0:
                return "Error: Cannot calculate Debt-to-Equity ratio, Total Equity is zero."
            ratio = total_debt / total_equity
            return f"Debt-to-Equity Ratio: {ratio:.2f}"

        tool_search_news = Tool(
            name="news_search",
            func=search_web_news,
            description="Tool to perform a DuckDuckGo news search. "
                        "Useful for current events or recent information. "
                        "Input should be a search query string. Returns up to 2 news results."
        )

        tool_debt_to_equity_calculator = Tool(
            name="debt_to_equity_calculator",
            func=calculate_debt_to_equity_ratio,
            description="Tool to calculate the Debt-to-Equity (D/E) ratio."
                        " Useful for assessing a company's financial leverage."
                        " Input should be 'total_debt' (float) and 'total_equity' (float). Returns the D/E ratio."
        )

        tools = [tool_search_news, tool_debt_to_equity_calculator]

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            You are a highly knowledgeable finance chatbot. Your purpose is to provide accurate, insightful,
            and actionable financial advice to users, tailored to their specific needs and contexts.

            Available tools: {tools}
            Available tool names: {tool_names}
            
            Responses should always follow this format:
            Question: The question the user wants to answer
            Thought: Think about what to do to answer the question
            Action: The tool to use (must be one of the available tools)
            Action Input: Input to the tool
            Observation: Result of the tool
        
            ...(Thought/Action/Action Input/Observation can be repeated once at most to answer the question)
            Thought: Determine that it's time to provide the final answer to the user
            Final Answer: The final answer to the user
            """),

            ("user", "Analyze this company's balance sheet: {data}\n{agent_scratchpad}")
        ])

        agent = create_react_agent(self.llm, tools, prompt_template)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,  # Keep verbose=True to ensure intermediate steps are printed to stdout
            handle_parsing_errors=True
        )

        data = self.get_data_from_csv(df_list)

        print("\n--- Agent's Reasoning Process ---")

        result = agent_executor.invoke({"data": data})

        print("\n--- Final Answer ---")
        print(result['output'])
        print("\n" + "=" * 80 + "\n")


    def get_data_from_csv(self, df_list: list) -> str:
        if len(df_list) == 1:
            df = df_list[0]
            c_cs = df.loc[0, "CurrentAssets(流動資産)"] if df.loc[0, "CurrentAssets(流動資産)"] != None else 0
            c_ncs = df.loc[0, "NoncurrentAssets(固定資産)"] if df.loc[0, "NoncurrentAssets(固定資産)"] != None else 0
            c_na = df.loc[1, "NetAssets(純資産)"] if df.loc[1, "NetAssets(純資産)"] != None else 0
            c_cl = df.loc[1, "CurrentLiabilities(流動負債)"] if df.loc[1, "CurrentLiabilities(流動負債)"] != None else 0
            c_ncl = df.loc[1, "NoncurrentLiabilities(固定負債)"] if df.loc[1, "NoncurrentLiabilities(固定負債)"] != None else 0

            data = (
                f"CurrentLiabilities: {c_cl}, NoncurrentLiabilities: {c_ncl}, CurrentAssets: {c_cs}, NoncurrentAssets: {c_ncs}, NetAssets: {c_na}"
            )

        elif len(df_list) == 2:
            prior_df = df_list[0]
            p_cs = prior_df.loc[0, "CurrentAssets(流動資産)"] if prior_df.loc[0, "CurrentAssets(流動資産)"] != None else 0
            p_ncs = prior_df.loc[0, "NoncurrentAssets(固定資産)"] if prior_df.loc[0, "NoncurrentAssets(固定資産)"] != None else 0
            p_na = prior_df.loc[1, "NetAssets(純資産)"] if prior_df.loc[1, "NetAssets(純資産)"] != None else 0
            p_cl = prior_df.loc[1, "CurrentLiabilities(流動負債)"] if prior_df.loc[1, "CurrentLiabilities(流動負債)"] != None else 0
            p_ncl = prior_df.loc[1, "NoncurrentLiabilities(固定負債)"] if prior_df.loc[1, "NoncurrentLiabilities(固定負債)"] != None else 0

            current_df = df_list[1]
            c_cs = current_df.loc[0, "CurrentAssets(流動資産)"] if current_df.loc[0, "CurrentAssets(流動資産)"] != None else 0
            c_ncs = current_df.loc[0, "NoncurrentAssets(固定資産)"] if current_df.loc[0, "NoncurrentAssets(固定資産)"] != None else 0
            c_na = current_df.loc[1, "NetAssets(純資産)"] if current_df.loc[1, "NetAssets(純資産)"] != None else 0
            c_cl = current_df.loc[1, "CurrentLiabilities(流動負債)"] if current_df.loc[1, "CurrentLiabilities(流動負債)"] != None else 0
            c_ncl = current_df.loc[1, "NoncurrentLiabilities(固定負債)"] if prior_df.loc[1, "NoncurrentLiabilities(固定負債)"] != None else 0

            data = (
                f"Prior: CurrentLiabilities: {p_cl}, NoncurrentLiabilities: {p_ncl}, CurrentAssets: {p_cs}, NoncurrentAssets: {p_ncs}, NetAssets: {p_na} "
                f"Current: CurrentLiabilities: {c_cl}, NoncurrentLiabilities: {c_ncl}, CurrentAssets: {c_cs}, NoncurrentAssets: {c_ncs}, NetAssets: {c_na}"
                )
        else:
            print("ダミーデータを使用")
            data = (
                "Prior: CurrentLiabilities: 971170000000, NoncurrentLiabilities: 1546007000000, CurrentAssets: 2726359000000, NoncurrentAssets: 78772000000, NetAssets: 288267000000"
                "Current: CurrentLiabilities: 1143592000000, NoncurrentLiabilities: 2387071000000, CurrentAssets: 3758495000000, NoncurrentAssets: 97160000000, NetAssets: 325624000000")

        return data