                    # Charger les sessions existantes
                    try:
                        if self._session_file.exists():
                            with open(self._session_file, 'r') as f:
                                data = json.load(f)
                                for session_id, session_data in data.items():
                                    created_at_str = session_data.get("created_at", "")
                                    self._sessions[session_id] = SessionInfo(
                                        session_id=session_id,
                                        title=session_data.get("title", ""),
                                        created_at=datetime.fromisoformat(created_at_str) if created_at_str else datetime.now(timezone.utc).isoformat(),
                                    )
                    except Exception as e:
                        _logger.warning(f"Erreur chargement sessions: {e}")