"""Tests for the notifications router."""

from app.models.notification import Notification, NotificationType, NotificationPriority


class TestListNotifications:
    def test_list_all(self, client, agent, sample_notification, agent_headers):
        response = client.get("/notifications/", headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_unread(self, client, agent, sample_notification, agent_headers):
        response = client.get("/notifications/?unread_only=true", headers=agent_headers)
        assert response.status_code == 200

    def test_list_with_limit(self, client, agent, sample_notification, agent_headers):
        response = client.get("/notifications/?limit=1", headers=agent_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 1


class TestMarkNotificationRead:
    def test_mark_read(self, client, agent, sample_notification, agent_headers):
        response = client.post(
            f"/notifications/{sample_notification.id}/read",
            headers=agent_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "marked_as_read"

    def test_mark_read_nonexistent(self, client, agent, agent_headers):
        response = client.post("/notifications/99999/read", headers=agent_headers)
        assert response.status_code == 404


class TestDismissNotification:
    def test_dismiss(self, client, agent, sample_notification, agent_headers):
        response = client.post(
            f"/notifications/{sample_notification.id}/dismiss",
            headers=agent_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "dismissed"

    def test_dismiss_nonexistent(self, client, agent, agent_headers):
        response = client.post("/notifications/99999/dismiss", headers=agent_headers)
        assert response.status_code == 404


class TestDeleteNotification:
    def test_delete_existing(self, client, agent, sample_notification, agent_headers):
        response = client.delete(
            f"/notifications/{sample_notification.id}", headers=agent_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_nonexistent(self, client, agent, agent_headers):
        response = client.delete("/notifications/99999", headers=agent_headers)
        assert response.status_code == 404


class TestNotificationModel:
    def test_create_notification(self, db):
        n = Notification(
            type=NotificationType.CONTRACT_SIGNED,
            priority=NotificationPriority.HIGH,
            title="Contract Signed",
            message="The purchase agreement has been signed",
            property_id=1,
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        assert n.id is not None
        assert n.is_read is False
        assert n.is_dismissed is False

    def test_notification_types(self):
        assert NotificationType.CONTRACT_SIGNED.value == "contract_signed"
        assert NotificationType.NEW_LEAD.value == "new_lead"
        assert NotificationType.PROPERTY_PRICE_CHANGE.value == "property_price_change"
        assert NotificationType.DAILY_DIGEST.value == "daily_digest"

    def test_notification_priorities(self):
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.MEDIUM.value == "medium"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"
