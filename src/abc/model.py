import abc

class BalisongDistributionBot(abc.ABC):
    @classmethod
    async def send_bit_for_emails(self):
        """
        Отправляет бит на все емейлы, добавленные пользователем,
        собирает
        :return:
        """
        ...