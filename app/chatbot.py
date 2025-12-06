# ==========================================================
# app/chatbot.py — WorkFriend WAI (v4.x Router + Mint UX + Spinner + Enter-to-send)
# ==========================================================

import gradio as gr
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
from app.chatbot_actions import add_user_actions, add_feedback_below_chatbot
from app.router import route, postprocess_answer


def init_chatbot():
    # ------------------------------------------------------
    # Paths + Model setup
    # ------------------------------------------------------
    ARTICLES_DIR = Path("content/articles")
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR = Path(".")
    INDEX_DIR = Path("index")

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_key
    )
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.28,
        openai_api_key=openai_key
    )

    # ------------------------------------------------------
    # Vector store build
    # ------------------------------------------------------
    docs = []
    for md_file in ARTICLES_DIR.glob("*.md"):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = [text[i:i + 1500] for i in range(0, len(text), 1500)]
        for chunk in chunks:
            docs.append({"content": chunk, "metadata": {"source": md_file.name}})

    vectordb = Chroma.from_texts(
        texts=[d["content"] for d in docs],
        embedding=embedding,
        metadatas=[d["metadata"] for d in docs],
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    # ======================================================
    # Router + Retrieval logic
    # ======================================================
    def retrieve_and_answer(question: str) -> str:
        system_prompt = route(question)

        retrieved_docs = retriever.invoke(question)
        context = "\n\n".join([d.page_content for d in retrieved_docs])

        prompt_tmpl = ChatPromptTemplate.from_template(
            "{system}\n\n"
            "Context:\n{context}\n\n"
            "Respond using this structure:\n"
            "1. **Answer** – clear, useful guidance\n"
            "2. **Why this matters** – reasoning\n"
            "3. **Plays / Examples** – scripts or micro-moves when helpful\n\n"
            "User Question: {question}"
        )

        filled = prompt_tmpl.format(
            system=system_prompt,
            context=context,
            question=question,
        )

        response = llm.invoke(filled)
        return postprocess_answer(response.content)

    def answer_fn(message, history):
        try:
            history = history + [{"role": "user", "content": message}]
            answer = retrieve_and_answer(message)
            history = history + [{"role": "assistant", "content": answer}]
            return history, ""   # Clears input box (important!!)
        except Exception as e:
            return history + [{"role":"assistant","content":f"⚠️ Error: {e}"}], ""

    # ======================================================
    # CSS (UX + Mint Buttons)
    # ======================================================
    custom_css = """
    .gradio-container *,
    .gradio-container,
    .block,
    .wrap,
    .gradio-app { margin:0!important; padding:0!important; }
    footer,.footer { display:none!important; }

    .chatbot-area {
        max-height:275px!important;
        min-height:275px!important;
        overflow:hidden!important;
    }
    .chatbot-area > div:not(.gr-label){
        max-height:275px!important;
        min-height:275px!important;
        overflow-y:auto!important;
    }

    .input-controls-row { margin-top:-12px!important; gap:1rem!important; }

    .wf-btn { background:#00C4A7!important; color:#fff!important;
        border-radius:8px!important; font-weight:600!important; height:38px!important; }
    .wf-btn:hover { background:#00A38A!important; transform:translateY(-1px)!important;}

    .right-controls { display:flex!important; flex-direction:column!important; gap:8px!important; width:180px!important; }

    @media (max-width:768px){
        .right-controls { width:120px!important; }
        .right-controls button:nth-child(2){ order:1!important;}
        .right-controls button:nth-child(1){ order:2!important;}
    }
    """

    theme = gr.themes.Default()

    # ======================================================
    # UI
    # ======================================================
    with gr.Blocks(theme=theme, css=custom_css) as demo:

        gr.Markdown("### 💤 WAI is waking up… (first load 5–10 sec)", elem_id="wai_wakeup")

        # Wake-up watcher
        gr.HTML("""
        <script>
        function wai_ready(){
            const c=document.querySelector('.chatbot-area'),t=document.querySelector('textarea'),b=document.querySelector('button');
            if(c&&t&&b){document.querySelector('#wai_wakeup').style.display="none";return;}
            setTimeout(wai_ready,400);
        }
        setTimeout(wai_ready,300);
        </script>
        """)

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(type="messages", height=420, elem_classes=["chatbot-area"])
        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(placeholder="Ask me something...", label="Your question:", scale=4)

            with gr.Column(elem_classes="right-controls", scale=0):
                copy_btn = gr.Button("📋 Copy Last Response", elem_classes=["wf-btn"])
                actions = add_user_actions(chatbot, retrieve_and_answer)
                retry_btn = actions.get("retry")
                if isinstance(retry_btn, gr.Button):
                    retry_btn.elem_classes=("wf-btn",)

                send_btn = gr.Button("Send", elem_classes=["wf-btn"])

        # Main bindings
        send_btn.click(answer_fn, [user_input, chatbot], [chatbot, user_input])
        user_input.submit(answer_fn, [user_input, chatbot], [chatbot, user_input])

        # ======================================================
        # Spinner Injection — no router change, no UX break
        # ======================================================
        gr.HTML("""
        <script>
        function wai_spinner(){
            const box=document.querySelector('.chatbot-area');
            if(!box)return;
            let s=document.createElement('div');
            s.innerHTML="⏳ Thinking...";
            s.style="font-size:.85rem;color:#00C4A7;margin:6px;opacity:.8;";
            box.appendChild(s);
            setTimeout(()=>s.remove(),15000);
        }
        document.addEventListener("click",e=>{
            if(e.target.innerText.trim()==="Send") wai_spinner();
        });
        document.addEventListener("keydown",e=>{
            if(e.target.tagName==="TEXTAREA"&&!e.shiftKey&&e.key==="Enter") wai_spinner();
        });
        </script>
        """)

        # Enter behaviour (preserved)
        gr.HTML("""
        <script>
        document.addEventListener("keydown",function(e){
            const ta=e.target;
            if(!ta||ta.tagName!=="TEXTAREA")return;
            if(e.shiftKey&&e.key==="Enter")return;
            if(!e.shiftKey&&e.key==="Enter"){
                e.preventDefault();
                document.querySelectorAll("button").forEach(b=>{
                    if(b.innerText.trim()==="Send")b.click();
                });
            }
        });
        </script>
        """)

    return demo
