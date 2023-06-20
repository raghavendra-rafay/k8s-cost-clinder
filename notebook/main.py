import pandas as pd
import tiktoken
import openai
import os
import numpy as np
from scipy.spatial.distance import euclidean
from dotenv import dotenv_values
import streamlit as st
from numpy.linalg import norm

openai.api_key = os.environ.get("OPENAI_API_KEY") or dotenv_values(".env")["OPENAI_API_KEY"]

def prepare_data(csv, encoding):
    df = pd.read_csv(csv)
    df = df.dropna()
    df = df[["vendor","instance_type","vcpu","memory_gib","cost_in_dollars"]]
    df["summarized"] = ("vendor: " + df.vendor.str.strip() + "; instance_type: " +   df.instance_type.str.strip()  + "; vcpu: " + df.vcpu.map(str) + "; memory_gib: " +  df.memory_gib.map(str) +  "; cost_in_dollars: " + df.cost_in_dollars.map(str))
    df["token"] = df.summarized.apply(lambda x:len(encoding.encode(x)))
    return df

def get_text_embedding(text, embeddding_mode="text-embedding-ada-002"):
    result = openai.Embedding.create(model=embeddding_mode, input=text)
    return result["data"][0]["embedding"]

def get_df_embeddings(df: pd.DataFrame) -> dict[tuple[str, str], list[float]]:
    return { idx: get_text_embedding(r.summarized) for idx, r in df.iterrows()}

def calculate_vector_similarity(x: list[float], y: list[float]) -> float:
    return np.dot(np.array(x), np.array(y))
    #return euclidean(np.array(x), np.array(y))

def get_docs_with_similarity(query: str, df_embedding: dict[(str, str), np.array]) -> list[float, (str, str)]:
    query_embedding = get_text_embedding(query)
    document_similarities = sorted([(calculate_vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in df_embedding.items()], reverse=True)
    return document_similarities

def create_prompt(question: str, context_embeddings: dict, df: pd.DataFrame, separator_len) -> str:
    relevant_document_sections = get_docs_with_similarity(question, context_embeddings)

    chosen_sections = []
    chosen_sections_len = 0
    chosen_sections_indexes = []

    for _, section_index in relevant_document_sections:
        document_section = df.loc[section_index]
        chosen_sections_len += document_section.token + separator_len
        if chosen_sections_len > 500:
            break

        chosen_sections.append("\n* " + document_section.summarized.replace("\n", " "))
        chosen_sections_indexes.append(str(section_index))

    header = """    
            As a data analyst, you have access to CSV data and are responsible for answering questions based on that data. One of the tasks is to identify the most cost-effective instance type given a specific vCPU value and Memory in GiB.

            To find the cost-effective instance type, you should first search for instances where the vCPU value is greater than or equal to the provided vCPU value and the Memory in GiB value is greater than or equal to the provided Memory in GiB value. Then, filter out the instance type with the lowest cost and return the corresponding instance type and cost values. If only one instance type meets the criteria, return its corresponding values.

            If you don't know the answer, you can try an alternative approach. Check for two instances of each instance type and verify whether the double of the vCPU value is greater than or equal to the provided vCPU value and the double of the Memory in GiB value is greater than or equal to the provided Memory in GiB value. If you find an instance type that satisfies these conditions and are cheaper among others, return its instance type, cost values, and the total number of instances (which will be two).

            If you still haven't found an answer after checking two instances, repeat the process by checking three instances of each instance type. Continue this pattern, increasing the number of instances by one each time, until you either find a suitable instance type or exhaust all possibilities.

            If you don't know the answer to a question or if it is completely irrelevant to the available data, simply respond with "I don't know."

            Now, please proceed to answer the following question:
          """


    return header + "".join(chosen_sections) + "\n\n Question: " + question + "\n Answer:"

def get_answer(query: str, df: pd.DataFrame, document_embeddings: dict[(str, str), np.array], separator_len) -> str:
    prompt = create_prompt(query, document_embeddings, df, separator_len)
    
    response = openai.Completion.create(prompt=prompt, temperature=0, max_tokens=500, model="text-davinci-003")
    return response["choices"][0]["text"]

def app_init(df: pd.DataFrame, document_embeddings: dict[(str, str), np.array], separator_len):
    st.set_page_config(page_title="Get information regarding your resources")
    st.header("📊 Minimize your cost")
    user_input = st.text_input("Provide vCPU and Memory in GiB, I will give you cheapest instance type!!")
    print(user_input)
    if user_input is not None and user_input != "":
      response = get_answer(user_input, df, document_embeddings, separator_len)
      st.write(response)

def app():
    file_location = "aws.csv"
    encoding = tiktoken.get_encoding("cl100k_base")
    df = prepare_data(file_location, encoding)
    document_embeddings = get_df_embeddings(df)
    separator_len = len(encoding.encode("\n* "))
    app_init(df, document_embeddings, separator_len)

class OpenApiModel:
    PROMPT_STR = 'Please suggest me cost effective instance_type(s) whose vCPUs >= {vCPU} and and Memory in GiB >= {memory} and How many instances will be required.'
    def __init__(self, location="aws.csv") -> None:
        encoding = tiktoken.get_encoding("cl100k_base")
        df = prepare_data(location, encoding)
        self.datafile = df
        document_embeddings = get_df_embeddings(df)
        self.document_embeddings = document_embeddings
        self.separator_len = len(encoding.encode("\n* "))

    def get_instance(self, vcpu, memory):
        query = self.PROMPT_STR.format(vCPU=vcpu, memory=memory)
        return get_answer(query, self.datafile, self.document_embeddings, self.separator_len)

if __name__ == "__main__":
    app()