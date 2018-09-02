from module.daemon import Daemon
class Config:
    bot_token="NDc4NTkyMjMxODYzODc3NjU0.DlM8nw.Zp4_kfdLKC2Jlt6myTaUA6mUFSY"
    bot_admin_id=""

    stone = Daemon(
        coinname = "Stone",
        token = "STONE",
        host="127.0.0.1:22324",
        user="someuser",
        password="somepassword",           
        txfee = 0.01,
        exfee=0.03,
        )
    
    coins = [
        Daemon(
            coinname="BitCoin",
            token="BTC",
            host="127.0.0.1:8444",
            user="rC3SseozBr",
            password="Xcil3oeReJBBoAjT9JbB1l",     
            txfee = 0.01,      
            exfee=0.03,
            deposit=True,
            enabled=True
        )
    ]
