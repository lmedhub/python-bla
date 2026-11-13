from apps.tasks.infrastructure.mailer import DjangoMailer


def test_sends_a_plain_text_email_from_the_default_address(mailoutbox, settings):
    DjangoMailer().send(to="alice@example.com", subject="Hello", body="Body text")

    [email] = mailoutbox
    assert email.to == ["alice@example.com"]
    assert email.subject == "Hello"
    assert email.body == "Body text"
    assert email.from_email == settings.DEFAULT_FROM_EMAIL
