from langchain.tools import tool
from src.vector_store import vector_store_manager
from src.data_manager import product_data_manager
from langchain_community.utilities import GoogleSerperAPIWrapper
import json

@tool
def search_catalog_tool(query: str):
    """
    Useful for searching the product catalog for inventory, descriptions, and general product information.
    Returns a list of matching products with their details and relevance scores.
    """
    results = vector_store_manager.search(query)
    
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "product_id": doc.metadata.get("product_id"),
            "product_name": doc.metadata.get("product_name"),
            "brand": doc.metadata.get("brand"),
            "price": doc.metadata.get("price"),
            "stock_quantity": doc.metadata.get("stock_quantity"),
            "rating": doc.metadata.get("average_rating"),
            "description": doc.page_content.strip(),
            "relevance_score": score
        })
        
    return json.dumps(formatted_results, indent=2)

# --- Helper Functions ---

def calculate_margin(price: float, cost: float) -> float:
    """
    Calculates the profit margin percentage.
    
    Returns 0.0 if price is non-positive to prevent division errors.
    """
    if price <= 0: return 0.0
    return ((price - cost) / price) * 100

# --- Unified Price Analysis Tool ---

@tool
def price_analysis_tool(action: str, threshold: float = 0.0, category: str = None, limit: int = 5, 
                         max_price: float = None, min_rating: float = None):
    """
    Performs math, filtering, and statistical analysis on the product catalog.
    
    Args:
        action: Type of analysis. Options: 
                ['lowest_margin', 'below_threshold', 'category_average', 'cheapest', 
                 'most_expensive', 'filter_products', 'exact_price']
        threshold: Margin percentage (e.g. 49.0) for 'below_threshold'.
        category: Category name to filter by.
        limit: Max results to return (default 5).
        max_price: Max price for 'filter_products' OR exact price for 'exact_price'.
        min_rating: Minimum rating for 'filter_products'.
    """
    df = product_data_manager.get_df().copy()
    
    # 1. Pre-calculate Margins locally
    # Ensures deterministic calculation using the defined helper function.
    if 'current_price' in df.columns and 'cost' in df.columns:
        df['margin_pct'] = df.apply(
            lambda row: calculate_margin(row['current_price'], row['cost']), 
            axis=1
        )
    else:
        return json.dumps({"error": "Missing price or cost data in catalog."})

    # 2. Execute analysis based on the requested action
    result = []
    
    # Define default output fields
    output_fields = ['product_name', 'current_price', 'cost', 'margin_pct']
    extended_fields = ['product_name', 'category', 'current_price', 'average_rating', 'stock_quantity', 'margin_pct']
    
    # Handle category_average logic (Aggregation - different structure)
    if action == "category_average":
        if category:
            df = df[df['category'].str.contains(category, case=False, na=False)]
        grouped = df.groupby('category')['margin_pct'].mean().round(2).reset_index()
        return json.dumps(grouped.to_dict(orient='records'), indent=2)

    # Handle standard actions
    working_df = df # Start with full df

    if action == "lowest_margin":
        working_df = working_df.sort_values(by='margin_pct', ascending=True)

    elif action == "below_threshold":
        working_df = working_df[working_df['margin_pct'] < threshold].sort_values(by='margin_pct', ascending=True)

    elif action == "cheapest":
        working_df = working_df.sort_values(by='current_price', ascending=True)

    elif action == "most_expensive":
        working_df = working_df.sort_values(by='current_price', ascending=False)

    elif action == "filter_products":
        output_fields = extended_fields
        if category:
            working_df = working_df[working_df['category'].str.contains(category, case=False, na=False)]
        if max_price is not None:
            working_df = working_df[working_df['current_price'] <= max_price]
        if min_rating is not None:
            working_df = working_df[working_df['average_rating'] >= min_rating]
        # Sort by rating descending, then by price ascending
        working_df = working_df.sort_values(by=['average_rating', 'current_price'], ascending=[False, True])

    elif action == "exact_price":
        output_fields = extended_fields
        if max_price is None:
            return json.dumps({"error": "exact_price action requires max_price parameter set to the target price."})
        working_df = working_df[working_df['current_price'] == max_price]
            
    else:
        return json.dumps({"error": f"Invalid action '{action}'."})

    # Final selection and formatting (Unified)
    # Ensure columns exist before selecting to prevent KeyError
    available_fields = [col for col in output_fields if col in working_df.columns]
    result = working_df[available_fields].head(limit).to_dict(orient='records')
    
    return json.dumps(result, indent=2)

@tool
def market_research_tool(query: str):
    """
    Performs external market research using Google Search.
    Useful for gathering competitor prices, trends, and recent news not available in the internal catalog.
    """
    search = GoogleSerperAPIWrapper()
    results = search.results(query)
    return json.dumps(results, indent=2)

# List of tools for the agent
tools_list = [
    search_catalog_tool, 
    price_analysis_tool,  
    market_research_tool
]
