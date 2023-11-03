class UserService:
    def __init__(self, users: list[dict[str, str]]):
        self.__users = {}
        for user in users:
            self.__users[user['name'].strip().lower()] = user['password']

    def get_users(self) -> dict[str, str]:
        return self.__users

    def has_user(self, username: str) -> bool:
        return username in self.__users

    def get_password_by_username(self, name: str) -> str:
        return self.__users.get(name, None)