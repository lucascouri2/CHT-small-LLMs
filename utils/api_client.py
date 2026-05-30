import requests

class APIClient:
    def __init__(self, base_url, session_id=None):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id

    def request(self, endpoint, method="GET", headers=None, params=None, data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = headers or {}
        if self.session_id:
            headers["Cookie"] = f"PHPSESSID={self.session_id}"

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                data=data,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def post(self, endpoint, data=None):
        return self.request(endpoint, method="POST", data=data)

    def get(self, endpoint, params=None):
        return self.request(endpoint, method="GET", params=params)