# ==========================================================
# app/chatbot.py — WorkFriend WAI (Stable UX + Router + Spinner)
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
        ARTICLES_DIR = Path(".")  # fallback

    openai_key = os.getenv("OPENAI_API_KEY")
    embedding = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.28, openai_api_key=openai_key)

    # ------------------------------------------------------
    # Build embeddings from /content/articles
    # ------------------------------------------------------
    docs=[]
    for md in ARTICLES_DIR.glob("*.md"):
        t=md.read_text(encoding="utf-8").strip()
        if not t: continue
        for i in range(0,len(t),1500):
            docs.append({"content":t[i:i+1500],"metadata":{"source":md.name}})

    vectordb=Chroma.from_texts(
        [x["content"] for x in docs],
        embedding,
        metadatas=[x["metadata"] for x in docs]
    )
    retriever=vectordb.as_retriever(search_kwargs={"k":3})

    # ------------------------------------------------------
    # Routing + LLM call
    # ------------------------------------------------------
    def retrieve_and_answer(msg):
        system = route(msg)

        ctx="\n\n".join([d.page_content for d in retriever.invoke(msg)])
        prompt=ChatPromptTemplate.from_template(
            "{system}\n\nContext:\n{ctx}\n\n"
            "Respond using:\n"
            "1. **Answer**\n"
            "2. **Why this matters**\n"
            "3. **Plays/Examples**\n\n"
            "User Question: {msg}"
        ).format(system=system,ctx=ctx,msg=msg)

        r=llm.invoke(prompt)
        return postprocess_answer(r.content)

    def answer_fn(message,history):
        history += [{"role":"user","content":message}]
        try:
            a=retrieve_and_answer(message)
            history+=[{"role":"assistant","content":a}]
            return history,""
        except Exception as e:
            return history+[{"role":"assistant","content":f"⚠️ {e}"}],""


    # ------------------------------------------------------
    # STABLE known-good UX CSS (from backup)
    # ------------------------------------------------------
    custom_css="""
    footer,.footer{display:none!important;}

    .chatbot-area{
        max-height:275px!important;
        min-height:275px!important;
        overflow-y:auto!important;
    }

    .input-controls-row{
        margin-top:-12px!important;
        align-items:flex-end!important;
        gap:1rem!important;
    }

    .wf-btn,button.wf-btn{
        background:#00C4A7!important;color:#fff!important;border:none!important;
        border-radius:8px!important;font-weight:600!important;height:38px!important;
        box-shadow:0 1px 2px rgba(0,0,0,.1)!important;
    }
    .wf-btn:hover{background:#00A38A!important;}

    .right-controls{
        display:flex!important;flex-direction:column!important;
        gap:8px!important;width:180px!important;
    }

    @media(max-width:768px){
        .right-controls{width:120px!important;}
        .right-controls button:nth-child(2){order:1!important;}
        .right-controls button:nth-child(1){order:2!important;}
    }
    """


    # ------------------------------------------------------
    # UI Layout (unchanged from working UX)
    # ------------------------------------------------------
    with gr.Blocks(css=custom_css) as demo:

        gr.Markdown("### 💤 WAI is waking up…", elem_id="wai_wakeup")

        # Wake watcher
        gr.HTML("""
        <script>
        function ready(){
            if(document.querySelector('.chatbot-area')&&document.querySelector('textarea')){
                const w=document.querySelector('#wai_wakeup');if(w)w.style.display="none";
                return;
            }
            setTimeout(ready,400);
        }
        setTimeout(ready,300);
        </script>
        """)

        gr.Markdown("### 💬 WorkFriend Chatbot")

        chatbot = gr.Chatbot(type="messages", height=420, elem_classes=["chatbot-area"])
        add_feedback_below_chatbot()

        with gr.Row(elem_classes="input-controls-row"):
            user_input = gr.Textbox(placeholder="Ask me something…", label="Your Question:", scale=4)

            with gr.Column(elem_classes="right-controls",scale=0):
                copy_btn=gr.Button("📋 Copy Last",elem_classes=["wf-btn"])
                actions=add_user_actions(chatbot,retrieve_and_answer)
                retry_btn=actions.get("retry")
                if retry_btn: retry_btn.elem_classes=["wf-btn"]
                send_btn=gr.Button("Send",elem_classes=["wf-btn"])


        # Send binds (keeps input next-to button UX fixed)
        send_btn.click(answer_fn,[user_input,chatbot],[chatbot,user_input])
        user_input.submit(answer_fn,[user_input,chatbot],[chatbot,user_input])


        # --------------------------------------------------
        # Spinner JS ONLY — no layout modification
        # --------------------------------------------------
        gr.HTML("""
        <script>
        function spin(){
            const box=document.querySelector('.chatbot-area');if(!box)return;
            let s=document.createElement('div');
            s.innerHTML="⏳ Thinking…";
            s.style="font-size:.85rem;color:#00C4A7;margin:6px;opacity:.75;";
            box.appendChild(s);
            setTimeout(()=>s.remove(),15000);
        }
        document.addEventListener("click",e=>{
            if(e.target.textContent.trim()==="Send")spin();
        });
        document.addEventListener("keydown",e=>{
            if(e.target.tagName==="TEXTAREA"&&!e.shiftKey&&e.key==="Enter")spin();
        });
        </script>
        """)

        # Enter key UX
        gr.HTML("""
        <script>
        document.addEventListener("keydown",function(e){
            const ta=e.target;if(!ta||ta.tagName!=="TEXTAREA")return;
            if(e.shiftKey&&e.key==="Enter")return;
            if(!e.shiftKey&&e.key==="Enter"){
                e.preventDefault();
                [...document.querySelectorAll("button")].find(b=>b.innerText.trim()==="Send")?.click();
            }
        });
        </script>
        """)

    return demo
