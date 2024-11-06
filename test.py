import httpx


def get_data_json():
    with httpx.Client() as client:
        response = client.get(
            "https://newsapi.org/v2/everything?q=technology&pageSize=1&apiKey=09b3a74ca8a84de7a86ceb4c1415dc72"
        )
        return response.json()


if __name__ == "__main__":
    print(get_data_json())
