import torch
import transformers
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForCausalLM,
)
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFacePipeline


class LLMAnalyzer:
    def __init__(self, HF_API: str, model_id: str = 'tarun7r/Finance-Llama-8B') -> None:
        self.api = HF_API
        self.model_id = model_id

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
        prompt_template = ChatPromptTemplate([
            {"role": "system", "content": "You are a highly knowledgeable finance chatbot. Your purpose is to provide accurate, insightful, and actionable financial advice to users, tailored to their specific needs and contexts."},
            {"role": "user", "content": "Analyze this company's balance sheet: {data}"}
        ])

        chain = (prompt_template
                 | self.llm
                 | StrOutputParser()
                 )
        data = self.get_data_from_csv(df_list)

        print(chain.invoke({"data": data}))


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
                f"Prior: CurrentLiabilities: {p_cl}, NoncurrentLiabilities: {p_ncl}, CurrentAssets: {p_cs}, NoncurrentAssets: {p_ncs}, NetAssets: {p_na}\n"
                f"Current: CurrentLiabilities: {c_cl}, NoncurrentLiabilities: {c_ncl}, CurrentAssets: {c_cs}, NoncurrentAssets: {c_ncs}, NetAssets: {c_na}"
                )
        else:
            print("ダミーデータを使用")
            data = (
                "Prior: CurrentLiabilities: 971170000000, NoncurrentLiabilities: 1546007000000, CurrentAssets: 2726359000000, NoncurrentAssets: 78772000000, NetAssets: 288267000000"
                "Current: CurrentLiabilities: 1143592000000, NoncurrentLiabilities: 2387071000000, CurrentAssets: 3758495000000, NoncurrentAssets: 97160000000, NetAssets: 325624000000")

        return data