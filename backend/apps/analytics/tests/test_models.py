import pytest

from apps.analytics.tests.factories import RedirectEventFactory


@pytest.mark.django_db
def test_redirect_event_keeps_nullable_listing_reference_without_personal_fields():
    event = RedirectEventFactory.create()

    assert event.listing_id is not None
    assert not {"session_id", "referer", "user_agent", "ip"} & {field.name for field in event._meta.fields}
