from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonThrottle(AnonRateThrottle):
    pass


class UserThrottle(UserRateThrottle):
    pass


class LoginThrottle(AnonRateThrottle):
    scope = "login"
