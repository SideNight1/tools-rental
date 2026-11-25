from locust import HttpUser, between, task


class RentalCatalogUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def open_catalog(self):
        with self.client.get("/", name="Каталог", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")