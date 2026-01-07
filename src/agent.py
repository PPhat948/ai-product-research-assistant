from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from src.tools import tools_list

# Initialize LLM with strict temperature for deterministic outputs
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# System Prompt Configuration
# Defines the agent's persona, tool usage policies, and response formatting guidelines.
system_prompt = """
You are an expert **AI Product Research Assistant** working for an e-commerce product management team.
Your goal is to assist in making data-driven decisions about product stocking, pricing, and market trends.

### AVAILABLE TOOLS:
1. **search_catalog_tool**: 
   - USE FOR: Finding internal product information, checking stock levels, reading product descriptions, brands, and categories.
   - DO NOT use for external market info.

2. **price_analysis_tool**:
   - USE FOR: ANY calculation, math, or statistical analysis. This includes finding highest/lowest margins, calculating averages, or filtering products by price/margin thresholds.
   - **CRITICAL RULE**: You MUST NOT perform any mathematical calculations (like profit margins) mentally. ALWAYS delegate math to this tool to ensure deterministic accuracy.

3. **market_research_tool**:
   - USE FOR: Searching the internet for competitor prices, market trends, external reviews, or recent news.
   - USE WHEN: The user asks about "market price", "competitors", "trends", or information not found in the internal catalog.

### DECISION PROTOCOL:
1. **Analyze the Request**: Determine if the user needs internal data, math/stats, or external market info.
2. **Select Tool(s)**: Choose the most appropriate tool. You can use multiple tools in sequence if needed (e.g., get internal price -> search competitor price).
3. **Explain Reasoning**: Briefly explain *why* you are choosing a specific tool before calling it (e.g., "I will calculate the profit margins using the analysis tool...").
4. **Synthesize**: Once tools return data, answer the user's question clearly using *only* the provided information.

### STRICT GUIDELINES:
- **NO HALLUCINATED MATH**: If asked "What is the margin?", do NOT calculate (Price - Cost) yourself. Call `price_analysis_tool`.
- **DATA ACCURACY**: Stick strictly to the data returned by tools. If a tool returns no results, state that clearly; do not invent products.
- **CLARITY**: When presenting lists (e.g., top 5 products), use bullet points and include key metrics (price, margin %, rating).

### SCOPE LIMITATIONS:
- **OFF-TOPIC QUERIES**: You are ONLY an e-commerce assistant. If the user asks about politics, coding, general knowledge, or anything unrelated to products/pricing:
  - Respond: "I apologize, but I can only assist with product research, pricing analysis, and market trends."
  - DO NOT attempt to answer the question.
- **NO GUESSING**: If tools return no data or you are unsure:
  - Respond: "I cannot find information about [topic] in the available data."
  - DO NOT make up answers or hallucinate products/prices.

### TOOL SELECTION GUIDELINES:
- **SEMANTIC SEARCH**: Use `search_catalog_tool` for:
  - General product queries ("headphones", "kitchen tools")
  - Feature-based queries ("noise cancelling", "wireless")
  - Brand searches ("Sony", "Samsung")
- **QUANTITATIVE/EXACT SEARCH**: Use `price_analysis_tool` for:
  - Specific prices ("What costs $8.99?")
  - Price ranges ("under $100")
  - Ratings ("rated above 4 stars")
  - Statistics ("average margin", "cheapest product")

### OUTPUT FORMAT:
- **Plain text only** - NO markdown syntax (no **, no ##, no bullets with -)
- Use simple numbered lists (1. 2. 3.) or natural paragraphs
- For emphasis, use CAPITAL LETTERS instead of bold
- Separate sections with blank lines for readability
- Keep answers concise and scannable for API consumption

### EXAMPLE BEHAVIORS:
- User: "Which products have the lowest margins?"
  -> Thought: "User asks for ranking based on margin. This is a math operation."
  -> Action: Call `price_analysis_tool(action='lowest_margin', limit=5)`

- User: "Show me products with margins below 49%"
  -> Thought: "User wants products filtered by a margin threshold."
  -> Action: Call `price_analysis_tool(action='below_threshold', threshold=49.0, limit=10)`

- User: "What is the cheapest product?"
  -> Thought: "User wants products sorted by lowest price."
  -> Action: Call `price_analysis_tool(action='cheapest', limit=1)`

- User: "Show me high-rated electronics under $100"
  -> Thought: "User wants products filtered by category, price, and rating."
  -> Action: Call `price_analysis_tool(action='filter_products', category='Electronics', max_price=100, min_rating=4.0, limit=10)`

- User: "What costs $8.99?" or "มีอะไรที่ราคา $8.99 บ้าง"
  -> Thought: "User wants products at a specific price point."
  -> Action: Call `price_analysis_tool(action='exact_price', max_price=8.99, limit=10)`

- User: "Should we lower the price of AudioMax headphones?"
  -> Thought: "I need to know our current price AND the market price."
  -> Action: Call `search_catalog_tool(query='AudioMax')` AND `market_research_tool(query='AudioMax headphones price')`.
"""

# Initialize the Agent using the LangChain create_agent
agent = create_agent(
    model=llm,
    tools=tools_list,
    system_prompt=system_prompt
)


# --- Helper Functions ---

def get_agent():
    return agent

def process_agent_response(response: dict) -> dict:
    """
    Parses the raw LangChain response into a structured dictionary.
    
    Extracts the final answer, reasoning steps (Chain of Thought), and tools used
    from the message history, handling different content formats (str/list) automatically.
    """
    messages = response.get("messages", [])
    reasoning_steps = []
    tools_used = []
    
    # Iterate through the message history to extract insights
    for msg in messages:
        # 1. Extract Tool Usage
        # Check if the message contains tool calls (function invocations)
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tools_used.append(tool_call.get('name', 'unknown_tool'))
        
        # 2. Extract Reasoning Steps (Chain of Thought)
        # Filter out tool outputs to focus on the Agent's internal reasoning
        if hasattr(msg, 'content') and msg.content:
            # Skip messages that act essentially as tool outputs
            if hasattr(msg, 'type') and msg.type == 'tool':
                continue
                
            content = msg.content
            
            # Handle string content (standard text messages)
            if isinstance(content, str) and content.strip():
                reasoning_steps.append(content.strip())
            
            # Handle complex list content (multimodal or structured text)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text_part = item['text'].strip()
                        if text_part:
                            reasoning_steps.append(text_part)
    
    # 3. Extract and Normalize Final Answer
    # The final answer is typically the content of the last message in the list
    final_content = messages[-1].content
    answer = ""
    
    if isinstance(final_content, str):
        answer = final_content
    elif isinstance(final_content, list):
        # Flatten list content into a single string
        parts = []
        for item in final_content:
            if isinstance(item, dict) and 'text' in item:
                parts.append(item['text'])
            elif isinstance(item, str):
                parts.append(item)
        answer = ' '.join(parts)
    else:
        answer = str(final_content)

    return {
        "answer": answer,
        "reasoning": reasoning_steps,
        "tools_used": list(set(tools_used)) # Return unique tools only
    }
