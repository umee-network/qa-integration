import statistics

class ExchangeRate:
    def __init__(self, denom, price):
        self.denom = denom
        self.price = price
    # Ex. UMEE:0.02
    def ToString(self):
        return self.denom + ":" + self.price

class ExchangeRates:
    def __init__(self, *rates: ExchangeRate):
        self.rates = rates
    # Ex. UMEE:0.02,ATOM:1.00,JUNO:0.50
    def ToString(self):
        str = ""
        for id, r in enumerate(self.rates):
            str = str + r.ToString()
            if(id+1 != len(self.rates)):
                str = str + ","
        return str
    def GetRate(self, denom):
        for r in self.rates:
            if(r.denom == denom):
                return r.price
        return "0.00"
    def Len(self):
        return len(self.rates)
    
    
def median_rates(exchange_rates_set):
    collected_rates = {}
    for exchange_rates in exchange_rates_set:
        for rate in exchange_rates.rates:
            if rate.denom in collected_rates:
                collected_rates[rate.denom].append(float(rate.price))
            else:
                collected_rates[rate.denom] = [float(rate.price)]
    median_rates = {}
    for denom, rates in collected_rates.items():
        median_rates[denom] = statistics.median(rates)
    return median_rates
