from locust import HttpUser, task, between
import random
import json

PRODUCTS = [
    "Smartphone", "Gaming Laptop", "Wireless Earbuds", "4K Monitor", 
    "Smart Watch", "Mechanical Keyboard", "USB-C Hub"
]

class APIUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def ask_inventory_question(self):
        product = random.choice(PRODUCTS)
        query = f"Check inventory for {product}"
        with self.client.post("/query", json={"query": query}, catch_response=True) as response:
            self._validate_response(response)

    @task(2)
    def ask_pricing_question(self):
        product = random.choice(PRODUCTS)
        query = f"Analyze the prices of {product} and show me the margin."
        with self.client.post("/query", json={"query": query}, catch_response=True) as response:
            self._validate_response(response)

    @task(1)
    def ask_market_question(self):
        query = "What is the current market trend for noise cancelling headphones?"
        with self.client.post("/query", json={"query": query}, catch_response=True) as response:
            self._validate_response(response)

    @task(1)
    def check_health(self):
        self.client.get("/health")

    def _validate_response(self, response):
        if response.status_code == 200:
            try:
                data = response.json()
                if not data.get("answer"):
                    response.failure("Response missing 'answer' field")
                elif "error" in str(data.get("answer")).lower():
                    # We can choose to treat app-level errors as failures or just log them
                    response.failure(f"App returned error: {data.get('answer')}")
                else:
                    response.success()
            except json.JSONDecodeError:
                response.failure("Response was not valid JSON")
        else:
            response.failure(f"Status code {response.status_code}")
