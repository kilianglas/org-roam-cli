from __future__ import annotations

from thefuzz import fuzz

from .models import Node, SearchResult


def fuzzy_search(
    query: str,
    nodes: list[Node],
    threshold: int = 40,
    limit: int = 20,
) -> list[SearchResult]:
    """Fuzzy search over node titles and aliases. Returns results sorted by score."""
    results: list[SearchResult] = []
    query_lower = query.lower()

    for node in nodes:
        best_score = 0

        if node.title:
            title_score = fuzz.partial_ratio(query_lower, node.title.lower())
            best_score = max(best_score, title_score)

            # Boost exact substring matches
            if query_lower in node.title.lower():
                best_score = max(best_score, 95)

        for alias in node.aliases:
            alias_score = fuzz.partial_ratio(query_lower, alias.lower())
            best_score = max(best_score, alias_score)

            if query_lower in alias.lower():
                best_score = max(best_score, 95)

        if best_score >= threshold:
            results.append(SearchResult(node=node, score=best_score))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
