"""
LlamaSearch AI Client.

This module provides the main Client class for interacting with LlamaSearch AI services.
"""

import time
from typing import Any, Dict, List, Optional, Union

import httpx
from llamasearchai.config import settings
from loguru import logger


class Client:
    """
    Client for the LlamaSearch AI platform.

    This client provides convenient access to all LlamaSearch AI features,
    including metasearch, vector operations, personalization, and more.

    Example:
        ```python
        import llamasearchai as llm

        # Initialize client
        client = llm.Client(api_key="your-api-key")

        # Perform a metasearch
        results = client.search("quantum computing advances")

        # Get personalized results
        personalized = client.personalize(results, user_id="user123")
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize the LlamaSearch AI client.

        Args:
            api_key: Optional API key for authentication. If not provided,
                the client will attempt to use the value from environment variables.
            base_url: Optional base URL for the LlamaSearch API. If not provided,
                the client will use the default URL based on configuration.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url or f"http://{settings.API_HOST}:{settings.API_PORT}"
        self.timeout = timeout

        # Set up the HTTP client
        self.http_client = httpx.Client(
            timeout=timeout,
            headers=self._get_headers(),
        )

        # Set up the Async HTTP client
        self.async_http_client = httpx.AsyncClient(
            timeout=timeout,
            headers=self._get_headers(),
        )

        # Initialize feature availability based on settings
        self.available_features = settings.FEATURES

        # Validate API key if provided
        if self.api_key:
            self._validate_api_key()

        logger.debug(
            f"Initialized LlamaSearch AI client with base URL: {self.base_url}"
        )

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers[settings.API_KEY_HEADER] = self.api_key

        return headers

    def _validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request.

        Returns:
            True if the API key is valid, False otherwise.
        """
        try:
            response = self.http_client.get(f"{self.base_url}/api/v1/validate")
            if response.status_code == 200:
                logger.debug("API key validation successful")
                return True
            else:
                logger.warning(f"API key validation failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False

    def _check_feature_available(self, feature: str) -> bool:
        """
        Check if a feature is available based on configuration.

        Args:
            feature: Feature name to check.

        Returns:
            True if the feature is available, False otherwise.

        Raises:
            ValueError: If the feature is not available.
        """
        if not self.available_features.get(feature, False):
            raise ValueError(
                f"Feature '{feature}' is not available in your configuration."
            )
        return True

    def search(
        self,
        query: str,
        num_results: int = 10,
        providers: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Perform a metasearch query across multiple search engines.

        Args:
            query: The search query.
            num_results: Number of results to return. Default is 10.
            providers: Optional list of providers to use. If not specified,
                the service will select the best providers for the query.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing search results and metadata.
        """
        self._check_feature_available("metasearch")

        params = {
            "query": query,
            "num_results": num_results,
            **({"providers": providers} if providers else {}),
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/search",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def personalize(
        self,
        results: Union[Dict[str, Any], List[Dict[str, Any]]],
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Personalize search results for a specific user.

        Args:
            results: Search results to personalize. This can be the direct output
                from the `search` method or a list of result items.
            user_id: ID of the user for personalization.
            context: Optional context information for personalization.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing personalized results and metadata.
        """
        self._check_feature_available("personalization")

        params = {
            "results": results,
            "user_id": user_id,
            **({"context": context} if context else {}),
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/personalize",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def recommend(
        self,
        user_id: str,
        items: Optional[List[str]] = None,
        count: int = 10,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate recommendations for a user.

        Args:
            user_id: ID of the user for recommendations.
            items: Optional list of item IDs to base recommendations on.
                If not provided, will use the user's history.
            count: Number of recommendations to generate. Default is 10.
            context: Optional context information for recommendations.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing recommended items and metadata.
        """
        self._check_feature_available("personalization")

        params = {
            "user_id": user_id,
            "count": count,
            **({"items": items} if items else {}),
            **({"context": context} if context else {}),
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/recommend",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def embed(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create vector embeddings for text.

        Args:
            text: Text or list of texts to embed.
            model: Optional embedding model to use. If not specified,
                the service will use the default model.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing embeddings and metadata.
        """
        self._check_feature_available("vector")

        params = {
            "text": text,
            **({"model": model} if model else {}),
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/embed",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def vector_search(
        self,
        query: Union[str, List[float]],
        collection: str,
        num_results: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Perform a vector similarity search.

        Args:
            query: Text query or vector to search with.
            collection: Vector collection to search in.
            num_results: Number of results to return. Default is 10.
            filter: Optional filter to apply to the search.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing search results and metadata.
        """
        self._check_feature_available("vector")

        params = {
            "query": query,
            "collection": collection,
            "num_results": num_results,
            **({"filter": filter} if filter else {}),
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/vector/search",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def upsert_vectors(
        self,
        collection: str,
        vectors: List[Dict[str, Any]],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Add or update vectors in a collection.

        Args:
            collection: Vector collection to add to.
            vectors: List of vector records to add.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing operation results and metadata.
        """
        self._check_feature_available("vector")

        params = {
            "collection": collection,
            "vectors": vectors,
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/vector/upsert",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def schedule(
        self,
        task: str,
        params: Dict[str, Any],
        cron: Optional[str] = None,
        run_at: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Schedule a task for execution.

        Args:
            task: Name of the task to execute.
            params: Parameters for the task.
            cron: Optional cron expression for recurring tasks.
            run_at: Optional ISO timestamp for one-time tasks.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing job information and metadata.
        """
        self._check_feature_available("scheduler")

        if not cron and not run_at:
            run_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 60))

        params = {
            "task": task,
            "params": params,
            **({"cron": cron} if cron else {}),
            **({"run_at": run_at} if run_at else {}),
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/scheduler/jobs",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def monitor(
        self,
        service: str,
        period: str = "1h",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Get monitoring metrics for a service.

        Args:
            service: Name of the service to monitor.
            period: Time period for metrics. Default is 1 hour.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing monitoring metrics and metadata.
        """
        self._check_feature_available("monitor")

        params = {
            "service": service,
            "period": period,
            **kwargs,
        }

        response = self.http_client.get(
            f"{self.base_url}/api/v1/monitor/metrics",
            params=params,
        )

        response.raise_for_status()
        return response.json()

    def backup(
        self,
        source: str,
        destination: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a backup of data.

        Args:
            source: Source to backup.
            destination: Destination for the backup.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing backup information and metadata.
        """
        self._check_feature_available("backup")

        params = {
            "source": source,
            "destination": destination,
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/backup",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def send_notification(
        self,
        user_id: str,
        message: str,
        channel: str = "email",
        priority: str = "normal",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send a notification to a user.

        Args:
            user_id: ID of the user to notify.
            message: Notification message.
            channel: Notification channel. Default is "email".
            priority: Notification priority. Default is "normal".
            **kwargs: Additional parameters to pass to the API.

        Returns:
            Dictionary containing notification status and metadata.
        """
        self._check_feature_available("notifications")

        params = {
            "user_id": user_id,
            "message": message,
            "channel": channel,
            "priority": priority,
            **kwargs,
        }

        response = self.http_client.post(
            f"{self.base_url}/api/v1/notifications/send",
            json=params,
        )

        response.raise_for_status()
        return response.json()

    def __enter__(self):
        """
        Enter the runtime context for the client.

        Returns:
            The client instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context for the client.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Exception traceback if an exception was raised.
        """
        self.http_client.close()
        self.async_http_client.aclose()
