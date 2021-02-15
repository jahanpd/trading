

# model needs to take the following data streams:
# lag variables (batch, features)
# daily time series (batch, timesteps, features) - feat = {log(return), change volume}
# intraday time series (batch, timesteps, log(return))