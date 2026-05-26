from locust import (
    HttpUser,
    task,
    between
)


class PitWallAPIUser(HttpUser):

    wait_time = between(1, 3)

    @task(3)
    def get_sessions(self):

        self.client.get(
            "/v1/sessions/?year=2024&session_type=R"
        )

    @task(2)
    def get_standings(self):

        self.client.get(
            "/v1/standings/drivers?year=2024"
        )

    @task(1)
    def predict_pit_strategy(self):

        self.client.post(
            "/v1/predictions/pit-strategy",
            json={
                "session_key": 9158,
                "driver_number": 1,
                "current_lap": 25,
                "tyre_compound": "MEDIUM",
                "tyre_age": 15,
                "gap_ahead": 2.3,
                "gap_behind": 4.1,
                "total_laps": 57,
                "track_temp": 42.0,
                "air_temp": 28.0,
            }
        )

    @task(1)
    def health_check(self):

        self.client.get("/health")
