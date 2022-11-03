import streamlit as st
from trafilatura import fetch_url, extract
from trafilatura.settings import use_config

from faq_gen import (
    get_df_with_chunks_embedded,
    search_material,
    generate_questions,
    join_chunks,
    get_qa_pair,
    generate_illustration,
)

# This is a workaround for a bug in trafilatura.
trafilatura_cfg = use_config()
trafilatura_cfg.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")


@st.cache(suppress_st_warning=True, persist=True)
def extract_text_from_url(url: str) -> str:
    """
    Extracts the text from the url, and returns the text

    :param url: the URL of the article to extract text from
    :type url: str
    :return: A string of text
    """
    print(f"Extracting text from {url}")
    downloaded = fetch_url(url)
    text_in = extract(downloaded, config=trafilatura_cfg)
    return text_in


# A simple Streamlit app that showcases the functionality of the FAQ generator

st.title("Eco FAQs")

st.write(
    "Use this tool to generate FAQs for your Climate Change education materials. "
    "Inspired by [Project Regeneration Nexus](https://regeneration.org/nexus), "
    "it uses OpenAI's APIs to generate questions and answers."
)
st.write(
    "The app is currently a POC. It extracts text from the selected nexus solution, "
    "chunks the text, embeds those chunks, and uses prompt-chaining to generate "
    "questions and answers pertaining to the text."
)

#  Extracted using GPT by pasting the HTML blob into playground and prompting with
#  "Extract all hrefs from above into a python list" :)
hrefs = [
    "/nexus/afforestation",
    "/nexus/agroecology",
    "/nexus/agroforestry",
    "/nexus/asparagopsis",
    "/nexus/azolla-fern",
    "/nexus/bamboo",
    "/nexus/beavers",
    "/nexus/biochar",
    "/nexus/buildings",
    "/nexus/clean-cookstoves",
    "/nexus/compost",
    "/nexus/degraded-land-restoration",
    "/nexus/eating-plants",
    "/nexus/education-girls",
    "/nexus/electric-vehicles",
    "/nexus/electrify-everything",
    "/nexus/energy-storage",
    "/nexus/fifteen-minute-city",
    "/nexus/fire-ecology",
    "/nexus/grasslands",
    "/nexus/heat-pumps",
    "/nexus/mangroves",
    "/nexus/marine-protected-areas",
    "/nexus/micromobility",
    "/nexus/nature-of-cities",
    "/nexus/net-zero-cities",
    "/nexus/offsets",
    "/nexus/ocean-farming",
    "/nexus/regenerative-agriculture",
    "/nexus/seaforestation",
    "/nexus/seagrasses",
    "/nexus/silvopasture",
    "/nexus/smart-microgrids",
    "/nexus/solar",
    "/nexus/tidal-salt-marshes",
    "/nexus/tropical-forests",
    "/nexus/urban-farming",
    "/nexus/urban-mobility",
    "/nexus/wetlands",
    "/nexus/wind",
]

top_similar = 4
left, right = st.columns(2)
form = left.form("template_form")
# url_input = form.text_input("Project Regeneration Nexus solutions on", value="regeneration.org/nexus/agroecology")
url_input = form.selectbox(
    "Project Regeneration Nexus Solutions on",
    list(map(lambda href: href.split("/")[-1], hrefs)),
)
topic_input = form.text_input(
    "Relevant Topic (optional)",
    placeholder="food diversity",
    value="action items",
)
audience_input = form.text_input(
    "Audience (optional)", placeholder="students", value="students"
)
num_questions_input = form.number_input(
    "Number of Questions", min_value=2, max_value=5, value=3
)
submit = form.form_submit_button("Generate FAQs")

with st.container():
    if submit and url_input:
        with st.spinner("Generating FAQs..."):
            text = extract_text_from_url(
                "https://regeneration.org/nexus/" + url_input
            )
            df = get_df_with_chunks_embedded(text)
            res = search_material(df, topic_input, n=top_similar)
            chunks = join_chunks(res["chunk"])
            generated_questions = generate_questions(
                chunks=chunks,
                topic=topic_input,
                audience=audience_input,
                num_questions=num_questions_input,
            )

            # TODO: could be done in parallel ##
            # with concurrent.futures.ThreadPoolExecutor() as executor:
            #     future1 = executor.submit(get_qa_pair, generated_questions, df)
            #     future2 = executor.submit(generate_illustration, url_input)
            #     qa_pair = future1.result()
            #     illustration_url = future2.result()
            #     executor.shutdown(wait=True)

            qa_pair = get_qa_pair(generated_questions, df)
            illustration_url = generate_illustration(prompt=url_input)

            # if we need content moderation
            # qa_pair = [pair for pair in qa_pair if not is_flagged_for_content_violation(pair['answer'])]
            with right:
                right.image(illustration_url)
                right.write(
                    "Reference to the page: [{}]({})".format(
                        url_input, "https://regeneration.org/nexus/" + url_input
                    )
                )
                for pair in qa_pair:
                    expander = right.expander(f"{pair['question']}")
                    expander.write(f"{pair['answer']}")
