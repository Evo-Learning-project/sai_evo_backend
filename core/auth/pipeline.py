def get_user_picture(backend, strategy, details, response, user=None, *args, **kwargs):
    url = None
    # if backend.name == "facebook":
    #     url = "https://graph.facebook.com/%s/picture?type=large" % response["id"]
    # if backend.name == "twitter":
    #     url = response.get("profile_image_url", "").replace("_normal", "")
    if backend.name == "google-oauth2":
        url = response["picture"]
    if url:
        user.avatar_url = url
        user.save()
