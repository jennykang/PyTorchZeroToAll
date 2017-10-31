# https://github.com/spro/practical-pytorch
import time
import os

import torch
import torch.nn as nn
from torch.autograd import Variable
from torch.utils.data import DataLoader

from text_loader import TextDataset

hidden_size = 100
n_layers = 3
batch_size = 32
n_epochs = 100
filename = 'shakespeare.txt'
n_characters = 128  # Ascii


def char2tensor(string):
    tensor = [ord(c) for c in string]
    tensor = torch.LongTensor(tensor)

    if torch.cuda.is_available():
        tensor = tensor.cuda()

    return Variable(tensor)

class RNN(nn.Module):

    def __init__(self, input_size, hidden_size, output_size, n_layers=1):
        super(RNN, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.n_layers = n_layers

        self.embedding = nn.Embedding(input_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size, n_layers)
        self.decoder = nn.Linear(hidden_size, output_size)

    def forward(self, input, hidden):
        input = self.embedding(input.view(1, -1))
        output, hidden = self.gru(input.view(1, 1, -1), hidden)
        output = self.decoder(output.view(1, -1))
        return output, hidden

    def init_hidden(self):
        if torch.cuda.is_available():
            hidden = torch.zeros(self.n_layers, 1, self.hidden_size).cuda()
        else:
            hidden = torch.zeros(self.n_layers, 1, self.hidden_size)

        return Variable(hidden)


def generate(decoder, prime_str='A', predict_len=100, temperature=0.8):
    hidden = decoder.init_hidden()
    prime_input = char2tensor(prime_str)
    predicted = prime_str

    # Use priming string to "build up" hidden state
    for p in range(len(prime_str) - 1):
        _, hidden = decoder(prime_input[p], hidden)

    inp = prime_input[-1]

    for p in range(predict_len):
        output, hidden = decoder(inp, hidden)

        # Sample from the network as a multinomial distribution
        output_dist = output.data.view(-1).div(temperature).exp()
        top_i = torch.multinomial(output_dist, 1)[0]

        # Add predicted character to string and use as next input
        predicted_char = chr(top_i)
        predicted += predicted_char
        inp = char2tensor(predicted_char)

    return predicted


def train(line):
    input = char2tensor(line[:-1])
    target = char2tensor(line[1:])

    hidden = decoder.init_hidden()
    decoder.zero_grad()
    loss = 0

    for c in range(len(input)):
        output, hidden = decoder(input[c], hidden)
        loss += criterion(output, target[c])

    loss.backward()
    decoder_optimizer.step()

    return loss.data[0] / len(input)


def save():
    save_filename = os.path.splitext(os.path.basename(filename))[0] + '.pt'
    torch.save(decoder, save_filename)
    print('Saved as %s' % save_filename)


decoder = RNN(n_characters, hidden_size, n_characters, n_layers)
if torch.cuda.is_available():
    decoder.cuda()

decoder_optimizer = torch.optim.Adam(decoder.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()


train_loader = DataLoader(dataset=TextDataset(),
                              batch_size=batch_size,
                              shuffle=True)


try:
    print("Training for %d epochs..." % n_epochs)
    for epoch in range(1, n_epochs+1):
        for i, (lines, _) in enumerate(train_loader):
            for line in lines:
                loss = train(line)

            print('[(%d %d%%) %.4f]' % (epoch, epoch / n_epochs * 100, loss))
            print(generate(decoder, 'Wh', 100), '\n')

    print("Saving...")
    save()

except KeyboardInterrupt:
    print("Saving before quit...")
    save()