from app.infrastructure.persistence.plex.repo.plexUserRepo import PlexUserRepo


def test_plex_user_repo_exposes_port_contract_methods() -> None:
    required_methods = [
        "get_active_users",
        "get_user_by_id",
        "get_user_by_name",
        "get_user_by_plex_token",
        "create_user",
        "update_user",
        "delete_user",
    ]

    for method_name in required_methods:
        assert hasattr(PlexUserRepo, method_name), f"Missing method: {method_name}"
