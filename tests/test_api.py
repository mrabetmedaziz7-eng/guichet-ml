from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.schemas import Prediction

client = TestClient(app)


def test_health_mode_mock():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["mode"] == "mock"


def test_detection_francais():
    r = client.post("/detect-language",
                    json={"text": "Je ne peux plus acceder a mon compte."})
    assert r.status_code == 200
    assert r.json()["language"] == "fr"


def test_detection_arabe():
    r = client.post("/detect-language", json={"text": "لا أستطيع الدخول إلى حسابي"})
    assert r.json()["language"] == "ar"


def test_detection_anglais():
    r = client.post("/detect-language", json={"text": "I cannot log in to my account"})
    assert r.json()["language"] == "en"


def test_texte_trop_court_rejete():
    assert client.post("/detect-language", json={"text": "ab"}).status_code == 422


def test_champ_text_absent():
    assert client.post("/detect-language", json={}).status_code == 422


def test_fournisseur_en_panne(monkeypatch):
    def panne(text):
        raise RuntimeError("secret interne: http://10.0.0.5 hf_xxx")

    monkeypatch.setattr(main.provider, "detect_language", panne)
    r = client.post("/detect-language", json={"text": "Bonjour tout le monde"})
    assert r.status_code == 503
    assert "secret" not in r.text and "hf_" not in r.text


def test_requires_review_si_score_faible(monkeypatch):
    monkeypatch.setattr(main.provider, "detect_language",
                        lambda t: [Prediction(label="fr", score=0.40)])
    r = client.post("/detect-language", json={"text": "Bonjour tout le monde"})
    assert r.json()["requires_review"] is True
