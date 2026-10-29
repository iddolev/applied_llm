# Frameworks: conclusions and recommendations

## Recommendation

Build the system without an LLM framework:

| Part | Choice |
|---|---|
| Embeddings | `sentence-transformers`, a local model such as `BAAI/bge-small-en-v1.5`, on CPU |
| Vector store | A numpy matrix plus `chunks.jsonl` (about 30k vectors, so brute-force search takes milliseconds); LanceDB if a real database becomes useful |
| Answering | The `anthropic` SDK, with structured output for the answer and its citations |
| Agent (hierarchical summaries) | The Anthropic SDK tool runner, which runs the ReAct loop |
| Observability and evaluation | LangFuse, self-hosted, added when we build the question set and compare systems; until then, JSONL logs |

The plain RAG baseline takes about 150 lines of our own code on top of these libraries.

## Why not a framework

These reasons apply to the four frameworks below (LiteLLM, a provider-abstraction layer rather than a framework, has its own reasons):

1. **The parts that matter are custom.** We chunk wikitext by section, start each chunk with its heading path (e.g. "Moral luck › Criticism"), and merge sections that are too short. We number the chunks in the prompt, have Claude cite them inline (`[3]`), check that the cited numbers exist, and turn them into links to the Wikipedia section. Frameworks provide generic versions of these steps, and we would end up overriding most of them.
2. **This is an experiment, not a product.** We will compare plain RAG, RAG with a reranker and an agent that navigates hierarchical summaries. We need to see and control the exact prompt, the retrieved chunks and their scores. Frameworks hide these behind layers of abstraction, which makes it harder to tell why a variant fails.
3. **The task is small.** The steps are chunk, embed, search, prompt and parse. Each is a few lines with the underlying libraries, so a framework would not shorten the code much. It would add another API to learn and debug.
4. **Dependency cost.** Frameworks bring many transitive dependencies and change their APIs often. For a project this size the maintenance burden is larger than the benefit.

A framework pays off when you need many integrations: dozens of document loaders, vector databases or model providers that are swapped often. That is not our situation. We have one corpus format, one embedding model, one vector store and one LLM provider.

### LlamaIndex

It is the most RAG-focused of these libraries: loading, chunking, embedding, indexing and a query engine that returns sources, in a few lines. It also implements hierarchical ideas such as tree indexes and recursive retrieval.

Why not:
- **Chunking:** its node parsers don't understand wikitext sections, so we would write a custom parser anyway.
- **Prompts and citations:** its prompts and response synthesis are hidden behind query-engine abstractions, and we want our own prompt and citation format.
- **Hierarchical retrieval:** its built-in versions are fixed designs, but we want to design and measure our own variant against the baseline.

### LangChain

It is a general LLM framework with components for RAG: loaders, splitters, vector store wrappers, retrievers and chains.

Why not:
- **Breadth:** its main value is the large set of integrations, which we don't need.
- **Wrappers:** it wraps model calls in its own message and chain abstractions. That makes it harder to use Anthropic-specific features directly, such as structured outputs, effort and prompt caching.
- **Stability:** it has a history of frequent breaking API changes and deprecations.

### Haystack

It is pipeline-oriented and aimed at production search systems: components connected into pipelines, with document stores, retrievers and rankers.

Why not:
- **Scale:** its strengths are for production systems serving traffic (serializable pipelines, document store backends, deployment), and we don't need them.
- **Structure:** the pipeline structure adds ceremony to an experiment in which we keep changing the steps.
- **Chunking:** as with the others, we would still write our own wikitext chunking and citation handling.

### LangGraph

It orchestrates stateful agents as graphs, with branching, parallel steps, persistence and checkpointing, resuming, and human-in-the-loop approval.

Why not:
- **Simple loop:** our agent is a ReAct loop: call Claude, run the tools it requests, repeat. The Anthropic SDK's tool runner handles that loop directly.
- **Unused features:** we don't need checkpointing, resuming or human approval steps.

When to reconsider: if the agent grows into parallel exploration of several branches with merged results, or a multi-agent setup.

### LiteLLM

It is a single, OpenAI-style interface to 100+ model providers (Anthropic, OpenAI, Gemini, Bedrock, local models through Ollama, ...): switching providers means changing the model string. It also comes as a proxy server that adds API key management, per-user budgets, rate limiting, fallbacks between providers, load balancing and central logging.

Why not:
- **One provider:** we call only Claude, so the `anthropic` SDK is the most direct path.
- **Lowest common denominator:** everything goes through an OpenAI-shaped format. We want Anthropic-specific features: structured outputs (`messages.parse` with Pydantic), the `effort` setting, prompt caching (important if the agent reads all article summaries with every question) and the SDK's tool runner. Through LiteLLM these are supported late, partially or awkwardly.
- **Another layer:** one more layer to debug when something behaves unexpectedly.
- **Proxy features:** budgets, keys and fallbacks address organisational needs (many users or services sharing LLM access), which we don't have.
- **Embeddings:** ours are local (`sentence-transformers`), so its embedding API support doesn't help.

When to reconsider:
- **Comparing answering models across providers**, e.g. Claude vs GPT vs a local model. Even then, use it only for the single answering call, or write a small function with one implementation per provider.
- **A shared service:** the system becomes something several people or services call, where cost tracking, budgets and fallbacks matter.

## Why LangFuse is different

LangFuse is not a framework. It records and evaluates what the system does, so it doesn't conflict with the reasons above. It is open source, can be self-hosted (so the data stays local), and works with the plain Anthropic SDK through a decorator, without LangChain. It gives us:

- **Traces:** for each question it records the retrieved chunks, the prompt, the answer, token counts, cost and latency. For the agent, it shows every navigation step as a tree, which helps explain why the agent took a wrong branch.
- **Datasets and experiments:** it stores the question set, runs each system variant against it and compares results side by side.
- **Scores:** it attaches LLM-as-judge or manual scores to each answer, for correctness and citation accuracy.

Arize Phoenix is a comparable alternative.

## When to revisit this decision

- **Several backends:** we need several vector databases, document formats or model providers and want to switch between them easily. Consider LlamaIndex or Haystack.
- **Complex agents:** the agent needs persistent state, parallel branches or human-in-the-loop steps. Consider LangGraph.
- **Several LLM providers:** we want to compare or switch between answering models from different providers. Consider LiteLLM for the answering call only.
- **Rewriting existing features:** we find ourselves building a feature a framework already provides well, such as a specific retrieval technique we want as a reference. Use the framework for that component or experiment only.
