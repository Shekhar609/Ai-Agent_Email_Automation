You are a senior AI engineer specializing in AI Agents, LangGraph, LangChain, and autonomous workflow systems.

Build a production-ready AI Email Automation Agent using LangGraph or LangChain.

## Goal

Create an intelligent AI email assistant that can:

* Read emails
* Classify emails
* Generate replies
* Send emails automatically
* Schedule follow-ups
* Maintain conversation memory
* Handle multi-step workflows autonomously

## Tech Stack

Backend:

* Python
* FastAPI

AI Framework:

* LangGraph (preferred)
* LangChain

LLM:

* OpenAI GPT-4o or Claude API

Database:

* PostgreSQL or MongoDB

Vector Database:

* ChromaDB or Pinecone

Email Integration:

* Gmail API
* Outlook API
* SMTP/IMAP

Task Queue:

* Celery + Redis

Frontend:

* React.js or Next.js

## Core AI Agent Features

### 1. Email Reader Agent

* Read incoming emails from Gmail
* Extract:

  * sender
  * subject
  * intent
  * urgency
  * entities
* Store email embeddings in vector DB

### 2. Email Classification Agent

Classify emails into:

* Sales
* Support
* HR
* Spam
* Meeting
* Follow-up
* Urgent

Use structured output parsers.

### 3. AI Reply Agent

Generate contextual replies automatically using:

* Previous email thread
* User memory
* Company knowledge base
* Tone selection

Support:

* Professional
* Friendly
* Sales
* Technical tones

### 4. Autonomous Workflow Agent

Using LangGraph:

* Build state-based workflows
* Add conditional routing
* Human approval node
* Retry/error handling
* Multi-agent collaboration

Example Flow:
Receive Email →
Classify →
Retrieve Context →
Generate Reply →
Human Approval →
Send Email →
Log Activity

### 5. Memory System

Implement:

* Conversation memory
* Long-term memory
* Semantic search
* Retrieval-Augmented Generation (RAG)

### 6. Scheduler Agent

* Detect follow-up requirements
* Schedule reminders
* Auto-send follow-up emails

### 7. Human-in-the-Loop

* Allow admin approval before sending
* Editable AI-generated drafts
* Confidence score system

### 8. Dashboard

Create dashboard for:

* Inbox monitoring
* AI-generated drafts
* Sent emails
* Analytics
* Agent activity logs

## LangGraph Requirements

Create:

* StateGraph workflow
* Multiple nodes
* Conditional edges
* Tool calling
* Memory checkpointing

Nodes should include:

* email_reader
* classifier
* retriever
* response_generator
* approval_node
* sender_node
* logger_node

## AI Tools Integration

Integrate tools for:

* Web search
* CRM lookup
* Calendar scheduling
* Document retrieval
* Knowledge base querying

## Security

* OAuth2 authentication
* Secure token storage
* Email encryption
* API rate limiting

## Deliverables

Generate:

1. Complete project architecture
2. Folder structure
3. LangGraph workflow implementation
4. FastAPI backend
5. Gmail integration
6. Vector DB setup
7. RAG pipeline
8. Multi-agent orchestration
9. Docker configuration
10. Deployment guide

Also include:

* Mermaid workflow diagrams
* Production best practices
* Scalability recommendations
* Monitoring/logging setup
* Example environment variables
* Unit tests

Provide complete working code with explanations.
