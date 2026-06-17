def build_retrieval_query(profile: dict) -> list[dict]:
    cities = profile["cities"]
    retrieval_locations = profile.get("retrieval_locations", cities)

    interests = profile.get("interests", [])
    must_include = profile.get("must_include", [])

    query_items = []

    for index, city in enumerate(cities):
        retrieval_location = (
            retrieval_locations[index]
            if index < len(retrieval_locations)
            else city
        )

        query_items.append({
            "query": f"{city} tourist attractions",
            "location": retrieval_location,
        })

        if interests:
            query_items.append({
                "query": f"{city} {' '.join(interests)}",
                "location": retrieval_location,
            })

        for item in must_include:
            query_items.append({
                "query": f"{city} {item}",
                "location": retrieval_location,
            })

    return query_items