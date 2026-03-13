"""
neo4j_client.py
Thin wrapper around the official Neo4j Python driver.

Provides a singleton Neo4jClient with a context-managed session helper
and a raw query executor. All Cypher statements elsewhere in the codebase
should go through this client.

Usage:
    client = get_neo4j_client()
    with client.session() as session:
        session.run("MATCH (n) RETURN count(n)")
"""
from contextlib import contextmanager
from typing import Generator

from neo4j import GraphDatabase, Session

from app.core.config import settings

_client_instance = None


class Neo4jClient:
    """
    Manages a Neo4j driver and exposes a session context manager.

    The driver is thread-safe and should be a singleton for the lifetime
    of the process.
    """

    def __init__(
        self,
        uri: str = settings.NEO4J_URI,
        user: str = settings.NEO4J_USER,
        password: str = settings.NEO4J_PASSWORD,
    ):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"Neo4jClient connected to {uri}")

    @contextmanager
    def session(self, **kwargs) -> Generator[Session, None, None]:
        """
        Yield a Neo4j Session, ensuring it is closed afterward.

        Example:
            with client.session() as s:
                s.run("MATCH (n) RETURN n LIMIT 1")
        """
        s = self._driver.session(**kwargs)
        try:
            yield s
        finally:
            s.close()

    def run(self, cypher: str, **params):
        """
        Execute a single Cypher statement and return all records as a list.

        Args:
            cypher: Cypher query string.
            **params: Named parameters referenced in the query.

        Returns:
            List of neo4j.Record objects.
        """
        with self.session() as s:
            result = s.run(cypher, **params)
            return list(result)

    def close(self):
        """Close the underlying driver. Call on app shutdown."""
        self._driver.close()


def get_neo4j_client() -> Neo4jClient:
    """Return the process-level singleton Neo4jClient."""
    global _client_instance
    if _client_instance is None:
        _client_instance = Neo4jClient()
    return _client_instance
