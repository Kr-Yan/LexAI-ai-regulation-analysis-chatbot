from typing import Dict, List
import os
from openai import OpenAI

# 🎯 SYSTEM PROMPT - MODIFY THIS TO CHANGE CHATBOT BEHAVIOR
SYSTEM_PROMPT = """You are an AI Policy Analysis Expert specializing in artificial intelligence governance, regulations, and policy frameworks.

Your role:
- Analyze AI policy documents with expertise and nuance
- Provide clear, well-sourced insights about AI governance
- Explain complex policy concepts in accessible terms
- Synthesize information from multiple sources
- Offer balanced perspectives on policy challenges and opportunities
- Always cite the specific documents you reference
- Focus on AI regulation, ethics, safety, and implementation strategies

Response style:
- Professional but approachable, like a senior policy consultant
- Analytical and evidence-based
- Clear structure with key insights highlighted
- Reference sources while providing original analysis
- If asked about non-AI topics, politely redirect to AI policy matters

Remember: You analyze and synthesize - don't just quote documents."""

class GPTChatEngine:
    """Chat engine using OpenAI's GPT-3.5-turbo"""
    
    def __init__(self, vector_store_manager):
        self.vector_store_manager = vector_store_manager
        self.memory = []
        self.client = None
        self.model_name = "gpt-3.5-turbo"
        self._setup_openai_client()
    
    def _setup_openai_client(self):
        """Initialize OpenAI client"""
        try:
            # Get API key from environment variable
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not found")
            
            self.client = OpenAI(api_key=api_key)
            print(f"✅ Successfully initialized OpenAI client with {self.model_name}")
            
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            print("Make sure to set OPENAI_API_KEY in your .env file")
            self.client = None
    
    
    def _generate_gpt_response(self, query: str, sources: List[Dict]) -> str:
        """Generate response using GPT-3.5-turbo"""
        
        if not self.client:
            return "OpenAI client not initialized. Please check your API key configuration."
        
        if not sources:
            return """I don't have relevant AI policy documents in my knowledge base. 

Please upload documents such as AI governance frameworks, regulatory guidelines, or policy research papers to enable detailed analysis."""
        
        # Prepare context from sources
        context_parts = []
        for i, source in enumerate(sources[:5], 1):  # Use top 5 sources
            content = source.get('content', '').strip()
            if content:
                # Include source metadata if available
                metadata = source.get('metadata', {})
                source_info = metadata.get('source', f'Document {i}')
                context_parts.append(f"[Source {i} - {source_info}]: {content}")
        
        if not context_parts:
            return "I found documents but couldn't extract relevant content for analysis."
        
        combined_context = "\n\n".join(context_parts)
        
        # Create conversation history for context
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        
        # Add recent conversation history (last 3 exchanges)
        recent_memory = self.memory[-6:] if len(self.memory) > 6 else self.memory
        for msg in recent_memory:
            if msg["type"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["type"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        # Add current query with context
        user_message = f"""Based on the following AI policy documents, please analyze and answer the question:

CONTEXT FROM DOCUMENTS:
{combined_context}

QUESTION: {query}

Please provide a comprehensive analysis referencing the specific documents and sources."""
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                top_p=0.9
            )
            
            if response.choices and len(response.choices) > 0:
                answer = response.choices[0].message.content.strip()
                return answer
            else:
                return "I received an empty response from the AI model. Please try again."
                
        except Exception as e:
            print(f"❌ Error calling OpenAI API: {e}")
            
            # Fallback response
            if "rate limit" in str(e).lower():
                return "I'm currently experiencing high demand. Please wait a moment and try again."
            elif "api key" in str(e).lower():
                return "There's an issue with the API configuration. Please check the API key settings."
            else:
                return f"I encountered an error while processing your request: {str(e)}"
    
    def chat(self, query: str) -> Dict:
        """Process chat with GPT-3.5-turbo"""
        try:
            print(f"🧠 Processing with {self.model_name}: {query}")
            
            # Add to memory
            self.memory.append({"type": "user", "content": query})
            
            # Search documents
            search_results = self.vector_store_manager.search(query, k=5)
            print(f"Found {len(search_results)} relevant sources")
            
            # Generate response using GPT
            answer = self._generate_gpt_response(query, search_results)
            
            # Format sources for response
            sources = []
            for result in search_results[:3]:
                sources.append({
                    "content": result['content'][:300] + "..." if len(result['content']) > 300 else result['content'],
                    "metadata": result.get('metadata', {}),
                    "similarity_score": result.get('similarity_score', 0)
                })
            
            response = {
                "answer": answer,
                "sources": sources,
                "status": "success",
                "model": self.model_name
            }
            
            # Add response to memory
            self.memory.append({"type": "assistant", "content": answer})
            
            # Keep memory manageable (last 10 exchanges)
            if len(self.memory) > 20:
                self.memory = self.memory[-20:]
            
            return response
            
        except Exception as e:
            print(f"❌ Error in GPT chat: {e}")
            return {
                "answer": f"I encountered an error while processing your request. Please try again.",
                "sources": [],
                "status": "error",
                "model": self.model_name
            }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory = []
        print(f"Memory cleared for {self.model_name}")


# Use the GPT engine
ChatEngine = GPTChatEngine
