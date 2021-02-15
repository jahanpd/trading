import torch as T
import torch.nn as nn

class recurrent_layer(nn.Module:
    def __init__(
        self,
        kernel_size=7,
        in_channels=3,  # [returns, delta_vol, returns index]
        out_channels=3,
        layers=2,
    ):
        super(recurrent_layer, self).__init__()

        self.kernel_size = kernel_size
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.layers = 2
        self.hidden = hidden
        self.conv = nn.Conv1d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size
        )
        self.rnn = nn.LSTM(
            input_size=out_channels,
            hidden_size=out_channels
            num_layers=layers,
            bidirectional=True
        )
        self.ffn = nn.Sequential([
            nn.Linear(out_channels*2, out_channels),
            nn.Softplus(),
            nn.Linear(out_channels, 1)
        ])
    
    def forward(self, x):
        # x input is (b, features, seq)
        x = self.conv(x)  # (b, out_c, seq - k)
        xs = x.shape
        x = x.permute(2, 0, 1)  # (seq, b, out_c)
        h0 = T.randn(self.layers*2, xs[0], self.hidden)
        c0 = T.randn(self.layers*2, xs[0], self.hidden)
        out, (hn, cn) = self.rnn(x, (h0, c0))  # (seq, b, out_c*2)
        return self.ffn(out[-1, :, :])  # (b, 1)


class model(nn.Module:
    def __init__(
        self,
    ):
        super(model, self).__init__()

        self.intraday5 = recurrent_layer(
            kernel_size=5,
            in_channels=3,  # [returns, delta_vol, returns index]
            out_channels=3,
            layers=2,)

        self.intraday100 = recurrent_layer(
            kernel_size=100,
            in_channels=3,  # [returns, delta_vol, returns index]
            out_channels=3,
            layers=2,)
        
        self.close5 = recurrent_layer(
            kernel_size=5,
            in_channels=3,  # [returns, delta_vol, returns index]
            out_channels=3,
            layers=2,)

        self.close100 = recurrent_layer(
            kernel_size=100,
            in_channels=3,  # [returns, delta_vol, returns index]
            out_channels=3,
            layers=2,)

        self.ffn = nn.Sequential(
            nn.Linear(4+3, 7),
            nn.Softplus(),
            nn.Linear(7, 7),
            nn.Softplus(),
            nn.Linear(7, 2),
        )

        def forward(self, close, intraday, technicals):
            
            i100 = self.intraday100(intraday)
            i5 = self.intraday5(intraday)
            c100 = self.close100(close)
            c5 = self.close5(close)

            h = T.cat([
                i100, i5, c100, c5, technicals
            ], 1)  # (b, 7)

            dist = self.ffn(h)  # (b, 2)
            mu = dist[:, 0]
            var = T.exp(dist[:, 1])

            return mu, var
