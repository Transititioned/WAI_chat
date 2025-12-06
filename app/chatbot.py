# ==========================================================
# WorkFriend Chatbot (v4.2 — Alpha Merge: UI Kept + Router Fix)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path

from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer   # <-- restored properly


def init_chatbot():

    # ------------------------------------------------------
    # 🧠 Model + Embeddings
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.32, openai_api_key=openai_key)

    # ------------------------------------------------------
    # 📚 Vector store (Articles only for alpha)
    # ------------------------------------------------------
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text: continue

        chunks = [text[i:i+1500] for i in range(0,len(text),1500)]
        for c in chunks:
            docs.append({"content":c,"metadata":{"source":md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs]
    )

    retriever = vectordb.as_retriever(search_kwargs={"k":3})

    # ------------------------------------------------------
    # 🔍 Retrieval + Router Answer Pipeline
    # ------------------------------------------------------
    def retrieve_and_answer(question:str):
        system_block = route(question)  # lens selector
        results = retriever.invoke(question)
        context = "\n\n".join([r.page_content for r in results])

        prompt = ChatPromptTemplate.from_template(
            "{system}\n\n## Context\n{context}\n\n"
            "### Respond using format:\n"
            "Answer: short & useful\n"
            "Why This Matters: reasoning summary\n"
            "Plays/Examples: tactical optional extras\n\n"
            "User Question: {question}"
        ).format(system=system_block,context=context,question=question)

        response = llm.invoke(prompt)
        final = postprocess_answer(question,response.content)
        return final

    # ------------------------------------------------------
    # Chat history wrapper
    # ------------------------------------------------------
    def answer_fn(message,history):
        try:
            history = history + [{"role":"user","content":message}]
            answer = retrieve_and_answer(message)
            answer += "\n\n⚠️ *WAI Alpha Release — please check suggestions manually.*"
            history = history + [{"role":"assistant","content":answer}]
            return history
        except Exception as e:
            return history+[{"role":"assistant","content":f"⚠️ Error: {e}"}]

    # ------------------------------------------------------
    # 💄 UI Styling
    # ------------------------------------------------------
    custom_css = """
    /* Preserve ALL styling from backup untouched */
    .gradio-container *, .gradio-container,
    .block, .wrap, .gradio-app, .svelte-1ipelgc {
        padding-top:0!important;padding-bottom:0!important;
        margin-top:0!important;margin-bottom:0!important;gap:0!important;
    }
    footer,.footer,.svelte-1ipelgc>div:last-child {display:none!important;height:0!important;}

    .chatbot-area {max-height:275px!important;min-height:275px!important;overflow:hidden!important;}
    .chatbot-area>div:not(.gr-label){max-height:275px!important;overflow-y:auto!important;}

    .input-controls-row {margin-top:-12px!important;align-items:flex-end!important;gap:1rem!important;}

    .wf-btn,.wf-btn button{
        background:#00C4A7!important;color:white!important;border:none!important;
        border-radius:8px!important;font-weight:600!important;font-size:.9rem!important;
        height:38px!important;width:100%!important;display:flex!important;
        align-items:center!important;justify-content:center!important;
        box-shadow:0 1px 2px rgba(0,0,0,.1)!important;
        transition:.2s!important;
    }
    .wf-btn:hover{background:#00A38A!important;transform:translateY(-1px);}
    .right-controls{display:flex!important;flex-direction:column!important;gap:8px!important;width:180px!important;}
    @media(max-width:768px){
        .right-controls{width:120px!important;}
        .chatbot-area{overflow-y:auto!important;padding-bottom:20px!important;}
    }
    """

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme,css=custom_css) as demo:

        gr.Markdown("### 💤 WAI is waking up…",elem_id="wai_wakeup")

        gr.HTML("""<script>
        function wai_check_ready(){
            const c=document.querySelector('.chatbot-area');
            const t=document.querySelector('textarea');
            const b=document.querySelector('button');
            if(c&&t&&b){document.getElementById('wai_wakeup').style.display='none';return;}
            setTimeout(wai_check_ready,500);
        }
        setTimeout(wai_check_ready,350);
        </script>""")

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(label="WorkFriend Conversation",type="messages",height=420,elem_classes=["chatbot-area"])
        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(label="Your question:",placeholder="Ask me something...",scale=4)

            with gr.Column(elem_classes="right-controls",scale=0):
                copy_btn=gr.Button("📋 Copy Last Response",elem_classes=["wf-btn"])
                actions=add_user_actions(chatbot,retrieve_and_answer)
                retry_btn=actions.get("retry")
                if retry_btn: retry_btn.elem_classes=["wf-btn"]
                send_btn=gr.Button("Send",elem_classes=["wf-btn"])

        send_btn.click(answer_fn,[user_input,chatbot],chatbot)
        user_input.submit(answer_fn,[user_input,chatbot],chatbot)

        gr.HTML("""<script>
        document.addEventListener("keydown",function(e){
            if(e.target.tagName==="TEXTAREA"&&!e.shiftKey&&e.key==="Enter"){
                e.preventDefault();document.querySelector("button:contains('Send')")?.click();
            }
        });
        </script>""")

    return demo
