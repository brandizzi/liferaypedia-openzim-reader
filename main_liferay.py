from liferaypedia_liferay_user import LiferayWebUser

user = LiferayWebUser("http://localhost:8080", "test@liferay.com", "t")
try:
    user.login()
    user.post_web_content(
        "My title",
        "<p>Body</p>",
        "my-friendly-url",
        [],
        site_friendly_url="guest",
    )
finally:
    user.close()
