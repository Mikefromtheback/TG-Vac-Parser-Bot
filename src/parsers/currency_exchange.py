import config
import currencyapicom
import datetime
import aiohttp


class CurrencyExchange:
    __client = currencyapicom.Client(config.KEY)
    __data = __client.latest(base_currency='USD',
                             currencies=['AZN', 'BYN', 'EUR', 'GEL', 'KGS', 'KZT', 'RUB', 'UAH', 'USD', 'UZS'])['data']
    __last_update = datetime.datetime.now()

    @staticmethod
    async def __get_exchange_rates():
        try:
            async with aiohttp.ClientSession() as session:
                url = f'https://api.currencyapi.com/v3/latest?apikey={config.KEY}&currencies=AZN%2CBYR%2CEUR%2CGEL%2CKGS%2CKZT%2CRUB%2CUAH%2CUZS'
                async with session.get(url) as resp:
                    if resp.status == 200:
                        CurrencyExchange.__data = await resp.json()['data']
                        CurrencyExchange.__last_update = datetime.datetime.now()
                    else:
                        print(f'[WARNING] currency api connection error, response code is {resp.status}, url is {url}')
        except aiohttp.ClientConnectorError as e:
            print('[WARNING] connection with currency api error', str(e))

    @staticmethod
    async def convert(value, code):
        delta = datetime.datetime.now() - CurrencyExchange.__last_update
        # request currency one of 24 hours because we have 300 requests per month
        if delta.total_seconds() > 86400:
            await CurrencyExchange.__get_exchange_rates()
        if code not in CurrencyExchange.__data:
            print('[WARNING] currency data haven`t exchange rates, currency code is ' + str(code))
            return None
        usd_value = int(value / CurrencyExchange.__data[code]['value'] / 100) * 100
        return usd_value
