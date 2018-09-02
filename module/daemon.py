class Daemon:
    coinname = ""
    host = ""
    token = ""
    user = ""
    password = ""
    txfee = 0
    exaddr = ""
    enabled = False
    exfee = 0
    deposit = False
    ask = 0
    bid = 0
    last = 0

    def __init__(self,coinname,token,host,user,password,txfee = 0,exfee = 0,exaddr = "",enabled = False,deposit = False):
        self.coinname = coinname
        self.token = token
        self.host = host
        self.user = user
        self.password = password
        self.txfee = txfee
        self.exfee = exfee
        self.exaddr = exaddr
        self.enabled = enabled
        self.deposit = deposit
