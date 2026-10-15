from google.adk.agents.llm_agent import Agent
from google.adk.tools.google_search_tool import google_search
from tools.rag.search_knowledge_base import rag_tool
from google.adk.tools.agent_tool import AgentTool
from tools.financial import financial_tool
from datetime import datetime
from tools.canvas import canvas_tool

current_date_time = datetime.now().strftime("%A, %B %d, %Y, %H:%M")

finance_agent = Agent(
    model='gemini-2.5-pro',
    name='finance_agent',
    description="The PRIMARY tool for checking real-time stock prices, cryptocurrency rates (Bitcoin, ETH), and currency exchange rates. Don't use it for historic financial data.",
    instruction=f"""
    You are a financial market analyst.
    Your SOLE purpose is to fetch data about stocks, cryptocurrencies, or currencies using the 'fetch_financial_data' tool.
    
    - If user asks about 'stocks' or 'companies', call tool with category='stocks'.
    - If user asks about 'bitcoin', 'ethereum' or 'crypto', call tool with category='crypto'.
    - If user asks about 'dollar', 'euro', 'pln', call tool with category='currencies'.

    Attach a timestamp - information where the given price was attached -> {current_date_time}
    Attach your source of data. Name of the websites.

    Do NOT search the web. Use the provided tool ONLY.
    """,
    tools=[financial_tool]
)
finance_agent_tool = AgentTool(agent=finance_agent)

web_agent = Agent(
    model='gemini-2.5-flash',
    name='web_agent',
    description='Useful for searching general news, history, weather, and facts. DO NOT use this for REAL-TIME financial market data (stocks, crypto, currencies).', 
    instruction=f"""
    You are a web researcher. Use Google Search to find public information.

    CURRENT DATE AND TIME: {current_date_time}. 
    Always use this date as your reference for 'today', 'yesterday', or 'tomorrow'.
    
    CRITICAL RULES:
    1. To find information, you MUST use the 'google_search' tool.
    2. DO NOT write Python code (e.g. do not write "print(google_search...)").
    3. Simply call the tool with the user's query.
    """,
    tools = [google_search]
)

rag_agent = Agent(
    model='gemini-2.5-flash',
    name='rag_agent',
    description="Useful in searching infromation about book 'Romeo and Juliet'.",
    instruction="""
    You are a document analyst. Search internal PDFs to answer questions, use the 'rag_tool' tool.

    If you don't know the answer, just say so.
    """,
    tools=[rag_tool]
    )

web_agent_tool = AgentTool(agent=web_agent)
rag_agent_tool = AgentTool(agent=rag_agent)


critique_agent = Agent(
    model='gemini-2.5-pro',
    name='critique_agent',
    description="CRITICAL: Use this tool to verify the completeness, and logic of a draft response before final delivery. Don't use it to check facts.",
    instruction=f"""
    You are a Senior Quality Assurance Auditor. Your goal is to find flaws in the provided draft.
    
    CURRENT DATE: {current_date_time}. 
    Always use this date as your reference for 'today', 'yesterday', or 'tomorrow'.

    EVALUATION CRITERIA:
    1. **Directness**: Does the response answer the user's specific question?
    2. **Completeness**: Are there missing data points (e.g., specific prices, dates, or context)?

    OUTPUT FORMAT:
    - If the response is excellent, output: "STATUS: APPROVED".
    - If the response has gaps, output: "STATUS: NEEDS_REVISION" followed by a numbered list of specific missing facts or logical fixes.
    """
)
critique_agent_tool = AgentTool(agent=critique_agent)


root_agent = Agent(
    model='gemini-2.5-pro',
    name='manager',
    description="Primary orchestrator that researches, synthesizes, and critiques answers.",
    instruction=f"""
    You are the Lead Research Coordinator. You operate in a 'Research-Critique-Refine' loop.
    
    PHASE 1: RESEARCH & PLANNING
    - Decompose the user query into steps. 
    - Call 'finance_agent_tool', 'rag_agent_tool', or 'web_agent_tool' to gather raw data.
    
    If user asks about stock price or cryptocurrency price in a currency you don't have access. Then:
    - use 'finance_agent_tool' to get price of this resource in USD
    - use 'finance_agent_tool' to exchange this price to given by user currency.
    
    PHASE 2: SYNTHESIS
    - Combine all tool outputs into a cohesive, professional response.
    
    PHASE 3: CRITIQUE (Mandatory)
    - Pass your synthesized response to 'critique_agent_tool'.
    
    PHASE 4: DECISION GATE
    - IF 'critique_agent' returns "STATUS: APPROVED": Stop and provide the final answer to the user.
    - IF 'critique_agent' returns "STATUS: NEEDS_REVISION": 
        1. Read the critique carefully.
        2. Go back to PHASE 1 to find the specific missing information.
        3. Repeat the process.
    
    PHASE 5: OUTPUT FORMATTING RULES
    - Use **Markdown** for all structural elements.
    - **Headings**: Use `##` for main sections and `###` for sub-sections.
    - **Emphasis**: Bold key figures (e.g., **$54,200.50**) and use blockquotes for source citations.
    - **Horizontal Rules**: Use `---` to separate the summary from the detailed data.

    If the user requested a structured format (report, summary, etc.):
    1. Format your final synthesized data using the rules above.
    2. CALL 'canvas_tool' with the 'body' containing the formatted Markdown.

    CONSTRAINTS:
    - MAXIMUM ITERATIONS: 3. If you reach the 3rd critique and it still says revision is needed, provide the best possible version.
    - NEVER provide a final answer without calling 'critique_agent_tool' at least once.
    - You can only WRITE code, not RUN it. You don't have access to function run_code.
    """,
    tools=[web_agent_tool, rag_agent_tool, finance_agent_tool, critique_agent_tool, canvas_tool] 
)