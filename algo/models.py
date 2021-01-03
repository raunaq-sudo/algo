from django.db import models

# Create your models here.
class site_data:
    request_token : str
    access_token : str
    api_secret : str
    api_key : str
    login_url : str
    flag : str
    option_token : str
    ce : bool
    pe : bool
    option_name : str
    entry_price : float
    exit_price: float

class trade_data:
    date : str
    instrument : str
    order_type : str
    ltp : float
    account_value : float


