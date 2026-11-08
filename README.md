# AgentDemo

A command-line order-support agent for Spice Route Store. It uses a local Ollama
chat model and two tools:

- `search_orders` looks up order status, amount, and delivery notes.
- `resolve_order_issue` changes an order's status to `REFUNDED` and records the
  refund in an in-memory ledger.

The refund policy is provided in the action tool's description: refund only
when the customer explicitly asks for a refund and the order is damaged or lost.
The demo data is hard-coded and resets whenever the program restarts; it does
not connect to a real store or payment system.

## Requirements

- Python
- [Ollama](https://ollama.com/) installed and running
- The `llama3.2` model, or another compatible model selected with
  `OLLAMA_CHAT_MODEL`

Install the Python dependencies from this directory:

```shell
python -m pip install -r requirements.txt
```

Download the default model:

```shell
ollama pull llama3.2
```

## Run

Start the interactive assistant:

```shell
python "agent_demo copy.py"
```

Enter a customer message at the `Customer:` prompt. Enter `exit` or `quit` to
stop. At exit, the program prints the number and total value of refunds issued
during that run.

To select another Ollama model, set `OLLAMA_CHAT_MODEL` before starting the
program. For example, in PowerShell:

```powershell
$env:OLLAMA_CHAT_MODEL = "llama3.1:8b"
python "agent_demo copy.py"
```

## Demo data

The sample orders are defined in the Python file:

| Order | Item | Initial status | Note |
|---|---|---|---|
| `ORD2041` | Malabar pepper 1kg | In transit | Courier delay, new ETA tomorrow |
| `ORD2043` | Cardamom 500g | Delivered | Delivered 2 days ago |
| `ORD2045` | Turmeric powder 1kg | Packed | Dispatching today, ETA 3 days |

This is a tool-description demonstration, not production refund software.
Refund decisions and tool execution should be verified before connecting
similar actions to real customer accounts or payment systems.
