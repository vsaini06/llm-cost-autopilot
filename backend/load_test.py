"""
500+ prompt load test.
Run from backend/ with: python load_test.py
Fires prompts at the live FastAPI server and prints final cost savings report.
"""

import asyncio
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import httpx
from rich.console import Console
from rich.table import Table

console = Console()

API_URL = "http://localhost:8000/v1/completions"

PROMPTS = [
    # Tier 1 — Simple (150 prompts)
    ("What is the capital of France?", 1),
    ("What does HTTP stand for?", 1),
    ("What is 15 multiplied by 6?", 1),
    ("Convert 100 Fahrenheit to Celsius.", 1),
    ("What year was the Eiffel Tower built?", 1),
    ("What does CPU stand for?", 1),
    ("What is the boiling point of water in Celsius?", 1),
    ("How many days are in a leap year?", 1),
    ("What does RAM stand for?", 1),
    ("What is the capital of Japan?", 1),
    ("What does API stand for?", 1),
    ("What is 2 to the power of 10?", 1),
    ("What does SQL stand for?", 1),
    ("What does JSON stand for?", 1),
    ("What HTTP status code means Not Found?", 1),
    ("What is the default port for HTTPS?", 1),
    ("What does CSS stand for?", 1),
    ("What does IDE stand for?", 1),
    ("What is the capital of Australia?", 1),
    ("What does OOP stand for?", 1),
    ("What does URL stand for?", 1),
    ("What does DNS stand for?", 1),
    ("What does Git stand for?", 1),
    ("What does CI/CD stand for?", 1),
    ("What is the default port for MySQL?", 1),
    ("What is the chemical symbol for gold?", 1),
    ("How many bytes are in a kilobyte?", 1),
    ("What is the speed of light?", 1),
    ("How many continents are there?", 1),
    ("What is a boolean in programming?", 1),
    ("What is null in programming?", 1),
    ("What is the largest planet in our solar system?", 1),
    ("How many hours are in a day?", 1),
    ("What is the currency of Japan?", 1),
    ("What year did World War II end?", 1),
    ("What is the capital of Canada?", 1),
    ("What does MVP stand for in software?", 1),
    ("What is a for loop?", 1),
    ("What is the index of the first element in a Python list?", 1),
    ("What does IoT stand for?", 1),
    ("Translate hello to French.", 1),
    ("Translate good morning to Spanish.", 1),
    ("What is the square root of 144?", 1),
    ("What is the time complexity of binary search?", 1),
    ("What is the extension for a Python file?", 1),
    ("What is the keyboard shortcut to undo on Windows?", 1),
    ("Who wrote Romeo and Juliet?", 1),
    ("Who invented the telephone?", 1),
    ("What is the capital of Germany?", 1),
    ("What is the capital of Brazil?", 1),
    ("What does REST stand for?", 1),
    ("What does CRUD stand for?", 1),
    ("What does JWT stand for?", 1),
    ("What does TLS stand for?", 1),
    ("What does VPN stand for?", 1),
    ("What is a primary key in a database?", 1),
    ("What does SLA stand for?", 1),
    ("What does ETL stand for?", 1),
    ("What is the capital of India?", 1),
    ("What does SDK stand for?", 1),
    ("What does CLI stand for?", 1),
    ("What is Python?", 1),
    ("What is a variable in programming?", 1),
    ("What is a function in programming?", 1),
    ("What is an array?", 1),
    ("What is a string in programming?", 1),
    ("What does FIFO stand for?", 1),
    ("What does LIFO stand for?", 1),
    ("What is a stack data structure?", 1),
    ("What is a queue data structure?", 1),
    ("What is the capital of Mexico?", 1),
    ("What does NLP stand for?", 1),
    ("What does ML stand for?", 1),
    ("What does AI stand for?", 1),
    ("What is a neural network?", 1),
    ("What does GPU stand for?", 1),
    ("What is an IP address?", 1),
    ("What does TCP stand for?", 1),
    ("What does UDP stand for?", 1),
    ("What is a subnet mask?", 1),
    ("What does HTTPS stand for?", 1),
    ("What is a cookie in web development?", 1),
    ("What is a session in web development?", 1),
    ("What does DOM stand for?", 1),
    ("What is React?", 1),
    ("What is Node.js?", 1),
    ("What does NPM stand for?", 1),
    ("What is TypeScript?", 1),
    ("What is a container in Docker?", 1),
    ("What does K8s stand for?", 1),
    ("What is a microservice?", 1),
    ("What is a monolith in software?", 1),
    ("What is a load balancer?", 1),
    ("What is a CDN?", 1),
    ("What does S3 stand for in AWS?", 1),
    ("What is EC2 in AWS?", 1),
    ("What is Lambda in AWS?", 1),
    ("What is a relational database?", 1),
    ("What is NoSQL?", 1),
    ("What is Redis?", 1),
    ("What is MongoDB?", 1),
    ("What is PostgreSQL?", 1),
    ("What is a foreign key?", 1),
    ("What is an index in a database?", 1),
    ("What is a transaction in a database?", 1),
    ("What does ACID stand for?", 1),
    ("What is a deadlock?", 1),
    ("What is a race condition?", 1),
    ("What is a thread?", 1),
    ("What is a process?", 1),
    ("What does async mean in programming?", 1),
    ("What is a callback function?", 1),
    ("What is a promise in JavaScript?", 1),
    ("What is recursion?", 1),
    ("What is Big O notation?", 1),
    ("What is O(n) time complexity?", 1),
    ("What is O(1) time complexity?", 1),
    ("What is a hash function?", 1),
    ("What is a linked list?", 1),
    ("What is a binary tree?", 1),
    ("What is a graph data structure?", 1),
    ("What is depth-first search?", 1),
    ("What is breadth-first search?", 1),
    ("What is dynamic programming?", 1),
    ("What is memoization?", 1),
    ("What is a greedy algorithm?", 1),
    ("What is a sorting algorithm?", 1),
    ("What is bubble sort?", 1),
    ("What is merge sort?", 1),
    ("What is quicksort?", 1),
    ("What is a heap data structure?", 1),
    ("What does SOLID stand for?", 1),
    ("What is the single responsibility principle?", 1),
    ("What is inheritance in OOP?", 1),
    ("What is polymorphism?", 1),
    ("What is encapsulation?", 1),
    ("What is abstraction in OOP?", 1),
    ("What is a design pattern?", 1),
    ("What is the singleton pattern?", 1),
    ("What is the factory pattern?", 1),
    ("What is the observer pattern?", 1),
    ("What is a webhook?", 1),
    ("What is rate limiting?", 1),
    ("What is caching?", 1),
    ("What is a reverse proxy?", 1),
    ("What is an API gateway?", 1),

    # Tier 2 — Moderate (200 prompts)
    ("Explain the difference between REST and GraphQL APIs.", 2),
    ("Summarize the key differences between TCP and UDP.", 2),
    ("Write a Python function that checks if a string is a palindrome.", 2),
    ("What are the pros and cons of using NoSQL over SQL databases?", 2),
    ("Explain how JWT authentication works.", 2),
    ("Write a SQL query to find the top 5 customers by total purchase amount.", 2),
    ("What is the difference between authentication and authorization?", 2),
    ("Explain how a hash map works internally.", 2),
    ("Write a function to reverse a linked list in Python.", 2),
    ("What are the SOLID principles in software engineering?", 2),
    ("Explain the difference between synchronous and asynchronous programming.", 2),
    ("Write unit tests for a Python function that calculates compound interest.", 2),
    ("Explain Docker containers vs virtual machines.", 2),
    ("What are the main differences between Python 2 and Python 3?", 2),
    ("Write a function that finds duplicate values in a list.", 2),
    ("Explain how indexing improves database query performance.", 2),
    ("What is the CAP theorem and why does it matter?", 2),
    ("Explain the difference between stack and heap memory.", 2),
    ("Write a Python decorator that logs function call time.", 2),
    ("What are the differences between supervised and unsupervised learning?", 2),
    ("Explain what a race condition is and how to prevent it.", 2),
    ("What is the difference between a process and a thread?", 2),
    ("Explain how garbage collection works in Python.", 2),
    ("What are webhooks and how do they differ from polling?", 2),
    ("Explain the observer design pattern with an example.", 2),
    ("Write a function that implements binary search.", 2),
    ("What is eventual consistency in distributed systems?", 2),
    ("Explain the difference between monolithic and microservices architecture.", 2),
    ("Explain how the event loop works in JavaScript.", 2),
    ("What are the differences between merge sort and quick sort?", 2),
    ("Explain how vector embeddings are used in semantic search.", 2),
    ("What is the difference between horizontal and vertical scaling?", 2),
    ("Write a Python function that retries a failed HTTP request up to 3 times.", 2),
    ("Explain the difference between a mutex and a semaphore.", 2),
    ("What are the tradeoffs between eager and lazy loading?", 2),
    ("Write a function to flatten a nested dictionary in Python.", 2),
    ("Explain how OAuth 2.0 works step by step.", 2),
    ("Summarize the key differences between Redis and Memcached.", 2),
    ("Write a Python generator that yields Fibonacci numbers.", 2),
    ("Explain the difference between optimistic and pessimistic locking.", 2),
    ("What are the main components of a Kubernetes cluster?", 2),
    ("Explain the difference between a primary key and a foreign key.", 2),
    ("Write a Python context manager for database connections.", 2),
    ("What is the difference between SQL JOIN types?", 2),
    ("Explain how HTTPS works with TLS handshake.", 2),
    ("Write a function that validates an email address using regex.", 2),
    ("Explain the difference between a compiled and interpreted language.", 2),
    ("What is the difference between a class and an object?", 2),
    ("Explain how the GIL works in Python.", 2),
    ("Write a Python script that reads a CSV and computes column averages.", 2),
    ("Explain the difference between deep copy and shallow copy.", 2),
    ("What is the difference between GET and POST HTTP methods?", 2),
    ("Explain how database transactions work.", 2),
    ("Write a function to check if a binary tree is balanced.", 2),
    ("What is the difference between an abstract class and an interface?", 2),
    ("Explain how DNS resolution works.", 2),
    ("Write a Python function that implements a simple LRU cache.", 2),
    ("Explain the difference between SQL and NoSQL databases.", 2),
    ("What are the main HTTP response status code categories?", 2),
    ("Explain how public key cryptography works.", 2),
    ("Write a Python function to count word frequencies in a string.", 2),
    ("Explain what CORS is and why it exists.", 2),
    ("What is the difference between cookies and local storage?", 2),
    ("Explain how a CDN improves web performance.", 2),
    ("Write a function that finds the longest common subsequence.", 2),
    ("Explain the difference between BFS and DFS.", 2),
    ("What is the difference between a stack and a queue?", 2),
    ("Explain how consistent hashing works.", 2),
    ("Write a Python function that implements merge sort.", 2),
    ("Explain the difference between stateful and stateless services.", 2),
    ("What are the tradeoffs of microservices vs monolith?", 2),
    ("Explain how a load balancer distributes traffic.", 2),
    ("Write a SQL query using window functions to rank employees by salary.", 2),
    ("Explain the difference between a view and a materialized view in SQL.", 2),
    ("What is the difference between OLTP and OLAP?", 2),
    ("Explain how connection pooling works.", 2),
    ("Write a Python function that implements a binary search tree.", 2),
    ("Explain the difference between synchronous and event-driven architecture.", 2),
    ("What are the main differences between REST and gRPC?", 2),
    ("Explain how message queues work.", 2),
    ("Write a Python function that parses a JSON config file.", 2),
    ("Explain the difference between vertical and horizontal database scaling.", 2),
    ("What is the difference between a cold start and warm start in serverless?", 2),
    ("Explain how feature flags work in software deployment.", 2),
    ("Write a Python function that implements quicksort.", 2),
    ("Explain the difference between blue-green and canary deployments.", 2),
    ("What are the main differences between SQL GROUP BY and PARTITION BY?", 2),
    ("Explain how circuit breakers work in microservices.", 2),
    ("Write a function that detects a cycle in a linked list.", 2),
    ("Explain the difference between a coroutine and a thread.", 2),
    ("What is the difference between SOAP and REST?", 2),
    ("Explain how service discovery works in microservices.", 2),
    ("Write a Python class that implements a min heap.", 2),
    ("Explain the difference between synchronous replication and asynchronous replication.", 2),
    ("What are the main differences between HTTP/1.1 and HTTP/2?", 2),
    ("Explain how WebSockets differ from HTTP.", 2),
    ("Write a Python function to implement a graph using adjacency lists.", 2),
    ("Explain the difference between symmetric and asymmetric encryption.", 2),
    ("What is the difference between a token and a session for authentication?", 2),
    ("Explain how a bloom filter works.", 2),
    ("Write a Python function that implements depth-first search.", 2),
    ("Explain the difference between a data lake and a data warehouse.", 2),
    ("What are the tradeoffs of using an ORM vs raw SQL?", 2),
    ("Explain how Kubernetes handles pod scheduling.", 2),
    ("Write a Python function that implements breadth-first search.", 2),
    ("Explain what idempotency means in API design.", 2),
    ("What is the difference between a saga and a two-phase commit?", 2),
    ("Explain how distributed tracing works.", 2),
    ("Write a Python function that implements a trie data structure.", 2),
    ("Explain the difference between forward proxy and reverse proxy.", 2),
    ("What are the main differences between REST and event-driven architecture?", 2),
    ("Explain how database sharding works.", 2),
    ("Write a Python function that finds the shortest path in a graph.", 2),
    ("Explain the difference between a hot standby and a warm standby.", 2),
    ("What are the main differences between a queue and a topic in messaging?", 2),
    ("Explain how column-oriented databases differ from row-oriented databases.", 2),
    ("Write a SQL query to find employees who earn more than their manager.", 2),
    ("Explain how an API rate limiter works.", 2),
    ("What is the difference between a monad and a functor?", 2),
    ("Explain how tail call optimization works.", 2),
    ("Write a Python function that compresses a string using run-length encoding.", 2),
    ("Explain the difference between a mutex and a monitor.", 2),
    ("What are the main differences between TCP and WebSocket?", 2),
    ("Explain how a skip list works.", 2),
    ("Write a Python function that implements Dijkstra's algorithm.", 2),
    ("Explain the difference between a B-tree and a B+ tree.", 2),
    ("What are the main components of a CI/CD pipeline?", 2),
    ("Explain how zero-downtime deployments work.", 2),
    ("Write a Python function that implements a graph topological sort.", 2),
    ("Explain the difference between a fat client and a thin client.", 2),
    ("What are the main differences between Apache Kafka and RabbitMQ?", 2),
    ("Explain how a distributed lock works.", 2),
    ("Write a Python function that finds all permutations of a string.", 2),
    ("Explain the difference between hard delete and soft delete.", 2),
    ("What are the main differences between a document store and a key-value store?", 2),
    ("Explain how multi-version concurrency control works.", 2),
    ("Write a Python function that implements a priority queue.", 2),
    ("Explain what eventual consistency means with a real example.", 2),
    ("What are the main differences between a mutex and a read-write lock?", 2),
    ("Explain how leader election works in distributed systems.", 2),
    ("Write a Python function that implements the knapsack problem.", 2),
    ("Explain the difference between push and pull models in messaging.", 2),
    ("What are the main differences between monorepo and polyrepo?", 2),
    ("Explain how a content delivery network caches content.", 2),
    ("Write a Python function that checks if a graph is bipartite.", 2),
    ("Explain the difference between a microkernel and a monolithic kernel.", 2),
    ("What are the main differences between REST and SOAP?", 2),
    ("Explain how database replication lag occurs and how to handle it.", 2),
    ("Write a Python function that implements the coin change problem.", 2),
    ("Explain the difference between a token bucket and a leaky bucket rate limiter.", 2),
    ("What are the main differences between a data mart and a data warehouse?", 2),
    ("Explain how Raft consensus algorithm works.", 2),
    ("Write a Python function that implements the longest increasing subsequence.", 2),
    ("Explain the difference between a service mesh and an API gateway.", 2),
    ("What are the main differences between optimistic and pessimistic concurrency?", 2),
    ("Explain how a write-ahead log works in databases.", 2),
    ("Write a Python function that solves the N-queens problem.", 2),
    ("Explain the difference between a shard key and a partition key.", 2),
    ("What are the main differences between CQRS and traditional CRUD?", 2),
    ("Explain how a distributed cache invalidation works.", 2),
    ("Write a Python function that implements the traveling salesman problem heuristic.", 2),
    ("Explain the difference between a hot path and a cold path in system design.", 2),
    ("What are the main differences between synchronous and asynchronous messaging?", 2),
    ("Explain how a two-phase commit works.", 2),
    ("Write a Python function that implements a segment tree.", 2),
    ("Explain the difference between a read replica and a write replica.", 2),
    ("What are the main differences between a task queue and a message queue?", 2),
    ("Explain how zero-knowledge proofs work.", 2),
    ("Write a Python function that implements the edit distance algorithm.", 2),
    ("Explain the difference between a hot cache and a cold cache.", 2),
    ("What are the main differences between a stream and a batch processing system?", 2),
    ("Explain how a gossip protocol works in distributed systems.", 2),
    ("Write a Python function that implements a union-find data structure.", 2),
    ("Explain the difference between a fanout exchange and a direct exchange in RabbitMQ.", 2),
    ("What are the main differences between a push gateway and a pull gateway in monitoring?", 2),
    ("Explain how a merkle tree works.", 2),
    ("Write a Python function that implements the Boyer-Moore string search.", 2),
    ("Explain the difference between a write-through and write-back cache.", 2),
    ("What are the main differences between RBAC and ABAC?", 2),
    ("Explain how a bloom filter reduces false negatives.", 2),
    ("Write a Python function that implements matrix chain multiplication.", 2),
    ("Explain the difference between a primary index and a secondary index.", 2),
    ("What are the main differences between a relational and a graph database?", 2),
    ("Explain how vector clocks work in distributed systems.", 2),
    ("Write a Python function that implements the A-star pathfinding algorithm.", 2),

    # Tier 3 — Complex (200 prompts)
    ("Design a scalable URL shortening service handling 100 million daily requests.", 3),
    ("Analyze the tradeoffs between relational and document databases for a multi-tenant SaaS product.", 3),
    ("Write a technical design document for a real-time collaborative text editor for 10,000 concurrent users.", 3),
    ("Compare transformer-based language models vs LSTM for long document understanding.", 3),
    ("Design a fraud detection system for a payment processor handling 50,000 transactions per second.", 3),
    ("Explain the architectural decisions behind a multi-region active-active database setup.", 3),
    ("Design the backend architecture for a ride-sharing app like Uber.", 3),
    ("Write a research summary comparing RAG vs fine-tuning for domain-specific LLM applications.", 3),
    ("Design a recommendation engine for an e-commerce platform with 50 million products.", 3),
    ("Compare microservices vs serverless architecture for a fintech startup expecting 10x growth.", 3),
    ("Write a complete implementation of a distributed rate limiter using Redis across multiple servers.", 3),
    ("Explain how you would migrate a monolithic Rails app to microservices with zero downtime.", 3),
    ("Design a system to detect and prevent prompt injection attacks in an LLM chatbot.", 3),
    ("Design a CQRS and event sourcing architecture for a banking application.", 3),
    ("Design a real-time leaderboard for a gaming platform with 5 million players.", 3),
    ("Explain how to implement multi-tenant SaaS with row-level security in PostgreSQL.", 3),
    ("Write a comprehensive security audit checklist for a FastAPI application handling financial data.", 3),
    ("Design an ML pipeline for predicting customer churn with 90 percent recall.", 3),
    ("Compare Kafka vs RabbitMQ vs Redis Streams for event-driven microservices at scale.", 3),
    ("Write a detailed technical proposal for zero-trust network architecture.", 3),
    ("Design a content moderation pipeline processing 1 million posts per day.", 3),
    ("Explain distributed tracing across 20 microservices using OpenTelemetry.", 3),
    ("Design a data warehouse for a retail company consolidating 50 store locations.", 3),
    ("Propose a strategy to reduce LLM inference costs by 70 percent without degrading experience.", 3),
    ("Write a technical design for an async job processing system handling 1 million tasks per day.", 3),
    ("Analyze architectural differences between GPT-4 and mixture-of-experts models.", 3),
    ("Design a feature flag system supporting A/B testing and gradual rollouts for 10 million users.", 3),
    ("Write a migration plan for a 10TB PostgreSQL database to Aurora with under 1 hour downtime.", 3),
    ("Explain how to build a semantic search engine over 5 million legal documents.", 3),
    ("Design a CI/CD pipeline for an ML model with canary deployment and automated rollback.", 3),
    ("Compare BERT, RoBERTa, and sentence-transformers for production NLP classification.", 3),
    ("Write a technical RFC for GraphQL federation across 8 existing REST microservices.", 3),
    ("Design a real-time anomaly detection system processing 500,000 metrics per second.", 3),
    ("Explain how to implement an LLM-powered code review assistant integrated with GitHub PRs.", 3),
    ("Write a capacity planning document for scaling a FastAPI service to 1 million requests per day.", 3),
    ("Design a multi-region disaster recovery strategy with RPO of 1 minute and RTO of 5 minutes.", 3),
    ("Analyze the tradeoffs of fine-tuning an open source LLM vs using a hosted API at scale.", 3),
    ("Write a complete system design for distributed cache invalidation across 10 microservices.", 3),
    ("Design an event-driven order management system for flash sales with 100,000 concurrent users.", 3),
    ("Explain model versioning, A/B testing, and gradual rollouts for an ML model at 50 million predictions per day.", 3),
    ("Write a technical deep dive on optimizing a RAG pipeline from 60 percent to 90 percent retrieval accuracy.", 3),
    ("Design a zero-downtime blue-green deployment for a stateful application with shared PostgreSQL.", 3),
    ("Analyze security implications of storing LLM conversation history in a healthcare chatbot.", 3),
    ("Write a comprehensive comparison of Airflow, Prefect, and Dagster for ML pipeline orchestration.", 3),
    ("Design a multi-model LLM routing system that classifies complexity and routes to cheapest capable model.", 3),
    ("Explain how to build a production-grade vector search engine over 10 million documents.", 3),
    ("Design a distributed job scheduler with exactly-once execution semantics.", 3),
    ("Write a technical proposal for implementing chaos engineering in a microservices platform.", 3),
    ("Analyze the CAP theorem implications for a globally distributed inventory management system.", 3),
    ("Design an observability platform for a platform processing 1 billion events per day.", 3),
    ("Explain how to implement a distributed transaction coordinator using the saga pattern.", 3),
    ("Design a multi-tenant vector database for an AI SaaS platform serving 10,000 customers.", 3),
    ("Write a technical RFC for implementing service mesh with Istio across 15 microservices.", 3),
    ("Analyze the performance implications of different database normalization levels at scale.", 3),
    ("Design a real-time fraud scoring system with sub-50ms latency requirements.", 3),
    ("Explain how to build a production RAG system with hybrid retrieval and citation verification.", 3),
    ("Design a distributed configuration management system for 500 microservices.", 3),
    ("Write a technical design for a streaming data pipeline processing 100GB per hour.", 3),
    ("Analyze the tradeoffs between synchronous and asynchronous communication in microservices.", 3),
    ("Design a platform for running untrusted code safely at scale.", 3),
    ("Explain how to implement a distributed search engine from scratch.", 3),
    ("Design a high-throughput logging system processing 10 million log lines per second.", 3),
    ("Write a technical proposal for migrating from a monolithic database to microservices databases.", 3),
    ("Analyze the security model of a zero-trust architecture for a financial institution.", 3),
    ("Design a real-time bidding system for digital advertising with sub-10ms response times.", 3),
    ("Explain how to implement a distributed pub-sub system from scratch.", 3),
    ("Design a platform for large-scale machine learning model training across 1000 GPUs.", 3),
    ("Write a technical RFC for implementing event sourcing in an existing CRUD application.", 3),
    ("Analyze the tradeoffs of different consistency models in distributed databases.", 3),
    ("Design a system for real-time collaborative coding with conflict resolution.", 3),
    ("Explain how to implement a production-grade feature store for machine learning.", 3),
    ("Design a distributed key-value store from scratch with consistency guarantees.", 3),
    ("Write a technical proposal for implementing GitOps for a 50-service Kubernetes platform.", 3),
    ("Analyze the performance characteristics of different indexing strategies in PostgreSQL.", 3),
    ("Design a multi-region active-active database with conflict resolution.", 3),
    ("Explain how to build a production-grade model serving platform with auto-scaling.", 3),
    ("Design a real-time analytics pipeline for processing clickstream data at scale.", 3),
    ("Write a technical RFC for implementing distributed caching with cache coherence.", 3),
    ("Analyze the tradeoffs of different microservices communication patterns.", 3),
    ("Design a platform for serving personalized content to 100 million users.", 3),
    ("Explain how to implement a distributed workflow engine from scratch.", 3),
    ("Design a high-availability message broker with guaranteed delivery semantics.", 3),
    ("Write a technical proposal for implementing a data mesh architecture.", 3),
    ("Analyze the security implications of a multi-tenant Kubernetes cluster.", 3),
    ("Design a real-time recommendation system with sub-100ms latency.", 3),
    ("Explain how to implement a production-grade A/B testing platform.", 3),
    ("Design a distributed transaction system with rollback capabilities.", 3),
    ("Write a technical RFC for migrating from REST to event-driven architecture.", 3),
    ("Analyze the tradeoffs of different sharding strategies for a social media platform.", 3),
    ("Design a platform for real-time collaborative document editing at scale.", 3),
    ("Explain how to build a production-grade semantic search system.", 3),
    ("Design a distributed rate limiting system with millisecond precision.", 3),
    ("Write a technical proposal for implementing zero-downtime database migrations.", 3),
    ("Analyze the performance implications of different caching strategies at scale.", 3),
    ("Design a multi-tenant AI platform with resource isolation and cost attribution.", 3),
    ("Explain how to implement a production-grade distributed tracing system.", 3),
    ("Design a real-time fraud detection system using graph neural networks.", 3),
    ("Write a technical RFC for implementing a service registry and discovery system.", 3),
    ("Analyze the tradeoffs of different consensus algorithms for distributed systems.", 3),
    ("Design a platform for large-scale batch processing with fault tolerance.", 3),
    ("Explain how to build a production-grade time series database.", 3),
    ("Design a distributed lock manager with deadlock detection.", 3),
    ("Write a technical proposal for implementing a unified observability platform.", 3),
    ("Analyze the security model of a distributed microservices authentication system.", 3),
    ("Design a real-time collaborative whiteboard with conflict-free replicated data types.", 3),
    ("Explain how to implement a production-grade ML model monitoring system.", 3),
    ("Design a distributed cache with intelligent eviction policies.", 3),
    ("Write a technical RFC for implementing infrastructure as code for a 100-service platform.", 3),
    ("Analyze the tradeoffs of different data partitioning strategies.", 3),
    ("Design a platform for serving large language models at scale.", 3),
    ("Explain how to build a production-grade API gateway with rate limiting.", 3),
    ("Design a distributed backup and recovery system with point-in-time recovery.", 3),
    ("Write a technical proposal for implementing a multi-cloud deployment strategy.", 3),
    ("Analyze the performance characteristics of different message queue implementations.", 3),
    ("Design a real-time inventory management system with consistency guarantees.", 3),
    ("Explain how to implement a production-grade graph database from scratch.", 3),
    ("Design a distributed session management system with sticky sessions.", 3),
    ("Write a technical RFC for implementing a platform-wide secret management system.", 3),
    ("Analyze the tradeoffs of different microservices deployment strategies.", 3),
    ("Design a platform for large-scale data anonymization and privacy compliance.", 3),
    ("Explain how to build a production-grade event streaming platform.", 3),
    ("Design a distributed configuration service with versioning and rollback.", 3),
    ("Write a technical proposal for implementing a developer platform with self-service infrastructure.", 3),
    ("Analyze the security implications of a serverless microservices architecture.", 3),
    ("Design a real-time multiplayer game backend with 1 million concurrent players.", 3),
    ("Explain how to implement a production-grade container orchestration system.", 3),
    ("Design a distributed file system with deduplication and compression.", 3),
    ("Write a technical RFC for implementing a unified data catalog.", 3),
    ("Analyze the tradeoffs of different API versioning strategies.", 3),
    ("Design a platform for real-time sports betting with sub-second odds updates.", 3),
    ("Explain how to build a production-grade column-oriented database.", 3),
    ("Design a distributed secret rotation system with zero-downtime.", 3),
    ("Write a technical proposal for implementing a platform-wide cost attribution system.", 3),
    ("Analyze the performance implications of different ORM strategies at scale.", 3),
    ("Design a real-time collaborative spreadsheet with conflict resolution.", 3),
    ("Explain how to implement a production-grade service mesh from scratch.", 3),
    ("Design a distributed query optimizer for a multi-database environment.", 3),
    ("Write a technical RFC for implementing a unified logging and alerting platform.", 3),
    ("Analyze the tradeoffs of different database connection pooling strategies.", 3),
    ("Design a platform for serving embeddings at billion-vector scale.", 3),
    ("Explain how to build a production-grade distributed SQL database.", 3),
    ("Design a real-time anomaly detection system for financial transactions.", 3),
    ("Write a technical proposal for implementing a platform-wide API governance system.", 3),
    ("Analyze the security model of a zero-trust microservices architecture.", 3),
    ("Design a distributed workflow orchestration system with compensation logic.", 3),
    ("Explain how to implement a production-grade vector similarity search engine.", 3),
    ("Design a multi-region active-passive failover system with automatic recovery.", 3),
    ("Write a technical RFC for implementing a platform-wide feature flag system.", 3),
    ("Analyze the tradeoffs of different event sourcing implementations.", 3),
    ("Design a platform for large-scale natural language processing pipelines.", 3),
    ("Explain how to build a production-grade distributed message broker.", 3),
    ("Design a real-time collaborative code editor with execution sandboxing.", 3),
    ("Write a technical proposal for implementing a unified developer experience platform.", 3),
    ("Analyze the performance characteristics of different graph database implementations.", 3),
    ("Design a distributed token bucket rate limiter with millisecond precision.", 3),
    ("Explain how to implement a production-grade distributed cache coherence protocol.", 3),
    ("Design a platform for real-time ML inference with dynamic batching.", 3),
    ("Write a technical RFC for implementing a unified identity and access management system.", 3),
    ("Analyze the tradeoffs of different distributed transaction patterns.", 3),
    ("Design a system for large-scale log aggregation and analysis.", 3),
    ("Explain how to build a production-grade distributed consensus system.", 3),
    ("Design a real-time collaborative data science notebook platform.", 3),
    ("Write a technical proposal for implementing a platform-wide chaos engineering system.", 3),
    ("Analyze the security implications of a multi-tenant vector database.", 3),
    ("Design a distributed metadata management system for a data lakehouse.", 3),
    ("Explain how to implement a production-grade distributed pub-sub system.", 3),
    ("Design a platform for serving fine-tuned language models at scale.", 3),
    ("Write a technical RFC for implementing a unified data quality monitoring system.", 3),
    ("Analyze the tradeoffs of different microservices testing strategies.", 3),
    ("Design a real-time supply chain optimization system with constraint satisfaction.", 3),
    ("Explain how to build a production-grade distributed search and indexing system.", 3),
    ("Design a distributed audit logging system with tamper-proof guarantees.", 3),
    ("Write a technical proposal for implementing a platform-wide performance testing system.", 3),
    ("Analyze the performance implications of different caching invalidation strategies.", 3),
    ("Design a multi-tenant machine learning platform with GPU resource scheduling.", 3),
    ("Explain how to implement a production-grade distributed workflow engine.", 3),
    ("Design a real-time financial risk calculation engine with regulatory compliance.", 3),
    ("Write a technical RFC for implementing a unified platform configuration management system.", 3),
    ("Analyze the tradeoffs of different data replication strategies in distributed systems.", 3),
    ("Design a platform for large-scale computer vision model training and serving.", 3),
    ("Explain how to build a production-grade distributed time series database.", 3),
    ("Design a real-time collaborative 3D modeling platform with conflict resolution.", 3),
]


async def send_prompt(client: httpx.AsyncClient, prompt: str, expected_tier: int, idx: int) -> dict:
    try:
        start = time.time()
        response = await client.post(
            API_URL,
            json={"prompt": prompt, "max_tokens": 512},
            timeout=120.0,
        )
        latency = int((time.time() - start) * 1000)

        if response.status_code == 200:
            data = response.json()
            return {
                "idx": idx,
                "success": True,
                "expected_tier": expected_tier,
                "actual_tier": data.get("complexity_tier"),
                "model_used": data.get("model_used"),
                "cost": data.get("cost", 0),
                "cost_if_gpt4o": data.get("cost_if_gpt4o", 0),
                "latency_ms": latency,
                "confidence": data.get("classifier_confidence", 0),
            }
        else:
            return {"idx": idx, "success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"idx": idx, "success": False, "error": str(e)}


async def run_load_test():
    console.print("\n[bold cyan]LLM Cost Autopilot — 500+ Prompt Load Test[/bold cyan]\n")
    console.print(f"Total prompts: [bold]{len(PROMPTS)}[/bold]")
    console.print(f"Tier 1: [bold]{sum(1 for _, t in PROMPTS if t == 1)}[/bold] | "
                  f"Tier 2: [bold]{sum(1 for _, t in PROMPTS if t == 2)}[/bold] | "
                  f"Tier 3: [bold]{sum(1 for _, t in PROMPTS if t == 3)}[/bold]\n")

    BATCH_SIZE = 10
    all_results = []

    async with httpx.AsyncClient() as client:
        for i in range(0, len(PROMPTS), BATCH_SIZE):
            batch = PROMPTS[i:i + BATCH_SIZE]
            tasks = [
                send_prompt(client, prompt, tier, i + j)
                for j, (prompt, tier) in enumerate(batch)
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, Exception):
                    all_results.append({"success": False, "error": str(r)})
                else:
                    all_results.append(r)

            completed = min(i + BATCH_SIZE, len(PROMPTS))
            console.print(f"Progress: {completed}/{len(PROMPTS)} prompts completed...", end="\r")

    console.print("\n")

    successful = [r for r in all_results if r.get("success")]
    failed = [r for r in all_results if not r.get("success")]

    total_cost = sum(r.get("cost", 0) for r in successful)
    total_hypothetical = sum(r.get("cost_if_gpt4o", 0) for r in successful)
    total_saved = total_hypothetical - total_cost
    pct_saved = (total_saved / total_hypothetical * 100) if total_hypothetical > 0 else 0

    tier_accuracy = sum(
        1 for r in successful
        if r.get("actual_tier") == r.get("expected_tier")
    ) / len(successful) * 100 if successful else 0

    summary = Table(title="Load Test Results", show_lines=True)
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", style="green")

    summary.add_row("Total prompts", str(len(PROMPTS)))
    summary.add_row("Successful", str(len(successful)))
    summary.add_row("Failed", str(len(failed)))
    summary.add_row("Tier classification accuracy", f"{tier_accuracy:.1f}%")
    summary.add_row("Total actual cost", f"${total_cost:.4f}")
    summary.add_row("Total hypothetical (all GPT-4o)", f"${total_hypothetical:.4f}")
    summary.add_row("Total saved", f"${total_saved:.4f}")
    summary.add_row("Cost reduction", f"{pct_saved:.1f}%")

    console.print(summary)

    model_counts = {}
    for r in successful:
        m = r.get("model_used", "unknown")
        model_counts[m] = model_counts.get(m, 0) + 1

    model_table = Table(title="Model Distribution", show_lines=False)
    model_table.add_column("Model", style="cyan")
    model_table.add_column("Requests", justify="right")
    model_table.add_column("% of Traffic", justify="right")

    for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
        pct = count / len(successful) * 100
        model_table.add_row(model, str(count), f"{pct:.1f}%")

    console.print(model_table)

    results_path = os.path.join(os.path.dirname(__file__), "data", "load_test_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "total_prompts": len(PROMPTS),
            "successful": len(successful),
            "failed": len(failed),
            "total_cost": round(total_cost, 6),
            "total_hypothetical": round(total_hypothetical, 6),
            "total_saved": round(total_saved, 6),
            "cost_reduction_pct": round(pct_saved, 2),
            "tier_accuracy_pct": round(tier_accuracy, 2),
            "model_distribution": model_counts,
        }, f, indent=2)

    console.print(f"\n[bold]Results saved to:[/bold] data/load_test_results.json")
    console.print(f"\n[bold green]HEADLINE: {pct_saved:.1f}% cost reduction on {len(successful)} real requests[/bold green]\n")


if __name__ == "__main__":
    asyncio.run(run_load_test())