# ==========================================================
# app/chatbot.py — WorkFriend Chatbot (Routing OK + UX Restored)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path

from app.router import route, postprocess_answer          # routing stays
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot


def init_chatbot():

    # ------------------------------------------------------
    # Model + Corpus (unchanged)
    # ------------------------------------------------------
    ARTICLES = Path("content/articles")
    if not ARTICLES.exists():
        ARTICLES = Path(".")
    INDEX = Path("index")

    key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.28, openai_api_key=key)

    docs = []
    for f in ARTICLES.glob("*.md"):
        t = f.read_text(encoding="utf-8").strip()
        if not t: continue
        chunks = [t[i:i+1500] for i in range(0,len(t),1500)]
        for c in chunks:
            docs.append({"content":c,"metadata":{"source":f.name}})

    vectordb = Chroma.from_texts(
        texts=[x["content"] for x in docs],
        embedding=embedding,
        metadatas=[x["metadata"] for x in docs]
    )
    retriever = vectordb.as_retriever(search_kwargs={"k":3})

    # ------------------------------------------------------
    # Router-aware structured prompt (this was working)
    # ------------------------------------------------------
    prompt = ChatPromptTemplate.from_template(
        "{system}\n\nContext:\n{context}\n\n"
        "Respond using:\n"
        "Answer: clear, useful guidance\n"
        "Why this matters: reasoning behind approach\n"
        "Plays / Examples: small scripts/moves when appropriate\n\n"
        "User: {question}"
    )

    def retrieve_and_answer(q):
        system = route(q)
        ctx = "\n\n".join([d.page_content for d in retriever.invoke(q)]) or "No relevant context found."
        msg = prompt.format(system=system, context=ctx, question=q)
        out = llm.invoke(msg)
        return postprocess_answer(q, out.content)

    def answer_fn(msg, history):
        history.append({"role":"user","content":msg})
        try:
            a = retrieve_and_answer(msg)
            history.append({"role":"assistant","content":a})
            return history
        except Exception as e:
            return history+[{"role":"assistant","content":f"⚠️ {e}"}]


    # =====================================================================
    #  MINT UX PATCH — restored exactly from your good version
    # =====================================================================
    custom_css = """
    footer, .footer {display:none!important;height:0!important;}

    .chatbot-area {max-height:275px!important;min-height:275px!important;overflow:hidden!important;margin:0!important;}
    .chatbot-area>div:not(.gr-label){max-height:275px!important;overflow-y:auto!important;}

    .wf-btn {background:#00C4A7!important;color:white!important;border:none!important;
             border-radius:8px!important;font-weight:600!important;font-size:.9rem!important;
             height:38px!important;width:100%!important;display:flex!important;align-items:center!important;
             justify-content:center!important;cursor:pointer!important;transition:.15s;}
    .wf-btn:hover{background:#00A38A!important;transform:translateY(-1px);}

    .right-controls{display:flex!important;flex-direction:column!important;gap:8px!important;width:180px!important;}

    @media(max-width:768px){
        .right-controls{width:120px!important;gap:6px!important;}
        .right-controls button:nth-child(2){order:1!important;}   /* Send on top */
        .right-controls button:nth-child(1){order:2!important;}   /* Retry below */
    }
    """

    theme = gr.themes.Default()

    with gr.Blocks(theme=theme, css=custom_css) as demo:

        # "wake up first then hide" — preserved
        gr.Markdown("### 💤 WAI is waking up… *(first load 5–10s)*",elem_id="wai_wakeup")

        gr.HTML("""
        <script>
        function ready(){const c=document.querySelector('.chatbot-area');const t=document.querySelector('textarea');
            const b=document.querySelector('button');if(c&&t&&b){const w=document.querySelector('#wai_wakeup');
            if(w)w.style.display='none';return;}setTimeout(ready,400);}setTimeout(ready,300);
        </script>""")

        gr.Markdown("### 💬 WAI — WorkFriend Assistant")

        chatbot = gr.Chatbot(type="messages", height=420, elem_classes=["chatbot-area"])
        add_feedback_below_chatbot()

        with gr.Row():
            user = gr.Textbox(label="Ask WAI…", placeholder="How do I run a governance review?", scale=4)

            with gr.Column(elem_classes="right-controls", scale=0):
                copy_btn = gr.Button("📋 Copy", elem_classes=["wf-btn"])
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if retry_btn:
                    retry_btn.elem_classes = (retry_btn.elem_classes or [])+["wf-btn"]
                send = gr.Button("Send", elem_classes=["wf-btn"])

        send.click(answer_fn,[user,chatbot],[chatbot])
        user.submit(answer_fn,[user,chatbot],[chatbot])

        # ENTER TO SEND — restored
        gr.HTML("""
        <script>
        document.addEventListener("keydown",e=>{
            if(e.target.tagName==="TEXTAREA"&&!e.shiftKey&&e.key==="Enter"){
                e.preventDefault();Array.from(document.querySelectorAll("button"))
                  .find(b=>b.textContent.trim()==="Send")?.click();
            }
        });
        </script>
        """)

    return demo
