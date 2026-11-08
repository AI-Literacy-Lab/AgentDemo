"""
REAL-WORLD DEMO: The support bot that refunded everyone
--------------------------------------------------------
Scenario
    Spice Route Store runs a WhatsApp support bot. Festival week, hundreds of
    "where is my order?" messages. The bot has two tools:

        search_orders         -> read-only lookup
        resolve_order_issue   -> action tool. Its CODE issues a FULL REFUND.

    The agent never sees the code. It only sees the description.
    Vague description  -> it refunds people who only asked for tracking.
    Precise description -> it refunds only when a refund is actually warranted.

Run
    python refund_agent_demo.py bad --script     # automatic 3-message demo, vague description
    python refund_agent_demo.py good --script    # same 3 messages, precise description
    python refund_agent_demo.py bad              # type your own messages

Setup
    ollama pull llama3.2
    pip install -U langchain langchain-core langchain-ollama langgraph
    Optional: OLLAMA_CHAT_MODEL=llama3.1:8b  (more reliable than 3B models)
"""

import os
import sys

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver          # MEMORY

CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2:latest")
# MODE = sys.argv[1] if len(sys.argv) > 1 else "bad"
SCRIPTED = "--script" in sys.argv

llm = ChatOllama(model=CHAT_MODEL, temperature=0)

# ---------------------------------------------------------------------------
# Fake store data (resets every run so the demo is repeatable)
# ---------------------------------------------------------------------------
ORDERS = {
    "ORD2041": {"item": "Malabar pepper 1kg", "amount": 1240, "status": "In transit", "note": "Courier delay, new ETA tomorrow"},
    "ORD2043": {"item": "Cardamom 500g", "amount": 1840, "status": "Delivered", "note": "Delivered 2 days ago"},
    "ORD2045": {"item": "Turmeric powder 1kg", "amount": 560, "status": "Packed", "note": "Dispatching today, ETA 3 days"},
}
LEDGER = []  # every refund the bot issues ends up here

# ---------------------------------------------------------------------------
# THE DESCRIPTIONS: this is all the agent knows about the action tool
# ---------------------------------------------------------------------------
# DESCRIPTIONS = {
#     "bad": "Handle customer order problems such as late delivery, delays, missing orders or complaints. Use this to fix the customer's issue.",
#     "good": (
#         "ISSUES A FULL REFUND to the customer's original payment method. "
#         "Money leaves the business and this cannot be undone. "
#         "Only call when the customer explicitly asks for a refund or their money back "
#         "AND the order arrived damaged or is lost. "
#         "NEVER call for delivery delays, tracking, or status questions: use search_orders for those."
#     ),
# }
# ##BAD Example
# DESCRIPTIONS=   "Handle customer order problems such as late delivery, delays, missing orders or complaints. Use this to fix the customer's issue."






# #GOOD Example
DESCRIPTIONS= '''ISSUES A FULL REFUND to the customer's original payment method.
Money leaves the business and this cannot be undone. 
Only call when the customer explicitly asks for a refund or their money back AND the order arrived damaged or is lost. 
NEVER call for delivery delays, tracking, or status questions: use search_orders for those.'''
# # ---------------------------------------------------------------------------
# TOOL 1: search (read-only)
# ---------------------------------------------------------------------------
@tool#(description="Look up orders by order ID or item name. Read-only: returns status, amount and delivery notes.")
def search_orders(query: str) -> str:
    """Look up orders by order ID or item name. Read-only: returns status, amount and delivery notes."""
    hits = [
        f"{oid}: {o['item']} | Rs. {o['amount']:,} | {o['status']} | {o['note']}"
        for oid, o in ORDERS.items()
        if query.upper() in oid or query.lower() in o["item"].lower()
    ]
    return "\n".join(hits) or "No matching orders."
# ---------------------------------------------------------------------------
# TOOL 2: action. Focus on the next line: it decides the agent's behaviour
# ---------------------------------------------------------------------------
@tool(description=DESCRIPTIONS)
def resolve_order_issue(order_id: str) -> str:
    # The agent CANNOT see this code. It only sees the description above.
    order = ORDERS.get(order_id.upper())
    if not order:
        return "Order not found."
    if order["status"] == "REFUNDED":
        return "Already refunded."
    order["status"] = "REFUNDED"
    LEDGER.append((order_id.upper(), order["amount"]))
    print(f"      💸 REAL EFFECT: Rs. {order['amount']:,} refunded to customer's UPI for {order_id.upper()}")
    return f"Issue on {order_id.upper()} resolved."


TOOLS = [search_orders, resolve_order_issue]

SYSTEM_PROMPT = (
    "You are the WhatsApp support assistant for Spice Route Store, an online spice shop."
    "Be brief and friendly. Use the tools to fix the customer's problem whenever possible."
)

# ---------------------------------------------------------------------------
# Agent (LangChain v1 create_agent, with fallback for older versions)
# ---------------------------------------------------------------------------
memory = MemorySaver()  
try:
    from langchain.agents import create_agent

    agent = create_agent(llm, TOOLS, system_prompt=SYSTEM_PROMPT,checkpointer=memory)
except ImportError:
    print("on)Falling back to langgraph.create_react_agent (older langchain-core versi")


def ask(text: str, thread_id: str) -> str:
    # Each message is handled independently so the A/B comparison stays clean
    result = agent.invoke({"messages": [HumanMessage(text)]}, config={"configurable": {"thread_id": thread_id}})
    msgs = result["messages"]
       # MEMORY: history now includes earlier turns, so only print what happened after THIS message
    start = max(i for i, m in enumerate(msgs) if isinstance(m, HumanMessage))
    for m in msgs[start + 1:]:
           if isinstance(m, AIMessage) and m.tool_calls:
               for tc in m.tool_calls:
                   print(f"   🔧 {tc['name']}({tc['args']})")
           elif isinstance(m, ToolMessage):
               print(f"      ↳ {m.content}")
    return msgs[-1].content


def summary():
    total = sum(a for _, a in LEDGER)
    print("=" * 60)
    print(f"Refunds issued by the bot: {len(LEDGER)} | Money out: Rs. {total:,}")
   
    print("=" * 60)


# ---------------------------------------------------------------------------
# Three real customer messages: only the 2nd deserves a refund
# ---------------------------------------------------------------------------
SCRIPT = [
    "Hi, my order ORD2041 was supposed to come yesterday. Where is it?",
    "The cardamom in ORD2043 arrived soaked and spoiled. I want my money back.",
    "ORD2045 is taking too long. Please sort this out.",
]

if __name__ == "__main__":
    print(f"Model: {CHAT_MODEL} ")
    #print(f'resolve_order_issue description the agent sees: "{DESCRIPTIONS[MODE]}"\n')

    if SCRIPTED:
        for msg in SCRIPT:
            print(f"Customer: {msg}")
            print(f"Agent: {ask(msg)}\n")
        summary()
    else:
        while True:
            q = input("Customer: ").strip()
            if q.lower() in {"exit", "quit"}:
                break
            if q:
                print(f"Agent: {ask(q, 'live')}\n")
        summary()