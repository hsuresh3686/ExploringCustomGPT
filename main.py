import streamlit as st
from openai import OpenAI
import functions

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Tomcat & HTTPD Support Assistant",
    page_icon="🔧",
    layout="centered"
)

# ---------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------
@st.cache_resource
def get_client():
    return OpenAI()
client = get_client()

# ---------------------------------------------------------
# Create / load assistant configuration
# ---------------------------------------------------------

@st.cache_resource
def get_assistant_config():
    return functions.create_assistant(client)

assistant_config = get_assistant_config()
VECTOR_STORE_ID = assistant_config["vector_store_id"]
MODEL = assistant_config.get("model", "gpt-5-mini")
INSTRUCTIONS = functions.INSTRUCTIONS

# ---------------------------------------------------------
# Create a conversation
# ---------------------------------------------------------

if "conversation_id" not in st.session_state:
    conversation = client.conversations.create()
    st.session_state.conversation_id = conversation.id

# ---------------------------------------------------------
# Initialize chat history
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------
# Page title
# ---------------------------------------------------------

st.title("🔧 Tomcat & Apache HTTPD Support Assistant")
st.caption(
    "Application Support troubleshooting assistant "
    "for Tomcat, Apache HTTPD, JVM, SSL/TLS, logs and related issues."
)

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("Assistant Information")
    st.write("**Model:**")
    st.code(MODEL)
    st.write("**Conversation ID:**")
    st.code(st.session_state.conversation_id)
    st.write("**Vector Store:**")
    st.code(VECTOR_STORE_ID)
    st.divider()
    if st.button("🗑️ Start New Conversation"):
        conversation = client.conversations.create()
        st.session_state.conversation_id = conversation.id
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------
# Display previous messages
# ---------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# Chat input
# ---------------------------------------------------------

user_input = st.chat_input(
    "Describe your Tomcat or Apache HTTPD error..."
)

# ---------------------------------------------------------
# Process user message
# ---------------------------------------------------------

if user_input:
    # Display user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )
    with st.chat_message("user"):
        st.markdown(user_input)
    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing the issue..."):
            try:
                response = client.responses.create(
                    model=MODEL,
                    instructions=INSTRUCTIONS,
                    conversation=st.session_state.conversation_id,
                    tools=[{"type": "file_search","vector_store_ids": [VECTOR_STORE_ID]}],
                    input=[{"role": "user","content": [{"type": "input_text","text": user_input}]}]
                )
                assistant_response = response.output_text
                if not assistant_response:
                    assistant_response = (
                        "The model did not return a text response."
                    )
                st.markdown(assistant_response)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_response
                    }
                )
            except Exception as exc:
                error_message = (
                    "Unable to process the request.\n\n"
                    "Error: {}".format(exc)
                )
                st.error(error_message)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message
                    }
                )